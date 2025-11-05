import os
import argparse
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from tabulate import tabulate

from data_loading.streaming_dataset_loader import StreamingFeatureDataset
from models.baseline_cnn import LCNNBaseline
from models.resnet_cnn import DeepResNetCNN
from utils_metrics import eer_and_auc, confusion


def parse_args():
    ap = argparse.ArgumentParser("Evaluate models on clean & augmented datasets")
    ap.add_argument("--ckpt", default=r"E:\FYP\models_saved\baseline_cnn_robust_fixed.pth")
    ap.add_argument("--model_type", choices=["baseline", "resnet"], default="baseline", 
                    help="Model architecture: baseline (LCNN) or resnet (Deep ResNet CNN)")
    ap.add_argument("--feature_type", choices=["lfcc", "mel"], default="lfcc")
    ap.add_argument("--target_T", type=int, default=400)
    ap.add_argument("--batch_size", type=int, default=512)
    ap.add_argument("--num_workers", type=int, default=6)
    ap.add_argument("--output_csv", default=r"E:\FYP\reports\logs\evaluation_results_comparison.csv")
    return ap.parse_args()


@torch.no_grad()
def evaluate(manifest_path, model, args, device, tag="Clean", source_filter=None):
    print(f"\n[EVAL] Evaluating on {tag} dataset:")
    df = pd.read_csv(manifest_path)
    
    # Filter by source if specified (for combined manifests)
    if source_filter and "source" in df.columns:
        df = df[df["source"] == source_filter].reset_index(drop=True)
        print(f"[FILTER] Filtered to '{source_filter}' samples: {len(df)}")
    
    df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)

    ds = StreamingFeatureDataset(
        df, feature_type=args.feature_type, max_frames=args.target_T, shuffle=False
    )
    dl = DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=True,
    )

    ys, ps = [], []
    with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
        for x, y in tqdm(dl, desc=f"{tag} Evaluation", dynamic_ncols=True, colour="cyan"):
            x = x.to(device, non_blocking=True)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[:, 1]
            ys.append(y.numpy())
            ps.append(probs.detach().cpu().numpy())

    y_true = np.concatenate(ys).astype(int)
    y_scores = np.concatenate(ps)
    y_pred = (y_scores >= 0.5).astype(int)

    eer, roc_auc = eer_and_auc(y_true, y_scores)
    tn, fp, fn, tp = confusion(y_true, y_pred)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))

    print(f"[OK] {tag} Results -> EER: {eer*100:.2f}%, AUC: {roc_auc:.3f}, Acc: {acc*100:.2f}%")
    return {
        "dataset": tag,
        "samples": len(df),
        "eer": round(eer * 100, 2),
        "auc": round(roc_auc, 3),
        "acc": round(acc * 100, 2),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp
    }


def main():
    args = parse_args()

    # --- Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        print(f"[GPU] Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[WARNING] CUDA not available - running on CPU (this will be slow).")

    # --- Model
    if args.model_type == "resnet":
        model = DeepResNetCNN().to(device)
        print("[MODEL] Using Deep ResNet CNN architecture")
    else:
        model = LCNNBaseline().to(device)
        print("[MODEL] Using LCNN Baseline architecture")
    
    ckpt = torch.load(args.ckpt, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"[OK] Loaded model checkpoint: {args.ckpt}")

    # --- Evaluate both datasets
    # Use combined manifest but filter by source to ensure correct HDF5 file
    combined_manifest = r"E:\FYP\data\features_merged\features_manifest_combined.csv"
    
    eval_configs = [
        ("Clean", combined_manifest, "clean"),
        ("Augmented", combined_manifest, "augmented"),
    ]

    results = []
    for tag, manifest, source_filter in eval_configs:
        res = evaluate(manifest, model, args, device, tag, source_filter)
        results.append(res)

    # --- Create results table
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"\n[SAVE] Saved comparison table -> {args.output_csv}\n")

    table = tabulate(
        df[["dataset", "eer", "auc", "acc"]],
        headers=["Dataset", "EER (lower)", "AUC (higher)", "ACC (higher)"],
        tablefmt="github",
        showindex=False,
    )
    print("[RESULTS] Evaluation Comparison:\n")
    print(table)
    print("\n[OK] Robustness Evaluation Complete.")


if __name__ == "__main__":
    main()
