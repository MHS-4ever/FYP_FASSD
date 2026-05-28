#!/usr/bin/env python3
"""Validate Phase 8B evidence table CSVs against frozen schema rules."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Allow running as script from repo root
_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence_table"
if str(_EVIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_EVIDENCE_DIR))

from phase8b_schema_utils import (  # noqa: E402
    ALLOWED_FINAL_FORENSIC_STATUS,
    ALLOWED_FORENSIC_RISK_LEVEL,
    ALLOWED_MANIPULATION_LABELS,
    ALLOWED_ORIGIN_LABELS,
    DIRECT_SYNTHETIC_TOKENS,
    FILE_EVIDENCE_SCORE_COLUMNS,
    FILE_TABLE_COLUMNS,
    FORBIDDEN_COLUMNS,
    REPO_ROOT,
    SEGMENT_SCORE_COLUMNS,
    SEGMENT_TABLE_COLUMNS,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8B evidence tables.")
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
        default="reports/phase8/validation/phase8b_evidence_table_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def _parse_scores(series: pd.Series) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for score column."""
    errors: list[str] = []
    warnings: list[str] = []
    non_blank = series[~_is_blank(series)]
    for idx, val in non_blank.items():
        try:
            f = float(val)
            if f < 0 or f > 1:
                errors.append(f"row {idx}: score {val} outside [0,1]")
        except (TypeError, ValueError):
            errors.append(f"row {idx}: non-numeric score {val!r}")
    return errors, warnings


