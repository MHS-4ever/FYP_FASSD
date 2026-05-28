#!/usr/bin/env python3
"""Validate Phase 8E-1A analysis outputs."""

from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_TASKS = {"origin_file_model", "replay_file_model", "mixer_file_model"}
FORBIDDEN_COLUMNS = {
    "fake_score",
    "real_score",
    "final_forensic_status",
    "suspicious_segment_flag",
    "evidence_origin_score",
    "origin_score",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8E-1A analysis outputs.")
    p.add_argument("--analysis_dir", default="reports/phase8/models/phase8e1a")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8e1a_analysis_validation_report.md",
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
    base = _resolve(args.analysis_dir)
    req = {
        "error_cases": base / "phase8e1a_error_cases.csv",
        "threshold_grid": base / "phase8e1a_threshold_grid.csv",
        "calibration": base / "phase8e1a_calibration_summary.csv",
        "probability": base / "phase8e1a_probability_distribution_summary.csv",
        "recommendations": base / "phase8e1a_threshold_recommendations.csv",
        "review": base / "phase8e1a_task_feature_set_review.csv",
        "report": base / "phase8e1a_review_report.md",
    }
    missing = [k for k, p in req.items() if not p.is_file()]
    if missing:
        return {"status": "FAIL", "blocking": [f"Missing required files: {missing}"], "warnings": []}

    err = _read(req["error_cases"])
    grid = _read(req["threshold_grid"])
    cal = _read(req["calibration"])
    prob = _read(req["probability"])
    rec = _read(req["recommendations"])
    rev = _read(req["review"])

    required_cols = {
        "error_cases": {"task_name", "feature_set", "file_id", "y_true", "y_pred_experimental", "y_proba_experimental", "error_type"},
        "threshold_grid": {"task_name", "feature_set", "threshold", "tn", "fp", "fn", "tp", "balanced_accuracy"},
        "calibration": {"task_name", "feature_set", "brier_score", "expected_calibration_error_ece"},
        "probability": {"task_name", "feature_set", "y_true_group", "count", "median_probability"},
        "recommendations": {"task_name", "feature_set", "recommended_threshold_candidate", "recommended_use"},
        "review": {"task_name", "feature_set", "recommended_for_phase8f", "reason"},
    }
    for name, cols in required_cols.items():
        df = {"error_cases": err, "threshold_grid": grid, "calibration": cal, "probability": prob, "recommendations": rec, "review": rev}[name]
        miss = sorted(cols - set(df.columns))
        if miss:
            blocking.append(f"{name} missing required columns: {miss}")

    for name, df in [("error_cases", err), ("threshold_grid", grid), ("calibration", cal), ("probability", prob), ("recommendations", rec), ("review", rev)]:
        tasks = set(df.get("task_name", pd.Series(dtype=str)).unique())
        if not tasks.issubset(ALLOWED_TASKS):
            blocking.append(f"{name} has unsupported tasks: {sorted(tasks - ALLOWED_TASKS)}")
        if df.get("task_name", pd.Series(dtype=str)).astype(str).str.contains("partial|segment", case=False, regex=True).any():
            blocking.append(f"{name} includes partial/segment task rows")
        bad_cols = sorted(FORBIDDEN_COLUMNS.intersection(set(df.columns)))
        if bad_cols:
            blocking.append(f"{name} has forbidden columns: {bad_cols}")

    # Threshold bounds.
    if "threshold" in grid.columns:
        th = pd.to_numeric(grid["threshold"], errors="coerce")
        if th.isna().any() or (th < 0).any() or (th > 1).any():
            blocking.append("threshold_grid has invalid threshold values outside [0,1].")

    # Numeric finite check for representative metrics.
    metric_cols = [
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "specificity",
        "false_positive_rate",
        "false_negative_rate",
        "clean_false_positive_rate",
        "positive_detected_rate",
    ]
    for c in metric_cols:
        if c in grid.columns:
            vals = pd.to_numeric(grid[c], errors="coerce")
            bad = vals.dropna().map(lambda x: not math.isfinite(float(x)))
            if bad.any():
                blocking.append(f"Non-finite values in threshold grid metric column: {c}")

    if len(rec) == 0:
        blocking.append("Threshold recommendations are empty.")

    report_txt = req["report"].read_text(encoding="utf-8").lower()
    for phrase in [
        "analysis only",
        "no training",
        "no calibration fitting",
        "not final forensic decisions",
        "no partial fabrication",
    ]:
        if phrase not in report_txt:
            warnings.append(f"Review report missing phrase: '{phrase}'")

    # No model artifacts in analysis dir.
    bad_artifacts = list(base.glob("*.joblib")) + list(base.glob("*.pkl")) + list(base.glob("*.pt"))
    if bad_artifacts:
        blocking.append(f"Unexpected model artifacts in analysis dir: {[p.name for p in bad_artifacts]}")
    active_dir = _resolve("models_saved/active")
    if active_dir.is_dir():
        any_active = list(active_dir.glob("**/*phase8e1a*"))
        if any_active:
            blocking.append("Found phase8e1a artifacts under models_saved/active.")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "tasks": sorted(set(err["task_name"].unique())),
        "threshold_recommendation_count": len(rec),
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8E-1A Analysis Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "## Summary",
        "",
        f"- tasks: {result.get('tasks', [])}",
        f"- threshold recommendation count: {result.get('threshold_recommendation_count', 0)}",
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
            "- Phase 8E-1A is analysis-only and does not train/refit/calibrate models.",
            "- Candidate thresholds are not final forensic decisions.",
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
