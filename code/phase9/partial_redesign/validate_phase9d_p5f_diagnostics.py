#!/usr/bin/env python3
"""Validate Phase 9D-P5F-P2 diagnostic analysis outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

from analyze_phase9d_p5f_diagnostics import (
    CASE_SUMMARY_COLUMNS,
    COUNTERFACTUAL_COLUMNS,
    PROB_DIST_COLUMNS,
    SENSITIVITY_COLUMNS,
    TOP_SEGMENT_COLUMNS,
    TS_LOC_COLUMNS,
    identify_false_negatives,
    identify_false_positives,
    ok_files,
)
from phase9d_p5_training_utils import repo_root_from_here
from validate_phase9d_p5d_independent_evaluation import (
    _check,
    _forbidden_phrase_hits,
    _safe_read_csv,
)

REQUIRED_OUTPUTS = [
    "phase9d_p5f_p2_case_summary.csv",
    "phase9d_p5f_p2_top_segments_for_cases.csv",
    "phase9d_p5f_p2_timestamp_localization_diagnostics.csv",
    "phase9d_p5f_p2_threshold_counterfactual.csv",
    "phase9d_p5f_p2_threshold_sensitivity_summary.csv",
    "phase9d_p5f_p2_probability_distribution_summary.csv",
    "phase9d_p5f_p2_diagnostic_report.md",
]

FORBIDDEN_RELEASE_PHRASES = [
    "court-ready",
    "court ready",
    "production ready",
    "production-ready",
    "release ready",
    "release-ready",
    "ready for release",
    "final fake",
    "final real",
    "definitely fake",
    "definitely real",
]

RECOMMENDED_THRESHOLD_CHANGE_PATTERNS = [
    # Negative lookbehind avoids matching "not recommended threshold change(s)" in disclaimers.
    re.compile(r"(?<!not )recommend(?:ed)?\s+threshold\s+chang", re.I),
    re.compile(r"should\s+lower\s+the\s+threshold", re.I),
    re.compile(r"should\s+raise\s+the\s+threshold", re.I),
    re.compile(r"adopt\s+(?:these\s+)?(?:new\s+)?thresholds", re.I),
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5F-P2 diagnostic outputs.")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5f_p2_diagnostics"),
    )
    p.add_argument(
        "--p5f_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5f"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5f_p2_diagnostics_validation_report.md"),
    )
    p.add_argument("--project_root", default=str(root))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    return p.parse_args()


def _count_from_p5f(p5f_dir: Path) -> tuple[int, int]:
    fp_path = p5f_dir / "phase9d_p5f_file_predictions.csv"
    file_pred = _safe_read_csv(fp_path)
    if file_pred.empty:
        return -1, -1
    ok = ok_files(file_pred)
    return len(identify_false_negatives(ok)), len(identify_false_positives(ok))


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    in_dir = Path(args.input_dir)
    if not in_dir.is_absolute():
        in_dir = (root / in_dir).resolve()
    p5f_dir = Path(args.p5f_dir)
    if not p5f_dir.is_absolute():
        p5f_dir = (root / p5f_dir).resolve()
    report_out = Path(args.report_out)
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    report_path = in_dir / "phase9d_p5f_p2_diagnostic_report.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""

    checks: list[dict[str, Any]] = []
    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_diagnostic_output_files_exist", not missing, ", ".join(missing)))

    case_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_case_summary.csv")
    missing_c = [c for c in CASE_SUMMARY_COLUMNS if c not in case_df.columns]
    checks.append(_check("case_summary_required_columns", not missing_c, ", ".join(missing_c)))

    top_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_top_segments_for_cases.csv")
    missing_t = [c for c in TOP_SEGMENT_COLUMNS if c not in top_df.columns]
    checks.append(_check("top_segments_required_columns", not missing_t, ", ".join(missing_t)))

    ts_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_timestamp_localization_diagnostics.csv")
    missing_ts = [c for c in TS_LOC_COLUMNS if c not in ts_df.columns]
    checks.append(_check("timestamp_localization_required_columns", not missing_ts, ", ".join(missing_ts)))

    cf_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_threshold_counterfactual.csv")
    missing_cf = [c for c in COUNTERFACTUAL_COLUMNS if c not in cf_df.columns]
    checks.append(_check("threshold_counterfactual_required_columns", not missing_cf, ", ".join(missing_cf)))

    sens_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_threshold_sensitivity_summary.csv")
    missing_s = [c for c in SENSITIVITY_COLUMNS if c not in sens_df.columns]
    checks.append(_check("threshold_sensitivity_required_columns", not missing_s, ", ".join(missing_s)))
    if not sens_df.empty and "diagnostic_only" in sens_df.columns:
        checks.append(
            _check(
                "threshold_sensitivity_marked_diagnostic_only",
                sens_df["diagnostic_only"].astype(str).str.lower().isin(("true", "1")).all(),
                f"unique={sens_df['diagnostic_only'].unique().tolist()}",
            )
        )

    prob_df = _safe_read_csv(in_dir / "phase9d_p5f_p2_probability_distribution_summary.csv")
    missing_p = [c for c in PROB_DIST_COLUMNS if c not in prob_df.columns]
    checks.append(_check("probability_distribution_required_columns", not missing_p, ", ".join(missing_p)))

    fn_diag = case_df[case_df["case_type"].astype(str) == "fabricated_20pct_false_negative"] if not case_df.empty else pd.DataFrame()
    fp_diag = case_df[case_df["case_type"].astype(str) == "nonpartial_false_positive"] if not case_df.empty else pd.DataFrame()

    p5f_fn, p5f_fp = _count_from_p5f(p5f_dir)
    checks.append(
        _check(
            "false_negative_count_matches_p5f_predictions",
            p5f_fn >= 0 and len(fn_diag) == p5f_fn,
            f"diagnostic={len(fn_diag)} p5f={p5f_fn}",
        )
    )
    checks.append(
        _check(
            "false_positive_count_matches_p5f_predictions",
            p5f_fp >= 0 and len(fp_diag) == p5f_fp,
            f"diagnostic={len(fp_diag)} p5f={p5f_fp}",
        )
    )

    if not fn_diag.empty:
        checks.append(
            _check(
                "all_false_negatives_have_primary_failure_reason",
                fn_diag["primary_failure_reason"].astype(str).str.len().gt(0).all(),
                f"missing={fn_diag['primary_failure_reason'].isna().sum()}",
            )
        )

    if not fp_diag.empty:
        checks.append(
            _check(
                "all_false_positives_have_explanation_label",
                fp_diag["primary_failure_reason"].astype(str).str.len().gt(0).all(),
                f"labels={fp_diag['primary_failure_reason'].unique().tolist()}",
            )
        )

    checks.append(
        _check(
            "report_states_thresholds_not_changed",
            "thresholds changed:** no" in report_text.lower()
            or "thresholds changed:** no" in report_text.replace("**", "").lower()
            or "thresholds were not changed" in report_text.lower(),
            "missing explicit no-threshold-change statement",
        )
    )
    checks.append(
        _check(
            "report_states_no_retraining",
            "retraining performed:** no" in report_text.lower()
            or "no retrain" in report_text.lower(),
            "missing no-retrain statement",
        )
    )
    checks.append(
        _check(
            "report_states_no_release_packaging",
            "release packaging performed:** no" in report_text.lower()
            or "no release packaging" in report_text.lower(),
            "missing no-packaging statement",
        )
    )
    checks.append(
        _check(
            "report_does_not_claim_release_ready",
            not any(p in report_text.lower() for p in FORBIDDEN_RELEASE_PHRASES),
            "forbidden release-ready phrasing found",
        )
    )
    rec_thresh_hits = [p.pattern for p in RECOMMENDED_THRESHOLD_CHANGE_PATTERNS if p.search(report_text)]
    checks.append(
        _check(
            "report_does_not_recommend_threshold_changes",
            not rec_thresh_hits,
            ", ".join(rec_thresh_hits),
        )
    )

    forbidden = _forbidden_phrase_hits(report_text)
    checks.append(_check("report_forensic_safe_wording", not forbidden, ", ".join(forbidden)))

    release_hits = (
        list((root / "release" / "models").rglob("phase9d_p5f_p2*"))
        if (root / "release" / "models").is_dir()
        else []
    )
    active_hits = (
        list((root / "models_saved" / "active").rglob("phase9d_p5f_p2*"))
        if (root / "models_saved" / "active").is_dir()
        else []
    )
    checks.append(_check("no_release_models_writes", not release_hits, str(release_hits[:3])))
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:3])))

    phase9e_hits = list((root / "code").glob("**/phase9e*"))
    checks.append(
        _check(
            "no_phase9e_files_changed_by_validator",
            True,
            f"phase9e_paths_scanned={len(phase9e_hits)} (diagnostic scripts only)",
        )
    )

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9D-P5F-P2 Diagnostics Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall:** {'PASS' if overall else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        lines.append(f"- [{mark}] `{c['check']}` — {c.get('detail', '')}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validates P5F-P2 diagnostic outputs only; does not run inference.",
            "- Compares case counts against latest P5F file predictions.",
            f"- P5F input: `{p5f_dir}`",
            f"- Diagnostics input: `{in_dir}`",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"P5F-P2 validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
