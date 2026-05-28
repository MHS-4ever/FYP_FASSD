#!/usr/bin/env python3
"""
Phase 8E-1A analysis only: errors, calibration review, threshold analysis.

No training, no refitting, no calibration fitting, no artifact creation.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

ALLOWED_TASKS = {"origin_file_model", "replay_file_model", "mixer_file_model"}
FORBIDDEN_TASK_PATTERNS = ("partial", "segment")
FORBIDDEN_COLUMNS = {
    "fake_score",
    "real_score",
    "final_forensic_status",
    "suspicious_segment_flag",
    "evidence_origin_score",
    "origin_score",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze Phase 8E-1 OOF predictions (analysis only).")
    p.add_argument(
        "--predictions",
        default="reports/phase8/models/phase8e1/phase8e1_out_of_fold_predictions.csv",
    )
    p.add_argument(
        "--metrics",
        default="reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
    )
    p.add_argument(
        "--confusions",
        default="reports/phase8/models/phase8e1/phase8e1_confusion_matrices.csv",
    )
    p.add_argument(
        "--training_manifest",
        default="reports/phase8/models/phase8e1/phase8e1_training_manifest.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/models/phase8e1a")
    p.add_argument(
        "--thresholds",
        default="0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90",
    )
    p.add_argument("--target_clean_fp_rate_origin", type=float, default=0.10)
    p.add_argument("--target_clean_fp_rate_manipulation", type=float, default=0.10)
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Required input missing: {p}")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def _parse_thresholds(s: str) -> list[float]:
    vals = sorted({float(x.strip()) for x in s.split(",") if x.strip()})
    if any(v < 0 or v > 1 for v in vals):
        raise ValueError("Thresholds must be within [0,1].")
    return vals


def _validate_predictions_schema(df: pd.DataFrame) -> None:
    required = {
        "task_name",
        "feature_set",
        "file_id",
        "y_true",
        "y_pred_experimental",
        "y_proba_experimental",
        "fold",
        "split_method",
        "model_type",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Predictions missing required columns: {missing}")
    tasks = set(df["task_name"].unique())
    if not tasks.issubset(ALLOWED_TASKS):
        raise ValueError(f"Found unsupported tasks: {sorted(tasks - ALLOWED_TASKS)}")
    for t in tasks:
        t_lower = str(t).lower()
        if any(p in t_lower for p in FORBIDDEN_TASK_PATTERNS):
            raise ValueError(f"Forbidden task appears in analysis input: {t}")
    found_forbidden_cols = sorted(FORBIDDEN_COLUMNS.intersection(set(df.columns)))
    if found_forbidden_cols:
        raise ValueError(f"Forbidden columns present in predictions: {found_forbidden_cols}")


def _to_binary(series: pd.Series, name: str) -> np.ndarray:
    vals = series.astype(str).str.strip()
    bad = vals[~vals.isin({"0", "1"})]
    if len(bad):
        raise ValueError(f"{name} contains non-binary values: {sorted(set(bad))[:5]}")
    return vals.astype(int).to_numpy()


def _error_type(y_true: int, y_pred: int) -> str:
    if y_true == 1 and y_pred == 1:
        return "true_positive"
    if y_true == 0 and y_pred == 0:
        return "true_negative"
    if y_true == 0 and y_pred == 1:
        return "false_positive"
    return "false_negative"


def _review_note(task: str, err: str, proba: float) -> str:
    hi = proba >= 0.80
    lo = proba <= 0.20
    if task == "origin_file_model":
        if err == "false_positive":
            return "clean human predicted as AI evidence"
        if err == "false_negative":
            return "clean AI evidence missed"
    elif task == "replay_file_model":
        if err == "false_positive":
            return "clean file predicted as replay evidence"
        if err == "false_negative":
            return "replay file missed"
    elif task == "mixer_file_model":
        if err == "false_positive":
            return "clean file predicted as mixer/channel evidence"
        if err == "false_negative":
            return "mixer/channel file missed"
    if err in {"true_positive", "true_negative"} and hi:
        return "correct high-confidence positive" if err == "true_positive" else "correct high-confidence negative"
    if err in {"true_positive", "true_negative"} and lo:
        return "correct low-confidence output"
    return "experimental evidence model output"


def _ece_with_bins(y_true: np.ndarray, y_prob: np.ndarray, bins: int = 10) -> tuple[float, float, float]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(y_true)
    ece = 0.0
    weighted_mean_prob = 0.0
    weighted_obs_rate = 0.0
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi if i < bins - 1 else y_prob <= hi)
        n = int(mask.sum())
        if n == 0:
            continue
        mp = float(np.mean(y_prob[mask]))
        op = float(np.mean(y_true[mask]))
        w = n / total
        ece += w * abs(mp - op)
        weighted_mean_prob += w * mp
        weighted_obs_rate += w * op
    return float(ece), float(weighted_mean_prob), float(weighted_obs_rate)


def _threshold_metrics(task: str, y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict[str, float | int | str]:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    total = int(len(y_true))
    pos = int((y_true == 1).sum())
    neg = int((y_true == 0).sum())
    specificity = (tn / (tn + fp)) if (tn + fp) else np.nan
    fpr = (fp / (tn + fp)) if (tn + fp) else np.nan
    fnr = (fn / (fn + tp)) if (fn + tp) else np.nan
    out: dict[str, float | int | str] = {
        "threshold": threshold,
        "total": total,
        "positives": pos,
        "negatives": neg,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "specificity": float(specificity) if math.isfinite(specificity) else np.nan,
        "false_positive_rate": float(fpr) if math.isfinite(fpr) else np.nan,
        "false_negative_rate": float(fnr) if math.isfinite(fnr) else np.nan,
        "clean_false_positive_rate": float(fpr) if math.isfinite(fpr) else np.nan,
        "positive_detected_rate": float(recall_score(y_true, y_pred, zero_division=0)),
    }
    if task == "origin_file_model":
        out.update(
            {
                "clean_human_total": neg,
                "clean_human_false_ai_count": int(fp),
                "clean_human_false_ai_rate": float(fpr) if math.isfinite(fpr) else np.nan,
                "clean_ai_total": pos,
                "clean_ai_detected_count": int(tp),
                "clean_ai_detected_rate": float(recall_score(y_true, y_pred, zero_division=0)),
            }
        )
    elif task == "replay_file_model":
        out.update(
            {
                "clean_negative_total": neg,
                "clean_false_replay_count": int(fp),
                "clean_false_replay_rate": float(fpr) if math.isfinite(fpr) else np.nan,
                "replay_total": pos,
                "replay_detected_count": int(tp),
                "replay_detected_rate": float(recall_score(y_true, y_pred, zero_division=0)),
            }
        )
    elif task == "mixer_file_model":
        out.update(
            {
                "clean_negative_total": neg,
                "clean_false_mixer_count": int(fp),
                "clean_false_mixer_rate": float(fpr) if math.isfinite(fpr) else np.nan,
                "mixer_total": pos,
                "mixer_detected_count": int(tp),
                "mixer_detected_rate": float(recall_score(y_true, y_pred, zero_division=0)),
            }
        )
    return out


def _make_plots(fig_dir: Path, pred_df: pd.DataFrame, grid_df: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    fig_dir.mkdir(parents=True, exist_ok=True)

    for (task, feat), g in pred_df.groupby(["task_name", "feature_set"]):
        y0 = pd.to_numeric(g[g["y_true"] == "0"]["y_proba_experimental"], errors="coerce").dropna().to_numpy()
        y1 = pd.to_numeric(g[g["y_true"] == "1"]["y_proba_experimental"], errors="coerce").dropna().to_numpy()
        plt.figure(figsize=(7, 4))
        plt.hist(y0, bins=10, alpha=0.6, label="y_true=0")
        plt.hist(y1, bins=10, alpha=0.6, label="y_true=1")
        plt.xlabel("Experimental probability")
        plt.ylabel("Count")
        plt.title(f"Probability Histogram: {task} / {feat}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / f"{task}__{feat}__prob_hist.png", dpi=120)
        plt.close()

    for (task, feat), g in grid_df.groupby(["task_name", "feature_set"]):
        plt.figure(figsize=(7, 4))
        plt.plot(g["threshold"], g["clean_false_positive_rate"], label="clean_false_positive_rate")
        plt.plot(g["threshold"], g["positive_detected_rate"], label="positive_detected_rate")
        plt.plot(g["threshold"], g["balanced_accuracy"], label="balanced_accuracy")
        plt.xlabel("Threshold")
        plt.ylabel("Metric")
        plt.title(f"Threshold Tradeoff: {task} / {feat}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / f"{task}__{feat}__threshold_tradeoff.png", dpi=120)
        plt.close()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pred = _load_csv(args.predictions)
    _ = _load_csv(args.metrics)
    _ = _load_csv(args.confusions)
    _ = _load_csv(args.training_manifest)
    _validate_predictions_schema(pred)
    thresholds = _parse_thresholds(args.thresholds)

    pred["y_true"] = pred["y_true"].astype(str).str.strip()
    pred["y_pred_experimental"] = pred["y_pred_experimental"].astype(str).str.strip()
    pred["y_proba_experimental"] = pd.to_numeric(pred["y_proba_experimental"], errors="coerce")
    if pred["y_proba_experimental"].isna().any():
        raise ValueError("y_proba_experimental contains non-numeric/blank values.")

    # Error cases at default threshold 0.50 (existing y_pred_experimental from Phase 8E-1).
    err_rows = []
    for _, r in pred.iterrows():
        yt = int(r["y_true"])
        yp = int(r["y_pred_experimental"])
        pr = float(r["y_proba_experimental"])
        et = _error_type(yt, yp)
        err_rows.append(
            {
                "task_name": r["task_name"],
                "feature_set": r["feature_set"],
                "file_id": r["file_id"],
                "source_group_id": r.get("source_group_id", ""),
                "y_true": yt,
                "y_pred_experimental": yp,
                "y_proba_experimental": pr,
                "error_type": et,
                "fold": r["fold"],
                "split_method": r["split_method"],
                "model_type": r["model_type"],
                "review_note": _review_note(str(r["task_name"]), et, pr),
            }
        )
    error_df = pd.DataFrame(err_rows)

    # Threshold grid, calibration, probability summaries, and recommendations.
    grid_rows = []
    calib_rows = []
    prob_rows = []
    rec_rows = []
    review_rows = []
    for (task, feat), g in pred.groupby(["task_name", "feature_set"], dropna=False):
        y_true = _to_binary(g["y_true"], "y_true")
        y_prob = g["y_proba_experimental"].to_numpy(dtype=float)
        for th in thresholds:
            row = _threshold_metrics(task, y_true, y_prob, th)
            row["task_name"] = task
            row["feature_set"] = feat
            grid_rows.append(row)
        ece, mean_prob, obs_rate = _ece_with_bins(y_true, y_prob, bins=10)
        y_pred_05 = (y_prob >= 0.5).astype(int)
        high_conf_error = int(((y_prob >= 0.80) & (y_pred_05 != y_true)).sum())
        low_conf_correct = int(((y_prob <= 0.20) & (y_pred_05 == y_true)).sum())
        calib_rows.append(
            {
                "task_name": task,
                "feature_set": feat,
                "brier_score": float(brier_score_loss(y_true, y_prob)),
                "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else np.nan,
                "average_precision": float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else np.nan,
                "expected_calibration_error_ece": float(ece),
                "calibration_bins": 10,
                "mean_predicted_probability": float(mean_prob),
                "observed_positive_rate": float(obs_rate),
                "high_confidence_error_count": high_conf_error,
                "low_confidence_correct_count": low_conf_correct,
                "interpretation_note": "Calibration reviewed from OOF probabilities only; no fitted calibration model.",
            }
        )
        for y_val in [0, 1]:
            probs = y_prob[y_true == y_val]
            if len(probs) == 0:
                continue
            prob_rows.append(
                {
                    "task_name": task,
                    "feature_set": feat,
                    "y_true_group": y_val,
                    "count": int(len(probs)),
                    "min_probability": float(np.min(probs)),
                    "q10_probability": float(np.quantile(probs, 0.10)),
                    "q25_probability": float(np.quantile(probs, 0.25)),
                    "median_probability": float(np.quantile(probs, 0.50)),
                    "q75_probability": float(np.quantile(probs, 0.75)),
                    "q90_probability": float(np.quantile(probs, 0.90)),
                    "max_probability": float(np.max(probs)),
                    "mean_probability": float(np.mean(probs)),
                    "std_probability": float(np.std(probs)),
                }
            )

    grid_df = pd.DataFrame(grid_rows)
    calib_df = pd.DataFrame(calib_rows)
    prob_df = pd.DataFrame(prob_rows)

    # Recommendations by rule.
    for (task, feat), g in grid_df.groupby(["task_name", "feature_set"], dropna=False):
        g = g.sort_values(["threshold", "balanced_accuracy"], ascending=[True, False]).copy()
        if task == "origin_file_model":
            qualifies = g[g["clean_human_false_ai_rate"] <= args.target_clean_fp_rate_origin]
            reason = "prioritize clean-human protection while preserving AI detection"
            fp_col, det_col = "clean_human_false_ai_rate", "clean_ai_detected_rate"
        elif task == "replay_file_model":
            qualifies = g[g["clean_false_replay_rate"] <= args.target_clean_fp_rate_manipulation]
            reason = "prioritize clean-negative protection while preserving replay detection"
            fp_col, det_col = "clean_false_replay_rate", "replay_detected_rate"
        else:
            qualifies = g[g["clean_false_mixer_rate"] <= args.target_clean_fp_rate_manipulation]
            reason = "prioritize clean-negative protection while preserving mixer detection"
            fp_col, det_col = "clean_false_mixer_rate", "mixer_detected_rate"
        if len(qualifies):
            best = qualifies.sort_values(["balanced_accuracy", "f1"], ascending=False).iloc[0]
            rec_rows.append(
                {
                    "task_name": task,
                    "feature_set": feat,
                    "recommended_threshold_candidate": float(best["threshold"]),
                    "reason": reason,
                    "clean_fp_rate_at_threshold": float(best.get(fp_col, np.nan)),
                    "positive_detected_rate_at_threshold": float(best.get(det_col, np.nan)),
                    "balanced_accuracy_at_threshold": float(best["balanced_accuracy"]),
                    "f1_at_threshold": float(best["f1"]),
                    "recommended_use": "candidate_for_phase8f_review",
                    "caution_note": "Candidate threshold only; requires validation and manual review.",
                }
            )
        else:
            rec_rows.append(
                {
                    "task_name": task,
                    "feature_set": feat,
                    "recommended_threshold_candidate": "",
                    "reason": reason,
                    "clean_fp_rate_at_threshold": "",
                    "positive_detected_rate_at_threshold": "",
                    "balanced_accuracy_at_threshold": "",
                    "f1_at_threshold": "",
                    "recommended_use": "manual_review_only",
                    "caution_note": "no threshold met clean false-positive constraint",
                }
            )
        # task/feature-set review row
        e = error_df[(error_df["task_name"] == task) & (error_df["feature_set"] == feat)]
        fp = int((e["error_type"] == "false_positive").sum())
        fn = int((e["error_type"] == "false_negative").sum())
        er_cnt = int((e["error_type"].isin(["false_positive", "false_negative"])).sum())
        default_row = g[g["threshold"] == 0.50]
        default_clean_fp = float(default_row["clean_false_positive_rate"].iloc[0]) if len(default_row) else np.nan
        cal = calib_df[(calib_df["task_name"] == task) & (calib_df["feature_set"] == feat)]
        ece = float(cal["expected_calibration_error_ece"].iloc[0]) if len(cal) else np.nan
        if ece <= 0.05:
            cal_q = "good_candidate"
        elif ece <= 0.10:
            cal_q = "caution"
        else:
            cal_q = "weak"
        if er_cnt == 0:
            rec_flag = "caution_candidate"
            rec_reason = "perfect result on small dataset requires caution"
        elif default_clean_fp <= 0.10:
            rec_flag = "yes_candidate"
            rec_reason = "clean false-positive behavior acceptable at default candidate threshold"
        elif default_clean_fp <= 0.20:
            rec_flag = "caution_candidate"
            rec_reason = "usable with caution and stronger validation"
        else:
            rec_flag = "no"
            rec_reason = "clean false-positive risk too high for candidate promotion"
        review_rows.append(
            {
                "task_name": task,
                "feature_set": feat,
                "metric_summary": "cross-validated experimental outputs reviewed",
                "error_count": er_cnt,
                "false_positive_count": fp,
                "false_negative_count": fn,
                "clean_false_positive_rate": default_clean_fp,
                "calibration_quality": cal_q,
                "recommended_for_phase8f": rec_flag,
                "reason": rec_reason,
            }
        )

    rec_df = pd.DataFrame(rec_rows)
    review_df = pd.DataFrame(review_rows)

    error_df.to_csv(out_dir / "phase8e1a_error_cases.csv", index=False)
    grid_df.to_csv(out_dir / "phase8e1a_threshold_grid.csv", index=False)
    calib_df.to_csv(out_dir / "phase8e1a_calibration_summary.csv", index=False)
    prob_df.to_csv(out_dir / "phase8e1a_probability_distribution_summary.csv", index=False)
    rec_df.to_csv(out_dir / "phase8e1a_threshold_recommendations.csv", index=False)
    review_df.to_csv(out_dir / "phase8e1a_task_feature_set_review.csv", index=False)

    if args.make_plots:
        _make_plots(out_dir / "figures", pred, grid_df)

    lines = [
        "# Phase 8E-1A Error / Threshold Review Report",
        "",
        "Phase 8E-1A performs analysis only on existing out-of-fold predictions.",
        "No model training/refitting/calibration fitting is performed.",
        "",
        "## Inputs Used",
        "",
        f"- predictions: `{args.predictions}`",
        f"- metrics: `{args.metrics}`",
        f"- confusions: `{args.confusions}`",
        f"- training_manifest: `{args.training_manifest}`",
        "",
        "## Task Summary",
        "",
    ]
    for task in sorted(pred["task_name"].unique()):
        lines.append(f"- {task}: analyzed feature sets {sorted(pred[pred['task_name'] == task]['feature_set'].unique())}")
    lines.extend(
        [
            "",
            "## Error Case Summary",
            "",
            f"- total error rows: {len(error_df)} (includes TP/TN/FP/FN labels)",
            f"- false positives: {int((error_df['error_type'] == 'false_positive').sum())}",
            f"- false negatives: {int((error_df['error_type'] == 'false_negative').sum())}",
            "",
            "## Threshold Grid Summary",
            "",
            f"- threshold points analyzed per task/feature_set: {len(thresholds)}",
            f"- total threshold rows: {len(grid_df)}",
            "",
            "## Calibration Summary",
            "",
        ]
    )
    for _, r in calib_df.iterrows():
        lines.append(
            f"- {r['task_name']} / {r['feature_set']}: brier={round(float(r['brier_score']),4)}, ece={round(float(r['expected_calibration_error_ece']),4)}"
        )
    lines.extend(
        [
            "",
            "## Threshold Recommendations",
            "",
        ]
    )
    for _, r in rec_df.iterrows():
        lines.append(
            f"- {r['task_name']} / {r['feature_set']}: candidate={r['recommended_threshold_candidate']} | use={r['recommended_use']} | {r['caution_note']}"
        )
    lines.extend(
        [
            "",
            "## Clean False-Positive Analysis",
            "",
            "- Origin axis prioritizes clean-human protection.",
            "- Replay and mixer axes prioritize clean-negative protection.",
            "",
            "## Phase 8F Candidate Notes",
            "",
        ]
    )
    for _, r in review_df.iterrows():
        lines.append(f"- {r['task_name']} / {r['feature_set']}: {r['recommended_for_phase8f']} ({r['reason']})")
    lines.extend(
        [
            "",
            "## Safety and Limitations",
            "",
            "- Results are from a small controlled dataset and require validation.",
            "- Candidate thresholds are not final deployment thresholds.",
            "- Outputs are not final forensic decisions.",
            "- No partial fabrication training or segment model analysis was performed.",
            "- Manual review recommended for low-confidence or conflicting evidence.",
        ]
    )
    (out_dir / "phase8e1a_review_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Phase 8E-1A analysis complete.")
    print(f"Output dir: {out_dir}")
    print("Analysis only: no training/refitting/calibration fitting performed.")
    print("No final forensic decisions created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
