"""
Phase 4: Train Hybrid ResNet-Environmental Model

Main training script for the hybrid model with:
- Mixed precision training (FP16)
- Per-domain metrics (ASVspoof vs Real-world)
- Multi-task learning (binary + multiclass)
- Class weighting for imbalanced data
- Efficient HDF5 data loading
- Checkpointing and logging

Usage:
    python train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 128 --epochs 20
"""

import argparse
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.amp import autocast
from torch.cuda.amp import GradScaler
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase3.multi_task_loss import MultiTaskLoss, compute_class_weights_from_labels
from phase4.hybrid_dataset import HybridDataset, collate_fn
from utils_metrics import eer_and_auc, confusion


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train Hybrid ResNet-Environmental Model')
    
    # Data paths
    parser.add_argument('--train_manifest', type=str, required=True,
                       help='Path to training manifest CSV')
    parser.add_argument('--val_manifest', type=str, required=True,
                       help='Path to validation manifest CSV')
    parser.add_argument('--spectrogram_h5', type=str, required=True,
                       help='Path to spectrogram HDF5 file (logmel_packed.h5)')
    parser.add_argument('--environmental_h5', type=str, required=True,
                       help='Path to environmental HDF5 file (environmental_packed.h5)')
    
    # Model and training
    parser.add_argument('--output_dir', type=str, default='models_saved',
                       help='Directory to save models and logs')
    parser.add_argument('--batch_size', type=int, default=64,
                       help='Batch size (default: 64, optimized for RTX 3050 6GB)')
    parser.add_argument('--epochs', type=int, default=20,
                       help='Number of epochs (default: 20)')
    parser.add_argument('--lr', type=float, default=1e-3,
                       help='Initial learning rate (default: 1e-3)')
    parser.add_argument('--weight_decay', type=float, default=1e-4,
                       help='Weight decay (default: 1e-4)')
    
    # Loss weights
    parser.add_argument('--binary_weight', type=float, default=0.7,
                       help='Weight for binary classification loss (default: 0.7)')
    parser.add_argument('--multiclass_weight', type=float, default=0.3,
                       help='Weight for multiclass classification loss (default: 0.3)')
    
    # Data loading
    parser.add_argument('--num_workers', type=int, default=8,
                       help='Number of data loading workers (default: 8)')
    parser.add_argument('--pin_memory', action='store_true', default=True,
                       help='Pin memory for faster GPU transfer')
    parser.add_argument('--prefetch_factor', type=int, default=2,
                       help='Prefetch factor for data loading (default: 2)')
    parser.add_argument('--persistent_workers', action='store_true', default=True,
                       help='Keep workers alive between epochs')
    
    # Training options
    parser.add_argument('--mixed_precision', action='store_true', default=True,
                       help='Use mixed precision training (FP16)')
    parser.add_argument('--gradient_clip', type=float, default=1.0,
                       help='Gradient clipping value (default: 1.0)')
    parser.add_argument('--use_class_weights', action='store_true', default=True,
                       help='Use class weights for imbalanced data')
    
    # Evaluation
    parser.add_argument('--val_eval_fraction', type=float, default=0.15,
                       help='Fraction of validation set to evaluate every epoch (default: 0.15)')
    parser.add_argument('--full_eval_interval', type=int, default=5,
                       help='Run full validation evaluation every N epochs (default: 5)')
    
    # Checkpointing
    parser.add_argument('--save_interval', type=int, default=5,
                       help='Save checkpoint every N epochs (default: 5)')
    parser.add_argument('--resume', type=str, default=None,
                       help='Path to checkpoint to resume from')
    
    return parser.parse_args()


def compute_class_weights(manifest_df):
    """
    Compute class weights from manifest.
    
    Returns:
        binary_weights: [bonafide_weight, spoof_weight]
        multiclass_weights: [bonafide, synthesis, conversion, replay]
    """
    # Binary class weights
    binary_labels = (manifest_df['label'] == 'spoof').astype(int).values
    binary_weights = compute_class_weights_from_labels(binary_labels, 2)
    
    # Multi-class weights
    attack_type_map = {
        'bonafide': 0,
        'synthesis': 1,
        'conversion': 2,
        'replay': 3
    }
    multiclass_labels = manifest_df['attack_type'].map(attack_type_map).fillna(0).astype(int).values
    multiclass_weights = compute_class_weights_from_labels(multiclass_labels, 4)
    
    return binary_weights, multiclass_weights


