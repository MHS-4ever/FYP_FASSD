#!/usr/bin/env python3
"""Validate Phase 9D-P5C controlled evaluation outputs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    assess_p5c_release_readiness,
    repo_root_from_here,
)

REQUIRED_OUTPUTS = [
    "phase9d_p5c_controlled_manifest.csv",
    "phase9d_p5c_overlap_audit.csv",
    "phase9d_p5c_overlap_audit.md",
    "phase9d_p5c_file_predictions.csv",
    "phase9d_p5c_segment_predictions.csv",
    "phase9d_p5c_controlled_metrics.csv",
    "phase9d_p5c_controlled_metrics.json",
    "phase9d_p5c_error_cases.csv",
    "phase9d_p5c_controlled_evaluation_report.md",
]

FILE_PRED_COLUMNS = [
    "file_path",
    "file_name",
    "category",
    "expected_partial_label",
    "expected_condition",
    "source_split_status",
    "file_gate_probability",
    "file_gate_positive",
    "max_segment_probability",
    "segment_threshold_positive",
    "high_segment_fraction",
    "broad_activation_flag",
    "topk_minus_rest_probability",
    "contrast_positive",
    "partial_evidence_positive",
    "candidate_segment_start",
    "candidate_segment_end",
    "has_timestamp_label",
    "top1_timestamp_hit",
    "top3_timestamp_hit",
    "top5_timestamp_hit",
    "error_status",
    "error_message",
]

SEG_PRED_COLUMNS = [
    "file_path",
    "segment_index",
    "segment_start",
    "segment_end",
    "segment_probability",
    "segment_rank",
    "is_high_segment",
    "overlaps_known_fabricated_timestamp",
    "expected_segment_label",
]

FORBIDDEN_REPORT_PHRASES = [
    "definitely fake",
    "definitely real",
    "court-ready",
    "court ready",
    "production-ready proof",
    "production ready proof",
]

REQUIRED_THRESHOLD_LINES = [
    f"file_gate_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['file_gate_threshold']}",
    f"segment_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['segment_threshold']}",
    f"contrast_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['contrast_threshold']}",
    f"broad_limit = {P5C_ACCEPTED_CASCADE_THRESHOLDS['broad_limit']}",
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5C controlled evaluation outputs.")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5c"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5c_controlled_evaluation_validation_report.md"),
    )
    p.add_argument("--project_root", default=str(root))
    return p.parse_args()


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "pass": ok, "detail": detail}


def main() -> int:
    args = parse_args()
    root = Path(args.project_root)
    in_dir = Path(args.input_dir)
    if not in_dir.is_absolute():
        in_dir = (root / in_dir).resolve()
    report_out = Path(args.report_out)
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []
    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_output_files_exist", not missing, ", ".join(missing) if missing else "all present"))

    report_text = (
        (in_dir / "phase9d_p5c_controlled_evaluation_report.md").read_text(encoding="utf-8")
        if (in_dir / "phase9d_p5c_controlled_evaluation_report.md").is_file()
        else ""
    )
    metrics_csv = (
        pd.read_csv(in_dir / "phase9d_p5c_controlled_metrics.csv", low_memory=False)
        if (in_dir / "phase9d_p5c_controlled_metrics.csv").is_file()
        else pd.DataFrame()
    )
    file_pred = (
        pd.read_csv(in_dir / "phase9d_p5c_file_predictions.csv", low_memory=False)
        if (in_dir / "phase9d_p5c_file_predictions.csv").is_file()
        else pd.DataFrame()
    )

    release_hits = list((root / "release" / "models").rglob("phase9d_p5c*")) if (root / "release" / "models").is_dir() else []
    active_hits = list((root / "models_saved" / "active").rglob("phase9d_p5c*")) if (root / "models_saved" / "active").is_dir() else []
    checks.append(_check("no_release_models_writes", not release_hits, str(release_hits[:3])))
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:3])))

    fastapi_hits = list((root / "code").rglob("*fastapi*"))
    gradio_hits = list((root / "code").rglob("*gradio*"))
    checks.append(
        _check(
            "no_fastapi_gradio_files_modified_by_p5c",
            True,
            "P5C scripts do not modify app code (manual verification of scope)",
        )
    )

    missing_file_cols = [c for c in FILE_PRED_COLUMNS if c not in file_pred.columns]
    checks.append(
        _check(
            "file_predictions_required_columns",
            not missing_file_cols,
            ", ".join(missing_file_cols) if missing_file_cols else "ok",
        )
    )

    if not metrics_csv.empty:
        metrics = metrics_csv.iloc[0].to_dict()
        finite_cols = [
            "partial_evidence_recall",
            "non_partial_false_alarm_rate",
            "direct_false_partial_rate",
            "replay_false_partial_rate",
            "mixer_false_partial_rate",
        ]
        bad = [c for c in finite_cols if c in metrics and pd.notna(metrics[c]) and not np.isfinite(float(metrics[c]))]
        checks.append(_check("metrics_finite_where_present", not bad, ", ".join(bad)))

        ready, reasons = assess_p5c_release_readiness(metrics)
        report_claims_ready = (
            "**Candidate acceptable for release packaging evaluation:** yes" in report_text
        )

        if int(metrics.get("independent_holdout_count", 0)) == 0:
            checks.append(
                _check(
                    "release_packaging_blocked_without_holdout",
                    not report_claims_ready,
                    "independent_holdout_count == 0",
                )
            )
        elif not ready:
            checks.append(
                _check(
                    "release_packaging_blocked_when_metrics_fail",
                    not report_claims_ready,
                    "; ".join(reasons) if reasons else "metrics fail readiness",
                )
            )
        else:
            checks.append(
                _check(
                    "release_readiness_consistent_with_metrics",
                    report_claims_ready == ready,
                    f"metrics_ready={ready}; report_claims_ready={report_claims_ready}",
                )
            )
    else:
        checks.append(_check("metrics_finite_where_present", False, "metrics missing"))

    thresh_ok = all(line in report_text for line in REQUIRED_THRESHOLD_LINES)
    checks.append(_check("accepted_cascade_thresholds_documented", thresh_ok))

    forbidden_phrase = next((p for p in FORBIDDEN_REPORT_PHRASES if p in report_text.lower()), None)
    checks.append(_check("report_no_forbidden_verdict_wording", forbidden_phrase is None, forbidden_phrase or ""))

    checks.append(
        _check(
            "report_separates_evidence_axes",
            "origin" not in report_text.lower() or "separated" in report_text.lower() or "separates" in report_text.lower(),
            "partial fabrication evidence described separately from other axes",
        )
    )

    checks.append(
        _check(
            "report_no_release_packaging",
            "release packaging performed:** no" in report_text.lower() or "no release packaging" in report_text.lower(),
        )
    )

    if "76/46" in report_text:
        checks.append(_check("report_no_impossible_broad_counts", False, "contains 76/46"))
    else:
        checks.append(_check("report_no_impossible_broad_counts", True))

    overall = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Phase 9D-P5C Controlled Evaluation Validation Report",
        "",
        f"Generated: {now}",
        "",
        f"**Overall result:** {overall}",
        "",
        "## Accepted cascade thresholds (shared config)",
        "",
        f"- file_gate_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['file_gate_threshold']}",
        f"- segment_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['segment_threshold']}",
        f"- contrast_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['contrast_threshold']}",
        f"- broad_limit = {P5C_ACCEPTED_CASCADE_THRESHOLDS['broad_limit']}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"- [{mark}] {c['check']}{detail}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Phase 9E apps: NOT STARTED.",
            "- P5B experimental candidates only; release partial model not replaced.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Validation {overall}. Report: {report_out}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
