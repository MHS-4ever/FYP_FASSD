"""
Phase 4: FAST Training Script for Hybrid Model

Optimized for HDF5 random access:
- ChunkedDataLoader: Reads batches directly, not sample-by-sample
- SortedBatchSampler: Minimizes disk seeks by grouping nearby HDF5 indices
- Single-threaded HDF5: Avoids multiprocessing overhead with h5py

Expected speedup: 10-50x faster than standard DataLoader with num_workers

Usage:
    python train_hybrid_fast.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 C:/FYP/data/features/logmel_packed.h5 --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 256 --epochs 20
"""

import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.amp import autocast
from torch.amp import GradScaler
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase3.multi_task_loss import MultiTaskLoss, compute_class_weights_from_labels
from phase4.hybrid_dataset_fast import FastHybridDataset, ChunkedDataLoader
from utils_metrics import eer_and_auc


def parse_args():
    parser = argparse.ArgumentParser(description='FAST Train Hybrid Model')
    
    # Data paths
    parser.add_argument('--train_manifest', type=str, required=True)
    parser.add_argument('--val_manifest', type=str, required=True)
    parser.add_argument('--spectrogram_h5', type=str, required=True)
    parser.add_argument('--environmental_h5', type=str, required=True)
    
    # Model and training
    parser.add_argument('--output_dir', type=str, default='models_saved')
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight_decay', type=float, default=1e-4)
    
    # Loss weights
    parser.add_argument('--binary_weight', type=float, default=0.7)
    parser.add_argument('--multiclass_weight', type=float, default=0.3)
    
    # Training options
    parser.add_argument('--mixed_precision', action='store_true', default=True)
    parser.add_argument('--gradient_clip', type=float, default=1.0)
    parser.add_argument('--use_class_weights', action='store_true', default=True)
    parser.add_argument('--profile_batches', type=int, default=0,
                        help='If >0, profile first N train batches (load_ms, h2d_ms, step_ms). Adds slight overhead.')
    
    # Evaluation
    parser.add_argument('--val_eval_fraction', type=float, default=0.15)
    parser.add_argument('--full_eval_interval', type=int, default=5)
    
    # Checkpointing
    parser.add_argument('--save_interval', type=int, default=5)
    parser.add_argument('--resume', type=str, default=None)
    
    return parser.parse_args()


def compute_class_weights(manifest_df):
    """Compute class weights from manifest."""
    binary_labels = (manifest_df['label'] == 'spoof').astype(int).values
    binary_weights = compute_class_weights_from_labels(binary_labels, 2)
    
    attack_type_map = {'bonafide': 0, 'synthesis': 1, 'conversion': 2, 'replay': 3}
    multiclass_labels = manifest_df['attack_type'].map(attack_type_map).fillna(0).astype(int).values
    multiclass_weights = compute_class_weights_from_labels(multiclass_labels, 4)
    
    return binary_weights, multiclass_weights


