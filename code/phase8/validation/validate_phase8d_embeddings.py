#!/usr/bin/env python3
"""Validate Phase 8D frozen SSL embedding outputs."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

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

VALID_STATUSES = frozenset(
    {
        "ok",
        "missing_audio",
        "unreadable_audio",
        "too_short",
        "silent_or_invalid",
        "model_error",
        "error",
    }
)

FILE_REQUIRED_BASE = [
    "schema_version",
    "file_id",
    "audio_path",
    "source_dataset",
    "split",
    "known_origin_label",
    "known_manipulation_labels",
    "embedding_model_name",
    "embedding_layer",
    "pooling",
    "target_sample_rate",
    "embedding_dim",
    "extraction_status",
    "warning_message",
]

SEG_REQUIRED_BASE = [
    "schema_version",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
    "embedding_model_name",
    "embedding_layer",
    "pooling",
    "target_sample_rate",
    "embedding_dim",
    "extraction_status",
    "warning_message",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8D embedding CSVs.")
    p.add_argument(
        "--file_embeddings",
        default="reports/phase8/embeddings/phase8d_file_ssl_embeddings.csv",
    )
    p.add_argument(
        "--segment_embeddings",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv",
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
        default="reports/phase8/validation/phase8d_ssl_embedding_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _is_blank(v: str) -> bool:
    return str(v).strip() in {"", "nan", "NaN", "None"}


def _embedding_columns(cols: list[str]) -> list[str]:
    return [c for c in cols if c.startswith("ssl_emb_")]


def _validate_embedding_values(df: pd.DataFrame, emb_cols: list[str]) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    warnings: list[str] = []
    for c in emb_cols:
        if c not in df.columns:
            continue
        non_blank = df[c].astype(str).map(lambda x: not _is_blank(x))
        for idx, val in df.loc[non_blank, c].items():
            try:
                f = float(val)
                if not math.isfinite(f):
                    blocking.append(f"{c} row {idx}: non-finite")
            except Exception:
                blocking.append(f"{c} row {idx}: non-numeric")
    if emb_cols:
        blank_mask = df[emb_cols].astype(str).apply(lambda col: col.map(_is_blank))
        row_blank = blank_mask.all(axis=1).sum()
        if row_blank > 0:
            warnings.append(f"{row_blank} rows have all embedding columns blank")
    return blocking, warnings


def validate(args: argparse.Namespace) -> dict:
    blocking: list[str] = []
    warnings: list[str] = []

    file_emb_path = _resolve(args.file_embeddings)
    seg_emb_path = _resolve(args.segment_embeddings)
    file_tbl_path = _resolve(args.file_table)
    seg_tbl_path = _resolve(args.segment_table)

    for p in (file_emb_path, seg_emb_path, file_tbl_path, seg_tbl_path):
        if not p.is_file():
            blocking.append(f"Missing required input: {p}")
    if blocking:
        return {"status": "FAIL", "blocking": blocking, "warnings": warnings}

    fdf = pd.read_csv(file_emb_path, dtype=str, keep_default_na=False)
    sdf = pd.read_csv(seg_emb_path, dtype=str, keep_default_na=False)
    ftab = pd.read_csv(file_tbl_path, dtype=str, keep_default_na=False)
    stab = pd.read_csv(seg_tbl_path, dtype=str, keep_default_na=False)

    for c in FILE_REQUIRED_BASE:
        if c not in fdf.columns:
            blocking.append(f"Missing file embedding column: {c}")
    for c in SEG_REQUIRED_BASE:
        if c not in sdf.columns:
            blocking.append(f"Missing segment embedding column: {c}")

    for c in FORBIDDEN_COLUMNS:
        if c in fdf.columns:
            blocking.append(f"Forbidden column in file embeddings: {c}")
        if c in sdf.columns:
            blocking.append(f"Forbidden column in segment embeddings: {c}")

    emb_cols_f = _embedding_columns(list(fdf.columns))
    emb_cols_s = _embedding_columns(list(sdf.columns))
    if not emb_cols_f:
        blocking.append("No embedding columns in file embeddings")
    if not emb_cols_s:
        blocking.append("No embedding columns in segment embeddings")

    # embedding_dim consistency
    if "embedding_dim" in fdf.columns and emb_cols_f:
        bad = fdf[pd.to_numeric(fdf["embedding_dim"], errors="coerce") != len(emb_cols_f)]
        if len(bad):
            blocking.append(f"file embedding_dim mismatch rows: {len(bad)}")
    if "embedding_dim" in sdf.columns and emb_cols_s:
        bad = sdf[pd.to_numeric(sdf["embedding_dim"], errors="coerce") != len(emb_cols_s)]
        if len(bad):
            blocking.append(f"segment embedding_dim mismatch rows: {len(bad)}")

    # id consistency
    file_ids = set(ftab["file_id"].astype(str))
    seg_ids = set(stab["segment_id"].astype(str))
    emb_file_ids = set(fdf["file_id"].astype(str)) if "file_id" in fdf.columns else set()
    emb_seg_ids = set(sdf["segment_id"].astype(str)) if "segment_id" in sdf.columns else set()
    if not emb_file_ids.issubset(file_ids):
        blocking.append(f"file_id mismatch: extra={len(emb_file_ids - file_ids)}")
    if not emb_seg_ids.issubset(seg_ids):
        blocking.append(f"segment_id mismatch: extra={len(emb_seg_ids - seg_ids)}")

    # statuses
    for val in fdf.get("extraction_status", pd.Series(dtype=str)).astype(str).unique():
        if val and val not in VALID_STATUSES:
            blocking.append(f"invalid file extraction_status: {val}")
    for val in sdf.get("extraction_status", pd.Series(dtype=str)).astype(str).unique():
        if val and val not in VALID_STATUSES:
            blocking.append(f"invalid segment extraction_status: {val}")

    b1, w1 = _validate_embedding_values(fdf, emb_cols_f)
    b2, w2 = _validate_embedding_values(sdf, emb_cols_s)
    blocking.extend(b1 + b2)
    warnings.extend(w1 + w2)

    file_all_blank_pct = round(
        float((fdf[emb_cols_f].astype(str).apply(lambda col: col.map(_is_blank)).all(axis=1).mean() * 100))
        if emb_cols_f and len(fdf)
        else 100.0,
        3,
    )
    segment_all_blank_pct = round(
        float((sdf[emb_cols_s].astype(str).apply(lambda col: col.map(_is_blank)).all(axis=1).mean() * 100))
        if emb_cols_s and len(sdf)
        else 100.0,
        3,
    )

    file_ok = int((fdf.get("extraction_status", pd.Series(dtype=str)) == "ok").sum())
    seg_ok = int((sdf.get("extraction_status", pd.Series(dtype=str)) == "ok").sum())
    file_model_err = int(fdf.get("extraction_status", pd.Series(dtype=str)).isin(["model_error", "error"]).sum())
    seg_model_err = int(sdf.get("extraction_status", pd.Series(dtype=str)).isin(["model_error", "error"]).sum())

    if len(fdf) > 0 and file_all_blank_pct >= 100.0:
        blocking.append("All file rows have blank embeddings (100%).")
    if len(sdf) > 0 and segment_all_blank_pct >= 100.0:
        blocking.append("All segment rows have blank embeddings (100%).")
    if len(fdf) > 0 and file_model_err == len(fdf):
        blocking.append("All file extraction statuses are model_error/error.")
    if len(sdf) > 0 and seg_model_err == len(sdf):
        blocking.append("All segment extraction statuses are model_error/error.")

    # no evidence columns filled (should not exist)
    evidence_cols = [c for c in list(fdf.columns) + list(sdf.columns) if c.startswith("evidence_")]
    if evidence_cols:
        blocking.append(f"Unexpected evidence_* columns in embeddings: {sorted(set(evidence_cols))[:5]}")

    status = "FAIL" if blocking else "PASS"
    return {
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "file_rows": len(fdf),
        "segment_rows": len(sdf),
        "embedding_dim": len(emb_cols_f) if emb_cols_f else 0,
        "file_status_counts": dict(Counter(fdf.get("extraction_status", pd.Series(dtype=str)))),
        "segment_status_counts": dict(Counter(sdf.get("extraction_status", pd.Series(dtype=str)))),
        "file_missingness_pct": file_all_blank_pct,
        "segment_missingness_pct": segment_all_blank_pct,
        "file_ok_count": file_ok,
        "segment_ok_count": seg_ok,
        "file_model_error_count": file_model_err,
        "segment_model_error_count": seg_model_err,
    }


def write_report(path: Path, result: dict, args: argparse.Namespace) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8D SSL Embedding Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "> Phase 8D produces frozen embeddings only (no training, no predictions).",
        "",
        "## Summary",
        "",
        f"- file embedding rows: {result.get('file_rows', 0)}",
        f"- segment embedding rows: {result.get('segment_rows', 0)}",
        f"- embedding dimension: {result.get('embedding_dim', 0)}",
        f"- file rows all-blank embedding: {result.get('file_missingness_pct', 0)}%",
        f"- segment rows all-blank embedding: {result.get('segment_missingness_pct', 0)}%",
        f"- file_ok_count: {result.get('file_ok_count', 0)}",
        f"- segment_ok_count: {result.get('segment_ok_count', 0)}",
        f"- file_model_error_count: {result.get('file_model_error_count', 0)}",
        f"- segment_model_error_count: {result.get('segment_model_error_count', 0)}",
        "",
        "## File extraction statuses",
        "",
    ]
    for k, v in sorted(result.get("file_status_counts", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Segment extraction statuses", ""])
    for k, v in sorted(result.get("segment_status_counts", {}).items()):
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
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result, args)
    print(f"Validation: {result.get('status')}")
    print(f"Report -> {out}")
    return 1 if result.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

