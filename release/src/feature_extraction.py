"""Live acoustic feature extraction for Phase 9C."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .utils import repo_root


def _import_phase8c():
    root = repo_root()
    feat_dir = root / "code" / "phase8" / "features"
    if str(feat_dir) not in sys.path:
        sys.path.insert(0, str(feat_dir))
    try:
        import phase8c_feature_utils as p8c  # type: ignore

        return p8c
    except Exception as exc:
        raise RuntimeError(
            "Phase 9C requires code.phase8.features.phase8c_feature_utils. "
            f"Import failed: {exc}"
        ) from exc


def safe_nanmean(values: Any, default: float = 0.0) -> float:
    """Row-safe nanmean without RuntimeWarning on empty/all-NaN slices."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return float(default)
    with np.errstate(all="ignore"):
        mean = np.nanmean(arr)
    if np.isnan(mean):
        return float(default)
    return float(mean)


def _row_nanmean_from_frame(row: pd.Series, cols: list[str], default: float = 0.0) -> float:
    vals = [row[c] for c in cols if c in row.index]
    return safe_nanmean(vals, default=default)


def extract_file_acoustic_features(y: np.ndarray, sr: int) -> dict[str, float]:
    p8c = _import_phase8c()
    seg, err = p8c.safe_audio_slice(y, sr, 0.0, len(y) / float(sr))
    if seg is None:
        return p8c.empty_feature_dict(p8c.FILE_FEATURE_NAMES)
    feats = p8c.extract_file_feature_dict(seg, sr)
    # Ensure full file acoustic schema is present for pipeline alignment.
    for name in p8c.FILE_FEATURE_NAMES:
        feats.setdefault(name, np.nan)
    return feats


def extract_segment_acoustic_features(
    segments: pd.DataFrame, y: np.ndarray, sr: int, mode: str = "full"
) -> pd.DataFrame:
    p8c = _import_phase8c()
    rows: list[dict[str, Any]] = []
    for _, seg in segments.iterrows():
        seg_y, err = p8c.safe_audio_slice(
            y, sr, float(seg["start_sec"]), float(seg["end_sec"])
        )
        base = seg.to_dict()
        if seg_y is None:
            feats = p8c.empty_feature_dict(p8c.SEGMENT_FEATURE_NAMES)
            base["extraction_status"] = err or "segment_error"
        else:
            feats = p8c.extract_segment_feature_dict(seg_y, sr, mode=mode)
            base["extraction_status"] = "ok"
        base.update(feats)
        rows.append(base)
    return pd.DataFrame(rows)


def get_default_file_acoustic_feature_names() -> list[str]:
    p8c = _import_phase8c()
    return list(p8c.FILE_FEATURE_NAMES)


def get_default_segment_acoustic_feature_names() -> list[str]:
    p8c = _import_phase8c()
    return list(p8c.SEGMENT_FEATURE_NAMES)


def ensure_ssl_embedding_columns(features: dict[str, Any], dim: int = 768) -> dict[str, Any]:
    out = dict(features)
    for i in range(dim):
        key = f"ssl_emb_{i:03d}"
        if key not in out:
            out[key] = np.nan
    return out


def align_features_to_metadata(
    features: dict[str, Any] | pd.Series,
    feature_names: list[str],
) -> pd.DataFrame:
    row = {name: np.nan for name in feature_names}
    src = features.to_dict() if isinstance(features, pd.Series) else dict(features)
    for name in feature_names:
        if name in src:
            val = src[name]
            try:
                row[name] = float(val)
            except (TypeError, ValueError):
                row[name] = np.nan
    return pd.DataFrame([row])


def acoustic_summary_vector(seg_df: pd.DataFrame) -> list[str]:
    cols = [
        c
        for c in seg_df.columns
        if c.startswith("rms_")
        or c.startswith("spectral_")
        or c.startswith("mfcc_")
        or c in {
            "peak_amplitude",
            "zero_crossing_rate_mean",
            "noise_floor_proxy",
            "snr_proxy",
        }
    ]
    return [c for c in cols if pd.api.types.is_numeric_dtype(seg_df[c])]


def compute_live_localization_features(seg_df: pd.DataFrame) -> pd.DataFrame:
    """Safe live localization features only (no timestamp-label-derived fields)."""
    out = seg_df.copy()
    ac_cols = acoustic_summary_vector(out)
    ssl_cols = [c for c in out.columns if c.startswith("ssl_emb_")]

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
        return safe_nanmean(np.abs(arr)) if len(arr) else 0.0

    if ac_cols:
        ac_median = out[ac_cols].median(numeric_only=True)
        out["acoustic_distance_from_file_median"] = out.apply(
            lambda r: _row_distance(r, ac_median, ac_cols), axis=1
        )
        ranks = out["acoustic_distance_from_file_median"].rank(pct=True, method="average")
        out["acoustic_deviation_percentile_within_file"] = ranks
        out["within_file_acoustic_deviation_score"] = (
            out["acoustic_distance_from_file_median"]
            / (out["acoustic_distance_from_file_median"].max() + 1e-9)
        )
    else:
        out["acoustic_distance_from_file_median"] = np.nan
        out["acoustic_deviation_percentile_within_file"] = np.nan
        out["within_file_acoustic_deviation_score"] = np.nan

    if ssl_cols:
        ssl_median = out[ssl_cols].median(numeric_only=True)
        out["ssl_distance_from_file_median"] = out.apply(
            lambda r: _row_distance(r, ssl_median, ssl_cols), axis=1
        )
        ranks = out["ssl_distance_from_file_median"].rank(pct=True, method="average")
        out["ssl_deviation_percentile_within_file"] = ranks
        out["within_file_ssl_deviation_score"] = (
            out["ssl_distance_from_file_median"]
            / (out["ssl_distance_from_file_median"].max() + 1e-9)
        )
    else:
        out["ssl_distance_from_file_median"] = np.nan
        out["ssl_deviation_percentile_within_file"] = np.nan
        out["within_file_ssl_deviation_score"] = np.nan

    out["combined_within_file_deviation_score"] = out.apply(
        lambda r: _row_nanmean_from_frame(
            r,
            ["within_file_acoustic_deviation_score", "within_file_ssl_deviation_score"],
        ),
        axis=1,
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
    out["combined_neighbor_transition_score"] = out.apply(
        lambda r: _row_nanmean_from_frame(
            r,
            ["neighbor_acoustic_transition_score", "neighbor_ssl_transition_score"],
        ),
        axis=1,
    )
    return out
