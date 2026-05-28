#!/usr/bin/env python3
"""Validate Phase 8E-3 result artifacts."""

from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_ALLOWED = {"partial_fabrication_segment_model"}
FORBIDDEN_COLS = {
    "suspicious_segment_flag",
    "final_forensic_status",
    "fake_score",
    "real_score",
    "evidence_origin_score",
    "origin_score",
}
FORBIDDEN_FEATURE_NAMES = {
    "fabricated_baseline",
    "outside_baseline",
    "inside_outside_margin",
    "inside_outside_separation",
    "max_fabricated_overlap",
    "total_fabricated_overlap",
    "overlaps_true_fabricated_region",
    "max_fabricated_overlap_ratio",
    "timestamp_segment_label",
    "training_label_available",
    "candidate_type",
    "candidate_reason",
    "allowed_use",
    "segment_label_source",
    "has_true_timestamp_labels",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "known_origin_label",
    "known_manipulation_labels",
    "y_true",
    "y_pred_experimental",
    "y_proba_experimental",
    "fold",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8E-3 experimental outputs.")
    p.add_argument("--results_dir", default="reports/phase8/models/phase8e3")
    p.add_argument("--phase8e2_dir", default="reports/phase8/models/phase8e2")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8e3_results_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def validate(args: argparse.Namespace) -> dict[str, object]:
    blocking: list[str] = []
    warnings: list[str] = []
    base = _resolve(args.results_dir)

    req = {
        "metrics": base / "phase8e3_partial_segment_metrics_summary.csv",
        "feature_metrics": base / "phase8e3_feature_set_metrics.csv",
        "oof": base / "phase8e3_out_of_fold_segment_predictions.csv",
        "conf": base / "phase8e3_confusion_matrices.csv",
        "file_summary": base / "phase8e3_file_level_localization_summary.csv",
        "threshold_grid": base / "phase8e3_threshold_grid.csv",
        "manifest": base / "phase8e3_training_manifest.csv",
        "model_card": base / "phase8e3_model_card.md",
        "report": base / "phase8e3_training_report.md",
    }
    miss = [k for k, p in req.items() if not p.is_file()]
    if miss:
        return {"status": "FAIL", "blocking": [f"Missing required files: {miss}"], "warnings": []}

    metrics = _read(req["metrics"])
    feature_metrics = _read(req["feature_metrics"])
    oof = _read(req["oof"])
    conf = _read(req["conf"])
    manifest = _read(req["manifest"])

    # Task checks
    for name, df in [("metrics", metrics), ("oof", oof), ("conf", conf), ("manifest", manifest)]:
        if "task_name" not in df.columns:
            blocking.append(f"{name} missing task_name")
            continue
        tasks = set(df["task_name"].astype(str).unique())
        if not tasks.issubset(TASK_ALLOWED):
            blocking.append(f"{name} has unsupported tasks: {sorted(tasks - TASK_ALLOWED)}")
        if any("origin" in t or "replay" in t or "mixer" in t for t in tasks):
            blocking.append(f"{name} contains non-E3 tasks.")
        if any("fake" in t for t in tasks):
            blocking.append(f"{name} contains fake/real classifier task.")

    # Forbidden cols
    for name, df in [("metrics", metrics), ("oof", oof), ("conf", conf), ("manifest", manifest)]:
        bad = sorted(FORBIDDEN_COLS.intersection(set(df.columns)))
        if bad:
            blocking.append(f"{name} has forbidden columns: {bad}")

    # Numeric checks
    for c in ["accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc", "average_precision", "brier_score"]:
        if c in metrics.columns:
            vals = pd.to_numeric(metrics[c], errors="coerce")
            if vals.dropna().map(lambda x: not math.isfinite(float(x))).any():
                blocking.append(f"Non-finite metric values in {c}")
    for c in ["tn", "fp", "fn", "tp"]:
        if c not in conf.columns:
            blocking.append(f"Confusion file missing {c}")
        else:
            vals = pd.to_numeric(conf[c], errors="coerce")
            if vals.isna().any() or (vals < 0).any():
                blocking.append(f"Invalid confusion values in {c}")

    if "split_method" not in metrics.columns or metrics["split_method"].astype(str).str.strip().eq("").any():
        blocking.append("split_method missing in metrics.")

    # Ensure expected feature sets are present and non-empty
    expected_sets = {"localization", "acoustic", "ssl", "combined"}
    if "feature_set" in metrics.columns:
        got_sets = set(metrics["feature_set"].astype(str).unique())
        missing_sets = sorted(expected_sets - got_sets)
        if missing_sets:
            warnings.append(f"Missing feature sets in metrics (if not requested this may be expected): {missing_sets}")
    if "feature_set" in feature_metrics.columns:
        got_sets = set(feature_metrics["feature_set"].astype(str).unique())
        for s in ("acoustic", "ssl", "combined"):
            if s not in got_sets:
                warnings.append(f"Feature set not present in feature metrics: {s}")

    # Check manifest features for forbidden feature names
    pattern = "|".join(sorted(FORBIDDEN_FEATURE_NAMES))
    for feature_col in ["features_preview", "excluded_non_numeric_features", "excluded_all_missing_features"]:
        if feature_col in manifest.columns:
            bad_manifest = manifest[manifest[feature_col].astype(str).str.contains(pattern, case=False, regex=True)]
            if len(bad_manifest) and feature_col == "features_preview":
                blocking.append("Manifest features_preview includes forbidden label-derived features.")
    if "excluded_forbidden_label_derived_features" not in manifest.columns:
        blocking.append("Manifest missing excluded_forbidden_label_derived_features.")
    if "excluded_forbidden_label_derived_count" not in manifest.columns:
        blocking.append("Manifest missing excluded_forbidden_label_derived_count.")
    else:
        forbidden_ct = pd.to_numeric(manifest["excluded_forbidden_label_derived_count"], errors="coerce")
        if forbidden_ct.isna().any() or (forbidden_ct < 0).any():
            blocking.append("Manifest has invalid excluded_forbidden_label_derived_count values.")
    if "feature_leakage_check_status" not in manifest.columns:
        blocking.append("Manifest missing feature_leakage_check_status.")
    else:
        if not manifest["feature_leakage_check_status"].astype(str).str.lower().eq("passed").all():
            blocking.append("feature_leakage_check_status must be 'passed' for every feature set/fold.")
    for c in ["usable_feature_count", "excluded_all_missing_count", "excluded_non_numeric_count"]:
        if c not in manifest.columns:
            warnings.append(f"Manifest missing debug feature column: {c}")
    if "usable_feature_count" in manifest.columns:
        usable = pd.to_numeric(manifest["usable_feature_count"], errors="coerce")
        if usable.isna().any() or (usable <= 0).any():
            blocking.append("Manifest has zero/non-numeric usable_feature_count entries.")

    # Active artifacts forbidden
    active_dir = _resolve("models_saved/active")
    if active_dir.is_dir():
        if list(active_dir.glob("**/*phase8e3*")):
            blocking.append("Found phase8e3 artifacts in models_saved/active.")

    report_text = req["report"].read_text(encoding="utf-8").lower()
    for phrase in ["experimental", "no final forensic decision", "timestamp labels are used only as y_true targets", "not proof of fabrication"]:
        if phrase not in report_text:
            warnings.append(f"Training report missing phrase: '{phrase}'")
    for required in [
        "timestamp labels are used only as y_true targets",
        "excluded from phase 8e-3 model features",
    ]:
        if required not in report_text:
            blocking.append(f"Training report missing required leakage statement: '{required}'")

    # optional fold leakage check by file_id across folds
    if {"file_id", "fold", "split_method"}.issubset(set(oof.columns)):
        fold_counts = oof.groupby("file_id")["fold"].nunique()
        multi = int((fold_counts > 1).sum())
        if multi > 0 and (oof["split_method"] != "StratifiedKFold").all():
            warnings.append(f"{multi} files appear across multiple folds; check grouping logic.")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "oof_rows": len(oof),
        "metrics_rows": len(metrics),
        "task_list": sorted(set(oof["task_name"].astype(str).unique())),
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8E-3 Results Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "## Summary",
        "",
        f"- task list: {result.get('task_list', [])}",
        f"- metrics rows: {result.get('metrics_rows', 0)}",
        f"- out-of-fold rows: {result.get('oof_rows', 0)}",
    ]
    if result.get("blocking"):
        lines.extend(["", "## Blocking Errors", ""])
        lines.extend(f"- {x}" for x in result["blocking"])  # type: ignore[index]
    if result.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {x}" for x in result["warnings"])  # type: ignore[index]
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Experimental only.",
            "- No final forensic decision.",
            "- Timestamp labels used for training target preparation.",
            "- Outputs are not proof of fabrication.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result)
    print(f"Validation: {result.get('status')}")
    print(f"Report -> {out}")
    return 1 if result.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
