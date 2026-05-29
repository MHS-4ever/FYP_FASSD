"""Reusable helpers for Phase 9D-P5 partial fabrication dataset redesign."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

FILE_GATE_POSITIVE_CATEGORIES = frozenset({"ai_fabricated", "human_fabricated"})
FILE_GATE_NEGATIVE_CATEGORIES = frozenset(
    {
        "ai_direct",
        "human_direct",
        "human_clean",
        "ai_replay",
        "human_replay",
        "ai_repeat",
        "human_repeat",
        "ai_mixer",
        "human_mixer",
    }
)
FILE_GATE_ELIGIBLE_CATEGORIES = FILE_GATE_POSITIVE_CATEGORIES | FILE_GATE_NEGATIVE_CATEGORIES

SEGMENT_NEGATIVE_SOURCE_TYPES = (
    "fabricated_outside_same_file",
    "clean_direct_negative",
    "replay_negative",
    "mixer_negative",
)

FILE_GATE_METADATA_COLUMNS = [
    "file_id",
    "audio_path",
    "source_dataset",
    "known_origin_label",
    "known_manipulation_labels",
    "file_category",
    "target_is_partial_fabrication_file",
    "partial_file_label_source",
    "feature_available_acoustic",
    "feature_available_ssl",
    "split_group_id",
    "leakage_group_id",
    "allowed_use",
    "model_feature_columns_json",
]

SEGMENT_METADATA_COLUMNS = [
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
    "file_category",
    "segment_source_type",
    "target_is_fabricated_segment",
    "timestamp_overlap_sec",
    "timestamp_overlap_ratio_segment",
    "timestamp_region_label",
    "fabrication_direction",
    "split_group_id",
    "leakage_group_id",
    "allowed_use",
    "model_feature_columns_json",
]

FORBIDDEN_AS_FEATURE_EXACT = frozenset(
    {
        "timestamp_region_label",
        "timestamp_overlap_sec",
        "timestamp_overlap_ratio_segment",
        "fabricated_start_sec",
        "fabricated_end_sec",
        "target_is_fabricated_segment",
        "target_is_partial_fabrication_file",
        "known_origin_label",
        "known_manipulation_labels",
        "file_category",
        "segment_source_type",
        "allowed_use",
        "model_feature_columns_json",
        "partial_file_label_source",
        "fabrication_direction",
        "partial_probability",
        "fake_score",
        "real_score",
        "timestamp_segment_label",
        "max_fabricated_overlap_ratio",
        "max_fabricated_overlap_sec",
        "overlaps_true_fabricated_region",
        "candidate_type",
        "candidate_reason",
    }
)

FORBIDDEN_AS_FEATURE_SUBSTRINGS = (
    "fabricated_baseline",
    "outside_baseline",
    "inside_outside_margin",
    "inside_outside_separation",
    "fusion_",
    "_fusion",
    "partial_fusion",
    "origin_probability",
    "replay_probability",
    "mixer_probability",
)

TIMESTAMP_LIKE_FEATURE_EXACT = frozenset(
    {
        "fabricated_start_sec",
        "fabricated_end_sec",
        "timestamp_overlap_sec",
        "timestamp_overlap_ratio_segment",
        "insert_start_sec",
        "insert_end_sec",
    }
)

SAFE_LOCALIZATION_FEATURES = [
    "acoustic_distance_from_file_median",
    "ssl_distance_from_file_median",
    "within_file_acoustic_deviation_score",
    "within_file_ssl_deviation_score",
    "combined_within_file_deviation_score",
    "neighbor_acoustic_transition_score",
    "neighbor_ssl_transition_score",
    "combined_neighbor_transition_score",
    "acoustic_deviation_percentile_within_file",
    "ssl_deviation_percentile_within_file",
]

ACOUSTIC_PREFIXES = ("rms_", "spectral_", "mfcc_")
ACOUSTIC_EXACT = {
    "peak_amplitude",
    "mean_amplitude",
    "std_amplitude",
    "dc_offset",
    "zero_crossing_rate_mean",
    "zero_crossing_rate_std",
    "clipping_ratio",
    "silence_ratio",
    "active_audio_ratio",
    "noise_floor_proxy",
    "snr_proxy",
    "dynamic_range_proxy",
    "spectral_entropy_mean",
    "spectral_entropy_std",
    "high_freq_rolloff_ratio",
    "bandwidth_occupied_95",
    "low_band_energy_ratio",
    "mid_band_energy_ratio",
    "high_band_energy_ratio",
    "very_high_band_energy_ratio",
}


def repo_root_from_here(here: Path) -> Path:
    return here.resolve().parents[3]


def normalize_path_str(value: str) -> str:
    return str(value).strip().replace("\\", "/")


def path_basename(value: str) -> str:
    return Path(normalize_path_str(value)).name


def path_stem_lower(value: str) -> str:
    return Path(normalize_path_str(value)).stem.lower()


def infer_file_category(audio_path: str) -> str:
    """Infer Phase 7C1 controlled folder category from audio_path."""
    p = normalize_path_str(audio_path).lower()
    parts = p.split("/")
    for idx, part in enumerate(parts):
        if part == "raw" and idx + 1 < len(parts):
            folder = parts[idx + 1]
            if folder in FILE_GATE_ELIGIBLE_CATEGORIES:
                return folder
            if folder == "human_clean":
                return "human_direct"
    stem = path_stem_lower(p)
    if "fabricated" in stem:
        if stem.startswith("human_") or "/human_fabricated/" in p:
            return "human_fabricated"
        return "ai_fabricated"
    if "mixer" in stem or "/ai_mixer/" in p or "/human_mixer/" in p:
        return "ai_mixer" if "ai_" in stem or "/ai_mixer/" in p else "human_mixer"
    if "replay" in stem or "repeat" in stem:
        if stem.startswith("human_") or "/human_repeat/" in p or "/human_replay/" in p:
            return "human_replay"
        return "ai_replay"
    if "direct" in stem or "/ai_direct/" in p or "/human_direct/" in p or "/human_clean/" in p:
        return "human_direct" if stem.startswith("human_") or "/human_" in p else "ai_direct"
    return "unknown"


def map_replay_category(file_category: str) -> str:
    if file_category in {"ai_repeat", "human_repeat", "ai_replay", "human_replay"}:
        return file_category.replace("repeat", "replay")
    return file_category


def segment_source_type_for_negative(file_category: str) -> str | None:
    cat = map_replay_category(file_category)
    if cat in {"ai_direct", "human_direct", "human_clean"}:
        return "clean_direct_negative"
    if cat in {"ai_replay", "human_replay"}:
        return "replay_negative"
    if cat in {"ai_mixer", "human_mixer"}:
        return "mixer_negative"
    return None


def fabrication_direction_from_category(file_category: str) -> str:
    if file_category == "ai_fabricated":
        return "ai_fabricated"
    if file_category == "human_fabricated":
        return "human_fabricated"
    return "none"


def is_partial_positive_category(file_category: str) -> bool:
    return file_category in FILE_GATE_POSITIVE_CATEGORIES


def select_file_acoustic_columns(columns: Iterable[str]) -> list[str]:
    out: list[str] = []
    for c in columns:
        if c in ACOUSTIC_EXACT:
            out.append(c)
        elif any(c.startswith(p) for p in ACOUSTIC_PREFIXES):
            out.append(c)
    return sorted(set(out))


def select_segment_acoustic_columns(columns: Iterable[str]) -> list[str]:
    out: list[str] = []
    for c in columns:
        if c in ACOUSTIC_EXACT and c not in {"mean_amplitude", "std_amplitude", "dc_offset"}:
            out.append(c)
        elif any(c.startswith(p) for p in ACOUSTIC_PREFIXES):
            out.append(c)
        elif c in {"peak_amplitude", "zero_crossing_rate_mean", "noise_floor_proxy", "snr_proxy"}:
            out.append(c)
    return sorted(set(out))


def select_ssl_columns(columns: Iterable[str]) -> list[str]:
    return sorted(c for c in columns if str(c).startswith("ssl_emb_"))


def row_has_features(row: pd.Series, cols: list[str]) -> bool:
    if not cols:
        return False
    present = 0
    for c in cols:
        if c not in row.index:
            continue
        val = row[c]
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue
        if str(val).strip() == "":
            continue
        present += 1
    return present >= max(1, len(cols) // 4)


def segment_overlap_metrics(
    seg_start: float,
    seg_end: float,
    fab_start: float,
    fab_end: float,
    overlap_threshold: float,
) -> dict[str, Any]:
    overlap_start = max(seg_start, fab_start)
    overlap_end = min(seg_end, fab_end)
    overlap_sec = max(0.0, overlap_end - overlap_start)
    seg_len = max(1e-9, seg_end - seg_start)
    overlap_ratio_segment = overlap_sec / seg_len

    if overlap_ratio_segment >= overlap_threshold:
        region_label = "inside_fabricated_region"
    elif overlap_sec > 0:
        region_label = "boundary_overlap"
    else:
        region_label = "outside_fabricated_region"

    return {
        "timestamp_overlap_sec": round(overlap_sec, 4),
        "timestamp_overlap_ratio_segment": round(overlap_ratio_segment, 4),
        "timestamp_region_label": region_label,
    }


def load_timestamp_annotation_rows(csv_path: Path, annotation_source: str) -> pd.DataFrame:
    if not csv_path.is_file():
        return pd.DataFrame(
            columns=[
                "annotation_source",
                "output_file",
                "fabricated_start_sec",
                "fabricated_end_sec",
            ]
        )
    df = pd.read_csv(csv_path, low_memory=False)
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        entry = {str(k).strip(): row[k] for k in df.columns}
        output_file = entry.get("output_file") or entry.get("filename") or entry.get("audio_path")
        if output_file is None or (isinstance(output_file, float) and math.isnan(output_file)):
            continue
        start = entry.get("insert_start_sec", entry.get("fabricated_start_sec", entry.get("start_sec")))
        end = entry.get("insert_end_sec", entry.get("fabricated_end_sec", entry.get("end_sec")))
        rows.append(
            {
                "annotation_source": annotation_source,
                "output_file": str(output_file).strip(),
                "fabricated_start_sec": start,
                "fabricated_end_sec": end,
            }
        )
    return pd.DataFrame(rows)


def build_file_match_index(file_df: pd.DataFrame) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for idx, row in file_df.iterrows():
        keys = {
            normalize_path_str(str(row.get("audio_path", ""))),
            path_basename(str(row.get("audio_path", ""))),
            path_stem_lower(str(row.get("audio_path", ""))),
            normalize_path_str(str(row.get("file_id", ""))),
            path_stem_lower(str(row.get("file_id", ""))),
        }
        for key in keys:
            if not key:
                continue
            index.setdefault(key.lower(), []).append(idx)
    return index


def match_timestamp_to_files(
    timestamp_df: pd.DataFrame,
    file_df: pd.DataFrame,
) -> pd.DataFrame:
    index = build_file_match_index(file_df)
    audit_rows: list[dict[str, Any]] = []
    for _, ts in timestamp_df.iterrows():
        output_file = str(ts.get("output_file", "")).strip()
        fab_start_raw = ts.get("fabricated_start_sec")
        fab_end_raw = ts.get("fabricated_end_sec")
        notes: list[str] = []
        match_status = "unmatched"
        matched_idx: int | None = None

        try:
            fab_start = float(fab_start_raw)
            fab_end = float(fab_end_raw)
        except (TypeError, ValueError):
            audit_rows.append(
                {
                    "annotation_source": ts.get("annotation_source"),
                    "output_file": output_file,
                    "matched_file_id": "",
                    "matched_audio_path": "",
                    "fabricated_start_sec": fab_start_raw,
                    "fabricated_end_sec": fab_end_raw,
                    "match_status": "invalid_time_range",
                    "notes": "non_numeric_or_missing_timestamp",
                }
            )
            continue

        if fab_end <= fab_start:
            match_status = "invalid_time_range"
            notes.append("end_sec_not_greater_than_start_sec")
        else:
            candidates: set[int] = set()
            lookup_keys = [
                normalize_path_str(output_file).lower(),
                path_basename(output_file).lower(),
                path_stem_lower(output_file),
            ]
            for key in lookup_keys:
                if key in index:
                    candidates.update(index[key])
            if len(candidates) == 1:
                matched_idx = next(iter(candidates))
                match_status = "matched"
            elif len(candidates) > 1:
                match_status = "ambiguous"
                notes.append(f"multiple_file_matches={len(candidates)}")
            else:
                notes.append("no_file_master_match")

        matched_file_id = ""
        matched_audio_path = ""
        if matched_idx is not None:
            mrow = file_df.loc[matched_idx]
            matched_file_id = str(mrow.get("file_id", ""))
            matched_audio_path = normalize_path_str(str(mrow.get("audio_path", "")))

        audit_rows.append(
            {
                "annotation_source": ts.get("annotation_source"),
                "output_file": output_file,
                "matched_file_id": matched_file_id,
                "matched_audio_path": matched_audio_path,
                "fabricated_start_sec": fab_start if match_status != "invalid_time_range" else fab_start_raw,
                "fabricated_end_sec": fab_end if match_status != "invalid_time_range" else fab_end_raw,
                "match_status": match_status,
                "notes": "; ".join(notes),
            }
        )
    return pd.DataFrame(audit_rows)


def timestamp_lookup_from_audit(audit_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    lookup: dict[str, dict[str, float]] = {}
    for _, row in audit_df.iterrows():
        if row.get("match_status") != "matched":
            continue
        fid = str(row.get("matched_file_id", "")).strip()
        if not fid:
            continue
        try:
            lookup[fid] = {
                "fabricated_start_sec": float(row["fabricated_start_sec"]),
                "fabricated_end_sec": float(row["fabricated_end_sec"]),
            }
        except (TypeError, ValueError):
            continue
    return lookup


def _acoustic_summary_vector(seg_df: pd.DataFrame) -> list[str]:
    cols = [
        c
        for c in seg_df.columns
        if c.startswith("rms_")
        or c.startswith("spectral_")
        or c.startswith("mfcc_")
        or c
        in {
            "peak_amplitude",
            "zero_crossing_rate_mean",
            "noise_floor_proxy",
            "snr_proxy",
        }
    ]
    numeric = []
    for c in cols:
        if c in seg_df.columns and pd.api.types.is_numeric_dtype(seg_df[c]):
            numeric.append(c)
    return numeric


def compute_live_localization_features(seg_df: pd.DataFrame) -> pd.DataFrame:
    """Safe within-file localization features (no timestamp-derived fields)."""
    out = seg_df.sort_values(["start_sec", "segment_id"], kind="mergesort").copy()
    ac_cols = _acoustic_summary_vector(out)
    ssl_cols = [c for c in out.columns if str(c).startswith("ssl_emb_")]

    def _row_distance(row: pd.Series, ref: pd.Series, cols: list[str]) -> float:
        if not cols:
            return float("nan")
        vals = []
        for c in cols:
            try:
                vals.append(float(row[c]) - float(ref[c]))
            except (TypeError, ValueError):
                vals.append(np.nan)
        arr = np.asarray(vals, dtype=float)
        if not np.isfinite(arr).any():
            return float("nan")
        return float(np.nanmean(np.abs(arr)))

    if ac_cols:
        ac_median = out[ac_cols].apply(pd.to_numeric, errors="coerce").median(numeric_only=True)
        out["acoustic_distance_from_file_median"] = out.apply(
            lambda r: _row_distance(r, ac_median, ac_cols), axis=1
        )
        ranks = out["acoustic_distance_from_file_median"].rank(pct=True, method="average")
        out["acoustic_deviation_percentile_within_file"] = ranks
        denom = out["acoustic_distance_from_file_median"].max() + 1e-9
        out["within_file_acoustic_deviation_score"] = out["acoustic_distance_from_file_median"] / denom
    else:
        out["acoustic_distance_from_file_median"] = np.nan
        out["acoustic_deviation_percentile_within_file"] = np.nan
        out["within_file_acoustic_deviation_score"] = np.nan

    if ssl_cols:
        ssl_median = out[ssl_cols].apply(pd.to_numeric, errors="coerce").median(numeric_only=True)
        out["ssl_distance_from_file_median"] = out.apply(
            lambda r: _row_distance(r, ssl_median, ssl_cols), axis=1
        )
        ranks = out["ssl_distance_from_file_median"].rank(pct=True, method="average")
        out["ssl_deviation_percentile_within_file"] = ranks
        denom = out["ssl_distance_from_file_median"].max() + 1e-9
        out["within_file_ssl_deviation_score"] = out["ssl_distance_from_file_median"] / denom
    else:
        out["ssl_distance_from_file_median"] = np.nan
        out["ssl_deviation_percentile_within_file"] = np.nan
        out["within_file_ssl_deviation_score"] = np.nan

    out["combined_within_file_deviation_score"] = _rowwise_nanmean(
        out[["within_file_acoustic_deviation_score", "within_file_ssl_deviation_score"]]
    )

    ac_trans = [np.nan]
    ssl_trans = [np.nan]
    for i in range(1, len(out)):
        prev = out.iloc[i - 1]
        cur = out.iloc[i]
        ac_trans.append(_row_distance(cur, prev, ac_cols) if ac_cols else np.nan)
        ssl_trans.append(_row_distance(cur, prev, ssl_cols) if ssl_cols else np.nan)
    out["neighbor_acoustic_transition_score"] = ac_trans
    out["neighbor_ssl_transition_score"] = ssl_trans
    out["combined_neighbor_transition_score"] = _rowwise_nanmean(
        out[["neighbor_acoustic_transition_score", "neighbor_ssl_transition_score"]]
    )
    return out


def _rowwise_nanmean(frame: pd.DataFrame) -> pd.Series:
    """Row-wise mean ignoring NaNs without empty-slice warnings."""
    vals = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    out = np.full(len(vals), np.nan, dtype=float)
    for i, row in enumerate(vals):
        finite = row[np.isfinite(row)]
        if finite.size:
            out[i] = float(finite.mean())
    return pd.Series(out, index=frame.index)


def is_forbidden_feature(name: str) -> bool:
    c = str(name).strip()
    if c in FORBIDDEN_AS_FEATURE_EXACT:
        return True
    cl = c.lower()
    return any(tok in cl for tok in FORBIDDEN_AS_FEATURE_SUBSTRINGS)


def build_file_gate_feature_columns(columns: Iterable[str]) -> list[str]:
    feats = select_file_acoustic_columns(columns) + select_ssl_columns(columns)
    return [c for c in feats if not is_forbidden_feature(c)]


def build_segment_localizer_feature_columns(columns: Iterable[str]) -> list[str]:
    feats = (
        select_segment_acoustic_columns(columns)
        + select_ssl_columns(columns)
        + [c for c in SAFE_LOCALIZATION_FEATURES if c in columns]
    )
    return [c for c in feats if not is_forbidden_feature(c)]


def build_leakage_audit(
    dataset_name: str,
    df_columns: Iterable[str],
    model_feature_columns: list[str],
) -> pd.DataFrame:
    """Audit forbidden columns vs proposed model feature lists."""
    feature_set = set(model_feature_columns)
    all_cols = sorted(set(df_columns))
    audited_names = set(FORBIDDEN_AS_FEATURE_EXACT) | set(TIMESTAMP_LIKE_FEATURE_EXACT)
    audited_names |= {c for c in all_cols if is_forbidden_feature(c)}

    rows: list[dict[str, str]] = []
    for col in sorted(audited_names):
        in_df = col in all_cols
        in_features = col in feature_set
        forbidden = is_forbidden_feature(col) or col in TIMESTAMP_LIKE_FEATURE_EXACT
        if not in_df:
            status = "absent"
            action = "none"
        elif in_features and forbidden:
            status = "forbidden_as_feature"
            action = "remove_from_model_features"
        elif in_df and forbidden:
            status = "present_as_metadata_ok"
            action = "keep_metadata_only"
        else:
            status = "absent"
            action = "none"
        rows.append(
            {
                "dataset": dataset_name,
                "column": col,
                "status": status,
                "in_model_feature_columns": str(in_features).lower(),
                "action": action,
            }
        )

    for col in sorted(feature_set):
        if col in audited_names:
            continue
        rows.append(
            {
                "dataset": dataset_name,
                "column": col,
                "status": "absent",
                "in_model_feature_columns": "true",
                "action": "usable_feature",
            }
        )
    return pd.DataFrame(rows)


def sample_negative_segments(
    df: pd.DataFrame,
    *,
    strategy: str,
    max_negative_segments_per_category: int,
    random_seed: int,
) -> pd.DataFrame:
    positives = df[df["target_is_fabricated_segment"].astype(str) == "1"].copy()
    negatives = df[df["target_is_fabricated_segment"].astype(str) == "0"].copy()
    rng = random_seed

    if strategy == "all":
        return pd.concat([positives, negatives], ignore_index=True)

    sampled_neg_parts: list[pd.DataFrame] = []
    pos_count = len(positives)

    for source_type in SEGMENT_NEGATIVE_SOURCE_TYPES:
        pool = negatives[negatives["segment_source_type"] == source_type]
        if pool.empty:
            continue
        if strategy == "cap_per_category":
            n = min(len(pool), max_negative_segments_per_category)
        elif strategy == "balanced_by_positive":
            n = min(len(pool), max(pos_count, 1), max_negative_segments_per_category)
        else:
            raise ValueError(f"Unknown negative_sample_strategy: {strategy}")
        sampled_neg_parts.append(pool.sample(n=n, random_state=rng))

    if sampled_neg_parts:
        negatives_out = pd.concat(sampled_neg_parts, ignore_index=True)
    else:
        negatives_out = negatives.iloc[0:0]
    return pd.concat([positives, negatives_out], ignore_index=True)


def compute_balance_summary(
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
) -> dict[str, Any]:
    warnings: list[str] = []
    fg_pos = int((file_gate_df["target_is_partial_fabrication_file"].astype(str) == "1").sum())
    fg_neg = int((file_gate_df["target_is_partial_fabrication_file"].astype(str) == "0").sum())
    seg_pos = int((segment_df["target_is_fabricated_segment"].astype(str) == "1").sum())
    seg_neg = int((segment_df["target_is_fabricated_segment"].astype(str) == "0").sum())

    neg_mask = segment_df["target_is_fabricated_segment"].astype(str) == "0"
    seg_neg_clean = int((neg_mask & (segment_df["segment_source_type"] == "clean_direct_negative")).sum())
    seg_neg_replay = int((neg_mask & (segment_df["segment_source_type"] == "replay_negative")).sum())
    seg_neg_mixer = int((neg_mask & (segment_df["segment_source_type"] == "mixer_negative")).sum())
    seg_neg_outside = int(
        (neg_mask & (segment_df["segment_source_type"] == "fabricated_outside_same_file")).sum()
    )

    pos_seg = segment_df[segment_df["target_is_fabricated_segment"].astype(str) == "1"]
    ai_fab_pos = int((pos_seg["fabrication_direction"] == "ai_fabricated").sum())
    human_fab_pos = int((pos_seg["fabrication_direction"] == "human_fabricated").sum())
    files_with_pos = int(pos_seg["file_id"].nunique()) if not pos_seg.empty else 0
    partial_files = segment_df[segment_df["file_category"].isin(FILE_GATE_POSITIVE_CATEGORIES)]
    files_without_pos = int(partial_files["file_id"].nunique()) - files_with_pos

    if fg_pos == 0 or fg_neg == 0:
        warnings.append("file_gate_missing_positive_or_negative_class")
    if seg_pos == 0 or seg_neg == 0:
        warnings.append("segment_missing_positive_or_negative_class")
    if seg_neg_outside == 0:
        warnings.append("no_outside_same_partial_negatives")
    if seg_neg_clean == 0:
        warnings.append("no_clean_direct_negatives")
    if seg_neg_replay == 0:
        warnings.append("no_replay_negatives")
    if seg_neg_mixer == 0:
        warnings.append("no_mixer_negatives")
    if files_without_pos > 0:
        warnings.append(f"partial_files_without_positive_segments={files_without_pos}")

    return {
        "file_gate_total_rows": len(file_gate_df),
        "file_gate_positive_count": fg_pos,
        "file_gate_negative_count": fg_neg,
        "segment_total_rows": len(segment_df),
        "segment_positive_count": seg_pos,
        "segment_negative_count": seg_neg,
        "segment_negative_clean_count": seg_neg_clean,
        "segment_negative_replay_count": seg_neg_replay,
        "segment_negative_mixer_count": seg_neg_mixer,
        "segment_negative_outside_same_partial_count": seg_neg_outside,
        "ai_fabricated_positive_segment_count": ai_fab_pos,
        "human_fabricated_positive_segment_count": human_fab_pos,
        "files_with_positive_segments": files_with_pos,
        "files_without_positive_segments": max(files_without_pos, 0),
        "warnings": "; ".join(warnings),
    }


def attach_model_feature_json(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    payload = json.dumps(feature_cols, separators=(",", ":"))
    out = df.copy()
    out["model_feature_columns_json"] = payload
    return out


def progress(msg: str, *, enabled: bool = True) -> None:
    if enabled:
        print(msg, flush=True)
