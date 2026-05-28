"""
Phase 8E-2 localization preparation utilities.

No training/prediction; descriptive candidate scoring only.
"""

from __future__ import annotations

import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA_VERSION = "phase8e2_v1"
ALLOWED_CANDIDATE_TYPES = {
    "within_file_deviation_candidate",
    "neighbor_transition_candidate",
    "inside_outside_candidate",
    "combined_localization_candidate",
    "both_deviation_and_transition",
    "not_top_candidate",
    "insufficient_data",
}
ALLOWED_LOCALIZATION_STATUS = {
    "unsupervised_candidates_only",
    "timestamp_supervision_available",
    "insufficient_segments",
    "missing_features",
    "error",
}
ALLOWED_USE_VALUES = {
    "manual_review_candidate",
    "phase8f_fusion_candidate",
    "not_supervised_training_label",
}

TIMESTAMP_COLUMNS_TO_CHECK = [
    "true_segment_timestamp",
    "suspicious_start_sec",
    "suspicious_end_sec",
    "fabricated_start_sec",
    "fabricated_end_sec",
    "splice_start_sec",
    "splice_end_sec",
    "segment_ground_truth_label",
    "true_segment_label",
    "is_fabricated_segment",
    "is_splice_segment",
    "timestamp_label_source",
]


def load_csv_required(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Required CSV missing: {p}")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def find_acoustic_cols(df: pd.DataFrame) -> list[str]:
    identity = {
        "schema_version",
        "file_id",
        "segment_id",
        "audio_path",
        "source_dataset",
        "split",
        "known_origin_label",
        "known_manipulation_labels",
        "start_sec",
        "end_sec",
        "segment_duration_sec",
        "feature_source",
        "extraction_status",
        "warning_message",
        "source_group_id",
        "leakage_group_id",
    }
    cols = []
    for c in df.columns:
        if c in identity:
            continue
        if c.startswith("ssl_emb_"):
            continue
        if c.startswith("target_") or c.startswith("eligible_"):
            continue
        if c in {"segment_label_source", "reason_not_training_label"}:
            continue
        if (
            c.startswith("rms_")
            or c.startswith("spectral_")
            or c.startswith("mfcc_")
            or c.endswith("_band_energy_ratio")
            or c in {"noise_floor_proxy", "snr_proxy", "dynamic_range_proxy", "bandwidth_occupied_95", "zero_crossing_rate_mean", "peak_amplitude", "clipping_ratio", "silence_ratio"}
        ):
            cols.append(c)
    return cols


def find_ssl_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("ssl_emb_")]


def robust_z_matrix(frame: pd.DataFrame) -> np.ndarray:
    x = frame.copy()
    x = x.mask(x.eq("")).apply(pd.to_numeric, errors="coerce")
    med = x.median(axis=0, skipna=True)
    mad = (x.sub(med, axis=1)).abs().median(axis=0, skipna=True)
    mad = mad.replace(0, np.nan)
    z = (x.sub(med, axis=1)).div(1.4826 * mad, axis=1)
    return z.to_numpy(dtype=float)


