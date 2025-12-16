# train_resnet.py
import os
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import matplotlib.pyplot as plt

from data_loading.streaming_dataset_loader import StreamingFeatureDataset
from models.resnet_cnn import DeepResNetCNN
from utils_metrics import eer_and_auc, confusion

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser("Deep ResNet CNN trainer for audio deepfake detection")
    ap.add_argument("--manifest", default=r"E:\FYP\data\features_merged\features_manifest_combined.csv")
    ap.add_argument("--feature_type", choices=["lfcc", "mel"], default="mel")

    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch_size", type=int, default=128)         # Reduced for deeper model
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight_decay", type=float, default=1e-4)    # L2 regularization
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--val_size", type=float, default=0.2)
    
    # Fast training options
    ap.add_argument("--eval_subset", type=float, default=0.15, 
                    help="Fraction of validation set to use for quick eval during training (default: 0.15 = 15%)")
    ap.add_argument("--full_eval_interval", type=int, default=5, 
                    help="Perform full validation every N epochs (default: 5). Set to 0 to disable.")

    ap.add_argument("--save", default=r"E:\FYP\models_saved\resnet_cnn_mel_robust.pth")
    ap.add_argument("--plot_dir", default=r"E:\FYP\reports\figures")

    # DataLoader performance knobs
    ap.add_argument("--num_workers", type=int, default=6)
    ap.add_argument("--prefetch_factor", type=int, default=4)
    ap.add_argument("--persistent_workers", action="store_true", default=True)

    return ap.parse_args()

# ---------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------
@torch.no_grad()
def evaluate(model, loader, device, max_batches=None, desc="Evaluating"):
    """
    Evaluate model on validation set.
    
    Args:
        max_batches: If set, only evaluate on first N batches for speed.
                     Use for quick checks during training. Set to None for full eval.
    """
    model.eval()
    ys, ps, yh = [], [], []

    loop = tqdm(loader, desc=desc, leave=False, dynamic_ncols=True, colour="cyan")
    with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
        for batch_idx, (x, y) in enumerate(loop):
            if max_batches and batch_idx >= max_batches:
                break
                
            x = x.to(device, non_blocking=True)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[:, 1]
            preds = probs >= 0.5

            ys.append(y.numpy())
            ps.append(probs.detach().cpu().numpy())
            yh.append(preds.detach().cpu().numpy())

    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    y_pred = np.concatenate(yh).astype(int)

    eer, roc_auc = eer_and_auc(y_true, y_scores)
    cm = confusion(y_true, y_pred)
    acc = (cm[3] + cm[0]) / max(1, sum(cm))
    return eer, roc_auc, acc, cm

