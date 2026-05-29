#!/usr/bin/env python3
"""Validate Phase 9D-P5B experimental training outputs."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_training_utils import (
    CASCADE_ACCEPTANCE_CONFIG,
    FILE_GATE_FEATURE_SETS,
    SEGMENT_FEATURE_SETS,
    assess_cascade_release_ready,
    check_training_report_cascade_alignment,
    compute_cascade_acceptance_diagnostics,
    format_acceptance_config_table,
    get_recommended_cascade_rows,
    parse_forbidden_feature_hits,
    repo_root_from_here,
)

REQUIRED_OUTPUTS = [
    "phase9d_p5b_file_gate_metrics.csv",
    "phase9d_p5b_file_gate_oof_predictions.csv",
    "phase9d_p5b_file_gate_threshold_grid.csv",
    "phase9d_p5b_segment_localizer_metrics.csv",
    "phase9d_p5b_segment_oof_predictions.csv",
    "phase9d_p5b_segment_threshold_grid.csv",
    "phase9d_p5b_segment_file_localization_metrics.csv",
    "phase9d_p5b_cascade_simulation_results.csv",
    "phase9d_p5b_feature_audit.csv",
    "phase9d_p5b_training_report.md",
]

FORBIDDEN_OUTPUT_TOKENS = ("fake_score", "real_score")
METRIC_COLS = (
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "average_precision",
    "brier_score",
)

CASCADE_REQUIRED_COLUMNS = (
    "file_gate_threshold",
    "segment_threshold",
    "contrast_threshold",
    "broad_limit",
    "partial_file_recall",
    "non_partial_false_alarm_rate",
    "direct_false_partial_rate",
    "replay_false_partial_rate",
    "mixer_false_partial_rate",
    "top1_hit_rate_when_positive",
    "top3_hit_rate_when_positive",
    "top5_hit_rate_when_positive",
    "broad_activation_rate_when_positive",
    "gated_partial_file_count",
    "recommended_threshold_pair",
    "recommendation_reason",
)


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5B training outputs.")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5b_training_validation_report.md"),
    )
    p.add_argument(
        "--project_root",
        default=str(root),
    )
    return p.parse_args()


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "pass": ok, "detail": detail}


def _finite_metrics(df: pd.DataFrame) -> tuple[bool, str]:
    if df.empty:
        return False, "metrics dataframe empty"
    bad = []
    for col in METRIC_COLS:
        if col not in df.columns:
            continue
        vals = pd.to_numeric(df[col], errors="coerce")
        if vals.notna().any() and not np.isfinite(vals.dropna()).all():
            bad.append(col)
    return (not bad, ", ".join(bad))


def _parse_broad_fraction(text: str) -> tuple[int | None, int | None]:
    m = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


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
    cascade_diagnostics: dict = {}

    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_output_files_exist", not missing, ", ".join(missing) if missing else "all present"))

    file_metrics = pd.read_csv(in_dir / "phase9d_p5b_file_gate_metrics.csv", low_memory=False) if (in_dir / "phase9d_p5b_file_gate_metrics.csv").is_file() else pd.DataFrame()
    seg_metrics = pd.read_csv(in_dir / "phase9d_p5b_segment_localizer_metrics.csv", low_memory=False) if (in_dir / "phase9d_p5b_segment_localizer_metrics.csv").is_file() else pd.DataFrame()
    file_oof = pd.read_csv(in_dir / "phase9d_p5b_file_gate_oof_predictions.csv", low_memory=False) if (in_dir / "phase9d_p5b_file_gate_oof_predictions.csv").is_file() else pd.DataFrame()
    seg_oof = pd.read_csv(in_dir / "phase9d_p5b_segment_oof_predictions.csv", low_memory=False) if (in_dir / "phase9d_p5b_segment_oof_predictions.csv").is_file() else pd.DataFrame()
    audit = pd.read_csv(in_dir / "phase9d_p5b_feature_audit.csv", low_memory=False) if (in_dir / "phase9d_p5b_feature_audit.csv").is_file() else pd.DataFrame()
    cascade = pd.read_csv(in_dir / "phase9d_p5b_cascade_simulation_results.csv", low_memory=False) if (in_dir / "phase9d_p5b_cascade_simulation_results.csv").is_file() else pd.DataFrame()
    report_text = (in_dir / "phase9d_p5b_training_report.md").read_text(encoding="utf-8") if (in_dir / "phase9d_p5b_training_report.md").is_file() else ""

    for fs in FILE_GATE_FEATURE_SETS:
        present = fs in set(file_metrics.get("feature_set", pd.Series(dtype=str)).astype(str))
        checks.append(_check(f"file_gate_metrics_{fs}", present, f"feature_set={fs}"))

    for fs in SEGMENT_FEATURE_SETS:
        present = fs in set(seg_metrics.get("feature_set", pd.Series(dtype=str)).astype(str))
        checks.append(_check(f"segment_metrics_{fs}", present, f"feature_set={fs}"))

    checks.append(_check("file_gate_oof_exists", not file_oof.empty, f"rows={len(file_oof)}"))
    checks.append(_check("segment_oof_exists", not seg_oof.empty, f"rows={len(seg_oof)}"))

    ok_fm, det_fm = _finite_metrics(file_metrics)
    checks.append(_check("file_gate_metrics_finite", ok_fm, det_fm))
    ok_sm, det_sm = _finite_metrics(seg_metrics)
    checks.append(_check("segment_metrics_finite", ok_sm, det_sm))

    if not audit.empty:
        leakage_ok = (audit["leakage_check_status"].astype(str) == "passed").all()
        checks.append(_check("feature_audit_leakage_passed", bool(leakage_ok)))
        integrity_ok = (audit.get("group_integrity_status", pd.Series(["passed"])) == "passed").all()
        checks.append(_check("group_integrity_documented", bool(integrity_ok), str(audit["split_method"].unique().tolist())))
    else:
        checks.append(_check("feature_audit_leakage_passed", False, "audit missing"))
        checks.append(_check("group_integrity_documented", False))

    forbidden_in_audit: list[str] = []
    if not audit.empty and "forbidden_feature_hits" in audit.columns:
        for hits in audit["forbidden_feature_hits"]:
            forbidden_in_audit.extend(parse_forbidden_feature_hits(hits))
    checks.append(_check("forbidden_features_not_used", not forbidden_in_audit, ";".join(forbidden_in_audit[:20])))

    split_doc = "StratifiedGroupKFold" in report_text or "GroupKFold" in report_text or (
        not audit.empty and audit["split_method"].astype(str).str.contains("Group").any()
    )
    checks.append(_check("group_aware_split_documented", bool(split_doc)))

    group_ok = True
    if not audit.empty and "group_integrity_violations" in audit.columns:
        group_ok = int(pd.to_numeric(audit["group_integrity_violations"], errors="coerce").fillna(0).max()) == 0
    checks.append(_check("same_file_not_split_across_folds", group_ok))

    checks.append(_check("cascade_simulation_exists", not cascade.empty, f"rows={len(cascade)}"))
    missing_cascade_cols = [c for c in CASCADE_REQUIRED_COLUMNS if c not in cascade.columns]
    checks.append(
        _check(
            "cascade_has_localized_evidence_columns",
            not missing_cascade_cols,
            ", ".join(missing_cascade_cols) if missing_cascade_cols else "contrast_threshold and broad_limit present",
        )
    )

    cascade_diagnostics = compute_cascade_acceptance_diagnostics(cascade, CASCADE_ACCEPTANCE_CONFIG)
    release_ok, release_detail = assess_cascade_release_ready(cascade, CASCADE_ACCEPTANCE_CONFIG)
    checks.append(_check("cascade_release_ready_recommendation", release_ok, release_detail))

    align_ok, align_detail = check_training_report_cascade_alignment(report_text, cascade, CASCADE_ACCEPTANCE_CONFIG)
    checks.append(_check("training_report_cascade_alignment", align_ok, align_detail))

    broad_ok = True
    broad_detail = ""
    if report_text:
        if "76/46" in report_text:
            broad_ok = False
            broad_detail = "report contains legacy impossible broad-activation count 76/46"
        else:
            m = re.search(r"P5B broad activation \(selected\):\s*(\d+)\s*/\s*(\d+)", report_text, re.IGNORECASE)
            if m:
                broad_num, partial_num = int(m.group(1)), int(m.group(2))
                broad_ok = broad_num <= partial_num
                broad_detail = f"broad={broad_num}/{partial_num}"
            else:
                broad_num, partial_num = _parse_broad_fraction(report_text)
                if broad_num is not None and partial_num is not None:
                    broad_ok = broad_num <= partial_num and partial_num <= 100
                    broad_detail = f"broad={broad_num}/{partial_num}"
    checks.append(_check("report_broad_activation_counts_plausible", broad_ok, broad_detail))

    checks.append(
        _check(
            "report_no_release_packaging",
            "release packaging performed:** no" in report_text.lower() or "no release packaging" in report_text.lower(),
        )
    )
    checks.append(
        _check(
            "report_no_packaging_evaluation_claim",
            "consider phase 9d-p5c packaging evaluation" not in report_text.lower(),
            "report must not recommend packaging when validation rules are not met",
        )
    )

    release_hits = list((root / "release" / "models").rglob("phase9d_p5b*")) if (root / "release" / "models").is_dir() else []
    active_hits = list((root / "models_saved" / "active").rglob("phase9d_p5b*")) if (root / "models_saved" / "active").is_dir() else []
    checks.append(_check("no_release_models_writes", not release_hits, str(release_hits[:5])))
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:5])))

    forbidden_cols = [c for c in pd.concat([file_oof, seg_oof], ignore_index=True).columns if c.lower() in FORBIDDEN_OUTPUT_TOKENS]
    checks.append(_check("no_fake_real_score_fields", not forbidden_cols, ", ".join(forbidden_cols)))

    overall = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Phase 9D-P5B Training Validation Report",
        "",
        f"Generated: {now}",
        "",
        f"**Overall result:** {overall}",
        "",
        "## Shared cascade acceptance thresholds",
        "",
        format_acceptance_config_table(CASCADE_ACCEPTANCE_CONFIG),
        "",
        "## Cascade diagnostics (from CSV)",
        "",
    ]

    min_direct = cascade_diagnostics.get("min_direct_false_partial_rate", np.nan)
    min_non_partial = cascade_diagnostics.get("min_non_partial_false_alarm_rate", np.nan)
    lines.append(f"- Minimum observed direct_false_partial_rate: {min_direct:.4f}" if np.isfinite(min_direct) else "- Minimum observed direct_false_partial_rate: n/a")
    lines.append(
        f"- Minimum observed non_partial_false_alarm_rate: {min_non_partial:.4f}"
        if np.isfinite(min_non_partial)
        else "- Minimum observed non_partial_false_alarm_rate: n/a"
    )
    rec_rows = get_recommended_cascade_rows(cascade)
    lines.append(f"- Valid recommended_threshold_pair rows in CSV: {len(rec_rows)}")
    lines.append(f"- Release-ready assessment: {'PASS' if release_ok else 'FAIL'} — {release_detail}")
    lines.append(f"- Report/CSV alignment: {'PASS' if align_ok else 'FAIL'} — {align_detail}")
    lines.extend(["", "## Checks", ""])

    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"- [{mark}] {c['check']}{detail}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validates experimental P5B outputs only.",
            "- Phase 9E apps: NOT STARTED.",
            "- Release partial model NOT replaced by this phase.",
            "- P5B-P2: training, report, and validator share CASCADE_ACCEPTANCE_CONFIG.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Validation {overall}. Report: {report_out}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