def train_epoch(model, dataloader, device, optimizer, loss_fn, scaler, args):
    """Train for one epoch using ChunkedDataLoader."""
    model.train()
    
    total_loss = 0.0
    binary_loss_sum = 0.0
    multiclass_loss_sum = 0.0
    n_batches = 0
    
    pbar = tqdm(dataloader, desc='Training')
    prof_n = int(getattr(args, 'profile_batches', 0) or 0)
    prof_count = 0
    prof_load_ms = []
    prof_h2d_ms = []
    prof_step_ms = []
    for batch in pbar:
        do_profile = (prof_count < prof_n) and (device.type == 'cuda')
        if do_profile:
            torch.cuda.synchronize()
            t_h2d0 = time.perf_counter()
        # Data is already batched from ChunkedDataLoader
        spectrograms = batch['spectrogram'].to(device, non_blocking=True)
        environmental = batch['environmental'].to(device, non_blocking=True)
        binary_labels = batch['binary_label'].to(device, non_blocking=True)
        multiclass_labels = batch['multiclass_label'].to(device, non_blocking=True)
        load_ms = float(batch.get('_load_ms', 0.0))
        
        if do_profile:
            torch.cuda.synchronize()
            h2d_ms = (time.perf_counter() - t_h2d0) * 1000.0
            t_step0 = time.perf_counter()
        
        optimizer.zero_grad()
        
        with autocast('cuda', enabled=args.mixed_precision):
            binary_logits, multiclass_logits = model(spectrograms, environmental)
            loss, binary_loss, multiclass_loss = loss_fn(
                binary_logits, multiclass_logits, binary_labels, multiclass_labels
            )
        
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
        
        if do_profile:
            torch.cuda.synchronize()
            step_ms = (time.perf_counter() - t_step0) * 1000.0
            prof_load_ms.append(load_ms)
            prof_h2d_ms.append(h2d_ms)
            prof_step_ms.append(step_ms)
            prof_count += 1
        
        total_loss += loss.item()
        binary_loss_sum += binary_loss.item()
        multiclass_loss_sum += multiclass_loss.item()
        n_batches += 1
        
        postfix = {
            'loss': f'{loss.item():.4f}',
            'b_loss': f'{binary_loss.item():.4f}',
            'mc_loss': f'{multiclass_loss.item():.4f}'
        }
        # Always show load time (this is the key bottleneck indicator)
        postfix['load_ms'] = f'{load_ms:.0f}'
        if do_profile:
            postfix['h2d_ms'] = f'{h2d_ms:.0f}'
            postfix['step_ms'] = f'{step_ms:.0f}'
        pbar.set_postfix(postfix)
    
    if prof_n > 0 and len(prof_load_ms) > 0:
        print("\n[PROFILE] First batches timing (avg):")
        print(f"  load_ms: {np.mean(prof_load_ms):.1f} ms")
        print(f"  h2d_ms:  {np.mean(prof_h2d_ms):.1f} ms")
        print(f"  step_ms: {np.mean(prof_step_ms):.1f} ms")
    
    return {
        'loss': total_loss / n_batches,
        'binary_loss': binary_loss_sum / n_batches,
        'multiclass_loss': multiclass_loss_sum / n_batches
    }


def evaluate_model(model, dataloader, device, loss_fn, domain_filter=None):
    """Evaluate model using ChunkedDataLoader."""
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
                mask = torch.tensor([d in domain_filter for d in domains])
                if not mask.any():
                    continue
                spectrograms = spectrograms[mask]
                environmental = environmental[mask]
                binary_labels = binary_labels[mask]
                multiclass_labels = multiclass_labels[mask]
                domains = [d for d, m in zip(domains, mask.tolist()) if m]
            
            with autocast('cuda'):
                binary_logits, multiclass_logits = model(spectrograms, environmental)
                loss, binary_loss, multiclass_loss = loss_fn(
                    binary_logits, multiclass_logits, binary_labels, multiclass_labels
                )
            
            total_loss += loss.item()
            binary_loss_sum += binary_loss.item()
            multiclass_loss_sum += multiclass_loss.item()
            n_batches += 1
            
            binary_probs = torch.softmax(binary_logits, dim=1)[:, 1].cpu().numpy()
            binary_preds = torch.argmax(binary_logits, dim=1).cpu().numpy()
            multiclass_preds = torch.argmax(multiclass_logits, dim=1).cpu().numpy()
            
            all_binary_preds.extend(binary_probs)
            all_binary_labels.extend(binary_labels.cpu().numpy())
            all_multiclass_preds.extend(multiclass_preds)
            all_multiclass_labels.extend(multiclass_labels.cpu().numpy())
            all_domains.extend(domains)
    
    all_binary_preds = np.array(all_binary_preds)
    all_binary_labels = np.array(all_binary_labels)
    all_multiclass_preds = np.array(all_multiclass_preds)
    all_multiclass_labels = np.array(all_multiclass_labels)
    
    eer, auc_score = eer_and_auc(all_binary_labels, all_binary_preds)
    binary_preds_binary = (all_binary_preds > 0.5).astype(int)
    binary_accuracy = np.mean(binary_preds_binary == all_binary_labels)
    multiclass_accuracy = np.mean(all_multiclass_preds == all_multiclass_labels)
    
    return {
        'loss': total_loss / n_batches if n_batches > 0 else 0.0,
        'binary_loss': binary_loss_sum / n_batches if n_batches > 0 else 0.0,
        'multiclass_loss': multiclass_loss_sum / n_batches if n_batches > 0 else 0.0,
        'binary_eer': eer,
        'binary_auc': auc_score,
        'binary_accuracy': binary_accuracy,
        'multiclass_accuracy': multiclass_accuracy,
        'n_samples': len(all_binary_labels)
    }


