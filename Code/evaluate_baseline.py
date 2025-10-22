import argparse, os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from data_loading.streaming_dataset_loader import StreamingFeatureDataset
from models.baseline_cnn import LCNNBaseline
from utils_metrics import eer_and_auc, confusion


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=r"E:\FYP\data\features_merged\features_manifest_combined.csv")
    ap.add_argument("--ckpt",     default=r"E:\FYP\models_saved\baseline_cnn_robust.pth")
    ap.add_argument("--feature_type", choices=["lfcc","mel"], default="lfcc")
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--batch_size", type=int, default=128)
    return ap.parse_args()


@torch.no_grad()
def main():
    args = parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🧠 Using device: {device}")

    df = pd.read_csv(args.manifest)
    df = df[df["label"].isin(["bonafide","spoof"])].reset_index(drop=True)
    ds = StreamingFeatureDataset(df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=False)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = LCNNBaseline().to(device)
    ckpt = torch.load(args.ckpt, map_location=device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    ys, ps = [], []
    for x, y in tqdm(dl, desc="Evaluating"):
        x = x.to(device, non_blocking=True)
        logits = model(x)
        prob1 = torch.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
        ys.append(y.numpy()); ps.append(prob1)

    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    eer, roc_auc = eer_and_auc(y_true, y_scores)
    y_hat = (y_scores >= 0.5).astype(int)
    tn, fp, fn, tp = confusion(y_true, y_hat)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))

    print(f"\n📊 Evaluation Results:")
    print(f"  EER: {eer*100:.2f}%")
    print(f"  ROC-AUC: {roc_auc:.3f}")
    print(f"  Accuracy: {acc*100:.2f}%")
    print(f"  Confusion (tn, fp, fn, tp): {(tn,fp,fn,tp)}")


if __name__ == "__main__":
    main()
