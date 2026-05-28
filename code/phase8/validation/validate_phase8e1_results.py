#!/usr/bin/env python3
"""Validate Phase 8E-1 experimental file-level results."""

from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

ALLOWED_TASKS = {"origin_file_model", "replay_file_model", "mixer_file_model"}
FORBIDDEN_COLUMNS = {
    "final_forensic_status",
    "suspicious_segment_flag",
    "fake_score",
    "real_score",
    "evidence_origin_score",
    "origin_score",
}
FORBIDDEN_EVIDENCE_COLUMNS = {
    "evidence_origin_human_score",
    "evidence_origin_ai_score",
    "evidence_origin_mixed_score",
    "evidence_origin_unknown_score",
    "evidence_replay_score",
    "evidence_mixer_channel_score",
    "evidence_partial_fabrication_score",
    "evidence_splice_score",
    "evidence_quality_score",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8E-1 outputs.")
    p.add_argument("--results_dir", default="reports/phase8/models/phase8e1")
    p.add_argument("--phase8e0_dir", default="reports/phase8/models/phase8e0")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8e1_results_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def validate(args: argparse.Namespace) -> dict[str, object]:
    blocking: list[str] = []
    warnings: list[str] = []
    base = _resolve(args.results_dir)
    phase8e0 = _resolve(args.phase8e0_dir)

    required_csv = {
        "metrics_summary": base / "phase8e1_metrics_summary.csv",
        "task_feature_metrics": base / "phase8e1_task_feature_set_metrics.csv",
        "oof_predictions": base / "phase8e1_out_of_fold_predictions.csv",
        "confusion": base / "phase8e1_confusion_matrices.csv",
        "feature_selection": base / "phase8e1_feature_selection_summary.csv",
        "manifest": base / "phase8e1_training_manifest.csv",
    }
    required_reports = {
        "model_cards": base / "phase8e1_model_cards.md",
        "training_report": base / "phase8e1_training_report.md",
    }
    for name, p in {**required_csv, **required_reports}.items():
        if not p.is_file():
            blocking.append(f"Missing required file: {name} -> {p}")
    if blocking:
        return {"status": "FAIL", "blocking": blocking, "warnings": warnings}

    metrics = _read(required_csv["metrics_summary"])
    oof = _read(required_csv["oof_predictions"])
    confusion = _read(required_csv["confusion"])
    manifest = _read(required_csv["manifest"])
    fsel = _read(required_csv["feature_selection"])

    # Required tasks
    for task in ALLOWED_TASKS:
        if not (metrics.get("task_name", pd.Series(dtype=str)) == task).any():
            blocking.append(f"Missing metrics rows for task: {task}")

    # No partial / segment tasks
    bad_task_rows = metrics[~metrics["task_name"].isin(ALLOWED_TASKS)] if "task_name" in metrics.columns else pd.DataFrame()
    if len(bad_task_rows):
        blocking.append(f"Unsupported tasks present in metrics: {sorted(set(bad_task_rows['task_name']))}")
    if metrics["task_name"].astype(str).str.contains("partial|segment", case=False, regex=True).any():
        blocking.append("Partial or segment model appears in metrics.")

    # OOF tasks
    if not oof["task_name"].isin(ALLOWED_TASKS).all():
        blocking.append("OOF predictions include unsupported task names.")

    for df_name, df in [("metrics", metrics), ("oof", oof), ("confusion", confusion), ("manifest", manifest), ("feature_selection", fsel)]:
        hit_forbidden = sorted(FORBIDDEN_COLUMNS.intersection(set(df.columns)))
        if hit_forbidden:
            blocking.append(f"{df_name} has forbidden columns: {hit_forbidden}")
        hit_evidence = sorted(FORBIDDEN_EVIDENCE_COLUMNS.intersection(set(df.columns)))
        if hit_evidence:
            blocking.append(f"{df_name} has Phase 8B evidence columns: {hit_evidence}")
        for c in hit_evidence:
            if df[c].astype(str).str.strip().ne("").any():
                blocking.append(f"{df_name} has filled evidence values in {c}")

    # Numeric metric sanity
    numeric_cols = [
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "average_precision",
        "brier_score",
    ]
    for c in numeric_cols:
        if c in metrics.columns:
            nums = _to_num(metrics[c])
            bad = nums.dropna().map(lambda x: not math.isfinite(float(x)))
            if bad.any():
                blocking.append(f"Non-finite metric values in {c}")

    # Confusion validity
    for c in ("tn", "fp", "fn", "tp"):
        if c not in confusion.columns:
            blocking.append(f"Confusion matrix missing column: {c}")
    if all(c in confusion.columns for c in ("tn", "fp", "fn", "tp")):
        for c in ("tn", "fp", "fn", "tp"):
            vals = _to_num(confusion[c])
            if vals.isna().any() or (vals < 0).any():
                blocking.append(f"Invalid confusion counts in {c}")

    # Clean false positive metrics present
    replay_has = {"clean_false_positive_count", "clean_false_positive_rate"}.issubset(set(metrics.columns))
    origin_has = {"clean_human_false_ai_count", "clean_human_false_ai_rate"}.issubset(set(metrics.columns))
    if not replay_has:
        blocking.append("Manipulation clean false positive metrics missing.")
    if not origin_has:
        blocking.append("Origin clean-human protection metrics missing.")

    # Split method documented
    if "split_method" not in metrics.columns or metrics["split_method"].astype(str).str.strip().eq("").any():
        blocking.append("split_method missing/blank in metrics.")

    # Artifacts location check
    bad_artifacts = []
    active_dir = _resolve("models_saved/active")
    if active_dir.is_dir():
        bad_artifacts = list(active_dir.glob("**/*phase8e1*")) + list(active_dir.glob("**/*origin_file_model*")) + list(active_dir.glob("**/*replay_file_model*")) + list(active_dir.glob("**/*mixer_file_model*"))
    if bad_artifacts:
        blocking.append("Phase 8E-1 artifacts found under models_saved/active/.")

    artifacts_dir = base / "artifacts"
    if artifacts_dir.exists():
        # Allowed if present here.
        pass

    # Training report policy checks
    report_text = required_reports["training_report"].read_text(encoding="utf-8").lower()
    for phrase in [
        "experimental",
        "no final forensic decision",
        "no partial fabrication training",
        "no segment-level model",
    ]:
        if phrase not in report_text:
            warnings.append(f"Training report missing explicit phrase: '{phrase}'")

    # Optional check that phase8e0 exists and untouched presence
    if not phase8e0.is_dir():
        warnings.append(f"phase8e0 directory not found: {phase8e0}")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "metrics_rows": len(metrics),
        "oof_rows": len(oof),
        "confusion_rows": len(confusion),
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8E-1 Results Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "## Summary",
        "",
        f"- metrics rows: {result.get('metrics_rows', 0)}",
        f"- out-of-fold rows: {result.get('oof_rows', 0)}",
        f"- confusion rows: {result.get('confusion_rows', 0)}",
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
            "- Phase 8E-1 results are experimental only.",
            "- Outputs are not final forensic decisions.",
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
