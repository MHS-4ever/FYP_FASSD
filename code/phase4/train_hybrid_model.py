"""
Train Hybrid ResNet-Environmental Model

Main training script for the hybrid model that combines spectrogram (ResNet) and
environmental features (MLP) for deepfake audio detection.

Features:
- Multi-task learning: Binary classification (real vs fake) + Multiclass (attack type)
- Mixed precision training (FP16)
- Learning rate scheduling
- Per-domain performance monitoring (ASVspoof vs Real-world)
- Class weighting for imbalanced data
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..'))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase3.multi_task_loss import MultiTaskLoss, compute_class_weights_from_labels
from phase4.hybrid_dataset import HybridFeatureDataset, create_environmental_scaler
from utils_metrics import eer_and_auc, confusion


def parse_args():
    """Parse command line arguments."""
    ap = argparse.ArgumentParser("Hybrid ResNet-Environmental Model Trainer")
    
    # Data paths
    ap.add_argument(
        '--train_manifest',
        type=str,
        default=r'E:\FYP\data\manifests\train_speaker_independent.csv',
        help='Path to training manifest CSV'
    )
    ap.add_argument(
        '--val_manifest',
        type=str,
        default=r'E:\FYP\data\manifests\val_speaker_independent.csv',
        help='Path to validation manifest CSV'
    )
    ap.add_argument(
        '--spectrogram_h5',
        type=str,
        default=r'E:\FYP\data\features\logmel_packed.h5',
        help='Path to spectrogram HDF5 file (logmel_packed.h5)'
    )
    ap.add_argument(
        '--environmental_h5',
        type=str,
        default=r'E:\FYP\data\features\environmental_packed.h5',
        help='Path to environmental HDF5 file (environmental_packed.h5)'
    )
    ap.add_argument(
        '--environmental_scaler',
        type=str,
        default=r'E:\FYP\models_saved\environment_scaler.pkl',
        help='Path to environmental feature scaler (will create if not exists)'
    )
    
    # Training hyperparameters (conservative defaults for limited RAM)
    ap.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
    ap.add_argument('--batch_size', type=int, default=64, help='Batch size (default: 64 for limited RAM, increase if you have more memory)')
    ap.add_argument('--lr', type=float, default=1e-3, help='Initial learning rate')
    ap.add_argument('--weight_decay', type=float, default=1e-4, help='Weight decay (L2 regularization)')
    ap.add_argument('--dropout', type=float, default=0.3, help='Dropout rate')
    ap.add_argument('--max_frames', type=int, default=400, help='Maximum time frames for spectrogram')
    
    # Loss weights
    ap.add_argument('--binary_weight', type=float, default=0.7, help='Weight for binary classification loss')
    ap.add_argument('--multiclass_weight', type=float, default=0.3, help='Weight for multiclass classification loss')
    
    # Evaluation options
    ap.add_argument(
        '--eval_subset',
        type=float,
        default=0.05,
        help='Fraction of validation set for quick eval during training (default: 0.05 = 5%%, increase if you have more time)'
    )
    ap.add_argument(
        '--full_eval_interval',
        type=int,
        default=10,
        help='Perform full validation every N epochs (default: 10 for faster training). Set to 0 to disable.'
    )
    
    # Output paths
    ap.add_argument(
        '--save',
        type=str,
        default=r'E:\FYP\models_saved\hybrid_resnet_environmental.pth',
        help='Path to save best model checkpoint'
    )
    ap.add_argument(
        '--log_dir',
        type=str,
        default=r'E:\FYP\reports\logs',
        help='Directory for training logs (CSV)'
    )
    ap.add_argument(
        '--plot_dir',
        type=str,
        default=r'E:\FYP\reports\figures',
        help='Directory for learning curve plots'
    )
    
    # DataLoader options (conservative defaults for limited RAM + external SSD)
    ap.add_argument('--num_workers', type=int, default=2, help='Number of DataLoader workers (default: 2 for limited RAM, increase if you have more memory)')
    ap.add_argument('--prefetch_factor', type=int, default=2, help='DataLoader prefetch factor (default: 2 for limited RAM, increase if you have more memory)')
    ap.add_argument('--persistent_workers', action='store_true', default=True, help='Use persistent workers')
    
    return ap.parse_args()


@torch.no_grad()
def evaluate(model, loader, device, max_batches=None, desc="Evaluating"):
    """
    Evaluate model on validation set.
    
    Returns:
        eer: Equal Error Rate (binary classification)
        roc_auc: ROC AUC (binary classification)
        binary_acc: Binary classification accuracy
        multiclass_acc: Multiclass classification accuracy
        cm_binary: Binary confusion matrix (TN, FP, FN, TP)
        cm_multiclass: Multiclass confusion matrix (shape: [4, 4])
        per_domain_metrics: Dict with per-domain metrics (if domain info available)
    """
    model.eval()
    
    # Collect predictions and labels
    binary_labels = []
    multiclass_labels = []
    binary_probs = []
    binary_preds = []
    multiclass_preds = []
    domains = []  # For per-domain analysis
    
    loop = tqdm(loader, desc=desc, leave=False, dynamic_ncols=True, colour="cyan")
    with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
        for batch_idx, (spec, env, binary_y, multiclass_y) in enumerate(loop):
            if max_batches and batch_idx >= max_batches:
                break
            
            spec = spec.to(device, non_blocking=True)
            env = env.to(device, non_blocking=True)
            
            # Forward pass
            binary_logits, multiclass_logits = model(spec, env)
            
            # Binary classification
            binary_prob = torch.softmax(binary_logits, dim=1)[:, 1]  # Probability of fake
            binary_pred = binary_prob >= 0.5
            
            # Multiclass classification
            multiclass_pred = torch.argmax(multiclass_logits, dim=1)
            
            # Collect results
            binary_labels.append(binary_y.numpy())
            multiclass_labels.append(multiclass_y.numpy())
            binary_probs.append(binary_prob.detach().cpu().numpy())
            binary_preds.append(binary_pred.detach().cpu().numpy())
            multiclass_preds.append(multiclass_pred.detach().cpu().numpy())
    
    # Concatenate results
    binary_labels = np.concatenate(binary_labels).astype(int)
    multiclass_labels = np.concatenate(multiclass_labels).astype(int)
    binary_probs = np.concatenate(binary_probs)
    binary_preds = np.concatenate(binary_preds).astype(int)
    multiclass_preds = np.concatenate(multiclass_preds).astype(int)
    
    # Compute binary metrics
    eer, roc_auc = eer_and_auc(binary_labels, binary_probs)
    cm_binary = confusion(binary_labels, binary_preds)
    binary_acc = (cm_binary[3] + cm_binary[0]) / max(1, sum(cm_binary))
    
    # Compute multiclass accuracy
    multiclass_acc = (multiclass_preds == multiclass_labels).mean()
    
    # Multiclass confusion matrix
    from sklearn.metrics import confusion_matrix as sk_confusion_matrix
    cm_multiclass = sk_confusion_matrix(multiclass_labels, multiclass_preds, labels=[0, 1, 2, 3])
    
    # Per-domain metrics (if available)
    per_domain_metrics = None
    
    return eer, roc_auc, binary_acc, multiclass_acc, cm_binary, cm_multiclass, per_domain_metrics


def plot_learning_curves(logs, out_dir):
    """Plot learning curves."""
    os.makedirs(out_dir, exist_ok=True)
    epochs = np.arange(1, len(logs["train_loss"]) + 1)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Loss curves
    axes[0, 0].plot(epochs, logs["train_loss"], label="Train Loss", color="tab:blue", marker="o")
    axes[0, 0].plot(epochs, logs["train_binary_loss"], label="Train Binary Loss", color="tab:cyan", marker="s", linestyle="--")
    axes[0, 0].plot(epochs, logs["train_multiclass_loss"], label="Train Multiclass Loss", color="tab:purple", marker="^", linestyle="--")
    axes[0, 0].set_title("Training Loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("Loss")
    axes[0, 0].grid(True, linestyle="--", alpha=0.5)
    axes[0, 0].legend()
    
    # Validation EER and AUC
    axes[0, 1].plot(epochs, logs["val_eer"], label="Val EER (%)", color="tab:red", marker="x")
    axes[0, 1].plot(epochs, logs["val_auc"], label="Val AUC", color="tab:green", marker="s")
    axes[0, 1].set_title("Binary Classification Metrics")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Value")
    axes[0, 1].grid(True, linestyle="--", alpha=0.5)
    axes[0, 1].legend()
    
    # Validation Accuracy
    axes[1, 0].plot(epochs, np.array(logs["val_binary_acc"]) * 100, label="Val Binary Acc (%)", color="tab:orange", marker="^")
    axes[1, 0].plot(epochs, np.array(logs["val_multiclass_acc"]) * 100, label="Val Multiclass Acc (%)", color="tab:pink", marker="d")
    axes[1, 0].set_title("Classification Accuracy")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("Accuracy (%)")
    axes[1, 0].grid(True, linestyle="--", alpha=0.5)
    axes[1, 0].legend()
    
    # Learning rate
    axes[1, 1].plot(epochs, logs["lr"], label="Learning Rate", color="tab:brown", marker="o")
    axes[1, 1].set_title("Learning Rate Schedule")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].set_ylabel("Learning Rate")
    axes[1, 1].set_yscale('log')
    axes[1, 1].grid(True, linestyle="--", alpha=0.5)
    axes[1, 1].legend()
    
    plt.tight_layout()
    out_path = os.path.join(out_dir, "learning_curves_hybrid.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[PLOT] Learning curves saved -> {out_path}")


def save_training_logs(logs, log_dir):
    """Save training logs to CSV."""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create DataFrame
    log_df = pd.DataFrame({
        'epoch': np.arange(1, len(logs["train_loss"]) + 1),
        'train_loss': logs["train_loss"],
        'train_binary_loss': logs["train_binary_loss"],
        'train_multiclass_loss': logs["train_multiclass_loss"],
        'val_eer': logs["val_eer"],
        'val_auc': logs["val_auc"],
        'val_binary_acc': logs["val_binary_acc"],
        'val_multiclass_acc': logs["val_multiclass_acc"],
        'lr': logs["lr"]
    })
    
    log_path = os.path.join(log_dir, "training_hybrid_model.csv")
    log_df.to_csv(log_path, index=False)
    print(f"[LOG] Training metrics saved -> {log_path}")


def main():
    args = parse_args()
    
    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[GPU] Using device: {device} (CUDA available: {torch.cuda.is_available()})")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    # Load manifests
    print(f"\n[DATA] Loading training manifest: {args.train_manifest}")
    train_df = pd.read_csv(args.train_manifest, low_memory=False)
    print(f"[DATA] Training samples: {len(train_df)}")
    print(f"[DATA] Training label distribution:\n{train_df['label'].value_counts()}\n")
    
    print(f"[DATA] Loading validation manifest: {args.val_manifest}")
    val_df = pd.read_csv(args.val_manifest, low_memory=False)
    print(f"[DATA] Validation samples: {len(val_df)}")
    print(f"[DATA] Validation label distribution:\n{val_df['label'].value_counts()}\n")
    
    # Filter samples that have both features
    train_df = train_df[
        (train_df['spectrogram_idx'] >= 0) & (train_df['environmental_idx'] >= 0)
    ].reset_index(drop=True)
    val_df = val_df[
        (val_df['spectrogram_idx'] >= 0) & (val_df['environmental_idx'] >= 0)
    ].reset_index(drop=True)
    
    print(f"[DATA] After filtering: Train={len(train_df)}, Val={len(val_df)}")
    
    # Create or load environmental scaler
    if os.path.exists(args.environmental_scaler):
        print(f"[SCALER] Loading environmental scaler from: {args.environmental_scaler}")
        with open(args.environmental_scaler, 'rb') as f:
            environmental_scaler = pickle.load(f)
    else:
        print(f"[SCALER] Creating new environmental scaler from training data...")
        environmental_scaler = create_environmental_scaler(
            train_df, args.environmental_h5, args.environmental_scaler
        )
    
    # Create datasets
    print("\n[LOADER] Initializing datasets...")
    train_dataset = HybridFeatureDataset(
        train_df,
        args.spectrogram_h5,
        args.environmental_h5,
        environmental_scaler=environmental_scaler,
        max_frames=args.max_frames,
        shuffle=True
    )
    val_dataset = HybridFeatureDataset(
        val_df,
        args.spectrogram_h5,
        args.environmental_h5,
        environmental_scaler=environmental_scaler,
        max_frames=args.max_frames,
        shuffle=False
    )
    
    # Create DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        prefetch_factor=args.prefetch_factor,
        pin_memory=True,
        persistent_workers=args.persistent_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size * 2,  # Larger batch for validation
        shuffle=False,
        num_workers=args.num_workers,
        prefetch_factor=args.prefetch_factor,
        pin_memory=True,
        persistent_workers=args.persistent_workers,
    )
    print("[OK] DataLoaders ready.\n")
    
    # Compute class weights
    print("[CLASS WEIGHTS] Computing class weights...")
    binary_labels_train = train_df['label'].apply(lambda x: 1 if x == 'spoof' else 0).values
    binary_class_weights = compute_class_weights_from_labels(binary_labels_train, 2)
    print(f"[CLASS WEIGHTS] Binary weights: {binary_class_weights}")
    
    # For multiclass, need attack_type labels
    attack_type_mapping = {'bonafide': 0, 'synthesis': 1, 'conversion': 2, 'replay': 3}
    multiclass_labels_train = train_df['attack_type'].apply(
        lambda x: attack_type_mapping.get(str(x).lower(), 0)
    ).values
    multiclass_class_weights = compute_class_weights_from_labels(multiclass_labels_train, 4)
    print(f"[CLASS WEIGHTS] Multiclass weights: {multiclass_class_weights}\n")
    
    # Create model
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=args.dropout).to(device)
    print("[MODEL] Hybrid ResNet-Environmental initialized")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[INFO] Total parameters: {total_params:,}")
    print(f"[INFO] Trainable parameters: {trainable_params:,}\n")
    
    # Create loss function
    criterion = MultiTaskLoss(
        binary_weight=args.binary_weight,
        multiclass_weight=args.multiclass_weight,
        binary_class_weights=binary_class_weights,
        multiclass_class_weights=multiclass_class_weights
    ).to(device)
    
    # Optimizer
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
        betas=(0.9, 0.999)
    )
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, min_lr=1e-6, verbose=True
    )
    
    # Mixed precision scaler
    scaler = torch.amp.GradScaler(enabled=(device.type == "cuda"))
    
    # Training logs
    logs = {
        "train_loss": [],
        "train_binary_loss": [],
        "train_multiclass_loss": [],
        "val_eer": [],
        "val_auc": [],
        "val_binary_acc": [],
        "val_multiclass_acc": [],
        "lr": []
    }
    
    best_eer = float("inf")
    best_epoch = 0
    
    # Calculate max batches for quick evaluation
    quick_eval_batches = max(1, int(len(val_loader) * args.eval_subset))
    
    # Training loop
    print("[TRAIN] Starting training...")
    print(f"[INFO] Quick eval on {args.eval_subset*100:.0f}% of validation set per epoch")
    if args.full_eval_interval > 0:
        print(f"[INFO] Full validation every {args.full_eval_interval} epochs")
    print()
    
    for epoch in range(1, args.epochs + 1):
        # Training phase
        model.train()
        running_loss = 0.0
        running_binary_loss = 0.0
        running_multiclass_loss = 0.0
        
        loop = tqdm(
            train_loader,
            desc=f"Epoch {epoch:02d}/{args.epochs:02d} [Training]",
            dynamic_ncols=True,
            colour="green"
        )
        
        for spec, env, binary_y, multiclass_y in loop:
            spec = spec.to(device, non_blocking=True)
            env = env.to(device, non_blocking=True)
            binary_y = binary_y.to(device, non_blocking=True)
            multiclass_y = multiclass_y.to(device, non_blocking=True)
            
            optimizer.zero_grad(set_to_none=True)
            
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                binary_logits, multiclass_logits = model(spec, env)
                total_loss, binary_loss, multiclass_loss = criterion(
                    binary_logits, multiclass_logits, binary_y, multiclass_y
                )
            
            scaler.scale(total_loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            running_loss += total_loss.item()
            running_binary_loss += binary_loss.item()
            running_multiclass_loss += multiclass_loss.item()
            
            loop.set_postfix(
                loss=f"{total_loss.item():.4f}",
                b_loss=f"{binary_loss.item():.4f}",
                mc_loss=f"{multiclass_loss.item():.4f}"
            )
        
        avg_loss = running_loss / len(train_loader)
        avg_binary_loss = running_binary_loss / len(train_loader)
        avg_multiclass_loss = running_multiclass_loss / len(train_loader)
        
        # Evaluation phase
        is_full_eval = args.full_eval_interval > 0 and epoch % args.full_eval_interval == 0
        is_last_epoch = epoch == args.epochs
        
        if is_full_eval or is_last_epoch:
            val_eer, val_auc, val_binary_acc, val_multiclass_acc, cm_binary, cm_multiclass, per_domain = evaluate(
                model, val_loader, device, max_batches=None, desc="Full Validation"
            )
            eval_tag = "[FULL]"
        else:
            val_eer, val_auc, val_binary_acc, val_multiclass_acc, cm_binary, cm_multiclass, per_domain = evaluate(
                model, val_loader, device, max_batches=quick_eval_batches, desc="Quick Validation"
            )
            eval_tag = "[QUICK]"
        
        # Update learning rate
        current_lr = optimizer.param_groups[0]['lr']
        scheduler.step(val_eer)
        
        # Log metrics
        logs["train_loss"].append(avg_loss)
        logs["train_binary_loss"].append(avg_binary_loss)
        logs["train_multiclass_loss"].append(avg_multiclass_loss)
        logs["val_eer"].append(val_eer * 100)
        logs["val_auc"].append(val_auc)
        logs["val_binary_acc"].append(val_binary_acc)
        logs["val_multiclass_acc"].append(val_multiclass_acc)
        logs["lr"].append(current_lr)
        
        print(
            f"[METRICS] {eval_tag} Epoch {epoch:02d} | "
            f"TrainLoss {avg_loss:.4f} (B:{avg_binary_loss:.4f}, MC:{avg_multiclass_loss:.4f}) | "
            f"ValEER {val_eer*100:.2f}% | AUC {val_auc:.3f} | "
            f"BinaryAcc {val_binary_acc*100:.2f}% | MulticlassAcc {val_multiclass_acc*100:.2f}% | "
            f"LR {current_lr:.2e}"
        )
        print(f"         Binary CM: TN={cm_binary[0]}, FP={cm_binary[1]}, FN={cm_binary[2]}, TP={cm_binary[3]}")
        
        # Save best model
        if val_eer < best_eer:
            best_eer = val_eer
            best_epoch = epoch
            os.makedirs(os.path.dirname(args.save), exist_ok=True)
            checkpoint = {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "eer": val_eer,
                "auc": val_auc,
                "binary_acc": val_binary_acc,
                "multiclass_acc": val_multiclass_acc,
                "args": vars(args)
            }
            torch.save(checkpoint, args.save)
            print(f"[SAVE] Best model saved (EER {val_eer*100:.2f}%) -> {args.save}")
        
        print()
    
    print("[OK] Training complete.")
    print(f"[RESULTS] Best validation EER: {best_eer*100:.2f}% (epoch {best_epoch})")
    print(f"[SAVE] Checkpoint saved at: {args.save}\n")
    
    # Save logs and plots
    save_training_logs(logs, args.log_dir)
    plot_learning_curves(logs, args.plot_dir)


if __name__ == "__main__":
    main()