def evaluate_model(model, dataloader, device, loss_fn, domain_filter=None):
    """
    Evaluate model on a dataset.
    
    Args:
        model: Model to evaluate
        dataloader: DataLoader for evaluation
        device: Device to run on
        loss_fn: Loss function
        domain_filter: Optional domain filter ('ASVspoof' or 'RealWorld')
    
    Returns:
        metrics: Dictionary of metrics
    """
    model.eval()
    
    all_binary_preds = []
    all_binary_labels = []
    all_multiclass_preds = []
    all_multiclass_labels = []
    all_domains = []
    
    total_loss = 0.0
    binary_loss_sum = 0.0
    multiclass_loss_sum = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc='Evaluating', leave=False):
            spectrograms = batch['spectrogram'].to(device)
            environmental = batch['environmental'].to(device)
            binary_labels = batch['binary_label'].to(device)
            multiclass_labels = batch['multiclass_label'].to(device)
            domains = batch['domain']
            
            # Filter by domain if specified
            if domain_filter:
                mask = [d in domain_filter for d in domains]
                if not any(mask):
                    continue
                spectrograms = spectrograms[mask]
                environmental = environmental[mask]
                binary_labels = binary_labels[mask]
                multiclass_labels = multiclass_labels[mask]
                domains = [d for d, m in zip(domains, mask) if m]
            
            # Forward pass
            with autocast('cuda'):
                binary_logits, multiclass_logits = model(spectrograms, environmental)
                loss, binary_loss, multiclass_loss = loss_fn(
                    binary_logits, multiclass_logits, binary_labels, multiclass_labels
                )
            
            total_loss += loss.item()
            binary_loss_sum += binary_loss.item()
            multiclass_loss_sum += multiclass_loss.item()
            n_batches += 1
            
            # Get predictions
            binary_probs = torch.softmax(binary_logits, dim=1)[:, 1].cpu().numpy()
            binary_preds = torch.argmax(binary_logits, dim=1).cpu().numpy()
            multiclass_preds = torch.argmax(multiclass_logits, dim=1).cpu().numpy()
            
            all_binary_preds.extend(binary_probs)
            all_binary_labels.extend(binary_labels.cpu().numpy())
            all_multiclass_preds.extend(multiclass_preds)
            all_multiclass_labels.extend(multiclass_labels.cpu().numpy())
            all_domains.extend(domains)
    
    # Compute metrics
    all_binary_preds = np.array(all_binary_preds)
    all_binary_labels = np.array(all_binary_labels)
    all_multiclass_preds = np.array(all_multiclass_preds)
    all_multiclass_labels = np.array(all_multiclass_labels)
    
    # Binary metrics
    eer, auc_score = eer_and_auc(all_binary_labels, all_binary_preds)
    # Binary accuracy: compare predictions (prob > 0.5) with labels
    binary_preds_binary = (all_binary_preds > 0.5).astype(int)
    binary_accuracy = np.mean(binary_preds_binary == all_binary_labels)
    
    # Multi-class accuracy
    multiclass_accuracy = np.mean(all_multiclass_preds == all_multiclass_labels)
    
    metrics = {
        'loss': total_loss / n_batches if n_batches > 0 else 0.0,
        'binary_loss': binary_loss_sum / n_batches if n_batches > 0 else 0.0,
        'multiclass_loss': multiclass_loss_sum / n_batches if n_batches > 0 else 0.0,
        'binary_eer': eer,
        'binary_auc': auc_score,
        'binary_accuracy': binary_accuracy,
        'multiclass_accuracy': multiclass_accuracy,
        'n_samples': len(all_binary_labels)
    }
    
    return metrics


