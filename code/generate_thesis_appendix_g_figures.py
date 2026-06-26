"""
Generate thesis Appendix G figures G.1–G.4 from saved checkpoints and documented eval splits.

Outputs (default: submissions/thesis_preparation/figures/appendix_g/):
  G1_baseline_lcnn_confusion_matrix.png
  G2_resnet_confusion_matrix.png
  G3_hybrid_roc_curve.png
  G4_hybrid_multiclass_confusion_matrix.png
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import auc, confusion_matrix, roc_curve
from torch.utils.data import DataLoader
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_loading.streaming_dataset_loader import StreamingFeatureDataset
from models.baseline_cnn import LCNNBaseline
from models.resnet_cnn import DeepResNetCNN
from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase4.hybrid_dataset_fast import ChunkedDataLoader, FastHybridDataset
from utils_metrics import eer_and_auc


def _save_cm_png(
    cm: np.ndarray,
    labels: list[str],
    title: str,
    out_path: str,
    xlabel: str = "Predicted label",
    ylabel: str = "True label",
):
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    fig.colorbar(im, ax=ax)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    thresh = cm.max() * 0.5 if cm.size else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = int(cm[i, j])
            ax.text(
                j,
                i,
                f"{val:,}",
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=9,
            )
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVE] {out_path}")


def _save_roc_png(y_true: np.ndarray, y_score: np.ndarray, title: str, out_path: str):
    fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=1)
    roc_auc = auc(fpr, tpr)
    eer, _ = eer_and_auc(y_true, y_score)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(fpr, tpr, linewidth=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    ax.text(
        0.55,
        0.08,
        f"EER = {eer * 100:.2f}%",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVE] {out_path}")


@torch.no_grad()
def _eval_binary_cnn(
    manifest_path: str,
    source_filter: str,
    feature_type: str,
    ckpt_path: str,
    model_kind: str,
    device: torch.device,
    batch_size: int = 512,
):
    df = pd.read_csv(manifest_path)
    if source_filter and "source" in df.columns:
        df = df[df["source"] == source_filter].reset_index(drop=True)
    df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)

    ds = StreamingFeatureDataset(df, feature_type=feature_type, max_frames=400, shuffle=False)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=device.type == "cuda")

    if model_kind == "resnet":
        model = DeepResNetCNN().to(device)
    else:
        model = LCNNBaseline().to(device)

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    model.eval()

    ys, ps = [], []
    for x, y in tqdm(dl, desc=f"{model_kind}/{source_filter}", dynamic_ncols=True):
        x = x.to(device)
        logits = model(x)
        prob = torch.softmax(logits, dim=1)[:, 1]
        ys.append(y.numpy())
        ps.append(prob.detach().cpu().numpy())

    y_true = np.concatenate(ys).astype(int)
    y_score = np.concatenate(ps)
    y_pred = (y_score >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    eer, roc_auc = eer_and_auc(y_true, y_score)
    return cm, y_true, y_score, eer, roc_auc, len(df)


@torch.no_grad()
def _eval_hybrid(test_manifest: str, ckpt_path: str, spec_h5: str, env_h5: str, unified_manifest: str, device: torch.device, batch_size: int = 128):
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    test_df = pd.read_csv(test_manifest, low_memory=False)
    ds = FastHybridDataset(
        test_df,
        spec_h5,
        env_h5,
        unified_manifest_path=unified_manifest,
        cache_env_in_ram=True,
        pin_memory=device.type == "cuda",
    )
    dl = ChunkedDataLoader(ds, batch_size=batch_size, shuffle=False, drop_last=False)

    y_true_bin, y_score, y_true_mc, y_pred_mc = [], [], [], []

    for batch in tqdm(dl, desc="hybrid", dynamic_ncols=True):
        spec = batch["spectrogram"].to(device, non_blocking=True)
        env = batch["environmental"].to(device, non_blocking=True)
        yb = batch["binary_label"].numpy().astype(int)
        ym = batch["multiclass_label"].numpy().astype(int)

        with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
            bin_logits, mc_logits = model(spec, env)

        bin_prob = torch.softmax(bin_logits, dim=1)[:, 1].detach().cpu().numpy()
        mc_pred = torch.argmax(mc_logits, dim=1).detach().cpu().numpy().astype(int)

        y_true_bin.append(yb)
        y_score.append(bin_prob)
        y_true_mc.append(ym)
        y_pred_mc.append(mc_pred)

    y_true_bin = np.concatenate(y_true_bin).astype(int)
    y_score = np.concatenate(y_score)
    y_true_mc = np.concatenate(y_true_mc)
    y_pred_mc = np.concatenate(y_pred_mc)

    bin_cm = confusion_matrix(y_true_bin, (y_score >= 0.5).astype(int), labels=[0, 1])
    mc_cm = confusion_matrix(y_true_mc, y_pred_mc, labels=[0, 1, 2, 3])
    mc_acc = float((y_true_mc == y_pred_mc).mean())
    eer, roc_auc = eer_and_auc(y_true_bin, y_score)
    return bin_cm, mc_cm, y_true_bin, y_score, eer, roc_auc, mc_acc, len(test_df)


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    p = argparse.ArgumentParser()
    p.add_argument("--output_dir", default=os.path.join(root, "submissions", "thesis_preparation", "figures", "appendix_g"))
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--batch_size_cnn", type=int, default=512)
    p.add_argument("--batch_size_hybrid", type=int, default=128)
    args = p.parse_args()

    device = torch.device(args.device)
    print(f"[DEVICE] {device}")

    combined_manifest = os.path.join(root, "data", "features_merged", "features_manifest_combined.csv")
    test_manifest = os.path.join(root, "data", "manifests", "test_speaker_independent.csv")
    unified_manifest = os.path.join(root, "data", "manifests", "unified_manifest.csv")
    spec_h5 = os.path.join(root, "data", "features", "logmel_chunked.h5")
    env_h5 = os.path.join(root, "data", "features", "environmental_packed.h5")

    # G.1 Baseline LCNN (LFCC robust, augmented test)
    cm_g1, _, _, eer_g1, auc_g1, n_g1 = _eval_binary_cnn(
        combined_manifest,
        "augmented",
        "lfcc",
        os.path.join(root, "models_saved", "baseline_cnn_lfcc_robust.pth"),
        "baseline",
        device,
        args.batch_size_cnn,
    )
    _save_cm_png(
        cm_g1,
        ["Bonafide", "Spoof"],
        f"Baseline CNN/LCNN — Augmented Test (n={n_g1:,})\nEER={eer_g1*100:.2f}%, AUC={auc_g1:.3f}",
        os.path.join(args.output_dir, "G1_baseline_lcnn_confusion_matrix.png"),
    )

    # G.2 ResNet (log-mel robust, augmented test)
    cm_g2, _, _, eer_g2, auc_g2, n_g2 = _eval_binary_cnn(
        combined_manifest,
        "augmented",
        "mel",
        os.path.join(root, "models_saved", "resnet_cnn_mel_robust.pth"),
        "resnet",
        device,
        args.batch_size_cnn,
    )
    _save_cm_png(
        cm_g2,
        ["Bonafide", "Spoof"],
        f"ResNet CNN — Augmented Test (n={n_g2:,})\nEER={eer_g2*100:.2f}%, AUC={auc_g2:.3f}",
        os.path.join(args.output_dir, "G2_resnet_confusion_matrix.png"),
    )

    # G.3 + G.4 Hybrid on speaker-independent test
    _, mc_cm, y_true, y_score, eer_h, auc_h, mc_acc, n_h = _eval_hybrid(
        test_manifest,
        os.path.join(root, "models_saved", "hybrid_resnet_environmental_best.pth"),
        spec_h5,
        env_h5,
        unified_manifest,
        device,
        args.batch_size_hybrid,
    )
    _save_roc_png(
        y_true,
        y_score,
        f"HybridResNetEnvironmental — Overall Test (n={n_h:,})",
        os.path.join(args.output_dir, "G3_hybrid_roc_curve.png"),
    )
    _save_cm_png(
        mc_cm,
        ["Bonafide", "Synthesis", "Conversion", "Replay"],
        f"HybridResNetEnvironmental — Multiclass Confusion (n={n_h:,})\nMulticlass accuracy = {mc_acc*100:.2f}%",
        os.path.join(args.output_dir, "G4_hybrid_multiclass_confusion_matrix.png"),
    )

    # Also copy to reports/evaluation for repo consistency
    eval_dir = os.path.join(root, "reports", "evaluation")
    os.makedirs(os.path.join(eval_dir, "confusion_matrices"), exist_ok=True)
    os.makedirs(os.path.join(eval_dir, "figures"), exist_ok=True)

    summary_path = os.path.join(args.output_dir, "appendix_g_figure_metadata.csv")
    pd.DataFrame(
        [
            {"figure": "G.1", "file": "G1_baseline_lcnn_confusion_matrix.png", "model": "baseline_cnn_lfcc_robust", "split": "augmented", "n": n_g1, "eer_pct": round(eer_g1 * 100, 2), "auc": round(auc_g1, 4)},
            {"figure": "G.2", "file": "G2_resnet_confusion_matrix.png", "model": "resnet_cnn_mel_robust", "split": "augmented", "n": n_g2, "eer_pct": round(eer_g2 * 100, 2), "auc": round(auc_g2, 4)},
            {"figure": "G.3", "file": "G3_hybrid_roc_curve.png", "model": "hybrid_resnet_environmental_best", "split": "test_speaker_independent", "n": n_h, "eer_pct": round(eer_h * 100, 2), "auc": round(auc_h, 4)},
            {"figure": "G.4", "file": "G4_hybrid_multiclass_confusion_matrix.png", "model": "hybrid_resnet_environmental_best", "split": "test_speaker_independent", "n": n_h, "eer_pct": round(eer_h * 100, 2), "auc": round(auc_h, 4)},
        ]
    ).to_csv(summary_path, index=False)
    print(f"[SAVE] {summary_path}")
    print("[DONE] Appendix G figures generated.")


if __name__ == "__main__":
    main()
