"""Segmentation for Phase 9C live inference."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def make_segments(
    y: np.ndarray,
    sr: int,
    segment_duration_sec: float = 4.0,
    hop_sec: float = 2.0,
) -> pd.DataFrame:
    y = np.asarray(y, dtype=np.float64)
    total_sec = len(y) / float(sr) if sr > 0 else 0.0
    seg_len = max(int(segment_duration_sec * sr), 1)
    hop_len = max(int(hop_sec * sr), 1)

    rows: list[dict[str, Any]] = []
    if total_sec <= segment_duration_sec:
        end = min(seg_len, len(y))
        rows.append(
            _segment_row(
                segment_id="seg_0000",
                start_sec=0.0,
                end_sec=total_sec,
                sample_start=0,
                sample_end=end,
                sr=sr,
            )
        )
        return pd.DataFrame(rows)

    start_sample = 0
    idx = 0
    while start_sample < len(y):
        end_sample = min(start_sample + seg_len, len(y))
        start_sec = start_sample / float(sr)
        end_sec = end_sample / float(sr)
        rows.append(
            _segment_row(
                segment_id=f"seg_{idx:04d}",
                start_sec=start_sec,
                end_sec=end_sec,
                sample_start=start_sample,
                sample_end=end_sample,
                sr=sr,
            )
        )
        if end_sample >= len(y):
            break
        start_sample += hop_len
        idx += 1

    if not rows:
        rows.append(
            _segment_row(
                segment_id="seg_0000",
                start_sec=0.0,
                end_sec=total_sec,
                sample_start=0,
                sample_end=len(y),
                sr=sr,
            )
        )
    return pd.DataFrame(rows)


def _segment_row(
    segment_id: str,
    start_sec: float,
    end_sec: float,
    sample_start: int,
    sample_end: int,
    sr: int,
) -> dict[str, Any]:
    return {
        "segment_id": segment_id,
        "start_sec": round(float(start_sec), 4),
        "end_sec": round(float(end_sec), 4),
        "segment_duration_sec": round(max(0.0, end_sec - start_sec), 4),
        "sample_start": int(sample_start),
        "sample_end": int(sample_end),
        "sample_rate": int(sr),
    }