def train_epoch(model, dataloader, device, optimizer, loss_fn, scaler, args):
    """Train for one epoch."""
    model.train()
    
    total_loss = 0.0
    binary_loss_sum = 0.0
    multiclass_loss_sum = 0.0
    n_batches = 0
    
    pbar = tqdm(dataloader, desc='Training')
    for batch in pbar:
        spectrograms = batch['spectrogram'].to(device, non_blocking=True)
        environmental = batch['environmental'].to(device, non_blocking=True)
        binary_labels = batch['binary_label'].to(device, non_blocking=True)
        multiclass_labels = batch['multiclass_label'].to(device, non_blocking=True)
        
        # Forward pass
        optimizer.zero_grad()
        
        with autocast('cuda', enabled=args.mixed_precision):
            binary_logits, multiclass_logits = model(spectrograms, environmental)
            loss, binary_loss, multiclass_loss = loss_fn(
                binary_logits, multiclass_logits, binary_labels, multiclass_labels
            )
        
        # Backward pass
        if args.mixed_precision:
            scaler.scale(loss).backward()
            if args.gradient_clip > 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            if args.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
            optimizer.step()
        
        total_loss += loss.item()
        binary_loss_sum += binary_loss.item()
        multiclass_loss_sum += multiclass_loss.item()
        n_batches += 1
        
        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'b_loss': f'{binary_loss.item():.4f}',
            'mc_loss': f'{multiclass_loss.item():.4f}'
        })
    
    return {
        'loss': total_loss / n_batches,
        'binary_loss': binary_loss_sum / n_batches,
        'multiclass_loss': multiclass_loss_sum / n_batches
    }