def validate(file_path: Path, seg_path: Path) -> dict:
    blocking: list[str] = []
    warnings: list[str] = []

    if not file_path.is_file():
        blocking.append(f"File table missing: {file_path}")
        return {"status": "FAIL", "blocking": blocking, "warnings": warnings}

    file_df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    seg_df = (
        pd.read_csv(seg_path, dtype=str, keep_default_na=False)
        if seg_path.is_file()
        else pd.DataFrame(columns=SEGMENT_TABLE_COLUMNS)
    )

    if not seg_path.is_file():
        warnings.append(f"Segment table missing (optional for FAIL): {seg_path}")

    # Forbidden columns
    for col in FORBIDDEN_COLUMNS:
        if col in file_df.columns:
            blocking.append(f"Forbidden column in file table: {col}")
        if col in seg_df.columns:
            blocking.append(f"Forbidden column in segment table: {col}")

    # Required columns
    for col in FILE_TABLE_COLUMNS:
        if col not in file_df.columns:
            blocking.append(f"Missing required file column: {col}")
    for col in SEGMENT_TABLE_COLUMNS:
        if col not in seg_df.columns and len(seg_df) > 0:
            blocking.append(f"Missing required segment column: {col}")

    if "schema_version" in file_df.columns and file_df["schema_version"].eq("").any():
        warnings.append("Some file rows have empty schema_version")

    # file_id unique
    if "file_id" in file_df.columns:
        empty_ids = file_df["file_id"].astype(str).str.strip().eq("")
        if empty_ids.any():
            blocking.append(f"Empty file_id in {empty_ids.sum()} rows")
        dupes = file_df["file_id"][file_df["file_id"].duplicated(keep=False)]
        if len(dupes):
            blocking.append(f"Duplicate file_id count: {dupes.nunique()}")

    # Origin / manipulation vocabulary
    if "known_origin_label" in file_df.columns:
        for val in file_df["known_origin_label"].unique():
            if val and val not in ALLOWED_ORIGIN_LABELS:
                blocking.append(f"Invalid known_origin_label: {val}")

    if "known_manipulation_labels" in file_df.columns:
        for val in file_df["known_manipulation_labels"].unique():
            if not val or val == "na":
                continue
            for part in str(val).split(";"):
                part = part.strip()
                if part in DIRECT_SYNTHETIC_TOKENS:
                    blocking.append(f"direct_synthetic used as manipulation: {part}")
                elif part and part not in ALLOWED_MANIPULATION_LABELS:
                    blocking.append(f"Invalid manipulation label: {part}")

    # Score columns numeric or blank
    for col in FILE_EVIDENCE_SCORE_COLUMNS:
        if col in file_df.columns:
            errs, _ = _parse_scores(file_df[col])
            blocking.extend([f"file.{col}: {e}" for e in errs])
            filled = (~_is_blank(file_df[col])).sum()
            if filled:
                warnings.append(
                    f"file.{col}: {filled} non-blank values (Phase 8B expects empty unless later phases)"
                )

    for col in SEGMENT_SCORE_COLUMNS:
        if col in seg_df.columns and len(seg_df):
            errs, _ = _parse_scores(seg_df[col])
            blocking.extend([f"segment.{col}: {e}" for e in errs])
            filled = (~_is_blank(seg_df[col])).sum()
            if filled:
                warnings.append(f"segment.{col}: {filled} non-blank values")

    # Fusion placeholders if present
    if "final_forensic_status" in file_df.columns:
        for val in file_df["final_forensic_status"].unique():
            if val and val not in ALLOWED_FINAL_FORENSIC_STATUS:
                blocking.append(f"Invalid final_forensic_status: {val}")

    if "forensic_risk_level" in file_df.columns:
        for val in file_df["forensic_risk_level"].unique():
            if val and val not in ALLOWED_FORENSIC_RISK_LEVEL:
                blocking.append(f"Invalid forensic_risk_level: {val}")

    if "manual_review_required" in file_df.columns:
        allowed = {"", "true", "false", "True", "False"}
        bad = file_df[~file_df["manual_review_required"].isin(allowed)]
        if len(bad):
            blocking.append(f"Invalid manual_review_required in {len(bad)} rows")

    # Segment FK and times
    file_ids = set(file_df["file_id"].astype(str)) if "file_id" in file_df.columns else set()
    files_without_segments: set[str] = set(file_ids)

    if len(seg_df) and "file_id" in seg_df.columns:
        for fid in seg_df["file_id"].unique():
            if fid not in file_ids:
                blocking.append(f"segment references unknown file_id: {fid}")
        for fid in file_ids:
            if (seg_df["file_id"] == fid).any():
                files_without_segments.discard(fid)

        duration_map = {}
        if "duration_sec" in file_df.columns:
            duration_map = dict(zip(file_df["file_id"], file_df["duration_sec"]))

        for idx, row in seg_df.iterrows():
            try:
                start = float(row["start_sec"])
                end = float(row["end_sec"])
                dur = float(row["segment_duration_sec"])
            except (TypeError, ValueError):
                blocking.append(f"segment row {idx}: invalid time fields")
                continue
            if end <= start:
                blocking.append(f"segment row {idx}: end_sec <= start_sec")
            if abs(dur - (end - start)) > 0.05:
                warnings.append(f"segment row {idx}: segment_duration_sec mismatch")
            fid = row["file_id"]
            fd = duration_map.get(fid, "")
            if fd:
                try:
                    if end > float(fd) + 0.05:
                        blocking.append(f"segment row {idx}: end_sec > file duration")
                except ValueError:
                    pass

    missing_meta = 0
    if "duration_sec" in file_df.columns:
        missing_meta = int(_is_blank(file_df["duration_sec"]).sum())

    origin_dist = Counter(file_df.get("known_origin_label", pd.Series(dtype=str)))
    manip_dist: Counter = Counter()
    if "known_manipulation_labels" in file_df.columns:
        for val in file_df["known_manipulation_labels"]:
            for part in str(val).split(";"):
                if part.strip():
                    manip_dist[part.strip()] += 1

    status = "FAIL" if blocking else "PASS"
    return {
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "file_rows": len(file_df),
        "segment_rows": len(seg_df),
        "missing_duration": missing_meta,
        "files_without_segments": len(files_without_segments),
        "origin_dist": dict(origin_dist),
        "manip_dist": dict(manip_dist),
    }


def write_report(path: Path, result: dict, file_path: Path, seg_path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8B Evidence Table Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result['status']}**",
        "",
        "## Inputs",
        "",
        f"- File table: `{file_path}`",
        f"- Segment table: `{seg_path}`",
        "",
        "## Counts",
        "",
        f"- File rows: {result.get('file_rows', 0)}",
        f"- Segment rows: {result.get('segment_rows', 0)}",
        f"- Files missing duration_sec: {result.get('missing_duration', 0)}",
        f"- Files without segment rows: {result.get('files_without_segments', 0)}",
        "",
        "## Label distribution (known_origin_label)",
        "",
    ]
    for k, v in sorted(result.get("origin_dist", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Manipulation label tokens (known_manipulation_labels)", ""])
    for k, v in sorted(result.get("manip_dist", {}).items(), key=lambda x: -x[1]):
        lines.append(f"- `{k}`: {v}")

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
    file_path = _resolve(args.file_table)
    seg_path = _resolve(args.segment_table)
    out_path = _resolve(args.output_report)

    result = validate(file_path, seg_path)
    write_report(out_path, result, file_path, seg_path)

    print(f"Validation: {result['status']}")
    print(f"Report -> {out_path}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
