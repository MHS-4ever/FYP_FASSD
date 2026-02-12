"""
Phase 5: Evaluate Phase 4 Hybrid Model on speaker-independent test set.

Outputs (default under reports/evaluation/):
- overall_metrics.csv
- asvspoof_evaluation.csv
- realworld_evaluation.csv
- per_domain_metrics.csv
- per_attack_metrics.csv
- confusion matrices (binary + multiclass)
- ROC curves (overall + domain splits)
- comprehensive_evaluation_report.md
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import torch
from torch.amp import autocast
from tqdm import tqdm

from sklearn.metrics import (
    roc_curve,
    confusion_matrix,
    classification_report,
    precision_recall_fscore_support,
)

# Add parent directory to path (code/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase4.hybrid_dataset_fast import FastHybridDataset, ChunkedDataLoader
from utils_metrics import eer_and_auc


ATTACK_TYPE_MAP = {"bonafide": 0, "synthesis": 1, "conversion": 2, "replay": 3}
ATTACK_TYPE_NAMES = ["bonafide", "synthesis", "conversion", "replay"]

def _safe_eer_and_auc(y_true: np.ndarray, y_scores: np.ndarray):
    """
    EER/AUC are undefined if y_true contains only one class.
    Return (nan, nan) in that case instead of crashing.
    """
    y_true = np.asarray(y_true)
    if np.unique(y_true).size < 2:
        return float("nan"), float("nan")
    return eer_and_auc(y_true, y_scores)


def parse_args():
    p = argparse.ArgumentParser("Phase 5 - Evaluate Hybrid Model (Phase 4)")
    p.add_argument("--ckpt", type=str, required=True, help="Checkpoint .pth (best from Phase 4)")
    p.add_argument("--test_manifest", type=str, required=True, help="Speaker-independent test manifest CSV")
    p.add_argument("--train_manifest", type=str, default=None, help="Optional train manifest CSV for speaker overlap check")
    p.add_argument("--spectrogram_h5", type=str, required=True)
    p.add_argument("--environmental_h5", type=str, required=True)
    p.add_argument("--unified_manifest", type=str, default="data/manifests/unified_manifest.csv")
    p.add_argument("--output_dir", type=str, default="reports/evaluation")
    p.add_argument("--batch_size", type=int, default=256)
    p.add_argument("--mixed_precision", type=int, default=1, help="1 to enable autocast, 0 to disable")
    p.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"])
    p.add_argument("--thresholds", type=str, default="0.5 0.65 0.70", help="Space-separated thresholds for detail evaluation (accuracy + bonafide FPR)")
    return p.parse_args()


def _ensure_dirs(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "confusion_matrices"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "figures"), exist_ok=True)


def _save_confusion_matrix_png(cm: np.ndarray, labels: list[str], title: str, out_path: str):
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(cm, interpolation="nearest")
    fig.colorbar(im, ax=ax)

    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)

    # annotate
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > cm.max() * 0.5 else "black")

    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _save_roc_png(y_true: np.ndarray, y_score: np.ndarray, title: str, out_path: str):
    import matplotlib.pyplot as plt
    from sklearn.metrics import auc as sk_auc

    y_true = np.asarray(y_true)
    if np.unique(y_true).size < 2:
        # ROC curve undefined for single-class y_true
        return

    fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=1)
    roc_auc = sk_auc(fpr, tpr)

    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(fpr, tpr, label=f"AUC={roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


@torch.no_grad()
def run_eval(df: pd.DataFrame, args, model, device) -> dict:
    dataset = FastHybridDataset(
        df,
        args.spectrogram_h5,
        args.environmental_h5,
        unified_manifest_path=args.unified_manifest,
        cache_env_in_ram=True,
        pin_memory=True,
    )
    loader = ChunkedDataLoader(dataset, batch_size=args.batch_size, shuffle=False, drop_last=False)

    y_true_bin = []
    y_score_spoof = []
    y_pred_bin = []

    y_true_mc = []
    y_pred_mc = []

    use_amp = bool(int(args.mixed_precision)) and (device.type == "cuda")

    for batch in tqdm(loader, desc="Evaluating", dynamic_ncols=True):
        x_spec = batch["spectrogram"].to(device, non_blocking=True)
        x_env = batch["environmental"].to(device, non_blocking=True)
        yb = batch["binary_label"].numpy().astype(int)
        ym = batch["multiclass_label"].numpy().astype(int)

        with autocast("cuda", enabled=use_amp):
            bin_logits, mc_logits = model(x_spec, x_env)
            bin_probs = torch.softmax(bin_logits, dim=1)[:, 1].detach().cpu().numpy()
            bin_pred = (bin_probs >= 0.5).astype(int)
            mc_pred = torch.argmax(mc_logits, dim=1).detach().cpu().numpy().astype(int)

        y_true_bin.append(yb)
        y_score_spoof.append(bin_probs)
        y_pred_bin.append(bin_pred)

        y_true_mc.append(ym)
        y_pred_mc.append(mc_pred)

    y_true_bin = np.concatenate(y_true_bin)
    y_score_spoof = np.concatenate(y_score_spoof)
    y_pred_bin = np.concatenate(y_pred_bin)

    y_true_mc = np.concatenate(y_true_mc)
    y_pred_mc = np.concatenate(y_pred_mc)

    eer, auc_score = _safe_eer_and_auc(y_true_bin, y_score_spoof)
    acc = float((y_pred_bin == y_true_bin).mean())

    tn, fp, fn, tp = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).ravel()
    bin_cm = np.array([[tn, fp], [fn, tp]], dtype=int)

    mc_cm = confusion_matrix(y_true_mc, y_pred_mc, labels=[0, 1, 2, 3])
    mc_acc = float((y_true_mc == y_pred_mc).mean())
    pr, rc, f1, sup = precision_recall_fscore_support(y_true_mc, y_pred_mc, labels=[0, 1, 2, 3], zero_division=0)

    return {
        "n": int(len(df)),
        "eer": float(eer),
        "auc": float(auc_score),
        "acc": float(acc),
        "bin_cm": bin_cm,
        "mc_cm": mc_cm,
        "mc_acc": float(mc_acc),
        "mc_pr": pr,
        "mc_rc": rc,
        "mc_f1": f1,
        "mc_support": sup,
        "y_true_bin": y_true_bin,
        "y_score_spoof": y_score_spoof,
        "y_pred_bin": y_pred_bin,
        "y_true_mc": y_true_mc,
        "y_pred_mc": y_pred_mc,
    }


def _subset_df(df: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    return df.loc[mask].reset_index(drop=True)


def main():
    args = parse_args()
    _ensure_dirs(args.output_dir)

    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"[DEVICE] {device}")
    if device.type == "cuda":
        print(f"[GPU] {torch.cuda.get_device_name(0)}")
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load checkpoint
    ckpt = torch.load(args.ckpt, map_location=device, weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)

    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    print(f"[OK] Loaded checkpoint: {args.ckpt}")

    # Load manifests
    test_df = pd.read_csv(args.test_manifest, low_memory=False)
    print(f"[DATA] Test samples: {len(test_df)}")

    # Speaker overlap verification (optional)
    speaker_overlap = None
    if args.train_manifest:
        train_df = pd.read_csv(args.train_manifest, low_memory=False, usecols=["speaker_id"])
        s_train = set(train_df["speaker_id"].astype(str).tolist())
        s_test = set(test_df["speaker_id"].astype(str).tolist()) if "speaker_id" in test_df.columns else set()
        overlap = sorted(list(s_train.intersection(s_test)))
        speaker_overlap = {"overlap_count": len(overlap), "example": overlap[:10]}
        print(f"[SPEAKER] Overlap train/test: {len(overlap)}")

    # Overall evaluation
    overall = run_eval(test_df, args, model, device)

    # Domain splits
    is_asv = test_df["dataset"].isin(["LA", "DF", "PA"]).values if "dataset" in test_df.columns else np.zeros(len(test_df), dtype=bool)
    is_rw = test_df["dataset"].isin(["RealWorld"]).values if "dataset" in test_df.columns else np.zeros(len(test_df), dtype=bool)

    asv = run_eval(_subset_df(test_df, is_asv), args, model, device) if is_asv.any() else None
    rw = run_eval(_subset_df(test_df, is_rw), args, model, device) if is_rw.any() else None

    # Save overall metrics CSVs
    overall_row = {
        "split": "overall",
        "samples": overall["n"],
        "eer": round(overall["eer"] * 100, 4),
        "auc": round(overall["auc"], 6),
        "acc": round(overall["acc"] * 100, 4),
        "multiclass_acc": round(overall["mc_acc"] * 100, 4),
    }
    pd.DataFrame([overall_row]).to_csv(os.path.join(args.output_dir, "overall_metrics.csv"), index=False)

    # Per-domain CSV
    per_domain_rows = []
    if "dataset" in test_df.columns:
        for dom in sorted(test_df["dataset"].dropna().unique().tolist()):
            m = (test_df["dataset"] == dom).values
            if not m.any():
                continue
            res = run_eval(_subset_df(test_df, m), args, model, device)
            per_domain_rows.append({
                "dataset": dom,
                "samples": res["n"],
                "eer": round(res["eer"] * 100, 4),
                "auc": round(res["auc"], 6),
                "acc": round(res["acc"] * 100, 4),
                "multiclass_acc": round(res["mc_acc"] * 100, 4),
            })
    pd.DataFrame(per_domain_rows).to_csv(os.path.join(args.output_dir, "per_domain_metrics.csv"), index=False)

    # Split CSVs
    if asv is not None:
        pd.DataFrame([{
            "split": "ASVspoof",
            "samples": asv["n"],
            "eer": round(asv["eer"] * 100, 4),
            "auc": round(asv["auc"], 6),
            "acc": round(asv["acc"] * 100, 4),
            "multiclass_acc": round(asv["mc_acc"] * 100, 4),
        }]).to_csv(os.path.join(args.output_dir, "asvspoof_evaluation.csv"), index=False)
    if rw is not None:
        pd.DataFrame([{
            "split": "RealWorld",
            "samples": rw["n"],
            "eer": round(rw["eer"] * 100, 4),
            "auc": round(rw["auc"], 6),
            "acc": round(rw["acc"] * 100, 4),
            "multiclass_acc": round(rw["mc_acc"] * 100, 4),
        }]).to_csv(os.path.join(args.output_dir, "realworld_evaluation.csv"), index=False)

    # Per-attack CSV (binary + multiclass)
    per_attack_rows = []
    if "attack_type" in test_df.columns:
        for at in sorted(test_df["attack_type"].fillna("unknown").unique().tolist()):
            m = (test_df["attack_type"].fillna("unknown") == at).values
            if not m.any():
                continue
            res = run_eval(_subset_df(test_df, m), args, model, device)
            per_attack_rows.append({
                "attack_type": at,
                "samples": res["n"],
                "eer": round(res["eer"] * 100, 4),
                "auc": round(res["auc"], 6),
                "acc": round(res["acc"] * 100, 4),
                "multiclass_acc": round(res["mc_acc"] * 100, 4),
            })
    pd.DataFrame(per_attack_rows).to_csv(os.path.join(args.output_dir, "per_attack_metrics.csv"), index=False)

    # Threshold sweep (detail evaluation): accuracy and bonafide FPR at each threshold
    thresh_list = [float(x) for x in args.thresholds.split()]
    y_true = overall["y_true_bin"]
    y_score = overall["y_score_spoof"]
    bonafide_mask = y_true == 0
    sweep_rows = []
    for t in thresh_list:
        pred = (y_score >= t).astype(int)
        acc = float((pred == y_true).mean()) * 100
        # Bonafide FPR: among bonafide samples, fraction predicted as spoof (1)
        if bonafide_mask.any():
            bonafide_fpr = float((pred[bonafide_mask] == 1).mean()) * 100
        else:
            bonafide_fpr = float("nan")
        sweep_rows.append({"threshold": t, "accuracy_pct": round(acc, 4), "bonafide_fpr_pct": round(bonafide_fpr, 4) if np.isfinite(bonafide_fpr) else None})
    pd.DataFrame(sweep_rows).to_csv(os.path.join(args.output_dir, "threshold_sweep.csv"), index=False)

    # Figures
    _save_confusion_matrix_png(overall["bin_cm"], ["bonafide(0)", "spoof(1)"], "Binary Confusion (Overall)", os.path.join(args.output_dir, "confusion_matrices", "overall_binary_cm.png"))
    _save_confusion_matrix_png(overall["mc_cm"], ATTACK_TYPE_NAMES, "Multiclass Confusion (Overall)", os.path.join(args.output_dir, "confusion_matrices", "overall_multiclass_cm.png"))

    _save_roc_png(overall["y_true_bin"], overall["y_score_spoof"], "ROC (Overall)", os.path.join(args.output_dir, "figures", "roc_overall.png"))
    if asv is not None:
        _save_roc_png(asv["y_true_bin"], asv["y_score_spoof"], "ROC (ASVspoof)", os.path.join(args.output_dir, "figures", "roc_asvspoof.png"))
    if rw is not None:
        _save_roc_png(rw["y_true_bin"], rw["y_score_spoof"], "ROC (RealWorld)", os.path.join(args.output_dir, "figures", "roc_realworld.png"))

    # Multiclass report
    mc_report = classification_report(
        overall["y_true_mc"],
        overall["y_pred_mc"],
        labels=[0, 1, 2, 3],
        target_names=ATTACK_TYPE_NAMES,
        zero_division=0,
        digits=4,
    )

    # Markdown report
    report_path = os.path.join(args.output_dir, "comprehensive_evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Phase 5: Comprehensive Evaluation Report\n\n")
        f.write(f"- Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"- Checkpoint: `{args.ckpt}`\n")
        f.write(f"- Test manifest: `{args.test_manifest}`\n")
        f.write(f"- Spectrogram H5: `{args.spectrogram_h5}`\n")
        f.write(f"- Environmental H5: `{args.environmental_h5}`\n")
        f.write(f"- Batch size: {args.batch_size}\n\n")

        if speaker_overlap is not None:
            f.write("## Speaker Overlap Check\n\n")
            f.write(f"- Overlap count: **{speaker_overlap['overlap_count']}**\n")
            f.write(f"- Example IDs: `{speaker_overlap['example']}`\n\n")

        f.write("## Overall (Test)\n\n")
        f.write(f"- Samples: **{overall['n']}**\n")
        if np.isfinite(overall["eer"]):
            f.write(f"- Binary EER: **{overall['eer']*100:.2f}%**\n")
        else:
            f.write(f"- Binary EER: **N/A (single-class subset)**\n")
        if np.isfinite(overall["auc"]):
            f.write(f"- Binary AUC: **{overall['auc']:.4f}**\n")
        else:
            f.write(f"- Binary AUC: **N/A (single-class subset)**\n")
        f.write(f"- Binary Accuracy (@0.5): **{overall['acc']*100:.2f}%**\n")
        f.write(f"- Multiclass Accuracy: **{overall['mc_acc']*100:.2f}%**\n\n")
        f.write("## Threshold sweep (detail evaluation)\n\n")
        f.write("Accuracy and bonafide FPR at multiple operating points (full test set):\n\n")
        f.write("| Threshold | Accuracy (%) | Bonafide FPR (%) |\n")
        f.write("|-----------|--------------|------------------|\n")
        for r in sweep_rows:
            bfpr = f"{r['bonafide_fpr_pct']:.2f}" if r["bonafide_fpr_pct"] is not None else "N/A"
            f.write(f"| {r['threshold']} | {r['accuracy_pct']:.2f} | {bfpr} |\n")
        f.write("\n- **Bonafide FPR**: among real (bonafide) samples, % predicted as spoof. Lower is better.\n")
        f.write("- Saved: `threshold_sweep.csv`\n\n")
        if asv is not None:
            f.write("## ASVspoof (Test)\n\n")
            f.write(f"- Samples: **{asv['n']}**\n")
            if np.isfinite(asv["eer"]):
                f.write(f"- Binary EER: **{asv['eer']*100:.2f}%**\n")
            else:
                f.write(f"- Binary EER: **N/A (single-class subset)**\n")
            if np.isfinite(asv["auc"]):
                f.write(f"- Binary AUC: **{asv['auc']:.4f}**\n\n")
            else:
                f.write(f"- Binary AUC: **N/A (single-class subset)**\n\n")

        if rw is not None:
            f.write("## RealWorld (Test)\n\n")
            f.write(f"- Samples: **{rw['n']}**\n")
            if np.isfinite(rw["eer"]):
                f.write(f"- Binary EER: **{rw['eer']*100:.2f}%**\n")
            else:
                f.write(f"- Binary EER: **N/A (single-class subset)**\n")
            if np.isfinite(rw["auc"]):
                f.write(f"- Binary AUC: **{rw['auc']:.4f}**\n\n")
            else:
                f.write(f"- Binary AUC: **N/A (single-class subset)**\n\n")

        f.write("## Multiclass (Attack Type) Classification Report (Overall)\n\n")
        f.write("```text\n")
        f.write(mc_report)
        f.write("\n```\n\n")

        f.write("## Saved Figures\n\n")
        f.write("- `confusion_matrices/overall_binary_cm.png`\n")
        f.write("- `confusion_matrices/overall_multiclass_cm.png`\n")
        f.write("- `figures/roc_overall.png`\n")
        if asv is not None:
            f.write("- `figures/roc_asvspoof.png`\n")
        if rw is not None:
            f.write("- `figures/roc_realworld.png`\n")

    print(f"[SAVE] Report -> {report_path}")
    print(f"[SAVE] CSVs and figures -> {args.output_dir}")
    print("[OK] Phase 5 evaluation complete.")


if __name__ == "__main__":
    main()


