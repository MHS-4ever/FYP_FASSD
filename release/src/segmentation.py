"""Segmentation skeleton for candidate segment generation."""

from __future__ import annotations

from typing import Any


def make_segments(audio_waveform, sample_rate: int, duration_sec: float, hop_sec: float) -> list[dict[str, Any]]:
    # TODO(Phase 9C): perform real sliding-window segmentation.
    return [
        {
            "segment_id": "seg_000",
            "start_sec": 0.0,
            "end_sec": float(duration_sec),
            "sample_rate": sample_rate,
            "status": "placeholder",
        }
    ]