def mean_abs_row(arr: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.nanmean(np.abs(arr), axis=1)


def euclidean_from_median(frame: pd.DataFrame) -> np.ndarray:
    x = frame.copy()
    x = x.mask(x.eq("")).apply(pd.to_numeric, errors="coerce")
    med = x.median(axis=0, skipna=True)
    d = x.sub(med, axis=1).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return np.sqrt(np.nansum(np.square(d), axis=1))


def robust_distance_to_baseline(frame: pd.DataFrame, baseline: pd.Series, scale: pd.Series | None = None) -> np.ndarray:
    x = frame.copy().mask(frame.eq("")).apply(pd.to_numeric, errors="coerce")
    b = pd.to_numeric(baseline, errors="coerce")
    if scale is None:
        mad = (x.sub(b, axis=1)).abs().median(axis=0, skipna=True)
        scale = (1.4826 * mad).replace(0, np.nan)
    else:
        scale = pd.to_numeric(scale, errors="coerce").replace(0, np.nan)
    z = x.sub(b, axis=1).div(scale, axis=1)
    with np.errstate(invalid="ignore"):
        return np.nanmean(np.abs(z.to_numpy(dtype=float)), axis=1)


def percentile_rank(values: pd.Series) -> pd.Series:
    v = pd.to_numeric(values, errors="coerce")
    return v.rank(pct=True, method="average")


def has_truthy_value(series: pd.Series) -> bool:
    s = series.astype(str).str.strip().str.lower()
    return s.isin({"1", "true", "yes", "y", "fabricated", "splice", "inside", "outside"}).any()


def timestamp_audit_for_file(file_df: pd.DataFrame) -> dict[str, Any]:
    found_cols = [c for c in TIMESTAMP_COLUMNS_TO_CHECK if c in file_df.columns]
    found_nonblank = [c for c in found_cols if file_df[c].astype(str).str.strip().ne("").any()]
    has_start_end = all(c in found_nonblank for c in ("fabricated_start_sec", "fabricated_end_sec")) or all(
        c in found_nonblank for c in ("suspicious_start_sec", "suspicious_end_sec")
    )
    has_segment_truth = any(c in found_nonblank for c in ("segment_ground_truth_label", "true_segment_label", "is_fabricated_segment"))
    has_true = bool(has_start_end or has_segment_truth)
    source = ""
    if "timestamp_label_source" in file_df.columns and file_df["timestamp_label_source"].astype(str).str.strip().ne("").any():
        source = ";".join(sorted(set(file_df["timestamp_label_source"].astype(str).str.strip())))
    if not found_nonblank:
        return {
            "has_true_timestamp_labels": "false",
            "timestamp_columns_found": "",
            "timestamp_label_source": source,
            "usable_for_supervised_segment_training": "false",
            "reason": "only inherited file-level partial label available",
        }
    if has_true:
        return {
            "has_true_timestamp_labels": "true",
            "timestamp_columns_found": ";".join(found_nonblank),
            "timestamp_label_source": source,
            "usable_for_supervised_segment_training": "true",
            "reason": "per-segment or start/end timestamp labels available",
        }
    return {
        "has_true_timestamp_labels": "false",
        "timestamp_columns_found": ";".join(found_nonblank),
        "timestamp_label_source": source,
        "usable_for_supervised_segment_training": "false",
        "reason": "timestamp labels incomplete",
    }


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def validate_allowed_values(df: pd.DataFrame, col: str, allowed: set[str]) -> list[str]:
    if col not in df.columns:
        return [f"missing column: {col}"]
    bad = sorted(set(df[col].astype(str)) - allowed)
    return [f"{col} has invalid values: {bad}"] if bad else []


def load_timestamp_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_timestamp_json(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".jsonl":
        return pd.read_json(p, lines=True, dtype=False).fillna("")
    # json array or object; normalize into rows
    raw = pd.read_json(p, dtype=False)
    if isinstance(raw, pd.DataFrame):
        return raw.fillna("")
    return pd.json_normalize(raw).fillna("")


def _guess_col(df: pd.DataFrame, candidates: list[str]) -> str:
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return ""


def autodetect_timestamp_columns(
    df: pd.DataFrame,
    timestamp_audio_path_col: str = "auto",
    timestamp_file_id_col: str = "auto",
    timestamp_start_col: str = "auto",
    timestamp_end_col: str = "auto",
    timestamp_label_col: str = "auto",
) -> dict[str, str]:
    return {
        "audio_path_col": (
            _guess_col(df, ["audio_path", "output_file", "file_path", "filename"])
            if timestamp_audio_path_col == "auto"
            else (timestamp_audio_path_col if timestamp_audio_path_col in df.columns else "")
        ),
        "file_id_col": (
            _guess_col(df, ["file_id", "id"])
            if timestamp_file_id_col == "auto"
            else (timestamp_file_id_col if timestamp_file_id_col in df.columns else "")
        ),
        "start_col": (
            _guess_col(df, ["fabricated_start_sec", "suspicious_start_sec", "insert_start_sec", "start_sec"])
            if timestamp_start_col == "auto"
            else (timestamp_start_col if timestamp_start_col in df.columns else "")
        ),
        "end_col": (
            _guess_col(df, ["fabricated_end_sec", "suspicious_end_sec", "insert_end_sec", "end_sec"])
            if timestamp_end_col == "auto"
            else (timestamp_end_col if timestamp_end_col in df.columns else "")
        ),
        "label_col": (
            _guess_col(df, ["label", "annotation_label", "true_segment_label", "segment_ground_truth_label"])
            if timestamp_label_col == "auto"
            else (timestamp_label_col if timestamp_label_col in df.columns else "")
        ),
    }


def _basename_norm(v: str) -> str:
    b = os.path.basename(str(v or "")).strip().lower()
    if not b:
        return ""
    if "." in b:
        b_noext = b[: b.rfind(".")]
    else:
        b_noext = b
    b_noext = re.sub(r"[^a-z0-9_]+", "_", b_noext).strip("_")
    return b_noext


def normalize_timestamp_annotations(
    df: pd.DataFrame,
    source_file: str,
    cols: dict[str, str],
    positive_label_values: set[str],
    negative_label_values: set[str],
) -> pd.DataFrame:
    rows = []
    for i, r in df.iterrows():
        start_raw = str(r.get(cols["start_col"], "")).strip() if cols["start_col"] else ""
        end_raw = str(r.get(cols["end_col"], "")).strip() if cols["end_col"] else ""
        label_raw = str(r.get(cols["label_col"], "")).strip() if cols["label_col"] else ""
        audio_raw = str(r.get(cols["audio_path_col"], "")).strip() if cols["audio_path_col"] else ""
        file_id_raw = str(r.get(cols["file_id_col"], "")).strip() if cols["file_id_col"] else ""

        status = "matched"
        warning = ""
        start_num = pd.to_numeric(pd.Series([start_raw]), errors="coerce").iloc[0]
        end_num = pd.to_numeric(pd.Series([end_raw]), errors="coerce").iloc[0]
        if pd.isna(start_num) or pd.isna(end_num):
            status = "missing_start_or_end"
        elif float(end_num) <= float(start_num):
            status = "invalid_time_range"

        lbl = label_raw.lower()
        if lbl in positive_label_values:
            label_norm = "positive"
        elif lbl in negative_label_values:
            label_norm = "negative"
        else:
            label_norm = lbl if lbl else "unknown"

        rows.append(
            {
                "annotation_id": f"{Path(source_file).stem}_{i}",
                "source_annotation_file": str(source_file),
                "file_id": file_id_raw,
                "audio_path": audio_raw,
                "annotation_filename": os.path.basename(audio_raw) if audio_raw else "",
                "matched_file_id": "",
                "matched_audio_path": "",
                "fabricated_start_sec": "" if pd.isna(start_num) else float(start_num),
                "fabricated_end_sec": "" if pd.isna(end_num) else float(end_num),
                "fabricated_duration_sec": ""
                if pd.isna(start_num) or pd.isna(end_num) or float(end_num) <= float(start_num)
                else float(end_num - start_num),
                "annotation_label": label_norm,
                "timestamp_label_source": "external_timestamp_annotation",
                "annotation_status": status,
                "warning_message": warning,
            }
        )
    return pd.DataFrame(rows)


def load_timestamp_annotations(
    paths: list[str],
    timestamp_format: str = "auto",
    timestamp_audio_path_col: str = "auto",
    timestamp_file_id_col: str = "auto",
    timestamp_start_col: str = "auto",
    timestamp_end_col: str = "auto",
    timestamp_label_col: str = "auto",
    positive_label_values: set[str] | None = None,
    negative_label_values: set[str] | None = None,
) -> pd.DataFrame:
    positive_label_values = positive_label_values or {
        "mixed",
        "fabricated",
        "partial_fabrication",
        "inserted",
        "ai_inserted",
        "human_inserted",
        "synthetic",
        "splice",
        "edited",
        "1",
        "true",
    }
    negative_label_values = negative_label_values or {
        "clean",
        "human",
        "bonafide",
        "nonfabricated",
        "non_fabricated",
        "0",
        "false",
    }
    all_rows = []
    for p in paths:
        pp = Path(p)
        if not pp.is_file():
            continue
        fmt = timestamp_format
        if fmt == "auto":
            s = pp.suffix.lower()
            if s == ".csv":
                fmt = "csv"
            elif s == ".json":
                fmt = "json"
            elif s == ".jsonl":
                fmt = "jsonl"
            else:
                fmt = "csv"
        raw = load_timestamp_csv(pp) if fmt == "csv" else load_timestamp_json(pp)
        cols = autodetect_timestamp_columns(
            raw,
            timestamp_audio_path_col=timestamp_audio_path_col,
            timestamp_file_id_col=timestamp_file_id_col,
            timestamp_start_col=timestamp_start_col,
            timestamp_end_col=timestamp_end_col,
            timestamp_label_col=timestamp_label_col,
        )
        norm = normalize_timestamp_annotations(
            raw,
            source_file=str(pp),
            cols=cols,
            positive_label_values=positive_label_values,
            negative_label_values=negative_label_values,
        )
        all_rows.append(norm)
    if not all_rows:
        return pd.DataFrame(
            columns=[
                "annotation_id",
                "source_annotation_file",
                "file_id",
                "audio_path",
                "annotation_filename",
                "matched_file_id",
                "matched_audio_path",
                "fabricated_start_sec",
                "fabricated_end_sec",
                "fabricated_duration_sec",
                "annotation_label",
                "timestamp_label_source",
                "annotation_status",
                "warning_message",
            ]
        )
    return pd.concat(all_rows, ignore_index=True)


def match_annotations_to_files(
    annotations_df: pd.DataFrame,
    file_master_df: pd.DataFrame,
    partial_files_df: pd.DataFrame,
) -> pd.DataFrame:
    partial_ids = set(partial_files_df["file_id"].astype(str))
    file_scope = file_master_df[file_master_df["file_id"].astype(str).isin(partial_ids)].copy()
    by_id = {str(r["file_id"]): (str(r["file_id"]), str(r.get("audio_path", ""))) for _, r in file_scope.iterrows()}
    by_audio = {}
    by_base = {}
    by_base_noext = {}
    for _, r in file_scope.iterrows():
        fid = str(r["file_id"])
        ap = str(r.get("audio_path", ""))
        by_audio.setdefault(ap.lower(), []).append((fid, ap))
        base = os.path.basename(ap).lower()
        by_base.setdefault(base, []).append((fid, ap))
        by_base_noext.setdefault(_basename_norm(ap), []).append((fid, ap))

    out = annotations_df.copy()
    for i, r in out.iterrows():
        if out.at[i, "annotation_status"] in {"missing_start_or_end", "invalid_time_range"}:
            continue
        fid = str(r.get("file_id", "")).strip()
        ap = str(r.get("audio_path", "")).strip()
        candidates: list[tuple[str, str]] = []
        if fid and fid in by_id:
            candidates = [by_id[fid]]
        elif ap and ap.lower() in by_audio:
            candidates = by_audio[ap.lower()]
        elif ap and os.path.basename(ap).lower() in by_base:
            candidates = by_base[os.path.basename(ap).lower()]
        elif ap and _basename_norm(ap) in by_base_noext:
            candidates = by_base_noext[_basename_norm(ap)]

        if len(candidates) == 1:
            out.at[i, "matched_file_id"] = candidates[0][0]
            out.at[i, "matched_audio_path"] = candidates[0][1]
            out.at[i, "annotation_status"] = "matched"
        elif len(candidates) > 1:
            out.at[i, "annotation_status"] = "ambiguous_match"
            out.at[i, "warning_message"] = "multiple file matches for annotation row"
        else:
            out.at[i, "annotation_status"] = "unmatched_file"
            out.at[i, "warning_message"] = "no matching partial file"
    return out


def compute_segment_timestamp_overlap(
    segment_df: pd.DataFrame,
    normalized_annotations_df: pd.DataFrame,
    min_overlap_ratio: float,
) -> pd.DataFrame:
    out = segment_df.copy()
    out["max_fabricated_overlap_sec"] = ""
    out["max_fabricated_overlap_ratio"] = ""
    out["total_fabricated_overlap_sec"] = ""
    out["overlaps_true_fabricated_region"] = "false"
    out["timestamp_segment_label"] = "unknown_no_timestamp"
    out["training_label_available"] = "false"
    out["timestamp_label_source"] = out.get("timestamp_label_source", "")

    ann = normalized_annotations_df[
        normalized_annotations_df["annotation_status"] == "matched"
    ].copy()
    if len(ann) == 0:
        return out

    by_file = {fid: g for fid, g in ann.groupby("matched_file_id", dropna=False)}
    ambiguous_files = set(
        normalized_annotations_df[
            normalized_annotations_df["annotation_status"] == "ambiguous_match"
        ]["matched_file_id"].astype(str)
    )

    for i, r in out.iterrows():
        fid = str(r.get("file_id", ""))
        seg_start = pd.to_numeric(pd.Series([r.get("start_sec", "")]), errors="coerce").iloc[0]
        seg_end = pd.to_numeric(pd.Series([r.get("end_sec", "")]), errors="coerce").iloc[0]
        if pd.isna(seg_start) or pd.isna(seg_end) or float(seg_end) <= float(seg_start):
            out.at[i, "timestamp_segment_label"] = "unknown_no_timestamp"
            continue
        seg_dur = float(seg_end - seg_start)
        if fid in ambiguous_files:
            out.at[i, "timestamp_segment_label"] = "ambiguous_timestamp"
            continue
        if fid not in by_file:
            out.at[i, "timestamp_segment_label"] = "unknown_no_timestamp"
            continue
        ag = by_file[fid]
        overlaps = []
        for _, a in ag.iterrows():
            a_start = pd.to_numeric(pd.Series([a.get("fabricated_start_sec", "")]), errors="coerce").iloc[0]
            a_end = pd.to_numeric(pd.Series([a.get("fabricated_end_sec", "")]), errors="coerce").iloc[0]
            if pd.isna(a_start) or pd.isna(a_end) or float(a_end) <= float(a_start):
                continue
            ov = max(0.0, min(float(seg_end), float(a_end)) - max(float(seg_start), float(a_start)))
            if ov > 0:
                overlaps.append(ov)
        if overlaps:
            max_ov = max(overlaps)
            total_ov = float(sum(overlaps))
            ratio = max_ov / seg_dur if seg_dur > 0 else 0.0
            out.at[i, "max_fabricated_overlap_sec"] = max_ov
            out.at[i, "max_fabricated_overlap_ratio"] = ratio
            out.at[i, "total_fabricated_overlap_sec"] = total_ov
            if ratio >= float(min_overlap_ratio):
                out.at[i, "overlaps_true_fabricated_region"] = "true"
                out.at[i, "timestamp_segment_label"] = "fabricated_region"
                out.at[i, "training_label_available"] = "true"
            else:
                out.at[i, "timestamp_segment_label"] = "outside_fabricated_region"
                out.at[i, "training_label_available"] = "true"
        else:
            out.at[i, "timestamp_segment_label"] = "outside_fabricated_region"
            out.at[i, "training_label_available"] = "true"
        out.at[i, "timestamp_label_source"] = "external_timestamp_annotation"
    return out
