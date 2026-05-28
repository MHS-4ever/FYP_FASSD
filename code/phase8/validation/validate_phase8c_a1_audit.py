#!/usr/bin/env python3
"""Validate Phase 8C-A1 audit outputs (descriptive only)."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_CSV = [
    "phase8c_a1_file_feature_summary.csv",
    "phase8c_a1_segment_feature_summary.csv",
    "phase8c_a1_missingness_report.csv",
    "phase8c_a1_group_difference_file_features.csv",
    "phase8c_a1_group_difference_segment_features.csv",
    "phase8c_a1_top_candidate_features.csv",
    "phase8c_a1_feature_correlation_summary.csv",
]

REQUIRED_REPORT = "phase8c_a1_acoustic_feature_audit_report.md"

FORBIDDEN_COLUMNS = frozenset(
    {
        "fake_score",
        "real_score",
        "ai_score",
        "replay_decision",
        "mixer_decision",
        "final_forensic_status",
        "suspicious_segment_flag",
        "evidence_origin_score",
        "origin_score",
    }
)

CANDIDATE_REQUIRED_COLS = [
    "comparison_name",
    "feature",
    "effect_size",
    "direction",
    "interpretation_note",
    "group_a_count",
    "group_b_count",
]

CAUTIOUS_PHRASES = (
    "not a standalone detector",
    "requires validation",
    "descriptive",
    "possible candidate",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8C-A1 audit outputs.")
    p.add_argument("--audit_dir", default="reports/phase8/features/audit")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8c_a1_audit_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def validate(audit_dir: Path) -> dict:
    blocking: list[str] = []
    warnings: list[str] = []

    missing_files = [f for f in REQUIRED_CSV + [REQUIRED_REPORT] if not (audit_dir / f).is_file()]
    if missing_files:
        blocking.append(f"Missing audit outputs: {missing_files}")

    for forbidden in FORBIDDEN_COLUMNS:
        for fname in REQUIRED_CSV:
            fp = audit_dir / fname
            if fp.is_file():
                cols = pd.read_csv(fp, nrows=0).columns
                if forbidden in cols:
                    blocking.append(f"Forbidden column {forbidden} in {fname}")

    model_artifacts = list(audit_dir.glob("**/*.pth")) + list(audit_dir.glob("**/*.pt")) + list(audit_dir.glob("**/*.ckpt"))
    if model_artifacts:
        blocking.append(f"Model artifact files found in audit dir: {len(model_artifacts)}")

    cand_path = audit_dir / "phase8c_a1_top_candidate_features.csv"
    cand_rows = 0
    if cand_path.is_file():
        cand = pd.read_csv(cand_path, dtype=str, keep_default_na=False)
        cand_rows = len(cand)
        for col in CANDIDATE_REQUIRED_COLS:
            if col not in cand.columns:
                blocking.append(f"Missing column in top candidates: {col}")
        if "interpretation_note" in cand.columns:
            notes = cand["interpretation_note"].astype(str).str.lower()
            if not notes.str.contains("|".join(CAUTIOUS_PHRASES), regex=True).any():
                warnings.append("Some interpretation notes may lack cautious wording")
    else:
        blocking.append("Top candidate features CSV missing")

    miss_path = audit_dir / "phase8c_a1_missingness_report.csv"
    miss_rows = 0
    if miss_path.is_file():
        miss = pd.read_csv(miss_path, dtype=str, keep_default_na=False)
        miss_rows = len(miss)
        if "missing_percent" in miss.columns:
            full_miss = miss[pd.to_numeric(miss["missing_percent"], errors="coerce") >= 100]
            if len(full_miss) == 0:
                warnings.append("No 100% missing features listed (may be ok if none)")
    else:
        blocking.append("Missingness report missing")

    report_path = audit_dir / REQUIRED_REPORT
    if report_path.is_file():
        text = report_path.read_text(encoding="utf-8").lower()
        if "descriptive" not in text and "not model performance" not in text:
            blocking.append("Audit report missing descriptive-only disclaimer")
        if "inherited" not in text and "file-level" not in text:
            warnings.append("Audit report may not document segment label inheritance")
        if "fake" in text and "fake/real" not in text and "not fake" not in text:
            warnings.append("Audit report mentions 'fake' — verify wording is negated")
    else:
        blocking.append(f"Missing {REQUIRED_REPORT}")

    status = "FAIL" if blocking else "PASS"
    return {
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "missing_files": missing_files,
        "cand_rows": cand_rows,
        "miss_rows": miss_rows,
        "found_files": [f for f in REQUIRED_CSV + [REQUIRED_REPORT] if (audit_dir / f).is_file()],
    }


def write_report(path: Path, result: dict, audit_dir: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8C-A1 Audit Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result['status']}**",
        "",
        f"**Audit directory:** `{audit_dir}`",
        "",
        "> Validates audit **artifacts** exist and contain no decision/prediction columns.",
        "> This is **descriptive analysis only** — not model performance.",
        "",
        "## Required files",
        "",
    ]
    for f in REQUIRED_CSV + [REQUIRED_REPORT]:
        mark = "OK" if f in result.get("found_files", []) else "MISSING"
        lines.append(f"- `{f}`: {mark}")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Top candidate rows: {result.get('cand_rows', 0)}",
            f"- Missingness rows: {result.get('miss_rows', 0)}",
            "",
        ]
    )
    if result.get("blocking"):
        lines.extend(["## Blocking errors", ""])
        lines.extend(f"- {e}" for e in result["blocking"])
    if result.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {w}" for w in result["warnings"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    audit_dir = _resolve(args.audit_dir)
    result = validate(audit_dir)
    out = _resolve(args.output_report)
    write_report(out, result, audit_dir)
    print(f"Validation: {result['status']}")
    print(f"Report -> {out}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
