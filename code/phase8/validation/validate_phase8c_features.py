#!/usr/bin/env python3
"""Validate Phase 8C acoustic feature CSVs against Phase 8B tables."""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_FEATURES_DIR = Path(__file__).resolve().parents[1] / "features"
if str(_FEATURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FEATURES_DIR))

from phase8c_feature_utils import (  # noqa: E402
    EXTRACTION_STATUSES,
    FILE_FEATURE_NAMES,
    FILE_IDENTITY_COLUMNS,
    FILE_TABLE_COLUMNS,
    REPO_ROOT,
    SEGMENT_FEATURE_NAMES,
    SEGMENT_IDENTITY_COLUMNS,
    SEGMENT_TABLE_COLUMNS,
)

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
        "evidence_origin_human_score",
        "evidence_origin_ai_score",
        "calibrated_origin_label",
    }
)

EVIDENCE_SCORE_PREFIXES = ("evidence_", "calibrated_", "final_forensic", "fusion_trace", "forensic_summary")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8C feature tables.")
    p.add_argument(
        "--file_features",
        default="reports/phase8/features/phase8c_file_acoustic_features.csv",
    )
    p.add_argument(
        "--segment_features",
        default="reports/phase8/features/phase8c_segment_acoustic_features.csv",
    )
    p.add_argument(
        "--file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8c_feature_validation_report.md",
    )
    p.add_argument(
        "--max_files_used",
        type=int,
        default=None,
        help="If builder used --max_files, pass same value for row-count check.",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def _missingness_pct(df: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    n = max(len(df), 1)
    for c in cols:
        if c not in df.columns:
            continue
        blank = _is_blank(df[c]).sum()
        out[c] = round(100.0 * blank / n, 2)
    return out


def validate(args: argparse.Namespace) -> dict:
    blocking: list[str] = []
    warnings: list[str] = []

    ff_path = _resolve(args.file_features)
    sf_path = _resolve(args.segment_features)
    ft_path = _resolve(args.file_table)
    st_path = _resolve(args.segment_table)

    if not ff_path.is_file():
        blocking.append(f"File features missing: {ff_path}")
        return {"status": "FAIL", "blocking": blocking, "warnings": warnings}

    ff = pd.read_csv(ff_path, dtype=str, keep_default_na=False)
    sf = pd.read_csv(sf_path, dtype=str, keep_default_na=False) if sf_path.is_file() else pd.DataFrame()
    ft = pd.read_csv(ft_path, dtype=str, keep_default_na=False) if ft_path.is_file() else pd.DataFrame()
    st = pd.read_csv(st_path, dtype=str, keep_default_na=False) if st_path.is_file() else pd.DataFrame()

    for col in FILE_TABLE_COLUMNS:
        if col not in ff.columns:
            blocking.append(f"Missing file feature column: {col}")
    for col in SEGMENT_TABLE_COLUMNS:
        if col not in sf.columns and len(sf):
            blocking.append(f"Missing segment feature column: {col}")

    for col in FORBIDDEN_COLUMNS:
        if col in ff.columns or col in sf.columns:
            blocking.append(f"Forbidden decision/evidence column present: {col}")

    for col in ff.columns:
        if any(col.startswith(p) for p in EVIDENCE_SCORE_PREFIXES) and col not in FILE_IDENTITY_COLUMNS:
            if col not in FILE_FEATURE_NAMES and col not in FILE_IDENTITY_COLUMNS:
                warnings.append(f"Unexpected evidence-like column in file features: {col}")

    # file_id match
    if "file_id" in ff.columns and "file_id" in ft.columns:
        ff_ids = set(ff["file_id"].astype(str))
        ft_ids = set(ft["file_id"].astype(str))
        if args.max_files_used:
            ft_ids = set(list(ft_ids)[: args.max_files_used])
        extra = ff_ids - ft_ids
        missing = ft_ids - ff_ids
        if extra:
            blocking.append(f"file_id in features not in 8B table: {len(extra)}")
        if missing and args.max_files_used is None:
            warnings.append(f"8B file_id without features: {len(missing)}")
        if ff["file_id"].duplicated().any():
            blocking.append("Duplicate file_id in file features")

    if len(sf) and "segment_id" in sf.columns and "segment_id" in st.columns:
        sf_ids = set(sf["segment_id"].astype(str))
        st_ids = set(st["segment_id"].astype(str))
        extra_seg = sf_ids - st_ids
        if extra_seg:
            blocking.append(f"segment_id not in 8B segment table: {len(extra_seg)}")
        if sf["segment_id"].duplicated().any():
            blocking.append("Duplicate segment_id in segment features")

    # extraction_status
    if "extraction_status" in ff.columns:
        for val in ff["extraction_status"].unique():
            if val and val not in EXTRACTION_STATUSES:
                blocking.append(f"Invalid extraction_status: {val}")

    # numeric features
    for col in FILE_FEATURE_NAMES:
        if col not in ff.columns:
            continue
        for idx, val in ff[col].items():
            if _is_blank(pd.Series([val])).iloc[0]:
                continue
            try:
                f = float(val)
                if not math.isfinite(f):
                    blocking.append(f"file {col} row {idx}: non-finite")
            except ValueError:
                blocking.append(f"file {col} row {idx}: non-numeric")

    warn_count = int((ff.get("warning_message", pd.Series(dtype=str)).astype(str).str.strip() != "").sum())
    status_counts = Counter(ff.get("extraction_status", pd.Series(dtype=str)))
    origin_dist = Counter(ff.get("known_origin_label", pd.Series(dtype=str)))

    file_missingness = _missingness_pct(ff, FILE_FEATURE_NAMES)
    seg_missingness = _missingness_pct(sf, SEGMENT_FEATURE_NAMES) if len(sf) else {}
    # Blank feature cells are allowed (e.g. fast segment mode skips MFCC/contrast).

    expected_files = len(ft) if args.max_files_used is None else min(args.max_files_used, len(ft))
    if args.max_files_used is None and len(ff) != len(ft):
        warnings.append(f"File feature rows ({len(ff)}) != 8B file rows ({len(ft)}) — was --max_files used?")

    status = "FAIL" if blocking else "PASS"
    return {
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "file_feature_rows": len(ff),
        "segment_feature_rows": len(sf),
        "expected_file_rows": expected_files,
        "warn_count": warn_count,
        "status_counts": dict(status_counts),
        "origin_dist": dict(origin_dist),
        "file_missingness_sample": file_missingness,
        "seg_missingness_sample": seg_missingness,
    }


def write_report(path: Path, result: dict, args: argparse.Namespace) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8C Feature Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result['status']}**",
        "",
        "> Phase 8C produces **raw acoustic/channel features only** — not evidence scores or forensic decisions.",
        "",
        "## Row counts",
        "",
        f"- File feature rows: {result.get('file_feature_rows', 0)}",
        f"- Segment feature rows: {result.get('segment_feature_rows', 0)}",
        f"- Expected file rows (8B): {result.get('expected_file_rows', 'n/a')}",
        f"- Warnings in feature rows: {result.get('warn_count', 0)}",
        "",
        "## Extraction status (file-level)",
        "",
    ]
    for k, v in sorted(result.get("status_counts", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Known origin labels (context only — not predictions)", ""])
    for k, v in sorted(result.get("origin_dist", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(
        [
            "",
            "## Feature missingness % (blank cells allowed)",
            "",
            "### File features (sample)",
            "",
        ]
    )
    for k, v in list(result.get("file_missingness_sample", {}).items())[:15]:
        lines.append(f"- `{k}`: {v}% blank")
    if result.get("seg_missingness_sample"):
        lines.extend(["", "### Segment features (sample)", ""])
        for k, v in list(result.get("seg_missingness_sample", {}).items())[:15]:
            lines.append(f"- `{k}`: {v}% blank")
    if result.get("blocking"):
        lines.extend(["", "## Blocking errors", ""])
        lines.extend(f"- {e}" for e in result["blocking"])
    if result.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {w}" for w in result["warnings"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result, args)
    print(f"Validation: {result['status']}")
    print(f"Report -> {out}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