def main():
    args = parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    log_dir = os.path.join(args.output_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Device setup
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
    print(f"\n[DATA] Train domain distribution:")
    print(train_df['dataset'].value_counts())
    
    # Unified manifest path
    unified_manifest_path = 'data/manifests/unified_manifest.csv'
    if not os.path.exists(unified_manifest_path):
        print(f"[WARNING] Unified manifest not found at {unified_manifest_path}")
        unified_manifest_path = None
    
    # Create FAST datasets
    print(f"\n[DATASET] Creating FAST datasets...")
    train_dataset = FastHybridDataset(
        train_df,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=unified_manifest_path
    )
    val_dataset = FastHybridDataset(
        val_df,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=unified_manifest_path
    )
    
    # Create FAST data loaders (ChunkedDataLoader)
    print(f"\n[LOADER] Creating ChunkedDataLoader (optimized for HDF5)...")
    train_loader = ChunkedDataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True
    )
    val_loader = ChunkedDataLoader(
        val_dataset,
        batch_size=args.batch_size * 2,
        shuffle=False,
        drop_last=False
    )
    
    # Quick validation subset (15%)
    val_subset_size = int(len(val_dataset) * args.val_eval_fraction)
    val_df_quick = val_df.sample(n=val_subset_size, random_state=42)
    val_dataset_quick = FastHybridDataset(
        val_df_quick,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=unified_manifest_path
    )
    val_loader_quick = ChunkedDataLoader(
        val_dataset_quick,
        batch_size=args.batch_size * 2,
        shuffle=False,
        drop_last=False
    )
    
    print(f"[LOADER] Train batches: {len(train_loader)}")
    print(f"[LOADER] Val batches (full): {len(val_loader)}")
    print(f"[LOADER] Val batches (quick): {len(val_loader_quick)}")
    
    # Class weights
    if args.use_class_weights:
        print(f"\n[WEIGHTS] Computing class weights...")
        binary_weights, multiclass_weights = compute_class_weights(train_df)
        print(f"[WEIGHTS] Binary: {binary_weights}")
        print(f"[WEIGHTS] Multiclass: {multiclass_weights}")
    else:
        binary_weights = None
        multiclass_weights = None
    
    # Model
    print(f"\n[MODEL] Creating model...")
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"[MODEL] Parameters: {total_params:,}")
    
    # Loss
    loss_fn = MultiTaskLoss(
        binary_weight=args.binary_weight,
        multiclass_weight=args.multiclass_weight,
        binary_class_weights=binary_weights,
        multiclass_class_weights=multiclass_weights
    ).to(device)
    
    # Optimizer
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
        betas=(0.9, 0.999)
    )
    
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, min_lr=1e-6
    )
    
    scaler = GradScaler('cuda') if args.mixed_precision else None
    
    # Resume
    start_epoch = 0
    best_val_eer = float('inf')
    if args.resume:
        print(f"\n[RESUME] Loading checkpoint from {args.resume}")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_eer = checkpoint.get('best_val_eer', float('inf'))
        print(f"[RESUME] Resuming from epoch {start_epoch}")
    
    logs = []
    
    print(f"\n[TRAINING] Starting FAST training...")
    print(f"[TRAINING] Epochs: {args.epochs}")
    print(f"[TRAINING] Batch size: {args.batch_size}")
    print(f"[TRAINING] Mixed precision: {args.mixed_precision}")
    print("="*80)
    
    for epoch in range(start_epoch, args.epochs):
        epoch_start = time.time()
        
        print(f"\n{'='*80}")
        print(f"EPOCH {epoch+1}/{args.epochs}")
        print(f"{'='*80}")
        
        # Train
        train_metrics = train_epoch(model, train_loader, device, optimizer, loss_fn, scaler, args)
        
        # Evaluate
        if (epoch + 1) % args.full_eval_interval == 0 or epoch == 0:
            print(f"\n[EVAL] Full validation...")
            val_metrics = evaluate_model(model, val_loader, device, loss_fn)
            
            # Per-domain
            val_metrics_asv = evaluate_model(model, val_loader, device, loss_fn, domain_filter=['LA', 'DF', 'PA'])
            val_metrics_real = evaluate_model(model, val_loader, device, loss_fn, domain_filter=['RealWorld'])
            
            val_metrics['asvspoof_eer'] = val_metrics_asv['binary_eer']
            val_metrics['asvspoof_auc'] = val_metrics_asv['binary_auc']
            val_metrics['realworld_eer'] = val_metrics_real['binary_eer']
            val_metrics['realworld_auc'] = val_metrics_real['binary_auc']
        else:
            print(f"\n[EVAL] Quick validation ({args.val_eval_fraction*100:.0f}%)...")
            val_metrics = evaluate_model(model, val_loader_quick, device, loss_fn)
            val_metrics['asvspoof_eer'] = None
            val_metrics['asvspoof_auc'] = None
            val_metrics['realworld_eer'] = None
            val_metrics['realworld_auc'] = None
        
        scheduler.step(val_metrics['loss'])
        current_lr = optimizer.param_groups[0]['lr']
        
        # Print
        print(f"\n[EPOCH {epoch+1}] Training:")
        print(f"  Loss: {train_metrics['loss']:.4f} (Binary: {train_metrics['binary_loss']:.4f}, Multiclass: {train_metrics['multiclass_loss']:.4f})")
        print(f"\n[EPOCH {epoch+1}] Validation:")
        print(f"  Loss: {val_metrics['loss']:.4f}")
        print(f"  Binary EER: {val_metrics['binary_eer']*100:.2f}%")
        print(f"  Binary AUC: {val_metrics['binary_auc']:.4f}")
        print(f"  Binary Accuracy: {val_metrics['binary_accuracy']*100:.2f}%")
        print(f"  Multiclass Accuracy: {val_metrics['multiclass_accuracy']*100:.2f}%")
        if val_metrics['asvspoof_eer'] is not None:
            print(f"  ASVspoof EER: {val_metrics['asvspoof_eer']*100:.2f}%")
            print(f"  RealWorld EER: {val_metrics['realworld_eer']*100:.2f}%")
        print(f"  LR: {current_lr:.2e}")
        
        # Log
        log_entry = {
            'epoch': epoch + 1,
            'train_loss': train_metrics['loss'],
            'val_loss': val_metrics['loss'],
            'val_binary_eer': val_metrics['binary_eer'],
            'val_binary_auc': val_metrics['binary_auc'],
            'val_binary_accuracy': val_metrics['binary_accuracy'],
            'val_multiclass_accuracy': val_metrics['multiclass_accuracy'],
            'learning_rate': current_lr,
            'epoch_time': time.time() - epoch_start
        }
        logs.append(log_entry)
        
        # Save
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
        
        if is_best:
            best_path = os.path.join(args.output_dir, 'hybrid_resnet_environmental_best.pth')
            torch.save(checkpoint, best_path)
            print(f"\n[SAVE] Best model (EER: {best_val_eer*100:.2f}%) -> {best_path}")
        
        if (epoch + 1) % args.save_interval == 0:
            checkpoint_path = os.path.join(args.output_dir, f'hybrid_resnet_environmental_epoch_{epoch+1}.pth')
            torch.save(checkpoint, checkpoint_path)
            print(f"[SAVE] Checkpoint -> {checkpoint_path}")
        
        # Save logs
        logs_df = pd.DataFrame(logs)
        logs_df.to_csv(os.path.join(log_dir, 'training_hybrid_fast.csv'), index=False)
        
        epoch_time = time.time() - epoch_start
        print(f"\n[EPOCH {epoch+1}] Completed in {epoch_time/60:.1f} minutes")
    
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"Best validation EER: {best_val_eer*100:.2f}%")
    
    # Cleanup
    train_dataset.close()
    val_dataset.close()
    val_dataset_quick.close()


if __name__ == '__main__':
    main()

