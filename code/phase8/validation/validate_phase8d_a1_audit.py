#!/usr/bin/env python3
"""Validate Phase 8D-A1 embedding audit outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_FILES = [
    "phase8d_a1_file_embedding_summary.csv",
    "phase8d_a1_segment_embedding_summary.csv",
    "phase8d_a1_missingness_report.csv",
    "phase8d_a1_group_difference_file_embeddings.csv",
    "phase8d_a1_group_difference_segment_embeddings.csv",
    "phase8d_a1_top_candidate_embedding_dims.csv",
    "phase8d_a1_embedding_correlation_summary.csv",
    "phase8d_a1_embedding_norm_summary.csv",
    "phase8d_a1_ssl_embedding_audit_report.md",
]

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

REQUIRED_TOP_COLS = [
    "comparison_name",
    "embedding_dim_name",
    "effect_size",
    "direction",
    "interpretation_note",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8D-A1 audit outputs.")
    p.add_argument("--audit_dir", default="reports/phase8/embeddings/audit")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8d_a1_audit_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def validate(audit_dir: Path) -> dict:
    blocking: list[str] = []
    warnings: list[str] = []

    found = [f for f in REQUIRED_FILES if (audit_dir / f).is_file()]
    missing = [f for f in REQUIRED_FILES if (audit_dir / f).is_file() is False]
    if missing:
        blocking.append(f"Missing required audit outputs: {missing}")

    for name in found:
        if not name.endswith(".csv"):
            continue
        cols = pd.read_csv(audit_dir / name, nrows=0).columns
        for c in FORBIDDEN_COLUMNS:
            if c in cols:
                blocking.append(f"Forbidden decision column {c} in {name}")

    cand_rows = 0
    miss_rows = 0
    top_path = audit_dir / "phase8d_a1_top_candidate_embedding_dims.csv"
    if top_path.is_file():
        top = pd.read_csv(top_path, dtype=str, keep_default_na=False)
        cand_rows = len(top)
        for c in REQUIRED_TOP_COLS:
            if c not in top.columns:
                blocking.append(f"Missing required top-candidate column: {c}")
        if "interpretation_note" in top.columns and len(top):
            notes = top["interpretation_note"].astype(str).str.lower()
            if not notes.str.contains("descriptive|not a standalone detector|requires validation in phase 8e").any():
                warnings.append("Cautious interpretation wording may be incomplete in some rows")

    miss_path = audit_dir / "phase8d_a1_missingness_report.csv"
    if miss_path.is_file():
        miss = pd.read_csv(miss_path, dtype=str, keep_default_na=False)
        miss_rows = len(miss)
        if "embedding_dim_name" not in miss.columns:
            blocking.append("Missingness report missing embedding_dim_name column")

    rpt_path = audit_dir / "phase8d_a1_ssl_embedding_audit_report.md"
    if rpt_path.is_file():
        text = rpt_path.read_text(encoding="utf-8").lower()
        if "descriptive analysis only" not in text:
            blocking.append("Audit report missing descriptive-only statement")
        if "no training" not in text or "no predictions" not in text:
            blocking.append("Audit report missing no-training/no-predictions statement")
        if "inherited" not in text and "file-level known labels" not in text:
            warnings.append("Audit report may not clearly mention inherited segment labels")

    # No model artifacts in audit dir
    model_artifacts = list(audit_dir.glob("**/*.pt")) + list(audit_dir.glob("**/*.pth")) + list(audit_dir.glob("**/*.ckpt"))
    if model_artifacts:
        blocking.append(f"Model artifact files found in audit dir: {len(model_artifacts)}")

    status = "FAIL" if blocking else "PASS"
    return {
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "found": found,
        "missing": missing,
        "candidate_rows": cand_rows,
        "missingness_rows": miss_rows,
    }


def write_report(path: Path, result: dict, audit_dir: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8D-A1 Audit Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result['status']}**",
        "",
        f"Audit directory: `{audit_dir}`",
        "",
        "## Required outputs",
        "",
    ]
    for f in REQUIRED_FILES:
        mark = "OK" if f in result["found"] else "MISSING"
        lines.append(f"- `{f}`: {mark}")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- candidate embedding rows: {result['candidate_rows']}",
            f"- missingness rows: {result['missingness_rows']}",
            "",
        ]
    )
    if result["blocking"]:
        lines.extend(["## Blocking errors", ""])
        lines.extend(f"- {e}" for e in result["blocking"])
    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
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
    raise SystemExit(main())

