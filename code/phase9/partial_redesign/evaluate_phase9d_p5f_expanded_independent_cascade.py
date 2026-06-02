#!/usr/bin/env python3
"""
Phase 9D-P5F: Expanded independent evaluation (P5D holdout + fabricated_20pct).

Experimental evidence only — no retrain, no release packaging.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from evaluate_phase9d_p5d_independent_cascade import (
    SEG_PRED_COLUMNS,
    compute_p5d_metrics,
    labels_complete,
    load_phase7_testing_label_lookup,
    resolve_testing_input_root,
)
from evaluate_phase9d_p5d_independent_cascade import (
    FILE_PRED_COLUMNS as P5D_FILE_PRED_COLUMNS,
)
from evaluate_phase9d_p5d_independent_cascade import (
    _try_sidecar_timestamps,
    infer_expected_condition,
    infer_expected_origin_label,
    infer_expected_partial_label,
    scan_testing_audio,
)
from phase9d_p5_evaluation_shared import (
    AUDIO_EXTENSIONS,
    cheap_file_hash,
    evaluate_manifest_cascade,
    rel_path,
)
from phase9d_p5_partial_utils import (
    normalize_path_str,
    path_basename,
    path_stem_lower,
    progress,
    repo_root_from_here,
)
from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5C_FILE_GATE_FEATURE_SET,
    P5C_SEGMENT_FEATURE_SET,
    load_dataset_csv,
    load_p5b_candidate_artifacts,
    now_utc_str,
)

P5F_RUN_STATUS_FILENAME = "phase9d_p5f_run_status.json"
P5F_ALLOWED_TEST_GROUPS = frozenset(
    {"t1", "t2", "t3", "t4", "t5", "fabricated", "fabricated_20pct"}
)
FILENAME_COL_CANDIDATES = (
    "file_name",
    "filename",
    "audio_file",
    "audio_name",
    "name",
    "source_file",
    "output_file",
    "fabricated_file",
    "target_file",
    "wav_file",
    "path",
    "file_path",
    "audio_path",
    "output_path",
    "real_source_path",
)
START_COL_CANDIDATES = (
    "timestamp_start",
    "start_sec",
    "fabricated_start_sec",
    "fake_start_sec",
    "start",
    "start_time",
    "start_time_sec",
    "fake_start",
    "fabricated_start",
    "insert_start",
    "insertion_start",
    "ai_start",
    "ai_start_sec",
    "replacement_start",
    "replaced_start",
)
END_COL_CANDIDATES = (
    "timestamp_end",
    "end_sec",
    "fabricated_end_sec",
    "fake_end_sec",
    "end",
    "end_time",
    "end_time_sec",
    "fake_end",
    "fabricated_end",
    "insert_end",
    "insertion_end",
    "ai_end",
    "ai_end_sec",
    "replacement_end",
    "replaced_end",
)
TIMESTAMP_MATCH_METHODS = frozenset(
    {
        "exact_file_name",
        "lowercase_file_name",
        "file_stem",
        "loose_audio_filename_column",
        "row_order_fallback",
        "sidecar_json",
        "missing",
    }
)
AUDIO_EXT_PATTERN = re.compile(r"\.(wav|mp3|flac|m4a|mp4|ogg)\b", re.I)
HUMAN_PARTIAL_STEM_PATTERN = re.compile(r"human_\d+_clean_partial_fake_20pct", re.I)

FILE_PRED_COLUMNS = list(P5D_FILE_PRED_COLUMNS) + [
    "timestamp_source",
    "timestamp_match_method",
    "is_new_fabricated_20pct",
]

MANIFEST_COLUMNS = [
    "file_path",
    "file_name",
    "file_stem",
    "parent_folder",
    "test_group",
    "expected_condition",
    "expected_partial_label",
    "expected_origin_label",
    "has_timestamp_label",
    "timestamp_start",
    "timestamp_end",
    "timestamp_source",
    "timestamp_match_method",
    "manifest_status",
]

TIMESTAMP_AUDIT_COLUMNS = [
    "timestamp_source_path",
    "sheet_name",
    "original_columns",
    "normalized_columns",
    "detected_file_column",
    "detected_start_column",
    "detected_end_column",
    "row_count",
    "matched_audio_count",
    "unmatched_timestamp_rows",
    "unmatched_audio_files",
    "load_status",
    "warning_message",
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(
        description="Phase 9D-P5F expanded independent testing-audio cascade evaluation."
    )
    p.add_argument("--input_root", default="testing_audios")
    p.add_argument("--output_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5f"))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    p.add_argument(
        "--p5d_manifest",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5d/phase9d_p5d_independent_manifest.csv"),
    )
    p.add_argument(
        "--file_gate_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_file_partial_gate_dataset.csv"),
    )
    p.add_argument(
        "--segment_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_segment_partial_localizer_dataset.csv"),
    )
    p.add_argument(
        "--p5c_manifest",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5c/phase9d_p5c_controlled_manifest.csv"),
    )
    p.add_argument(
        "--file_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv"),
    )
    p.add_argument(
        "--segment_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv"),
    )
    p.add_argument("--ssl_device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--disable_ssl_cpu_fallback", action="store_true")
    p.add_argument("--ssl_chunk_sec", type=float, default=30.0)
    p.add_argument("--ssl_chunk_hop_sec", type=float, default=None)
    p.add_argument("--ssl_chunk_max_chunks", type=int, default=200)
    p.add_argument("--disable_ssl_chunked_fallback", action="store_true")
    p.add_argument("--prefer_cpu_for_long_audio", action="store_true")
    p.add_argument("--long_audio_sec", type=float, default=60.0)
    p.add_argument("--max_audio_duration_sec", type=float, default=None)
    p.add_argument("--max_segments_per_file", type=int, default=500)
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _normalize_col_name(name: str) -> str:
    s = str(name).strip().lower()
    for ch in (" ", "-"):
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def _normalized_column_map(df: pd.DataFrame) -> dict[str, str]:
    return {_normalize_col_name(c): str(c) for c in df.columns}


def _pick_column_norm(norm_map: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for cand in candidates:
        key = _normalize_col_name(cand)
        if key in norm_map:
            return norm_map[key]
    return None


def _natural_sort_key(text: str) -> list[Any]:
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", str(text))]


def _list_fabricated_20pct_audio(fab_dir: Path) -> list[Path]:
    files = [
        f
        for f in fab_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return sorted(files, key=lambda p: _natural_sort_key(p.name))


def _parse_time_to_seconds(value: Any, column_name: str) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    col = _normalize_col_name(column_name)
    if "ms" in col or "millisecond" in col:
        num = pd.to_numeric(value, errors="coerce")
        if np.isfinite(num):
            return float(num) / 1000.0
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() in ("nan", "none"):
            return None
        if ":" in text:
            parts = text.split(":")
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                return None
            if len(nums) == 2:
                return nums[0] * 60.0 + nums[1]
            if len(nums) == 3:
                return nums[0] * 3600.0 + nums[1] * 60.0 + nums[2]
            return None
        num = pd.to_numeric(text, errors="coerce")
        if np.isfinite(num):
            return float(num)
        return None

    num = pd.to_numeric(value, errors="coerce")
    if np.isfinite(num):
        return float(num)
    return None


def _looks_like_audio_filename(value: str) -> bool:
    text = str(value).strip().lower()
    if not text or text in ("nan", "none"):
        return False
    if AUDIO_EXT_PATTERN.search(text):
        return True
    if HUMAN_PARTIAL_STEM_PATTERN.search(text):
        return True
    return False


def _detect_loose_filename_column(df: pd.DataFrame, norm_map: dict[str, str]) -> str | None:
    best_col: str | None = None
    best_score = 0
    for norm, orig in norm_map.items():
        if norm in {_normalize_col_name(c) for c in FILENAME_COL_CANDIDATES}:
            return orig
        score = 0
        series = df[orig].astype(str)
        for val in series.head(min(20, len(series))):
            if _looks_like_audio_filename(val):
                score += 1
        if any(k in norm for k in ("file", "path", "audio", "output", "wav", "name")):
            score += 1
        if score > best_score:
            best_score = score
            best_col = orig
    if best_col and best_score >= 2:
        return best_col
    return None


def _register_timestamp_entry(
    lookup: dict[str, dict[str, Any]],
    raw_name: str,
    start_sec: float,
    end_sec: float,
    match_method: str,
) -> None:
    entry = {
        "timestamp_start": float(start_sec),
        "timestamp_end": float(end_sec),
        "has_timestamp_label": True,
        "timestamp_match_method": match_method,
    }
    basename = path_basename(raw_name)
    lookup[basename.lower()] = entry
    lookup[Path(basename).stem.lower()] = {**entry, "timestamp_match_method": "file_stem"}


def _parse_timestamp_rows(
    df: pd.DataFrame,
    *,
    file_col: str | None,
    start_col: str,
    end_col: str,
    loose_file: bool,
) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        start_sec = _parse_time_to_seconds(row.get(start_col), start_col)
        end_sec = _parse_time_to_seconds(row.get(end_col), end_col)
        if start_sec is None or end_sec is None or not np.isfinite(start_sec) or not np.isfinite(end_sec):
            continue
        raw_name = ""
        if file_col:
            raw_name = str(row.get(file_col, "")).strip()
        parsed.append(
            {
                "row_index": int(idx) if isinstance(idx, (int, np.integer)) else len(parsed),
                "raw_name": raw_name,
                "timestamp_start": float(start_sec),
                "timestamp_end": float(end_sec),
                "loose_file": loose_file,
            }
        )
    return parsed


def _apply_row_order_fallback(
    parsed_rows: list[dict[str, Any]],
    audio_files: list[Path],
) -> tuple[dict[str, dict[str, Any]], int, list[str]]:
    lookup: dict[str, dict[str, Any]] = {}
    unmatched_audio: list[str] = []
    if len(parsed_rows) != len(audio_files):
        return lookup, 0, [f"row_count={len(parsed_rows)} audio_count={len(audio_files)}"]

    rows_sorted = sorted(parsed_rows, key=lambda r: r["row_index"])
    audio_sorted = sorted(audio_files, key=lambda p: _natural_sort_key(p.name))
    matched = 0
    for row, audio_path in zip(rows_sorted, audio_sorted):
        _register_timestamp_entry(
            lookup,
            audio_path.name,
            row["timestamp_start"],
            row["timestamp_end"],
            "row_order_fallback",
        )
        matched += 1
    return lookup, matched, unmatched_audio


def _load_sheet_timestamps(
    sheet_df: pd.DataFrame,
    *,
    source_path: Path,
    sheet_name: str,
    audio_files: list[Path],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    norm_map = _normalized_column_map(sheet_df)
    orig_cols = list(sheet_df.columns)
    norm_cols = [_normalize_col_name(c) for c in orig_cols]

    start_col = _pick_column_norm(norm_map, START_COL_CANDIDATES)
    end_col = _pick_column_norm(norm_map, END_COL_CANDIDATES)
    file_col = _pick_column_norm(norm_map, FILENAME_COL_CANDIDATES)
    loose_file = False
    if file_col is None:
        file_col = _detect_loose_filename_column(sheet_df, norm_map)
        loose_file = file_col is not None

    audit: dict[str, Any] = {
        "timestamp_source_path": str(source_path),
        "sheet_name": sheet_name,
        "original_columns": "|".join(orig_cols),
        "normalized_columns": "|".join(norm_cols),
        "detected_file_column": file_col or "",
        "detected_start_column": start_col or "",
        "detected_end_column": end_col or "",
        "row_count": int(len(sheet_df)),
        "matched_audio_count": 0,
        "unmatched_timestamp_rows": "",
        "unmatched_audio_files": "",
        "load_status": "failed",
        "warning_message": "",
    }

    if not start_col or not end_col:
        audit["warning_message"] = (
            f"missing start/end columns (start={start_col}, end={end_col})"
        )
        return {}, audit

    parsed = _parse_timestamp_rows(
        sheet_df, file_col=file_col, start_col=start_col, end_col=end_col, loose_file=loose_file
    )
    if not parsed:
        audit["warning_message"] = "no parseable timestamp rows"
        return {}, audit

    lookup: dict[str, dict[str, Any]] = {}
    unmatched_ts_rows: list[str] = []
    matched_names: set[str] = set()

    if file_col:
        for item in parsed:
            raw = item["raw_name"]
            if not raw or raw.lower() in ("nan", "none"):
                unmatched_ts_rows.append(f"row_{item['row_index']}")
                continue
            basename = path_basename(raw)
            method = "loose_audio_filename_column" if item["loose_file"] else "exact_file_name"
            _register_timestamp_entry(
                lookup, basename, item["timestamp_start"], item["timestamp_end"], method
            )
            matched_names.add(basename.lower())
        audit["matched_audio_count"] = len(matched_names)
        audit["load_status"] = "ok"
        return lookup, audit

    matched, matched_n, _ = _apply_row_order_fallback(parsed, audio_files)
    if matched_n > 0:
        lookup = matched
        audit["matched_audio_count"] = matched_n
        audit["detected_file_column"] = "(row_order_fallback)"
        audit["load_status"] = "ok_row_order_fallback"
        audit["warning_message"] = (
            "Filename column not detected; matched timestamps to audio using sorted row order"
        )
        return lookup, audit

    audit["warning_message"] = (
        f"no filename column and row_count={len(parsed)} != audio_count={len(audio_files)}"
    )
    audit["unmatched_timestamp_rows"] = ";".join(unmatched_ts_rows[:10])
    return {}, audit


def load_fabricated_20pct_timestamps(
    folder: Path,
    audio_files: list[Path] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], str, str]:
    """
    Return (lookup, audit_rows, source_label, warning_message).
    lookup keys: file name / stem (lower) -> timestamp fields + timestamp_match_method.
    """
    audio_files = audio_files or _list_fabricated_20pct_audio(folder) if folder.is_dir() else []
    xlsx = folder / "fabricated_20pct_timestamps.xlsx"
    csv_path = folder / "fabricated_20pct_timestamps.csv"
    source_path: Path | None = xlsx if xlsx.is_file() else (csv_path if csv_path.is_file() else None)

    if source_path is None:
        audit = {
            "timestamp_source_path": "",
            "sheet_name": "",
            "original_columns": "",
            "normalized_columns": "",
            "detected_file_column": "",
            "detected_start_column": "",
            "detected_end_column": "",
            "row_count": 0,
            "matched_audio_count": 0,
            "unmatched_timestamp_rows": "",
            "unmatched_audio_files": "",
            "load_status": "missing_file",
            "warning_message": "fabricated_20pct timestamp spreadsheet not found (xlsx/csv)",
        }
        return {}, [audit], "", audit["warning_message"]

    audit_rows: list[dict[str, Any]] = []
    lookup: dict[str, dict[str, Any]] = {}
    warning = ""

    try:
        if source_path.suffix.lower() in (".xlsx", ".xls"):
            xl = pd.ExcelFile(source_path, engine="openpyxl")
            sheets = xl.sheet_names
        else:
            sheets = ["csv"]
    except Exception as exc:
        audit = {
            "timestamp_source_path": str(source_path),
            "sheet_name": "",
            "original_columns": "",
            "normalized_columns": "",
            "detected_file_column": "",
            "detected_start_column": "",
            "detected_end_column": "",
            "row_count": 0,
            "matched_audio_count": 0,
            "unmatched_timestamp_rows": "",
            "unmatched_audio_files": "",
            "load_status": "read_error",
            "warning_message": str(exc),
        }
        return {}, [audit], source_path.name, f"timestamp spreadsheet unreadable: {exc}"

    for sheet in sheets:
        try:
            if source_path.suffix.lower() in (".xlsx", ".xls"):
                sheet_df = pd.read_excel(source_path, sheet_name=sheet, engine="openpyxl")
            else:
                sheet_df = pd.read_csv(source_path, low_memory=False)
        except Exception as exc:
            audit_rows.append(
                {
                    "timestamp_source_path": str(source_path),
                    "sheet_name": sheet,
                    "original_columns": "",
                    "normalized_columns": "",
                    "detected_file_column": "",
                    "detected_start_column": "",
                    "detected_end_column": "",
                    "row_count": 0,
                    "matched_audio_count": 0,
                    "unmatched_timestamp_rows": "",
                    "unmatched_audio_files": "",
                    "load_status": "read_error",
                    "warning_message": str(exc),
                }
            )
            continue

        sheet_lookup, audit = _load_sheet_timestamps(
            sheet_df,
            source_path=source_path,
            sheet_name=sheet,
            audio_files=audio_files,
        )
        audit_rows.append(audit)
        if sheet_lookup and not lookup:
            lookup = sheet_lookup
            warning = str(audit.get("warning_message", ""))

    if not lookup:
        if not warning and audit_rows:
            warning = str(audit_rows[-1].get("warning_message", "timestamp load failed"))
        return {}, audit_rows, source_path.name, warning

    matched_audio = {path_basename(p).lower() for p in audio_files}
    matched_keys = {k for k in lookup if _looks_like_audio_filename(k) or k in matched_audio}
    unmatched_audio = [
        p.name for p in audio_files if p.name.lower() not in {path_basename(k).lower() for k in matched_keys}
    ]
    for ar in audit_rows:
        if ar.get("load_status", "").startswith("ok"):
            ar["unmatched_audio_files"] = ";".join(unmatched_audio[:10])
            if len(unmatched_audio) > 10:
                ar["unmatched_audio_files"] += f" (+{len(unmatched_audio) - 10} more)"

    return lookup, audit_rows, str(source_path.name), warning


def _apply_fabricated_timestamp_to_row(
    row: dict[str, Any],
    *,
    fabricated_ts_lookup: dict[str, dict[str, Any]],
    fabricated_ts_source: str,
    warnings: list[str],
) -> None:
    name_lower = str(row.get("file_name", "")).lower()
    stem_lower = str(row.get("file_stem", "")).lower()
    ts = fabricated_ts_lookup.get(name_lower) or fabricated_ts_lookup.get(stem_lower)
    if ts:
        row["has_timestamp_label"] = True
        row["timestamp_start"] = ts["timestamp_start"]
        row["timestamp_end"] = ts["timestamp_end"]
        row["timestamp_source"] = fabricated_ts_source or "fabricated_20pct_timestamps"
        row["timestamp_match_method"] = ts.get("timestamp_match_method", "file_stem")
    else:
        row["has_timestamp_label"] = False
        row["timestamp_start"] = ""
        row["timestamp_end"] = ""
        row["timestamp_source"] = "missing_or_unmatched"
        row["timestamp_match_method"] = "missing"
        warnings.append(f"missing timestamp row for {row.get('file_name')}")


def scan_testing_audio_p5f(
    input_root: Path,
    project_root: Path,
    *,
    phase7_lookup: dict[str, dict[str, Any]] | None = None,
    fabricated_ts_lookup: dict[str, dict[str, Any]] | None = None,
    fabricated_ts_source: str = "",
) -> tuple[list[dict[str, Any]], str]:
    """Scan P5F folders; apply fabricated_20pct spreadsheet timestamps."""
    rows = scan_testing_audio(input_root, project_root, phase7_lookup=phase7_lookup)
    fabricated_ts_lookup = fabricated_ts_lookup or {}
    warnings: list[str] = []

    out_rows: list[dict[str, Any]] = []
    for row in rows:
        group = str(row.get("test_group", "")).lower()
        if group not in P5F_ALLOWED_TEST_GROUPS:
            continue

        row.setdefault("timestamp_match_method", "missing")

        if group == "fabricated_20pct":
            row["expected_partial_label"] = 1
            row["expected_condition"] = "fabricated"
            row["parent_folder"] = "fabricated_20pct"
            row["test_group"] = "fabricated_20pct"
            if not row.get("expected_origin_label"):
                row["expected_origin_label"] = "human_likely"
            _apply_fabricated_timestamp_to_row(
                row,
                fabricated_ts_lookup=fabricated_ts_lookup,
                fabricated_ts_source=fabricated_ts_source,
                warnings=warnings,
            )
        else:
            if row.get("has_timestamp_label"):
                row["timestamp_match_method"] = "sidecar_json"
            row["timestamp_source"] = row.get("timestamp_source", "") or (
                "sidecar_json" if row.get("has_timestamp_label") else ""
            )

        out_rows.append(row)

    fab_dir = input_root / "fabricated_20pct"
    if fab_dir.is_dir():
        existing_paths = {normalize_path_str(str(r["file_path"])) for r in out_rows}
        for f in _list_fabricated_20pct_audio(fab_dir):
            rel = rel_path(f, project_root)
            if normalize_path_str(rel) in existing_paths:
                continue
            name_lower = f.name.lower()
            has_ts, ts_start, ts_end = _try_sidecar_timestamps(f)
            row = {
                "file_path": rel,
                "file_name": f.name,
                "file_stem": f.stem,
                "parent_folder": "fabricated_20pct",
                "test_group": "fabricated_20pct",
                "expected_condition": "fabricated",
                "expected_partial_label": 1,
                "expected_origin_label": infer_expected_origin_label(name_lower) or "human_likely",
                "has_timestamp_label": has_ts,
                "timestamp_start": ts_start,
                "timestamp_end": ts_end,
                "timestamp_source": "sidecar_json" if has_ts else "",
                "timestamp_match_method": "sidecar_json" if has_ts else "missing",
                "manifest_status": "included",
            }
            if not has_ts:
                _apply_fabricated_timestamp_to_row(
                    row,
                    fabricated_ts_lookup=fabricated_ts_lookup,
                    fabricated_ts_source=fabricated_ts_source,
                    warnings=warnings,
                )
            out_rows.append(row)

    warn_msg = "; ".join(warnings[:5])
    if len(warnings) > 5:
        warn_msg += f" (+{len(warnings) - 5} more)"
    return out_rows, warn_msg


def _load_path_name_stem_sets(manifest: pd.DataFrame, path_col: str = "file_path") -> tuple[set[str], set[str], set[str]]:
    paths: set[str] = set()
    names: set[str] = set()
    stems: set[str] = set()
    if manifest.empty or path_col not in manifest.columns:
        return paths, names, stems
    for p in manifest[path_col].astype(str):
        paths.add(normalize_path_str(p))
        names.add(path_basename(p).lower())
        stems.add(path_stem_lower(p))
    return paths, names, stems


def build_p5f_overlap_audit(
    manifest: pd.DataFrame,
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    p5c_manifest: pd.DataFrame,
    p5d_manifest: pd.DataFrame,
    root: Path,
) -> pd.DataFrame:
    train_paths, train_names, train_stems = _load_path_name_stem_sets(file_gate_df, "audio_path")
    for p in segment_df.get("audio_path", pd.Series(dtype=str)).astype(str):
        train_paths.add(normalize_path_str(p))
        train_names.add(path_basename(p).lower())
        train_stems.add(path_stem_lower(p))

    p5c_paths, p5c_names, p5c_stems = _load_path_name_stem_sets(p5c_manifest, "file_path")
    p5d_paths, p5d_names, p5d_stems = _load_path_name_stem_sets(p5d_manifest, "file_path")

    rows: list[dict[str, Any]] = []
    for _, m in manifest.iterrows():
        fp = normalize_path_str(str(m["file_path"]))
        name = path_basename(fp).lower()
        stem = path_stem_lower(fp)
        abs_path = root / fp
        file_hash = cheap_file_hash(abs_path) if abs_path.is_file() else ""
        if fp in train_paths or name in train_names or stem in train_stems:
            status = "seen_in_p5_training"
        elif fp in p5c_paths or name in p5c_names or stem in p5c_stems:
            status = "seen_in_p5c_controlled"
        elif fp in p5d_paths or name in p5d_names or stem in p5d_stems:
            status = "seen_in_previous_p5d"
        elif abs_path.is_file():
            status = "independent_holdout"
        else:
            status = "unknown_overlap_status"
        rows.append(
            {
                "file_path": fp,
                "file_name": m["file_name"],
                "normalized_file_name": name,
                "file_stem": stem,
                "file_hash_prefix": file_hash,
                "overlap_status": status,
                "is_new_fabricated_20pct": str(m.get("test_group", "")).lower() == "fabricated_20pct",
            }
        )
    return pd.DataFrame(rows)


def normalize_p5f_file_predictions(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        base = {c: r.get(c, np.nan) for c in FILE_PRED_COLUMNS}
        for c in FILE_PRED_COLUMNS:
            if c not in base:
                base[c] = np.nan
        if pd.isna(base.get("is_new_fabricated_20pct")):
            base["is_new_fabricated_20pct"] = str(r.get("test_group", "")).lower() == "fabricated_20pct"
        rows.append(base)
    return pd.DataFrame(rows, columns=FILE_PRED_COLUMNS)


def _rate(group: pd.DataFrame, col: str) -> float | None:
    if group.empty:
        return None
    return float(group[col].astype(bool).mean())


def compute_p5f_metrics(
    file_df: pd.DataFrame,
    overlap_df: pd.DataFrame,
    manifest: pd.DataFrame,
    robustness_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = compute_p5d_metrics(file_df, overlap_df, robustness_stats=robustness_stats)
    metrics["seen_in_previous_p5d_count"] = int((overlap_df["overlap_status"] == "seen_in_previous_p5d").sum())

    ok = file_df[file_df["error_status"].astype(str) == "ok"].copy()
    fab_all = file_df[file_df["test_group"].astype(str) == "fabricated_20pct"]
    fab_ok = ok[ok["test_group"].astype(str) == "fabricated_20pct"]
    fab_partial = fab_ok[fab_ok["expected_partial_label"].astype(int) == 1]

    metrics["fabricated_20pct_file_count"] = int(len(fab_all))
    metrics["fabricated_20pct_evaluated_count"] = int(len(fab_ok))
    metrics["fabricated_20pct_failed_count"] = int(len(fab_all) - len(fab_ok))
    metrics["fabricated_20pct_recall"] = (
        float(fab_partial["partial_evidence_positive"].astype(bool).mean()) if len(fab_partial) else None
    )

    fab_ts = fab_ok[fab_ok["has_timestamp_label"].astype(bool)]
    metrics["fabricated_20pct_timestamp_label_count"] = int(len(fab_ts))
    fab_ts_pos = fab_ts[fab_ts["partial_evidence_positive"].astype(bool)]
    if len(fab_ts_pos):
        metrics["fabricated_20pct_top1_hit_rate"] = _rate(fab_ts_pos, "top1_timestamp_hit")
        metrics["fabricated_20pct_top3_hit_rate"] = _rate(fab_ts_pos, "top3_timestamp_hit")
        metrics["fabricated_20pct_top5_hit_rate"] = _rate(fab_ts_pos, "top5_timestamp_hit")
        err = pd.to_numeric(fab_ts_pos["candidate_timestamp_error_seconds"], errors="coerce")
        valid = err[np.isfinite(err)]
        metrics["fabricated_20pct_median_candidate_timestamp_error_seconds"] = (
            float(np.median(valid)) if len(valid) else None
        )
    else:
        metrics["fabricated_20pct_top1_hit_rate"] = None
        metrics["fabricated_20pct_top3_hit_rate"] = None
        metrics["fabricated_20pct_top5_hit_rate"] = None
        metrics["fabricated_20pct_median_candidate_timestamp_error_seconds"] = None

    metrics["expanded_partial_file_count"] = int(metrics.get("partial_file_count", 0))
    metrics["expanded_timestamp_positive_count"] = int(metrics.get("timestamp_positive_count", 0))

    metrics["new_partial_positive_count"] = int(len(fab_partial))
    metrics["new_partial_recall"] = metrics["fabricated_20pct_recall"]
    metrics["new_partial_top5_hit_rate"] = metrics.get("fabricated_20pct_top5_hit_rate")
    if len(fab_partial):
        fn = fab_partial[~fab_partial["partial_evidence_positive"].astype(bool)]
        metrics["new_partial_false_negative_count"] = int(len(fn))
    else:
        metrics["new_partial_false_negative_count"] = 0

    fw = dict(metrics.get("folder_wise", {}))
    if not fab_ok.empty:
        fw["fabricated_20pct"] = {
            "files": int(len(fab_ok)),
            "partial_evidence_positive_rate": float(fab_ok["partial_evidence_positive"].astype(bool).mean()),
            "partial_evidence_recall": metrics["fabricated_20pct_recall"],
        }
    metrics["folder_wise"] = fw

    if not manifest.empty and "has_timestamp_label" in manifest.columns:
        m_fab = manifest[manifest["test_group"].astype(str) == "fabricated_20pct"]
        metrics["fabricated_20pct_manifest_timestamp_count"] = int(m_fab["has_timestamp_label"].astype(bool).sum())
    else:
        metrics["fabricated_20pct_manifest_timestamp_count"] = 0

    return metrics


def evaluate_p5f_release_gates(
    metrics: dict[str, Any],
    *,
    labels_complete: bool,
) -> dict[str, Any]:
    failures: list[str] = []
    holdout = int(metrics.get("independent_holdout_count", 0))
    failed_files = int(metrics.get("failed_files", 0))
    partial_count = int(metrics.get("partial_file_count", 0))
    ts_pos = int(metrics.get("timestamp_positive_count", 0))

    if holdout <= 0:
        failures.append("independent_holdout_count <= 0")
    if failed_files > 0:
        failures.append(f"failed_files={failed_files} > 0")
    if partial_count < 5:
        failures.append(f"partial_file_count={partial_count} < 5")
    if ts_pos < 5:
        failures.append(f"timestamp_positive_count={ts_pos} < 5")

    def _check_rate(col: str, max_val: float | None, min_val: float | None = None) -> None:
        val = metrics.get(col, np.nan)
        if not np.isfinite(val):
            failures.append(f"{col} unavailable")
            return
        if max_val is not None and float(val) > float(max_val):
            failures.append(f"{col} {float(val):.4f} > {float(max_val):.4f}")
        if min_val is not None and float(val) < float(min_val):
            failures.append(f"{col} {float(val):.4f} < {float(min_val):.4f}")

    if labels_complete:
        _check_rate("direct_false_partial_rate", 0.20)
        _check_rate("replay_false_partial_rate", 0.05)
        _check_rate("mixer_false_partial_rate", 0.05)
    else:
        failures.append("labels/conditions incomplete")

    _check_rate("partial_evidence_recall", None, 0.65)
    _check_rate("non_partial_false_alarm_rate", 0.20)
    _check_rate("broad_activation_rate_when_positive", 0.10)
    _check_rate("top5_hit_rate_when_positive", None, 0.80)
    # P5F expanded holdout: new fabricated_20pct partial-evidence recall (7/10 = 0.70 blocks packaging review)
    _check_rate("fabricated_20pct_recall", None, 0.80)
    _check_rate("new_partial_recall", None, 0.80)
    fab_fn = int(metrics.get("new_partial_false_negative_count", 0))
    if fab_fn > 0:
        failures.append(f"new_partial_false_negative_count={fab_fn} > 0")

    return {
        "release_packaging_ready": len(failures) == 0,
        "failure_reasons": failures,
        "independent_holdout_count": holdout,
        "partial_file_count": partial_count,
        "timestamp_positive_count": ts_pos,
    }


def assess_p5f_release_readiness(
    metrics: dict[str, Any],
    *,
    labels_complete: bool,
) -> tuple[str, bool, list[str]]:
    gates = evaluate_p5f_release_gates(metrics, labels_complete=labels_complete)
    failures = list(gates["failure_reasons"])
    ready = bool(gates["release_packaging_ready"])
    if ready:
        return (
            "Candidate acceptable for release packaging evaluation: yes, but packaging is not performed in P5F-P1.",
            True,
            [],
        )
    return (
        "Candidate acceptable for release packaging evaluation: no.",
        False,
        failures,
    )


def init_p5f_run_status(out_dir: Path, input_root: Path) -> dict[str, Any]:
    payload = {
        "phase": "Phase 9D-P5F",
        "run_started_at": now_utc_str(),
        "run_completed_at": "",
        "status": "running",
        "input_root": str(input_root),
        "error_message": "",
        "traceback_summary": "",
        "output_generation_complete": False,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / P5F_RUN_STATUS_FILENAME).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def write_p5f_run_status(out_dir: Path, payload: dict[str, Any]) -> None:
    (out_dir / P5F_RUN_STATUS_FILENAME).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_p5f_report(
    path: Path,
    *,
    input_root: Path,
    scanned_groups: list[str],
    manifest: pd.DataFrame,
    overlap_df: pd.DataFrame,
    metrics: dict[str, Any],
    artifacts: dict[str, Any],
    assessment: str,
    packaging_ready: bool,
    failure_reasons: list[str],
    timestamp_source: str,
    timestamp_warning: str,
    timestamp_audit_rows: list[dict[str, Any]] | None = None,
    examples_success: pd.DataFrame,
    examples_false: pd.DataFrame,
    examples_fn: pd.DataFrame,
    file_pred: pd.DataFrame,
) -> None:
    th = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    paths = artifacts.get("paths", {})
    packaging_line = (
        "**Candidate acceptable for release packaging evaluation: yes**, but packaging is not performed in P5F-P1."
        if packaging_ready
        else "**Candidate acceptable for release packaging evaluation: no.**"
    )

    lines = [
        "# Phase 9D-P5F Expanded Independent Evaluation Report (Experimental)",
        "",
        f"Generated: {now_utc_str()}",
        "",
        "**Production claim:** NO — experimental partial-fabrication evidence indicator only.",
        "",
        "**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.",
        "",
        "## Purpose",
        "",
        "Expand independent labelled partial-positive evaluation by adding `fabricated_20pct` "
        "(10 new 20% partial-fabrication files with timestamp spreadsheet) to the existing P5D "
        "testing holdout (t1–t5, fabricated).",
        "",
        "P5F evaluates only; it does not retrain models, change thresholds, or package release artifacts.",
        "",
        "## Input folders",
        "",
        f"- Input root: `{input_root}`",
        f"- Scanned folders: {', '.join(scanned_groups) if scanned_groups else '(none)'}",
        f"- Total manifest files: {len(manifest)}",
        f"- New fabricated_20pct files: {metrics.get('fabricated_20pct_file_count', 0)}",
        "",
        "## fabricated_20pct timestamp loading",
        "",
        f"- Timestamp file path: `{timestamp_source or 'not loaded'}`",
    ]
    ok_audit = next(
        (r for r in (timestamp_audit_rows or []) if str(r.get("load_status", "")).startswith("ok")),
        None,
    )
    if ok_audit:
        lines.append(f"- Sheet used: `{ok_audit.get('sheet_name', '')}`")
        lines.append(f"- Detected file column: `{ok_audit.get('detected_file_column', '')}`")
        lines.append(f"- Detected start column: `{ok_audit.get('detected_start_column', '')}`")
        lines.append(f"- Detected end column: `{ok_audit.get('detected_end_column', '')}`")
        lines.append(f"- Matched audio count: {ok_audit.get('matched_audio_count', 0)}")
        lines.append(f"- Spreadsheet row count: {ok_audit.get('row_count', 0)}")
    if timestamp_warning:
        lines.append(f"- Warning: {timestamp_warning}")
    if ok_audit and str(ok_audit.get("load_status", "")) == "ok_row_order_fallback":
        lines.append(
            "- Filename column was not detected; timestamps were matched to fabricated_20pct audio files "
            "using sorted row order. This is acceptable for controlled generated files but should be manually verified."
        )
    lines.append(f"- fabricated_20pct_timestamp_label_count: {metrics.get('fabricated_20pct_timestamp_label_count', 0)}")
    lines.append(f"- expanded_timestamp_positive_count: {metrics.get('expanded_timestamp_positive_count', 0)}")
    lines.append(f"- timestamp_positive_count: {metrics.get('timestamp_positive_count', 0)}")
    if not manifest.empty and "timestamp_match_method" in manifest.columns:
        fab_m = manifest[manifest["test_group"].astype(str) == "fabricated_20pct"]
        if not fab_m.empty:
            summary = fab_m["timestamp_match_method"].astype(str).value_counts().to_dict()
            lines.append(f"- timestamp_match_method summary (fabricated_20pct): {summary}")

    lines.extend(
        [
            "",
            "## Overlap audit summary",
            "",
            f"- Independent holdout: {metrics.get('independent_holdout_count', 0)}",
            f"- Seen in P5 training: {metrics.get('seen_in_p5_training_count', 0)}",
            f"- Seen in P5C controlled: {metrics.get('seen_in_p5c_controlled_count', 0)}",
            f"- Seen in previous P5D: {metrics.get('seen_in_previous_p5d_count', 0)}",
            f"- Unknown overlap: {metrics.get('unknown_overlap_count', 0)}",
            "",
            "Overlap with training, P5C, or prior P5D runs is reported explicitly and not hidden.",
            "",
            "## Accepted P5B cascade thresholds",
            "",
            f"- file_gate_threshold = {th['file_gate_threshold']}",
            f"- segment_threshold = {th['segment_threshold']}",
            f"- contrast_threshold = {th['contrast_threshold']}",
            f"- broad_limit = {th['broad_limit']}",
            "",
            f"- File gate feature set: `{P5C_FILE_GATE_FEATURE_SET}`",
            f"- Segment localizer feature set: `{P5C_SEGMENT_FEATURE_SET}`",
            "",
            "## Candidate model artifacts (P5B experimental only)",
            "",
            f"- File gate: `{paths.get('file_gate', 'missing')}`",
            f"- Segment localizer v2: `{paths.get('segment_localizer', 'missing')}`",
            f"- Cascade config: `{paths.get('cascade_config', 'missing')}`",
            "",
            "Only P5B experimental candidate artifacts were used. "
            "No release or reference-model artifacts were activated.",
            "",
            "## Expanded partial-fabrication metrics",
            "",
            f"- expanded_partial_file_count: {metrics.get('expanded_partial_file_count', 0)}",
            f"- expanded_timestamp_positive_count: {metrics.get('expanded_timestamp_positive_count', 0)}",
            f"- partial_evidence_recall: {metrics.get('partial_evidence_recall', np.nan)}",
            f"- fabricated_20pct_recall: {metrics.get('fabricated_20pct_recall', np.nan)}",
            f"- new_partial_positive_count: {metrics.get('new_partial_positive_count', 0)}",
            f"- new_partial_recall: {metrics.get('new_partial_recall', np.nan)}",
            f"- new_partial_false_negative_count: {metrics.get('new_partial_false_negative_count', 0)}",
            "",
            "## fabricated_20pct localization (timestamp-labelled)",
            "",
            f"- fabricated_20pct_timestamp_label_count: {metrics.get('fabricated_20pct_timestamp_label_count', 0)}",
            f"- fabricated_20pct_top1_hit_rate: {metrics.get('fabricated_20pct_top1_hit_rate', np.nan)}",
            f"- fabricated_20pct_top3_hit_rate: {metrics.get('fabricated_20pct_top3_hit_rate', np.nan)}",
            f"- fabricated_20pct_top5_hit_rate: {metrics.get('fabricated_20pct_top5_hit_rate', np.nan)}",
            f"- fabricated_20pct_median_candidate_timestamp_error_seconds: "
            f"{metrics.get('fabricated_20pct_median_candidate_timestamp_error_seconds', np.nan)}",
            "",
            "## False partial evidence (non-partial labels)",
            "",
        ]
    )
    if examples_false.empty:
        lines.append("- None in evaluated ok set.")
    else:
        for _, r in examples_false.head(8).iterrows():
            lines.append(
                f"- `{r['file_path']}` ({r.get('expected_condition', 'n/a')}) — "
                f"experimental partial-fabrication candidate segment flagged; "
                f"gate={r.get('file_gate_probability', np.nan):.3f}; manual review recommended"
            )

    lines.extend(["", "## fabricated_20pct false negatives (expected partial, no evidence)", ""])
    if examples_fn.empty:
        lines.append("- None in evaluated ok set.")
    else:
        for _, r in examples_fn.head(10).iterrows():
            lines.append(f"- `{r['file_path']}` — partial_evidence_positive=False; manual review recommended")

    lines.extend(
        [
            "",
            "## Robustness behavior",
            "",
            f"- mp4_file_count: {metrics.get('mp4_file_count', 0)}",
            f"- mp4_evaluated_count: {metrics.get('mp4_evaluated_count', 0)}",
            f"- ssl_cuda_oom_count: {metrics.get('ssl_cuda_oom_count', 0)}",
            f"- ssl_chunked_fallback_success_count: {metrics.get('ssl_chunked_fallback_success_count', 0)}",
            f"- ssl_long_audio_recovered_count: {metrics.get('ssl_long_audio_recovered_count', 0)}",
            f"- failed_files: {metrics.get('failed_files', 0)}",
            "",
            "P5F reuses P5D-R2 memory-safe SSL extraction (chunked fallback for long audio).",
            "",
            "## Release readiness assessment",
            "",
            packaging_line,
            "",
            f"Assessment: {assessment}",
            "",
        ]
    )
    if failure_reasons:
        lines.append("Blocking reasons:")
        for r in failure_reasons[:12]:
            lines.append(f"- {r}")
        lines.append("")

    lines.extend(
        [
            "## Limitations",
            "",
            "- Independent holdout depends on overlap audit; new fabricated_20pct files should be reviewed for training leakage.",
            "- Timestamp labels come from fabricated_20pct_timestamps spreadsheet; alignment quality requires manual review.",
            "- Outputs are experimental evidence indicators and candidate segments — not final authenticity verdicts.",
            "- Small expanded holdout; condition strata remain limited.",
            "",
            "## Recommended next action",
            "",
            (
                "Proceed to explicit release-packaging review phase if gates pass; otherwise add more "
                "independent labelled partial positives and review false partial / false negative cases."
            ),
            "",
            "P5F-P1 fixes timestamp spreadsheet loading and reruns localization evaluation only; packaging remains a later explicit decision.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    show = not args.no_progress
    root = repo_root_from_here(Path(__file__))
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    p5b_dir = Path(args.p5b_dir)
    if not p5b_dir.is_absolute():
        p5b_dir = (root / p5b_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    input_root = resolve_testing_input_root(root, args.input_root)
    run_status = init_p5f_run_status(out_dir, input_root)

    try:
        return _run_p5f(args, show, root, out_dir, p5b_dir, input_root, run_status)
    except BaseException as exc:
        run_status["status"] = "failed"
        run_status["error_message"] = str(exc)
        run_status["traceback_summary"] = traceback.format_exc()[-4000:]
        run_status["output_generation_complete"] = False
        run_status["run_completed_at"] = now_utc_str()
        write_p5f_run_status(out_dir, run_status)
        raise


def _run_p5f(
    args: argparse.Namespace,
    show: bool,
    root: Path,
    out_dir: Path,
    p5b_dir: Path,
    input_root: Path,
    run_status: dict[str, Any],
) -> int:
    scanned_dirs = [
        d.name
        for d in sorted(input_root.iterdir())
        if d.is_dir() and d.name.lower() in P5F_ALLOWED_TEST_GROUPS
    ]

    fab_dir = input_root / "fabricated_20pct"
    audio_files = _list_fabricated_20pct_audio(fab_dir) if fab_dir.is_dir() else []
    if fab_dir.is_dir():
        ts_lookup, ts_audit_rows, ts_source, ts_warn = load_fabricated_20pct_timestamps(fab_dir, audio_files)
    else:
        ts_lookup, ts_audit_rows, ts_source, ts_warn = {}, [], "", "fabricated_20pct folder missing"
    audit_path = out_dir / "phase9d_p5f_timestamp_loading_audit.csv"
    pd.DataFrame(ts_audit_rows, columns=TIMESTAMP_AUDIT_COLUMNS).reindex(columns=TIMESTAMP_AUDIT_COLUMNS).to_csv(
        audit_path, index=False
    )

    progress("Loading P5B experimental candidate models...", enabled=show)
    artifacts = load_p5b_candidate_artifacts(p5b_dir)

    progress("Building P5F expanded manifest...", enabled=show)
    phase7_lookup = load_phase7_testing_label_lookup(root)
    manifest_rows, scan_warn = scan_testing_audio_p5f(
        input_root,
        root,
        phase7_lookup=phase7_lookup,
        fabricated_ts_lookup=ts_lookup,
        fabricated_ts_source=ts_source,
    )
    if scan_warn and not ts_warn:
        ts_warn = scan_warn
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(out_dir / "phase9d_p5f_expanded_manifest.csv", index=False)

    fg_path = Path(args.file_gate_dataset) if Path(args.file_gate_dataset).is_absolute() else root / args.file_gate_dataset
    sg_path = Path(args.segment_dataset) if Path(args.segment_dataset).is_absolute() else root / args.segment_dataset
    file_gate_df = load_dataset_csv(fg_path)
    segment_df = load_dataset_csv(sg_path)

    p5c_path = Path(args.p5c_manifest) if Path(args.p5c_manifest).is_absolute() else root / args.p5c_manifest
    p5c_manifest = pd.read_csv(p5c_path, low_memory=False) if p5c_path.is_file() else pd.DataFrame()

    p5d_path = Path(args.p5d_manifest) if Path(args.p5d_manifest).is_absolute() else root / args.p5d_manifest
    p5d_manifest = pd.read_csv(p5d_path, low_memory=False) if p5d_path.is_file() else pd.DataFrame()

    overlap_df = build_p5f_overlap_audit(manifest, file_gate_df, segment_df, p5c_manifest, p5d_manifest, root)
    overlap_df.to_csv(out_dir / "phase9d_p5f_overlap_audit.csv", index=False)
    manifest["source_split_status"] = manifest["file_path"].map(
        dict(zip(overlap_df["file_path"], overlap_df["overlap_status"]))
    )

    overlap_md = [
        "# Phase 9D-P5F Overlap Audit",
        "",
        f"Generated: {now_utc_str()}",
        "",
        f"- Input root: `{input_root}`",
        f"- Independent holdout: {(overlap_df['overlap_status'] == 'independent_holdout').sum()}",
        f"- Seen in P5 training: {(overlap_df['overlap_status'] == 'seen_in_p5_training').sum()}",
        f"- Seen in P5C controlled: {(overlap_df['overlap_status'] == 'seen_in_p5c_controlled').sum()}",
        f"- Seen in previous P5D: {(overlap_df['overlap_status'] == 'seen_in_previous_p5d').sum()}",
        f"- Unknown: {(overlap_df['overlap_status'] == 'unknown_overlap_status').sum()}",
        f"- New fabricated_20pct files: {(manifest['test_group'].astype(str) == 'fabricated_20pct').sum()}",
        "",
    ]
    (out_dir / "phase9d_p5f_overlap_audit.md").write_text("\n".join(overlap_md) + "\n", encoding="utf-8")

    fm_path = Path(args.file_master) if Path(args.file_master).is_absolute() else root / args.file_master
    sm_path = Path(args.segment_master) if Path(args.segment_master).is_absolute() else root / args.segment_master
    file_master = pd.read_csv(fm_path, low_memory=False) if fm_path.is_file() else pd.DataFrame()
    segment_master = pd.read_csv(sm_path, low_memory=False) if sm_path.is_file() else pd.DataFrame()

    progress("Running expanded cascade inference (live extraction when needed)...", enabled=show)
    import time

    t0 = time.perf_counter()
    ssl_chunk_hop = args.ssl_chunk_hop_sec if args.ssl_chunk_hop_sec is not None else float(args.ssl_chunk_sec)

    file_pred, seg_pred, error_list, robustness_stats = evaluate_manifest_cascade(
        manifest=manifest,
        overlap_df=overlap_df,
        file_master=file_master,
        segment_master=segment_master,
        artifacts=artifacts,
        root=root,
        show=show,
        progress_fn=lambda msg: progress(msg, enabled=show),
        use_live_extraction=True,
        ssl_device=args.ssl_device,
        disable_ssl_cpu_fallback=args.disable_ssl_cpu_fallback,
        disable_ssl_chunked_fallback=args.disable_ssl_chunked_fallback,
        ssl_chunk_sec=float(args.ssl_chunk_sec),
        ssl_chunk_hop_sec=ssl_chunk_hop,
        ssl_chunk_max_chunks=int(args.ssl_chunk_max_chunks),
        prefer_cpu_for_long_audio=bool(args.prefer_cpu_for_long_audio),
        long_audio_sec=float(args.long_audio_sec),
        max_audio_duration_sec=args.max_audio_duration_sec,
        max_segments_per_file=args.max_segments_per_file,
    )
    robustness_stats["evaluation_runtime_seconds"] = float(time.perf_counter() - t0)

    if not manifest.empty:
        mkey = manifest.copy()
        mkey["_np"] = mkey["file_path"].astype(str).map(normalize_path_str)
        for col in ("timestamp_source", "timestamp_match_method"):
            if col in mkey.columns:
                col_map = dict(zip(mkey["_np"], mkey[col].astype(str)))
                file_pred[col] = file_pred["file_path"].astype(str).map(
                    lambda p, c=col: col_map.get(normalize_path_str(p), "missing" if c == "timestamp_match_method" else "")
                )
    file_pred["is_new_fabricated_20pct"] = file_pred["test_group"].astype(str).eq("fabricated_20pct")

    file_pred = normalize_p5f_file_predictions(file_pred)
    file_pred.to_csv(out_dir / "phase9d_p5f_file_predictions.csv", index=False)

    if seg_pred.empty:
        seg_pred = pd.DataFrame(columns=SEG_PRED_COLUMNS)
    else:
        for c in SEG_PRED_COLUMNS:
            if c not in seg_pred.columns:
                seg_pred[c] = np.nan
        seg_pred = seg_pred.reindex(columns=SEG_PRED_COLUMNS)
    seg_pred.to_csv(out_dir / "phase9d_p5f_segment_predictions.csv", index=False)

    err_df = pd.DataFrame(error_list)
    if not err_df.empty and "failure_type" in err_df.columns:
        err_df["failure_type"] = (
            err_df["failure_type"]
            .replace(
                {
                    "feature_extraction_failure": "acoustic_feature_failure",
                    "file_gate_predict_failure": "prediction_failure",
                    "segment_predict_failure": "prediction_failure",
                }
            )
            .fillna("prediction_failure")
        )
    if err_df.empty:
        err_df = pd.DataFrame(columns=["file_path", "failure_type", "error_message"])
    err_df.to_csv(out_dir / "phase9d_p5f_error_cases.csv", index=False)

    metrics = compute_p5f_metrics(file_pred, overlap_df, manifest, robustness_stats=robustness_stats)
    metrics["accepted_cascade_thresholds"] = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    metrics["timestamp_spreadsheet_source"] = ts_source
    metrics["timestamp_spreadsheet_warning"] = ts_warn
    ok_audit = next((r for r in ts_audit_rows if str(r.get("load_status", "")).startswith("ok")), None)
    if ok_audit:
        metrics["timestamp_spreadsheet_load_status"] = ok_audit.get("load_status", "")
        metrics["timestamp_spreadsheet_detected_file_column"] = ok_audit.get("detected_file_column", "")
        metrics["timestamp_spreadsheet_matched_audio_count"] = int(ok_audit.get("matched_audio_count", 0))

    csv_row = {
        k: ("" if v is None else v)
        for k, v in metrics.items()
        if k
        not in (
            "folder_wise",
            "unknown_condition_positive_rate_status",
            "median_candidate_timestamp_error_missing_reason",
            "timestamp_spreadsheet_warning",
        )
    }
    pd.DataFrame([csv_row]).to_csv(out_dir / "phase9d_p5f_expanded_metrics.csv", index=False)

    def _json_default(val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, float) and np.isnan(val):
            return None
        return str(val) if isinstance(val, (np.floating, np.integer)) else val

    (out_dir / "phase9d_p5f_expanded_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=_json_default), encoding="utf-8"
    )

    lbl_ok = labels_complete(manifest)
    assessment, packaging_ready, failure_reasons = assess_p5f_release_readiness(metrics, labels_complete=lbl_ok)

    ok = file_pred[file_pred["error_status"].astype(str) == "ok"]
    examples_success = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(1)
    ].sort_values("max_segment_probability", ascending=False)
    examples_false = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(0)
    ].sort_values("file_gate_probability", ascending=False)
    examples_fn = ok[
        (~ok["partial_evidence_positive"].astype(bool)) & ok["test_group"].astype(str).eq("fabricated_20pct")
    ]

    write_p5f_report(
        out_dir / "phase9d_p5f_expanded_evaluation_report.md",
        input_root=input_root,
        scanned_groups=scanned_dirs,
        manifest=manifest,
        overlap_df=overlap_df,
        metrics=metrics,
        artifacts=artifacts,
        assessment=assessment,
        packaging_ready=packaging_ready,
        failure_reasons=failure_reasons,
        timestamp_source=ts_source,
        timestamp_warning=ts_warn,
        timestamp_audit_rows=ts_audit_rows,
        examples_success=examples_success,
        examples_false=examples_false,
        examples_fn=examples_fn,
        file_pred=file_pred,
    )

    if args.make_plots:
        progress("P5F: --make_plots requested; no plots implemented.", enabled=show)

    run_status["status"] = "completed"
    run_status["run_completed_at"] = now_utc_str()
    run_status["output_generation_complete"] = True
    run_status["error_message"] = ""
    run_status["traceback_summary"] = ""
    run_status["timestamp_spreadsheet_source"] = ts_source
    run_status["timestamp_spreadsheet_warning"] = ts_warn
    run_status["timestamp_loading_audit_path"] = str(audit_path)
    write_p5f_run_status(out_dir, run_status)

    progress(f"P5F complete. Outputs: {out_dir}", enabled=show)
    progress("No release packaging performed.", enabled=show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