def main():
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    log_dir = os.path.join(args.output_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n[DEVICE] Using device: {device}")
    if device.type == 'cuda':
        print(f"[GPU] {torch.cuda.get_device_name(0)}")
        print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    # Load manifests
    print(f"\n[DATA] Loading manifests...")
    train_df = pd.read_csv(args.train_manifest, low_memory=False)
    val_df = pd.read_csv(args.val_manifest, low_memory=False)
    
    print(f"[DATA] Train samples: {len(train_df)}")
    print(f"[DATA] Val samples: {len(val_df)}")
    
    # Check domain distribution
    print(f"\n[DATA] Train domain distribution:")
    print(train_df['dataset'].value_counts())
    print(f"\n[DATA] Val domain distribution:")
    print(val_df['dataset'].value_counts())
    
    # Create datasets
    print(f"\n[DATASET] Creating datasets...")
    # Unified manifest path for index mapping (HDF5 indices are based on unified manifest)
    unified_manifest_path = 'data/manifests/unified_manifest.csv'
    if not os.path.exists(unified_manifest_path):
        print(f"[WARNING] Unified manifest not found at {unified_manifest_path}")
        unified_manifest_path = None
    
    train_dataset = HybridDataset(
        train_df,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=unified_manifest_path
    )
    val_dataset = HybridDataset(
        val_df,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=unified_manifest_path
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=args.pin_memory,
        prefetch_factor=args.prefetch_factor if args.num_workers > 0 else None,
        persistent_workers=args.persistent_workers if args.num_workers > 0 else False,
        collate_fn=collate_fn
    )
    
    # Validation loader (full for periodic eval, subset for quick eval)
    val_loader_full = DataLoader(
        val_dataset,
        batch_size=args.batch_size * 2,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=args.pin_memory,
        prefetch_factor=args.prefetch_factor if args.num_workers > 0 else None,
        persistent_workers=args.persistent_workers if args.num_workers > 0 else False,
        collate_fn=collate_fn
    )
    
    # Create subset for quick evaluation
    val_subset_size = int(len(val_dataset) * args.val_eval_fraction)
    val_subset_indices = np.random.choice(len(val_dataset), val_subset_size, replace=False)
    val_subset = torch.utils.data.Subset(val_dataset, val_subset_indices)
    val_loader_quick = DataLoader(
        val_subset,
        batch_size=args.batch_size * 2,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=args.pin_memory,
        prefetch_factor=args.prefetch_factor if args.num_workers > 0 else None,
        persistent_workers=args.persistent_workers if args.num_workers > 0 else False,
        collate_fn=collate_fn
    )
    
    # Compute class weights
    if args.use_class_weights:
        print(f"\n[WEIGHTS] Computing class weights...")
        binary_weights, multiclass_weights = compute_class_weights(train_df)
        print(f"[WEIGHTS] Binary weights: {binary_weights}")
        print(f"[WEIGHTS] Multiclass weights: {multiclass_weights}")
    else:
        binary_weights = None
        multiclass_weights = None
    
    # Create model
    print(f"\n[MODEL] Creating model...")
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] Total parameters: {total_params:,}")
    print(f"[MODEL] Trainable parameters: {trainable_params:,}")
    
    # Create loss function
    loss_fn = MultiTaskLoss(
        binary_weight=args.binary_weight,
        multiclass_weight=args.multiclass_weight,
        binary_class_weights=binary_weights,
        multiclass_class_weights=multiclass_weights
    ).to(device)
    
    # Create optimizer
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
        betas=(0.9, 0.999)
    )
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        verbose=True
    )
    
    # Mixed precision scaler
    scaler = GradScaler() if args.mixed_precision else None
    
    # Resume from checkpoint if specified
    start_epoch = 0
    best_val_eer = float('inf')
    if args.resume:
        print(f"\n[RESUME] Loading checkpoint from {args.resume}")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_eer = checkpoint.get('best_val_eer', float('inf'))
        if scaler and 'scaler_state_dict' in checkpoint:
            scaler.load_state_dict(checkpoint['scaler_state_dict'])
        print(f"[RESUME] Resuming from epoch {start_epoch}")
    
    # Training logs
    logs = []
    
    print(f"\n[TRAINING] Starting training...")
    print(f"[TRAINING] Epochs: {args.epochs}")
    print(f"[TRAINING] Batch size: {args.batch_size}")
    print(f"[TRAINING] Mixed precision: {args.mixed_precision}")
    print(f"[TRAINING] Learning rate: {args.lr}")
    print("="*80)
    
    for epoch in range(start_epoch, args.epochs):
        epoch_start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"EPOCH {epoch+1}/{args.epochs}")
        print(f"{'='*80}")
        
        # Train
        train_metrics = train_epoch(model, train_loader, device, optimizer, loss_fn, scaler, args)
        
        # Evaluate (quick eval every epoch, full eval periodically)
        if (epoch + 1) % args.full_eval_interval == 0 or epoch == 0:
            print(f"\n[EVAL] Running full validation evaluation...")
            val_metrics = evaluate_model(model, val_loader_full, device, loss_fn)
            
            # Per-domain evaluation
            val_metrics_asv = evaluate_model(model, val_loader_full, device, loss_fn, domain_filter=['LA', 'DF', 'PA'])
            val_metrics_real = evaluate_model(model, val_loader_full, device, loss_fn, domain_filter=['RealWorld'])
            
            val_metrics['asvspoof_eer'] = val_metrics_asv['binary_eer']
            val_metrics['asvspoof_auc'] = val_metrics_asv['binary_auc']
            val_metrics['realworld_eer'] = val_metrics_real['binary_eer']
            val_metrics['realworld_auc'] = val_metrics_real['binary_auc']
        else:
            print(f"\n[EVAL] Running quick validation evaluation ({args.val_eval_fraction*100:.0f}% of val set)...")
            val_metrics = evaluate_model(model, val_loader_quick, device, loss_fn)
            val_metrics['asvspoof_eer'] = None
            val_metrics['asvspoof_auc'] = None
            val_metrics['realworld_eer'] = None
            val_metrics['realworld_auc'] = None
        
        # Update learning rate
        scheduler.step(val_metrics['loss'])
        current_lr = optimizer.param_groups[0]['lr']
        
        # Print metrics
        print(f"\n[EPOCH {epoch+1}] Training:")
        print(f"  Loss: {train_metrics['loss']:.4f} (Binary: {train_metrics['binary_loss']:.4f}, Multiclass: {train_metrics['multiclass_loss']:.4f})")
        print(f"\n[EPOCH {epoch+1}] Validation:")
        print(f"  Loss: {val_metrics['loss']:.4f} (Binary: {val_metrics['binary_loss']:.4f}, Multiclass: {val_metrics['multiclass_loss']:.4f})")
        print(f"  Binary EER: {val_metrics['binary_eer']*100:.2f}%")
        print(f"  Binary AUC: {val_metrics['binary_auc']:.4f}")
        print(f"  Binary Accuracy: {val_metrics['binary_accuracy']*100:.2f}%")
        print(f"  Multiclass Accuracy: {val_metrics['multiclass_accuracy']*100:.2f}%")
        if val_metrics['asvspoof_eer'] is not None:
            print(f"  ASVspoof Domain EER: {val_metrics['asvspoof_eer']*100:.2f}%")
            print(f"  ASVspoof Domain AUC: {val_metrics['asvspoof_auc']:.4f}")
            print(f"  Real-world Domain EER: {val_metrics['realworld_eer']*100:.2f}%")
            print(f"  Real-world Domain AUC: {val_metrics['realworld_auc']:.4f}")
        print(f"  Learning Rate: {current_lr:.2e}")
        
        # Log metrics
        log_entry = {
            'epoch': epoch + 1,
            'train_loss': train_metrics['loss'],
            'train_binary_loss': train_metrics['binary_loss'],
            'train_multiclass_loss': train_metrics['multiclass_loss'],
            'val_loss': val_metrics['loss'],
            'val_binary_loss': val_metrics['binary_loss'],
            'val_multiclass_loss': val_metrics['multiclass_loss'],
            'val_binary_eer': val_metrics['binary_eer'],
            'val_binary_auc': val_metrics['binary_auc'],
            'val_binary_accuracy': val_metrics['binary_accuracy'],
            'val_multiclass_accuracy': val_metrics['multiclass_accuracy'],
            'val_asvspoof_eer': val_metrics.get('asvspoof_eer'),
            'val_asvspoof_auc': val_metrics.get('asvspoof_auc'),
            'val_realworld_eer': val_metrics.get('realworld_eer'),
            'val_realworld_auc': val_metrics.get('realworld_auc'),
            'learning_rate': current_lr,
            'epoch_time': time.time() - epoch_start_time
        }
        logs.append(log_entry)
        
        # Save checkpoint
        is_best = val_metrics['binary_eer'] < best_val_eer
        if is_best:
            best_val_eer = val_metrics['binary_eer']
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_val_eer': best_val_eer,
            'val_metrics': val_metrics,
            'args': vars(args)
        }
        if scaler:
            checkpoint['scaler_state_dict'] = scaler.state_dict()
        
        # Save best model
        if is_best:
            best_path = os.path.join(args.output_dir, 'hybrid_resnet_environmental_best.pth')
            torch.save(checkpoint, best_path)
            print(f"\n[CHECKPOINT] Saved best model (EER: {best_val_eer*100:.2f}%) -> {best_path}")
        
        # Save periodic checkpoint
        if (epoch + 1) % args.save_interval == 0:
            checkpoint_path = os.path.join(args.output_dir, f'hybrid_resnet_environmental_epoch_{epoch+1}.pth')
            torch.save(checkpoint, checkpoint_path)
            print(f"[CHECKPOINT] Saved checkpoint -> {checkpoint_path}")
        
        # Save training logs
        logs_df = pd.DataFrame(logs)
        logs_path = os.path.join(log_dir, 'training_hybrid_model.csv')
        logs_df.to_csv(logs_path, index=False)
        
        epoch_time = time.time() - epoch_start_time
        print(f"\n[EPOCH {epoch+1}] Completed in {epoch_time/60:.1f} minutes")
    
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"Best validation EER: {best_val_eer*100:.2f}%")
    print(f"Final model saved to: {os.path.join(args.output_dir, 'hybrid_resnet_environmental_best.pth')}")
    print(f"Training logs saved to: {logs_path}")
    
    # Cleanup
    train_dataset.close()
    val_dataset.close()


if __name__ == '__main__':
    main()

