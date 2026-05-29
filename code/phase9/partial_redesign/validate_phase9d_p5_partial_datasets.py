#!/usr/bin/env python3
"""Validate Phase 9D-P5 partial redesign datasets before training."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

from phase9d_p5_partial_utils import (
    FILE_GATE_METADATA_COLUMNS,
    SEGMENT_METADATA_COLUMNS,
    SEGMENT_NEGATIVE_SOURCE_TYPES,
    TIMESTAMP_LIKE_FEATURE_EXACT,
    is_forbidden_feature,
    repo_root_from_here,
)


REQUIRED_OUTPUTS = [
    "phase9d_p5_file_partial_gate_dataset.csv",
    "phase9d_p5_segment_partial_localizer_dataset.csv",
    "phase9d_p5_timestamp_target_audit.csv",
    "phase9d_p5_feature_leakage_audit.csv",
    "phase9d_p5_dataset_balance_summary.csv",
    "phase9d_p5_partial_redesign_report.md",
    "phase9d_p5_file_gate_feature_columns.json",
    "phase9d_p5_segment_localizer_feature_columns.json",
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5 partial datasets.")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5_partial_dataset_validation_report.md"),
    )
    return p.parse_args()


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "pass": ok, "detail": detail}


def main() -> int:
    args = parse_args()
    root = repo_root_from_here(Path(__file__))
    in_dir = Path(args.input_dir)
    if not in_dir.is_absolute():
        in_dir = (root / in_dir).resolve()
    report_out = Path(args.report_out)
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []
    warnings: list[str] = []

    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_output_files_exist", not missing, ", ".join(missing) if missing else "all present"))

    file_gate_path = in_dir / "phase9d_p5_file_partial_gate_dataset.csv"
    segment_path = in_dir / "phase9d_p5_segment_partial_localizer_dataset.csv"
    ts_audit_path = in_dir / "phase9d_p5_timestamp_target_audit.csv"
    leakage_path = in_dir / "phase9d_p5_feature_leakage_audit.csv"
    balance_path = in_dir / "phase9d_p5_dataset_balance_summary.csv"
    redesign_report_path = in_dir / "phase9d_p5_partial_redesign_report.md"
    file_feat_json = in_dir / "phase9d_p5_file_gate_feature_columns.json"
    seg_feat_json = in_dir / "phase9d_p5_segment_localizer_feature_columns.json"

    file_gate = pd.read_csv(file_gate_path, low_memory=False) if file_gate_path.is_file() else pd.DataFrame()
    segment = pd.read_csv(segment_path, low_memory=False) if segment_path.is_file() else pd.DataFrame()
    ts_audit = pd.read_csv(ts_audit_path, low_memory=False) if ts_audit_path.is_file() else pd.DataFrame()
    leakage = pd.read_csv(leakage_path, low_memory=False) if leakage_path.is_file() else pd.DataFrame()
    balance = pd.read_csv(balance_path, low_memory=False) if balance_path.is_file() else pd.DataFrame()

    if not file_gate.empty:
        fg_pos = (file_gate["target_is_partial_fabrication_file"].astype(str) == "1").any()
        fg_neg = (file_gate["target_is_partial_fabrication_file"].astype(str) == "0").any()
        checks.append(_check("file_gate_has_positive_and_negative", fg_pos and fg_neg))

        missing_meta = [c for c in FILE_GATE_METADATA_COLUMNS if c not in file_gate.columns]
        checks.append(_check("file_gate_metadata_columns", not missing_meta, ", ".join(missing_meta)))

        forbidden_tokens = [c for c in file_gate.columns if c.lower() in {"fake_score", "real_score"}]
        checks.append(_check("file_gate_no_fake_real_score", not forbidden_tokens, ", ".join(forbidden_tokens)))
    else:
        checks.extend(
            [
                _check("file_gate_has_positive_and_negative", False, "file gate dataset missing"),
                _check("file_gate_metadata_columns", False),
                _check("file_gate_no_fake_real_score", False),
            ]
        )

    if not segment.empty:
        seg_pos = (segment["target_is_fabricated_segment"].astype(str) == "1").any()
        seg_neg = (segment["target_is_fabricated_segment"].astype(str) == "0").any()
        checks.append(_check("segment_has_positive_and_negative", seg_pos and seg_neg))

        neg_types_present = {
            st: bool((segment["segment_source_type"] == st).any())
            for st in SEGMENT_NEGATIVE_SOURCE_TYPES
        }
        checks.append(
            _check(
                "segment_negatives_include_all_categories",
                all(neg_types_present.values()),
                json.dumps(neg_types_present),
            )
        )

        missing_meta = [c for c in SEGMENT_METADATA_COLUMNS if c not in segment.columns]
        checks.append(_check("segment_metadata_columns", not missing_meta, ", ".join(missing_meta)))

        forbidden_tokens = [c for c in segment.columns if c.lower() in {"fake_score", "real_score"}]
        checks.append(_check("segment_no_fake_real_score", not forbidden_tokens, ", ".join(forbidden_tokens)))
    else:
        checks.extend(
            [
                _check("segment_has_positive_and_negative", False, "segment dataset missing"),
                _check("segment_negatives_include_all_categories", False),
                _check("segment_metadata_columns", False),
                _check("segment_no_fake_real_score", False),
            ]
        )

    matched_rows = int((ts_audit["match_status"] == "matched").sum()) if not ts_audit.empty else 0
    checks.append(_check("timestamp_audit_has_matched_rows", matched_rows > 0, f"matched={matched_rows}"))

    file_feats = json.loads(file_feat_json.read_text(encoding="utf-8")) if file_feat_json.is_file() else []
    seg_feats = json.loads(seg_feat_json.read_text(encoding="utf-8")) if seg_feat_json.is_file() else []
    ts_in_feats = [
        c
        for c in file_feats + seg_feats
        if c in TIMESTAMP_LIKE_FEATURE_EXACT or "fabricated_" in c or "timestamp_overlap" in c
    ]
    checks.append(
        _check(
            "no_timestamp_values_in_model_features",
            not ts_in_feats,
            ", ".join(ts_in_feats) if ts_in_feats else "clean",
        )
    )

    forbidden_in_feats = [c for c in file_feats + seg_feats if is_forbidden_feature(c)]
    checks.append(
        _check(
            "leakage_audit_no_forbidden_usable_features",
            not forbidden_in_feats and not leakage.empty,
            ", ".join(forbidden_in_feats),
        )
    )
    if not leakage.empty:
        bad_leak = leakage[
            (leakage["in_model_feature_columns"].astype(str).str.lower() == "true")
            & (leakage["status"] == "forbidden_as_feature")
        ]
        checks.append(_check("leakage_audit_rows_clean", bad_leak.empty, f"bad_rows={len(bad_leak)}"))
    else:
        checks.append(_check("leakage_audit_rows_clean", False, "leakage audit missing"))

    balance_nonempty = not balance.empty and balance.iloc[0].notna().any()
    checks.append(_check("class_balance_not_empty", balance_nonempty))

    report_text = redesign_report_path.read_text(encoding="utf-8") if redesign_report_path.is_file() else ""
    no_training_note = "no training" in report_text.lower() or "training performed:** no" in report_text.lower()
    checks.append(_check("report_states_no_training", no_training_note))

    failed = [c for c in checks if not c["pass"]]
    for c in checks:
        if c["pass"] and c.get("detail"):
            if "missing" in c["detail"] or "bad_rows" in c["detail"]:
                warnings.append(f"{c['check']}: {c['detail']}")

    if balance_nonempty and str(balance.iloc[0].get("warnings", "")).strip():
        warnings.append(str(balance.iloc[0]["warnings"]))

    overall = "PASS" if not failed else "FAIL"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Phase 9D-P5 Partial Dataset Validation Report",
        "",
        f"Generated: {now}",
        "",
        f"**Overall result:** {overall}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"- [{mark}] {c['check']}{detail}")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for w in warnings:
            lines.append(f"- {w}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validation only; no model training performed by this script.",
            "- Phase 9E apps: NOT STARTED.",
            "- Phase 9D-P5B training: NOT STARTED (run after validation PASS).",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Validation {overall}. Report: {report_out}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
