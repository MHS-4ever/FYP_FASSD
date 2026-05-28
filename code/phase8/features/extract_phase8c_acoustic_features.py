#!/usr/bin/env python3
"""
Phase 8C — Extract acoustic/channel features from Phase 8B evidence tables.

Raw features only. Does not modify evidence tables or fill evidence scores.
Phase 8C-P1: progress, resume, flush, fast/full segment modes.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_FEATURES_DIR = Path(__file__).resolve().parent
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
for _p in (_FEATURES_DIR, _COMMON_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from phase8c_feature_utils import (  # noqa: E402
    FILE_TABLE_COLUMNS,
    REPO_ROOT,
    SCHEMA_VERSION,
    SEGMENT_FEATURE_NAMES,
    SEGMENT_TABLE_COLUMNS,
    empty_feature_dict,
    extract_file_feature_dict,
    extract_segment_feature_dict,
    format_feature_value,
    load_audio_mono,
    safe_audio_slice,
    validate_numeric_features,
)
from progress_utils import iter_with_progress, progress_method  # noqa: E402

AUDIO_CACHE: dict[str, tuple] = {}


@dataclass
class ExtractionStats:
    runtime_sec: float = 0.0
    files_processed: int = 0
    segments_processed: int = 0
    files_skipped_resume: int = 0
    segments_skipped_resume: int = 0
    warnings: list[str] = field(default_factory=list)
    file_status_counts: Counter = field(default_factory=Counter)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 8C acoustic feature extraction.")
    p.add_argument(
        "--file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument(
        "--output_file_features",
        default="reports/phase8/features/phase8c_file_acoustic_features.csv",
    )
    p.add_argument(
        "--output_segment_features",
        default="reports/phase8/features/phase8c_segment_acoustic_features.csv",
    )
    p.add_argument(
        "--report",
        default="reports/phase8/features/phase8c_feature_extraction_report.md",
    )
    p.add_argument("--target_sample_rate", type=int, default=16000)
    p.add_argument("--max_files", type=int, default=None)
    p.add_argument("--allow_missing_audio", action="store_true")
    p.add_argument(
        "--skip_existing",
        action="store_true",
        help="DEPRECATED: use --resume instead (file_id only; can leave segments inconsistent).",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Skip file_id/segment_id already present in output CSVs.",
    )
    p.add_argument(
        "--segment_feature_mode",
        choices=("fast", "full"),
        default="fast",
        help="fast: skip heavy segment features (MFCC, contrast); full: complete set.",
    )
    p.add_argument("--no_progress", action="store_true", help="Disable progress display.")
    p.add_argument("--progress_every", type=int, default=100, help="Fallback progress interval.")
    p.add_argument("--flush_every_files", type=int, default=25)
    p.add_argument("--flush_every_segments", type=int, default=500)
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _load_cached_audio(audio_path: str, target_sr: int) -> tuple:
    key = f"{audio_path}|{target_sr}"
    if key not in AUDIO_CACHE:
        AUDIO_CACHE[key] = load_audio_mono(audio_path, target_sr)
    return AUDIO_CACHE[key]


def _status_from_load(err: str) -> str:
    if not err:
        return "ok"
    if err.startswith("missing_audio"):
        return "missing_audio"
    if err.startswith("unreadable_audio"):
        return "unreadable_audio"
    if err == "too_short":
        return "too_short"
    if err == "silent_or_invalid":
        return "silent_or_invalid"
    return "error"


def _load_resume_ids(path: Path, column: str) -> set[str]:
    if not path.is_file():
        return set()
    try:
        df = pd.read_csv(path, usecols=[column], dtype=str, keep_default_na=False)
        return set(df[column].astype(str))
    except (ValueError, KeyError):
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        if column not in df.columns:
            return set()
        return set(df[column].astype(str))


def _init_output_csv(path: Path, columns: list[str], resume: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if resume and path.is_file() and path.stat().st_size > 0:
        return
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def _append_rows_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows, columns=columns)
    header = not path.is_file() or path.stat().st_size == 0
    df.to_csv(path, mode="a", header=header, index=False)


def _row_to_file_features(
    row: pd.Series,
    target_sr: int,
    allow_missing: bool,
) -> tuple[dict, str, str, str]:
    audio_path = str(row.get("audio_path", "")).strip()
    y, sr, source, err = _load_cached_audio(audio_path, target_sr)
    status = _status_from_load(err)

    if status != "ok" or y is None or sr is None:
        if not allow_missing and status == "missing_audio":
            raise RuntimeError(f"missing audio: {audio_path}")
        feats = empty_feature_dict()
        return feats, status, source, err or status

    try:
        feats = extract_file_feature_dict(y, sr)
        warns = validate_numeric_features(feats)
        warn_msg = "; ".join(warns) if warns else ""
        return feats, "ok", source, warn_msg
    except Exception as exc:
        return empty_feature_dict(), "error", source, str(exc)


def _row_to_segment_features(
    y_full,
    sr: int,
    start_sec: float,
    end_sec: float,
    segment_mode: str,
) -> tuple[dict, str, str]:
    if y_full is None or sr is None:
        return empty_feature_dict(SEGMENT_FEATURE_NAMES), "missing_audio", "parent audio not loaded"
    seg, err = safe_audio_slice(y_full, sr, start_sec, end_sec)
    if seg is None:
        return empty_feature_dict(SEGMENT_FEATURE_NAMES), _status_from_load(err), err
    try:
        feats = extract_segment_feature_dict(seg, sr, mode=segment_mode)
        return feats, "ok", ""
    except Exception as exc:
        return empty_feature_dict(SEGMENT_FEATURE_NAMES), "error", str(exc)


def _build_file_row(row: pd.Series, args: argparse.Namespace, feats: dict, status: str, source: str, warn: str) -> dict:
    out = {
        "schema_version": SCHEMA_VERSION,
        "file_id": str(row["file_id"]),
        "audio_path": row.get("audio_path", ""),
        "source_dataset": row.get("source_dataset", ""),
        "split": row.get("split", ""),
        "known_origin_label": row.get("known_origin_label", ""),
        "known_manipulation_labels": row.get("known_manipulation_labels", ""),
        "duration_sec": row.get("duration_sec", ""),
        "sample_rate": str(args.target_sample_rate),
        "feature_source": source,
        "extraction_status": status,
        "warning_message": warn,
    }
    for k in feats:
        out[k] = format_feature_value(feats[k])
    return out


def run_extraction(args: argparse.Namespace) -> tuple[ExtractionStats, Path, Path]:
    t0 = time.perf_counter()
    stats = ExtractionStats()

    if args.skip_existing and not args.resume:
        args.resume = True
        stats.warnings.append("DEPRECATED: --skip_existing enabled; treating as --resume")

    file_table_path = _resolve(args.file_table)
    segment_table_path = _resolve(args.segment_table)
    out_file = _resolve(args.output_file_features)
    out_seg = _resolve(args.output_segment_features)

    if not file_table_path.is_file():
        raise SystemExit(f"File table not found: {file_table_path}")
    if not segment_table_path.is_file():
        raise SystemExit(f"Segment table not found: {segment_table_path}")

    file_df = pd.read_csv(file_table_path, dtype=str, keep_default_na=False)
    seg_df = pd.read_csv(segment_table_path, dtype=str, keep_default_na=False)

    if args.max_files is not None:
        file_df = file_df.head(args.max_files)

    resume_file_ids = _load_resume_ids(out_file, "file_id") if args.resume else set()
    resume_segment_ids = _load_resume_ids(out_seg, "segment_id") if args.resume else set()
    stats.files_skipped_resume = sum(1 for fid in file_df["file_id"] if str(fid) in resume_file_ids)

    _init_output_csv(out_file, FILE_TABLE_COLUMNS, args.resume)
    _init_output_csv(out_seg, SEGMENT_TABLE_COLUMNS, args.resume)

    file_buffer: list[dict] = []
    seg_buffer: list[dict] = []
    progress_on = not args.no_progress

    file_records = list(file_df.iterrows())
    total_files = len(file_records)

    for _, row in iter_with_progress(
        file_records,
        total=total_files,
        desc="files",
        enabled=progress_on,
        progress_every=args.progress_every,
    ):
        fid = str(row["file_id"])
        if fid in resume_file_ids:
            continue

        try:
            feats, status, source, warn = _row_to_file_features(
                row, args.target_sample_rate, args.allow_missing_audio
            )
        except RuntimeError as exc:
            if not args.allow_missing_audio:
                raise
            feats = empty_feature_dict()
            status = "missing_audio"
            source = "phase8c_acoustic_numpy_fallback"
            warn = str(exc)

        if warn:
            stats.warnings.append(f"{fid}: {warn}")

        file_buffer.append(_build_file_row(row, args, feats, status, source, warn))
        stats.files_processed += 1
        stats.file_status_counts[status] += 1

        if len(file_buffer) >= args.flush_every_files:
            _append_rows_csv(out_file, file_buffer, FILE_TABLE_COLUMNS)
            file_buffer.clear()

    if file_buffer:
        _append_rows_csv(out_file, file_buffer, FILE_TABLE_COLUMNS)
        file_buffer.clear()

    seg_records = [
        (idx, srow)
        for idx, srow in seg_df.iterrows()
        if str(srow.get("segment_id", "")) not in resume_segment_ids
    ]
    stats.segments_skipped_resume = len(seg_df) - len(seg_records)

    total_segments = len(seg_records)

    for _, srow in iter_with_progress(
        seg_records,
        total=total_segments,
        desc="segments",
        enabled=progress_on,
        progress_every=args.progress_every,
        unit="seg",
    ):
        sid = str(srow.get("segment_id", ""))
        fid = str(srow["file_id"])
        audio_path = str(srow.get("audio_path", "")).strip()
        y, sr, source, err = _load_cached_audio(audio_path, args.target_sample_rate)
        if err and not args.allow_missing_audio:
            stats.warnings.append(f"segment {sid}: {err}")

        try:
            start = float(srow["start_sec"])
            end = float(srow["end_sec"])
        except (TypeError, ValueError):
            stats.warnings.append(f"segment {sid}: invalid times")
            start, end = 0.0, 0.0

        feats, status, warn = _row_to_segment_features(
            y, sr, start, end, args.segment_feature_mode
        )
        if warn:
            stats.warnings.append(f"{sid}: {warn}")

        seg_out = {
            "schema_version": SCHEMA_VERSION,
            "file_id": fid,
            "segment_id": sid,
            "audio_path": audio_path,
            "start_sec": srow.get("start_sec", ""),
            "end_sec": srow.get("end_sec", ""),
            "segment_duration_sec": srow.get("segment_duration_sec", ""),
            "feature_source": source if y is not None else "",
            "extraction_status": status,
            "warning_message": warn,
        }
        for k in feats:
            seg_out[k] = format_feature_value(feats[k])
        seg_buffer.append(seg_out)
        stats.segments_processed += 1

        if len(seg_buffer) >= args.flush_every_segments:
            _append_rows_csv(out_seg, seg_buffer, SEGMENT_TABLE_COLUMNS)
            seg_buffer.clear()

    if seg_buffer:
        _append_rows_csv(out_seg, seg_buffer, SEGMENT_TABLE_COLUMNS)

    stats.runtime_sec = time.perf_counter() - t0
    return stats, out_file, out_seg


def write_report(
    path: Path,
    args: argparse.Namespace,
    stats: ExtractionStats,
    out_file: Path,
    out_seg: Path,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    file_rows = 0
    seg_rows = 0
    status_counts: dict = {}
    if out_file.is_file():
        ff = pd.read_csv(out_file, dtype=str, keep_default_na=False)
        file_rows = len(ff)
        if "extraction_status" in ff.columns:
            status_counts = ff["extraction_status"].value_counts().to_dict()
    if out_seg.is_file():
        seg_rows = len(pd.read_csv(out_seg, dtype=str, keep_default_na=False))

    lines = [
        "# Phase 8C Feature Extraction Report",
        "",
        f"**Generated:** {now}",
        f"**Schema version:** {SCHEMA_VERSION}",
        "",
        "## Runtime summary",
        "",
        f"- Total runtime: **{stats.runtime_sec:.1f} s**",
        f"- Files processed (this run): {stats.files_processed}",
        f"- Segments processed (this run): {stats.segments_processed}",
        f"- Files skipped (resume): {stats.files_skipped_resume}",
        f"- Segments skipped (resume): {stats.segments_skipped_resume}",
        f"- Segment feature mode: `{args.segment_feature_mode}`",
        f"- Progress method: `{progress_method()}`",
        f"- Warnings (this run): {len(stats.warnings)}",
        "",
        "## Output row totals (on disk)",
        "",
        f"- File feature rows: {file_rows}",
        f"- Segment feature rows: {seg_rows}",
        "",
        "## Extraction status (file-level, all rows on disk)",
        "",
    ]
    for k, v in sorted(status_counts.items()):
        lines.append(f"- `{k}`: {v}")
    if stats.file_status_counts:
        lines.extend(["", "## Extraction status (this run only)", ""])
        for k, v in sorted(stats.file_status_counts.items()):
            lines.append(f"- `{k}`: {v}")

    lines.extend(
        [
            "",
            "## Segment modes",
            "",
            "- **fast** (default): MFCC and spectral_contrast left blank; suitable for first full-table pass.",
            "- **full**: all segment columns computed (slower).",
            "",
            "## What Phase 8C did NOT do",
            "",
            "- No model training or checkpoint inference",
            "- No evidence score columns filled",
            "- No fake/real decisions",
            "",
            "## Outputs",
            "",
            f"- `{args.output_file_features}`",
            f"- `{args.output_segment_features}`",
            "",
        ]
    )
    if stats.warnings:
        lines.extend(["## Warnings (sample)", ""])
        for w in stats.warnings[:200]:
            lines.append(f"- {w}")
        if len(stats.warnings) > 200:
            lines.append(f"- … and {len(stats.warnings) - 200} more")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_terminal_summary(stats: ExtractionStats, args: argparse.Namespace) -> None:
    print("--- Phase 8C extraction summary ---")
    print(f"Runtime: {stats.runtime_sec:.1f}s")
    print(f"Files processed: {stats.files_processed} (skipped resume: {stats.files_skipped_resume})")
    print(f"Segments processed: {stats.segments_processed} (skipped resume: {stats.segments_skipped_resume})")
    print(f"segment_feature_mode: {args.segment_feature_mode}")
    print(f"Progress: {progress_method()} (no_progress={args.no_progress})")
    print(f"Warnings: {len(stats.warnings)}")
    for k, v in sorted(stats.file_status_counts.items()):
        print(f"  status[{k}]: {v}")


def main() -> int:
    args = parse_args()
    stats, out_file, out_seg = run_extraction(args)
    out_report = _resolve(args.report)
    write_report(out_report, args, stats, out_file, out_seg)
    _print_terminal_summary(stats, args)
    print(f"File features -> {out_file}")
    print(f"Segment features -> {out_seg}")
    print(f"Report -> {out_report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
