import argparse, os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from data_loading.dataset_loader import FeatureDataset
from models.baseline_cnn import LCNNBaseline
from utils_metrics import eer_and_auc, confusion

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=r"D:\UNI\FYP\data\features\features_manifest_labeled.csv")
    ap.add_argument("--ckpt",     default=r"D:\UNI\FYP\models_saved\baseline_cnn.pth")
    ap.add_argument("--feature_type", choices=["lfcc","mel"], default="lfcc")
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--batch_size", type=int, default=64)
    return ap.parse_args()

@torch.no_grad()
def main():
    args = parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    df = pd.read_csv(args.manifest)
    df = df[df["label"].isin(["bonafide","spoof"])].reset_index(drop=True)

    ds = FeatureDataset(df, feature_type=args.feature_type, target_T=args.target_T)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=False)

    model = LCNNBaseline().to(device)
    ckpt = torch.load(args.ckpt, map_location=device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    ys, ps = [], []
    for x,y in dl:
        x = x.to(device)
        logits = model(x)
        prob1 = torch.softmax(logits, dim=1)[:,1].cpu().numpy()
        ys.append(y.numpy()); ps.append(prob1)

    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    eer, roc_auc = eer_and_auc(y_true, y_scores)
    y_hat = (y_scores >= 0.5).astype(int)
    tn, fp, fn, tp = confusion(y_true, y_hat)
    acc = (tp + tn) / max(1, (tp+tn+fp+fn))

    print(f"Evaluation on manifest:")
    print(f"  EER: {eer*100:.2f}%")
    print(f"  ROC-AUC: {roc_auc:.3f}")
    print(f"  Accuracy: {acc*100:.2f}%")
    print(f"  Confusion (tn, fp, fn, tp): {(tn,fp,fn,tp)}")

if __name__ == "__main__":
    main()
