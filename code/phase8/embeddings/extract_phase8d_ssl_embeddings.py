#!/usr/bin/env python3
"""
Phase 8D — Frozen SSL embedding extraction (file + segment level).

No training, no fine-tuning, no predictions.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_EMB_DIR = Path(__file__).resolve().parent
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
for _p in (_EMB_DIR, _COMMON_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from progress_utils import iter_with_progress, progress_method  # noqa: E402
from phase8d_ssl_utils import (  # noqa: E402
    EMBEDDING_PROVENANCE_COLUMNS,
    EXTRACTION_STATUSES,
    FILE_EMBEDDING_BASE_COLUMNS,
    FILE_IDENTITY_COLUMNS,
    FILE_METADATA_COLUMNS,
    REPO_ROOT,
    SCHEMA_VERSION,
    SEGMENT_EMBEDDING_BASE_COLUMNS,
    SEGMENT_IDENTITY_COLUMNS,
    SEGMENT_METADATA_COLUMNS,
    empty_embedding_row,
    extract_ssl_embedding,
    freeze_model,
    get_device,
    load_audio_mono,
    load_ssl_model_and_processor,
    make_embedding_columns,
    read_existing_ids_for_resume,
    slice_audio,
    write_rows_append_safe,
)


@dataclass
class RunStats:
    runtime_sec: float = 0.0
    files_processed: int = 0
    files_skipped_resume: int = 0
    segments_processed: int = 0
    segments_skipped_resume: int = 0
    warnings: list[str] = field(default_factory=list)
    file_status_counts: Counter = field(default_factory=Counter)
    segment_status_counts: Counter = field(default_factory=Counter)
    file_all_blank_rows: int = 0
    segment_all_blank_rows: int = 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract frozen SSL embeddings for Phase 8D.")
    p.add_argument(
        "--file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument(
        "--output_file_embeddings",
        default="reports/phase8/embeddings/phase8d_file_ssl_embeddings.csv",
    )
    p.add_argument(
        "--output_segment_embeddings",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv",
    )
    p.add_argument(
        "--output_file_metadata",
        default="reports/phase8/embeddings/phase8d_file_ssl_embedding_metadata.csv",
    )
    p.add_argument(
        "--output_segment_metadata",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embedding_metadata.csv",
    )
    p.add_argument(
        "--report",
        default="reports/phase8/embeddings/phase8d_ssl_embedding_extraction_report.md",
    )
    p.add_argument("--model_name", default="microsoft/wavlm-base-plus")
    p.add_argument("--target_sample_rate", type=int, default=16000)
    p.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--batch_size", type=int, default=1)
    p.add_argument("--max_files", type=int, default=None)
    p.add_argument("--max_segments", type=int, default=None)
    p.add_argument(
        "--segment_mode",
        choices=("file_and_segments", "file_only", "segments_only"),
        default="file_and_segments",
    )
    p.add_argument("--pooling", choices=("mean", "mean_std"), default="mean")
    p.add_argument(
        "--use_safetensors",
        dest="use_safetensors",
        action="store_true",
        default=True,
        help="Use safetensors weights when loading model (default: true).",
    )
    p.add_argument(
        "--no_use_safetensors",
        dest="use_safetensors",
        action="store_false",
        help="Disable safetensors loading (not recommended).",
    )
    p.add_argument(
        "--allow_bin_weights",
        action="store_true",
        help="Explicitly allow .bin weights (forces use_safetensors=False).",
    )
    p.add_argument("--allow_missing_audio", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--flush_every_files", type=int, default=25)
    p.add_argument("--flush_every_segments", type=int, default=250)
    p.add_argument("--no_progress", action="store_true")
    p.add_argument("--progress_every", type=int, default=100)
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _status_from_audio_err(err: str) -> str:
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


def _init_csv(path: Path, columns: list[str], resume: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if resume and path.is_file() and path.stat().st_size > 0:
        return
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def _base_file_identity(row: pd.Series) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "file_id": row.get("file_id", ""),
        "audio_path": row.get("audio_path", ""),
        "source_dataset": row.get("source_dataset", ""),
        "split": row.get("split", ""),
        "known_origin_label": row.get("known_origin_label", ""),
        "known_manipulation_labels": row.get("known_manipulation_labels", ""),
    }


def _base_segment_identity(row: pd.Series) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "file_id": row.get("file_id", ""),
        "segment_id": row.get("segment_id", ""),
        "audio_path": row.get("audio_path", ""),
        "start_sec": row.get("start_sec", ""),
        "end_sec": row.get("end_sec", ""),
        "segment_duration_sec": row.get("segment_duration_sec", ""),
    }


def _build_metadata_file_row(row: pd.Series, args: argparse.Namespace, status: str, warn: str) -> dict[str, Any]:
    return {
        "file_id": row.get("file_id", ""),
        "audio_path": row.get("audio_path", ""),
        "known_origin_label": row.get("known_origin_label", ""),
        "known_manipulation_labels": row.get("known_manipulation_labels", ""),
        "duration_sec": row.get("duration_sec", ""),
        "sample_rate": row.get("sample_rate", ""),
        "embedding_model_name": args.model_name,
        "pooling": args.pooling,
        "extraction_status": status,
        "warning_message": warn,
    }


def _build_metadata_segment_row(row: pd.Series, args: argparse.Namespace, status: str, warn: str) -> dict[str, Any]:
    return {
        "file_id": row.get("file_id", ""),
        "segment_id": row.get("segment_id", ""),
        "audio_path": row.get("audio_path", ""),
        "start_sec": row.get("start_sec", ""),
        "end_sec": row.get("end_sec", ""),
        "segment_duration_sec": row.get("segment_duration_sec", ""),
        "embedding_model_name": args.model_name,
        "pooling": args.pooling,
        "extraction_status": status,
        "warning_message": warn,
    }


def _prepare_embedding_columns(args: argparse.Namespace, model: Any, processor: Any, device: Any) -> tuple[int, list[str]]:
    sr = args.target_sample_rate
    y = np.zeros(sr, dtype=np.float32)
    try:
        emb = extract_ssl_embedding(y, sr, processor, model, device, args.pooling)
    except Exception:
        hidden = int(getattr(model.config, "hidden_size", 768))
        emb = np.zeros(hidden * (2 if args.pooling == "mean_std" else 1), dtype=np.float32)
    cols = make_embedding_columns(emb)
    return len(cols), cols


def _provenance(args: argparse.Namespace, embedding_dim: int, status: str, warn: str) -> dict[str, Any]:
    return {
        "embedding_model_name": args.model_name,
        "embedding_layer": "last_hidden_state",
        "pooling": args.pooling,
        "target_sample_rate": args.target_sample_rate,
        "embedding_dim": embedding_dim,
        "extraction_status": status,
        "warning_message": warn,
    }


def _extract_file_rows(
    args: argparse.Namespace,
    file_df: pd.DataFrame,
    model: Any,
    processor: Any,
    device: Any,
    emb_cols: list[str],
    stats: RunStats,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, tuple[np.ndarray | None, int | None, str]]]:
    rows: list[dict[str, Any]] = []
    meta_rows: list[dict[str, Any]] = []
    cache: dict[str, tuple[np.ndarray | None, int | None, str]] = {}

    progress_on = not args.no_progress
    file_records = list(file_df.iterrows())
    for _, row in iter_with_progress(
        file_records,
        total=len(file_records),
        desc="file_embeddings",
        enabled=progress_on,
        progress_every=args.progress_every,
        unit="file",
    ):
        audio_path = str(row.get("audio_path", ""))
        y, sr, err = load_audio_mono(audio_path, args.target_sample_rate)
        status = _status_from_audio_err(err)
        warn = err
        emb_vec = None
        if status == "ok" and y is not None and sr is not None:
            try:
                emb_vec = extract_ssl_embedding(y, sr, processor, model, device, args.pooling)
            except Exception as exc:
                status = "model_error"
                warn = f"model_error: {exc}"
        elif status == "missing_audio" and not args.allow_missing_audio:
            raise RuntimeError(f"Missing audio and --allow_missing_audio not set: {audio_path}")

        if warn:
            stats.warnings.append(f"{row.get('file_id','')}: {warn}")
        stats.file_status_counts[status] += 1
        stats.files_processed += 1

        emb_map = empty_embedding_row(len(emb_cols))
        if emb_vec is not None:
            for c, v in zip(emb_cols, emb_vec.tolist()):
                emb_map[c] = float(v)
        else:
            stats.file_all_blank_rows += 1

        out = {
            **_base_file_identity(row),
            **_provenance(args, len(emb_cols), status, warn),
            **emb_map,
        }
        rows.append(out)
        meta_rows.append(_build_metadata_file_row(row, args, status, warn))
        cache[str(row.get("file_id", ""))] = (y, sr, err)

        if str(device).startswith("cuda"):
            torch = __import__("torch")
            torch.cuda.empty_cache()

    return rows, meta_rows, cache


def _extract_segment_rows(
    args: argparse.Namespace,
    seg_df: pd.DataFrame,
    model: Any,
    processor: Any,
    device: Any,
    emb_cols: list[str],
    audio_cache: dict[str, tuple[np.ndarray | None, int | None, str]],
    stats: RunStats,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    meta_rows: list[dict[str, Any]] = []
    progress_on = not args.no_progress
    seg_records = list(seg_df.iterrows())
    for _, row in iter_with_progress(
        seg_records,
        total=len(seg_records),
        desc="segment_embeddings",
        enabled=progress_on,
        progress_every=args.progress_every,
        unit="seg",
    ):
        fid = str(row.get("file_id", ""))
        audio_path = str(row.get("audio_path", ""))

        if fid in audio_cache:
            y_full, sr, base_err = audio_cache[fid]
        else:
            y_full, sr, base_err = load_audio_mono(audio_path, args.target_sample_rate)
            audio_cache[fid] = (y_full, sr, base_err)

        if base_err and not args.allow_missing_audio and base_err.startswith("missing_audio"):
            raise RuntimeError(f"Missing audio and --allow_missing_audio not set: {audio_path}")

        status = _status_from_audio_err(base_err)
        warn = base_err
        emb_vec = None
        if status == "ok" and y_full is not None and sr is not None:
            seg, seg_err = slice_audio(
                y_full,
                sr,
                float(row.get("start_sec", 0.0)),
                float(row.get("end_sec", 0.0)),
            )
            if seg_err:
                status = _status_from_audio_err(seg_err)
                warn = seg_err
            else:
                try:
                    emb_vec = extract_ssl_embedding(seg, sr, processor, model, device, args.pooling)
                except Exception as exc:
                    status = "model_error"
                    warn = f"model_error: {exc}"

        if warn:
            stats.warnings.append(f"{row.get('segment_id','')}: {warn}")
        stats.segment_status_counts[status] += 1
        stats.segments_processed += 1

        emb_map = empty_embedding_row(len(emb_cols))
        if emb_vec is not None:
            for c, v in zip(emb_cols, emb_vec.tolist()):
                emb_map[c] = float(v)
        else:
            stats.segment_all_blank_rows += 1

        out = {
            **_base_segment_identity(row),
            **_provenance(args, len(emb_cols), status, warn),
            **emb_map,
        }
        rows.append(out)
        meta_rows.append(_build_metadata_segment_row(row, args, status, warn))

        if str(device).startswith("cuda"):
            torch = __import__("torch")
            torch.cuda.empty_cache()
    return rows, meta_rows


def _write_report(path: Path, args: argparse.Namespace, stats: RunStats, emb_dim: int) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8D SSL Embedding Extraction Report",
        "",
        f"**Generated:** {now}",
        f"**Runtime:** {stats.runtime_sec:.2f} sec",
        "",
        "## Configuration",
        "",
        f"- model_name: `{args.model_name}`",
        f"- pooling: `{args.pooling}`",
        f"- segment_mode: `{args.segment_mode}`",
        f"- device: `{args.device}`",
        f"- use_safetensors: `{args.use_safetensors}`",
        f"- allow_bin_weights: `{args.allow_bin_weights}`",
        f"- batch_size: {args.batch_size} (processed safely one-at-a-time)",
        f"- embedding_dim: {emb_dim}",
        f"- progress: `{progress_method()}`",
        "",
        "## Runtime summary",
        "",
        f"- files_processed: {stats.files_processed}",
        f"- files_skipped_resume: {stats.files_skipped_resume}",
        f"- segments_processed: {stats.segments_processed}",
        f"- segments_skipped_resume: {stats.segments_skipped_resume}",
        f"- warnings_count: {len(stats.warnings)}",
        f"- file_ok_count: {stats.file_status_counts.get('ok', 0)}",
        f"- file_model_error_count: {stats.file_status_counts.get('model_error', 0)}",
        f"- file_all_blank_rows: {stats.file_all_blank_rows}",
        f"- segment_ok_count: {stats.segment_status_counts.get('ok', 0)}",
        f"- segment_model_error_count: {stats.segment_status_counts.get('model_error', 0)}",
        f"- segment_all_blank_rows: {stats.segment_all_blank_rows}",
        "",
        "## Extraction statuses (files)",
        "",
    ]
    for k, v in sorted(stats.file_status_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Extraction statuses (segments)", ""])
    for k, v in sorted(stats.segment_status_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(
        [
            "",
        "## Guarantees",
            "",
        "- Model frozen: `model.eval()`, `requires_grad_(False)`, `torch.no_grad()`",
        "- Loader uses `AutoFeatureExtractor + AutoModel` (no tokenizer/ASR decoding)",
        "- Raw waveform masks are not applied directly to hidden-state frames.",
            "- No training / no fine-tuning / no classifier / no predictions",
            "- No modification of Phase 8B or Phase 8C files",
            "",
            "## Outputs",
            "",
            f"- `{args.output_file_embeddings}`",
            f"- `{args.output_segment_embeddings}`",
            f"- `{args.output_file_metadata}`",
            f"- `{args.output_segment_metadata}`",
        ]
    )
    if stats.warnings:
        lines.extend(["", "## Warning samples", ""])
        for w in stats.warnings[:200]:
            lines.append(f"- {w}")
        if len(stats.warnings) > 200:
            lines.append(f"- ... and {len(stats.warnings) - 200} more")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    t0 = time.perf_counter()
    stats = RunStats()

    if args.batch_size != 1:
        print("Warning: batch_size is accepted but current implementation processes one sample at a time for safety.")
    if args.allow_bin_weights:
        args.use_safetensors = False

    out_file_emb = _resolve(args.output_file_embeddings)
    out_seg_emb = _resolve(args.output_segment_embeddings)
    out_file_meta = _resolve(args.output_file_metadata)
    out_seg_meta = _resolve(args.output_segment_metadata)
    out_report = _resolve(args.report)

    file_df = pd.read_csv(_resolve(args.file_table), dtype=str, keep_default_na=False)
    seg_df = pd.read_csv(_resolve(args.segment_table), dtype=str, keep_default_na=False)
    if args.max_files is not None:
        file_df = file_df.head(args.max_files)
    if args.max_segments is not None:
        seg_df = seg_df.head(args.max_segments)

    if args.segment_mode == "file_only":
        seg_df = seg_df.iloc[0:0]
    elif args.segment_mode == "segments_only":
        file_df = file_df.iloc[0:0]

    # resume
    file_done = read_existing_ids_for_resume(out_file_emb, "file_id") if args.resume else set()
    seg_done = read_existing_ids_for_resume(out_seg_emb, "segment_id") if args.resume else set()
    if args.resume:
        stats.files_skipped_resume = int(file_df["file_id"].astype(str).isin(file_done).sum())
        stats.segments_skipped_resume = int(seg_df["segment_id"].astype(str).isin(seg_done).sum())
        file_df = file_df[~file_df["file_id"].astype(str).isin(file_done)]
        seg_df = seg_df[~seg_df["segment_id"].astype(str).isin(seg_done)]

    device = get_device(args.device)
    model, processor = load_ssl_model_and_processor(
        args.model_name,
        device,
        use_safetensors=args.use_safetensors,
    )
    freeze_model(model)

    emb_dim, emb_cols = _prepare_embedding_columns(args, model, processor, device)
    file_cols = FILE_EMBEDDING_BASE_COLUMNS + emb_cols
    seg_cols = SEGMENT_EMBEDDING_BASE_COLUMNS + emb_cols

    _init_csv(out_file_emb, file_cols, args.resume)
    _init_csv(out_seg_emb, seg_cols, args.resume)
    _init_csv(out_file_meta, FILE_METADATA_COLUMNS, args.resume)
    _init_csv(out_seg_meta, SEGMENT_METADATA_COLUMNS, args.resume)

    # Files
    file_buffer: list[dict[str, Any]] = []
    file_meta_buffer: list[dict[str, Any]] = []
    audio_cache: dict[str, tuple[np.ndarray | None, int | None, str]] = {}
    if len(file_df) > 0:
        rows, meta_rows, audio_cache = _extract_file_rows(
            args, file_df, model, processor, device, emb_cols, stats
        )
        for r, m in zip(rows, meta_rows):
            file_buffer.append(r)
            file_meta_buffer.append(m)
            if len(file_buffer) >= args.flush_every_files:
                write_rows_append_safe(out_file_emb, file_buffer, file_cols)
                write_rows_append_safe(out_file_meta, file_meta_buffer, FILE_METADATA_COLUMNS)
                file_buffer.clear()
                file_meta_buffer.clear()
        if file_buffer:
            write_rows_append_safe(out_file_emb, file_buffer, file_cols)
            write_rows_append_safe(out_file_meta, file_meta_buffer, FILE_METADATA_COLUMNS)

    # Segments
    seg_buffer: list[dict[str, Any]] = []
    seg_meta_buffer: list[dict[str, Any]] = []
    if len(seg_df) > 0:
        seg_rows, seg_meta_rows = _extract_segment_rows(
            args, seg_df, model, processor, device, emb_cols, audio_cache, stats
        )
        for r, m in zip(seg_rows, seg_meta_rows):
            seg_buffer.append(r)
            seg_meta_buffer.append(m)
            if len(seg_buffer) >= args.flush_every_segments:
                write_rows_append_safe(out_seg_emb, seg_buffer, seg_cols)
                write_rows_append_safe(out_seg_meta, seg_meta_buffer, SEGMENT_METADATA_COLUMNS)
                seg_buffer.clear()
                seg_meta_buffer.clear()
        if seg_buffer:
            write_rows_append_safe(out_seg_emb, seg_buffer, seg_cols)
            write_rows_append_safe(out_seg_meta, seg_meta_buffer, SEGMENT_METADATA_COLUMNS)

    stats.runtime_sec = time.perf_counter() - t0
    _write_report(out_report, args, stats, emb_dim)

    print("--- Phase 8D extraction summary ---")
    print(f"Runtime: {stats.runtime_sec:.2f}s")
    print(f"Progress method: {progress_method()}")
    print(f"files_processed={stats.files_processed}, files_skipped_resume={stats.files_skipped_resume}")
    print(f"segments_processed={stats.segments_processed}, segments_skipped_resume={stats.segments_skipped_resume}")
    print(f"embedding_dim={emb_dim}, pooling={args.pooling}, model={args.model_name}")
    print(f"use_safetensors={args.use_safetensors}, allow_bin_weights={args.allow_bin_weights}")
    print(f"warnings={len(stats.warnings)}")
    print("Model frozen: yes (eval + requires_grad False + no_grad)")
    print(f"outputs: {out_file_emb}, {out_seg_emb}")
    print("No training/predictions performed. Phase 8E not started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