# ---------------------------------------------------------------------
# Plot curves
# ---------------------------------------------------------------------
def plot_learning_curves(logs, out_dir, feature_type):
    os.makedirs(out_dir, exist_ok=True)
    epochs = np.arange(1, len(logs["train_loss"]) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(epochs, logs["train_loss"], label="Train Loss", color="tab:blue", marker="o")
    plt.plot(epochs, logs["val_eer"], label="Val EER (%)", color="tab:red", marker="x")
    plt.title(f"ResNet CNN - Loss & EER ({feature_type.upper()} features)")
    plt.xlabel("Epoch")
    plt.ylabel("Value")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(epochs, logs["val_auc"], label="Val AUC", color="tab:green", marker="s")
    plt.plot(epochs, np.array(logs["val_acc"]) * 100, label="Val Acc (%)", color="tab:orange", marker="^")
    plt.title(f"ResNet CNN - Validation Metrics ({feature_type.upper()} features)")
    plt.xlabel("Epoch")
    plt.ylabel("Value")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    out_path = os.path.join(out_dir, f"learning_curves_resnet_{feature_type}.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[PLOT] Learning curve saved -> {out_path}")

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    args = parse_args()

    # --- Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[GPU] Using device: {device} (CUDA available: {torch.cuda.is_available()})")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True  # Enable TF32 for matmul (faster on Ampere+)
        torch.backends.cudnn.allow_tf32 = True         # Enable TF32 for cuDNN (faster convolutions)

    # --- Load manifest
    df = pd.read_csv(args.manifest)
    print(f"\n[DATA] Loaded manifest with {len(df)} samples")
    print(f"[DATA] Label distribution:\n{df['label'].value_counts()}\n")

    # Filter valid labels
    df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)

    # --- Train/Val split
    train_df, val_df = train_test_split(
        df, test_size=args.val_size, random_state=42, stratify=df["label"]
    )
    print(f"[SPLIT] Train: {len(train_df)} | Val: {len(val_df)}")

    # --- Datasets & DataLoaders
    print("[LOADER] Initializing streaming datasets...")
    train_ds = StreamingFeatureDataset(
        train_df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=True
    )
    val_ds = StreamingFeatureDataset(
        val_df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=False
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        prefetch_factor=args.prefetch_factor,
        pin_memory=True,
        persistent_workers=args.persistent_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size * 2,
        shuffle=False,
        num_workers=args.num_workers,
        prefetch_factor=args.prefetch_factor,
        pin_memory=True,
        persistent_workers=args.persistent_workers,
    )
    print("[OK] DataLoaders ready.\n")

    # --- Class weights for imbalanced data
    label_counts = train_df["label"].value_counts()
    n_bonafide = label_counts.get("bonafide", 1)
    n_spoof = label_counts.get("spoof", 1)
    total = len(train_df)
    w_bonafide = total / (2 * n_bonafide)
    w_spoof = total / (2 * n_spoof)
    class_weights = torch.tensor([w_bonafide, w_spoof], dtype=torch.float32).to(device)
    print(f"[INFO] Class weights: bonafide={w_bonafide:.4f}, spoof={w_spoof:.4f}\n")

    # --- Model
    model = DeepResNetCNN(n_classes=2, dropout=args.dropout).to(device)
    print("[MODEL] Deep ResNet CNN initialized")
    print(f"[INFO] Total parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"[INFO] Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}\n")

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # Learning rate scheduler - reduce on plateau
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=2, verbose=True
    )

    scaler = torch.amp.GradScaler("cuda")

    # --- Training loop
    print("[TRAIN] Starting training...")
    print(f"[INFO] Quick eval on {args.eval_subset*100:.0f}% of validation set per epoch")
    if args.full_eval_interval > 0:
        print(f"[INFO] Full validation every {args.full_eval_interval} epochs")
    print()
    
    # Calculate max batches for quick evaluation
    quick_eval_batches = max(1, int(len(val_loader) * args.eval_subset))
    
    logs = {"train_loss": [], "val_eer": [], "val_auc": [], "val_acc": []}
    best_eer = float("inf")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        loop = tqdm(
            train_loader,
            desc=f"Epoch {epoch:02d}/{args.epochs:02d} [Training]",
            dynamic_ncols=True,
            colour="green"
        )

        for x, y in loop:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(x)
                loss = criterion(logits, y)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

        avg_loss = running_loss / len(train_loader)
        
        # Quick evaluation on subset for speed (or full eval at intervals)
        is_full_eval = args.full_eval_interval > 0 and epoch % args.full_eval_interval == 0
        is_last_epoch = epoch == args.epochs
        
        if is_full_eval or is_last_epoch:
            val_eer, val_auc, val_acc, val_cm = evaluate(
                model, val_loader, device, max_batches=None, desc="Full Validation"
            )
            eval_tag = "[FULL]"
        else:
            val_eer, val_auc, val_acc, val_cm = evaluate(
                model, val_loader, device, max_batches=quick_eval_batches, desc="Quick Validation"
            )
            eval_tag = "[QUICK]"

        logs["train_loss"].append(avg_loss)
        logs["val_eer"].append(val_eer * 100)
        logs["val_auc"].append(val_auc)
        logs["val_acc"].append(val_acc)

        print(
            f"[METRICS] {eval_tag} Epoch {epoch:02d} | "
            f"TrainLoss {avg_loss:.4f} | "
            f"ValEER {val_eer*100:.2f}% | "
            f"AUC {val_auc:.3f} | "
            f"Acc {val_acc*100:.2f}% | "
            f"CM={val_cm}"
        )

        # Update learning rate based on validation EER
        scheduler.step(val_eer)

        # Save best model
        if val_eer < best_eer:
            best_eer = val_eer
            os.makedirs(os.path.dirname(args.save), exist_ok=True)
            checkpoint = {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "eer": val_eer,
                "auc": val_auc,
                "args": vars(args)
            }
            torch.save(checkpoint, args.save)
            print(f"[SAVE] Best model saved (EER {val_eer*100:.2f}%) -> {args.save}")

        print()

    print("[OK] Training complete.")
    print(f"[RESULTS] Best validation EER: {best_eer*100:.2f}%")
    print(f"[SAVE] Checkpoint saved at: {args.save}\n")

    plot_learning_curves(logs, args.plot_dir, args.feature_type)

# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()

