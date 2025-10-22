# train_baseline.py
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
from models.baseline_cnn import LCNNBaseline
from utils_metrics import eer_and_auc, confusion

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser("Baseline LCNN trainer (streaming features)")
    ap.add_argument("--manifest", default=r"E:\FYP\data\features_merged\features_manifest_combined.csv")
    ap.add_argument("--feature_type", choices=["lfcc", "mel"], default="lfcc")

    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch_size", type=int, default=256)         # tuned for 6GB VRAM
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--val_size", type=float, default=0.2)

    ap.add_argument("--save", default=r"E:\FYP\models_saved\baseline_cnn_robust.pth")
    ap.add_argument("--plot_dir", default=r"E:\FYP\reports\figures")

    # DataLoader performance knobs (tuned for external SSD + RTX 3050)
    ap.add_argument("--num_workers", type=int, default=6)
    ap.add_argument("--prefetch_factor", type=int, default=4)
    ap.add_argument("--persistent_workers", action="store_true", default=True)

    return ap.parse_args()

# ---------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------
@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    ys, ps, yh = [], [], []

    loop = tqdm(loader, desc="Evaluating", leave=False, dynamic_ncols=True)
    for x, y in loop:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        logits = model(x)
        prob1 = torch.softmax(logits, dim=1)[:, 1]

        ys.append(y.detach().cpu().numpy())
        ps.append(prob1.detach().cpu().numpy())
        yh.append((prob1.detach().cpu().numpy() >= 0.5).astype(int))

    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    y_hat = np.concatenate(yh).astype(int)

    eer, roc_auc = eer_and_auc(y_true, y_scores)
    tn, fp, fn, tp = confusion(y_true, y_hat)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))
    return eer, roc_auc, acc, (tn, fp, fn, tp)

# ---------------------------------------------------------------------
# Plot curves
# ---------------------------------------------------------------------
def plot_learning_curves(logs, out_dir, feature_type):
    os.makedirs(out_dir, exist_ok=True)
    epochs = np.arange(1, len(logs["train_loss"]) + 1)

    plt.figure(figsize=(10, 6))
    plt.plot(epochs, logs["train_loss"], label="Train Loss", color="tab:red", marker="o")
    plt.plot(epochs, np.array(logs["val_eer"]) * 100, label="Val EER (%)", color="tab:blue", marker="x")
    plt.plot(epochs, logs["val_auc"], label="Val AUC", color="tab:green", marker="s")
    plt.plot(epochs, np.array(logs["val_acc"]) * 100, label="Val Acc (%)", color="tab:orange", marker="^")
    plt.title(f"Learning Curves ({feature_type.upper()} features)")
    plt.xlabel("Epoch")
    plt.ylabel("Metric Value")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    out_path = os.path.join(out_dir, f"learning_curves_{feature_type}.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"📊 Learning curve saved → {out_path}")

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    args = parse_args()

    # Make sure output dirs exist
    os.makedirs(os.path.dirname(args.save), exist_ok=True)
    os.makedirs(args.plot_dir, exist_ok=True)

    # CUDA setup
    torch.backends.cudnn.benchmark = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🧠 Using device: {device} (CUDA available: {torch.cuda.is_available()})")

    # -------- Load & split
    df = pd.read_csv(args.manifest)
    df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)
    print(f"📄 Loaded manifest with {len(df)} samples")

    train_df, val_df = train_test_split(
        df, test_size=args.val_size, stratify=df["label"], random_state=42
    )
    print(f"📊 Train: {len(train_df)} | Val: {len(val_df)}")

    # -------- Datasets & Loaders
    print("🔄 Initializing streaming datasets...")
    train_ds = StreamingFeatureDataset(
        train_df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=True
    )
    val_ds = StreamingFeatureDataset(
        val_df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=False
    )

    train_dl = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=args.persistent_workers,
        prefetch_factor=args.prefetch_factor,
    )
    val_dl = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        num_workers=max(2, args.num_workers // 2),
        pin_memory=True,
        persistent_workers=args.persistent_workers,
        prefetch_factor=max(2, args.prefetch_factor // 2),
    )
    print("✅ DataLoaders ready.\n")

    # -------- Class weights (imbalanced data)
    counts = train_df["label"].value_counts()
    w_spoof = counts["bonafide"] / (counts["spoof"] + 1e-6)
    w_bona = 1.0
    class_weights = torch.tensor([w_spoof, w_bona], dtype=torch.float32, device=device)

    # -------- Model / Optim
    model = LCNNBaseline().to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda")  # ✅ PyTorch 2.x API

    best_eer = 1.0
    logs = {"train_loss": [], "val_eer": [], "val_auc": [], "val_acc": []}

    print("\n🚀 Starting training...\n")

    # We can’t safely use len(train_dl) with Iterable-style datasets.
    steps_per_epoch = int(np.ceil(len(train_df) / args.batch_size))

    for ep in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0

        print(f"\nEpoch {ep}/{args.epochs} [Training]:")
        loop = tqdm(
            train_dl,
            total=steps_per_epoch,
            desc=f"Epoch {ep:02d}/{args.epochs} [Training]",
            dynamic_ncols=True,
            leave=True,
        )

        # Training batches
        for bidx, (x, y) in enumerate(loop, start=1):
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda"):
                logits = model(x)
                loss = criterion(logits, y)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            total_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

            # Stop the loop after we’ve consumed an epoch’s worth of samples
            if bidx >= steps_per_epoch:
                break

        avg_loss = total_loss / max(1, bidx)
        scheduler.step()

        # -------- Validation
        eer, roc_auc, acc, cm = evaluate(model, val_dl, device)
        logs["train_loss"].append(avg_loss)
        logs["val_eer"].append(eer)
        logs["val_auc"].append(roc_auc)
        logs["val_acc"].append(acc)

        print(
            f"📈 Epoch {ep:02d} | TrainLoss {avg_loss:.4f} | "
            f"ValEER {eer*100:.2f}% | AUC {roc_auc:.3f} | "
            f"Acc {acc*100:.2f}% | CM={cm}"
        )

        # Save best
        if eer < best_eer:
            best_eer = eer
            torch.save(
                {"model": model.state_dict(), "args": vars(args), "best_val_eer": best_eer},
                args.save,
            )
            print(f"💾 Best model saved (EER {best_eer*100:.2f}%) → {args.save}")

    # -------- Finish
    print("\n✅ Training complete.")
    print(f"🏁 Best validation EER: {best_eer*100:.2f}%")
    if os.path.exists(args.save):
        print(f"📂 Checkpoint saved at: {args.save}")

    plot_learning_curves(logs, args.plot_dir, args.feature_type)

# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
