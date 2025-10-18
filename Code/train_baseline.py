import os, argparse
import numpy as np
import pandas as pd
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from data_loading.dataset_loader import FeatureDataset
from models.baseline_cnn import LCNNBaseline
from utils_metrics import eer_and_auc, confusion


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=r"D:\UNI\FYP\data\features\features_manifest_labeled.csv")
    ap.add_argument("--feature_type", choices=["lfcc", "mel"], default="lfcc")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--val_size", type=float, default=0.2)
    ap.add_argument("--save", default=r"D:\UNI\FYP\models_saved\baseline_cnn.pth")
    ap.add_argument("--num_workers", type=int, default=0)  # set >0 only if stable
    return ap.parse_args()


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    ys, ps, yh = [], [], []
    for x, y in tqdm(loader, desc="Evaluating", leave=False):
        x = x.to(device)
        logits = model(x)
        prob1 = torch.softmax(logits, dim=1)[:, 1]
        ys.append(y.numpy())
        ps.append(prob1.cpu().numpy())
        yh.append((prob1.cpu().numpy() >= 0.5).astype(int))
    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    y_hat = np.concatenate(yh).astype(int)
    eer, roc_auc = eer_and_auc(y_true, y_scores)
    tn, fp, fn, tp = confusion(y_true, y_hat)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))
    return eer, roc_auc, acc, (tn, fp, fn, tp)


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(args.save), exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🧠 Using device: {device}")

    # -------- data
    df = pd.read_csv(args.manifest)
    df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)
    print(f"📄 Loaded manifest with {len(df)} samples")

    # stratified split
    train_df, val_df = train_test_split(
        df, test_size=args.val_size, stratify=df["label"], random_state=42
    )
    print(f"📊 Train: {len(train_df)} | Val: {len(val_df)}")

    print("🔄 Initializing datasets...")
    train_ds = FeatureDataset(train_df, feature_type=args.feature_type, target_T=args.target_T)
    val_ds = FeatureDataset(val_df, feature_type=args.feature_type, target_T=args.target_T)

    print("🧾 Building DataLoaders...")
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                          num_workers=args.num_workers, pin_memory=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers, pin_memory=True)

    print("✅ DataLoaders ready.\n")

    # class imbalance weights
    counts = train_df["label"].value_counts()
    w_spoof = counts["bonafide"] / (counts["spoof"] + 1e-6)
    w_bona = 1.0
    class_weights = torch.tensor([w_spoof, w_bona], dtype=torch.float32).to(device)

    model = LCNNBaseline().to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    scaler = torch.amp.GradScaler("cuda" if device == "cuda" else "cpu")

    best_eer = 1.0
    for ep in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        loop = tqdm(train_dl, desc=f"Epoch {ep}/{args.epochs} [Training]", leave=True)

        for x, y in loop:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda" if device == "cuda" else "cpu"):
                logits = model(x)
                loss = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

        scheduler.step()

        # Evaluate after each epoch
        eer, roc_auc, acc, cm = evaluate(model, val_dl, device)
        print(f"📈 Epoch {ep:02d} | TrainLoss {total_loss/len(train_dl):.4f} "
              f"| ValEER {eer*100:.2f}% | AUC {roc_auc:.3f} | Acc {acc*100:.2f}% "
              f"| CM={cm}")

        # Save best model (by EER)
        if eer < best_eer:
            best_eer = eer
            torch.save({"model": model.state_dict(),
                        "args": vars(args),
                        "best_val_eer": best_eer}, args.save)
            print(f"💾 Best model saved (EER {best_eer*100:.2f}%) → {args.save}")

    print("\n✅ Training complete.")
    print(f"🏁 Best validation EER: {best_eer*100:.2f}%")
    if os.path.exists(args.save):
        print(f"📂 Checkpoint saved at: {args.save}")


if __name__ == "__main__":
    main()
