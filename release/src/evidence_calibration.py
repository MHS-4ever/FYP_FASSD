"""Phase 6 — evidence strength bands and inconclusive states for release UI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .utils import read_yaml_safe, release_root

BAND_LOW = "Low evidence"
BAND_MEDIUM = "Medium evidence"
BAND_HIGH = "High evidence"
STATE_INCONCLUSIVE = "Inconclusive"
STATE_INSUFFICIENT = "Insufficient evidence"

AXIS_KEYS = {
    "origin": "origin",
    "replay": "replay",
    "mixer": "mixer",
    "mixer_channel": "mixer",
    "partial": "partial_segment",
    "partial_segment": "partial_segment",
}


def _default_calibration() -> dict[str, Any]:
    return {
        "schema_version": "phase6_evidence_calibration_v1",
        "fitted_on": "default_threshold_relative",
        "axes": {
            "origin": {"low_max": 0.50, "medium_max": 0.92, "threshold": 0.92},
            "replay": {"low_max": 0.40, "medium_max": 0.65, "threshold": 0.65},
            "mixer": {"low_max": 0.50, "medium_max": 0.75, "threshold": 0.75},
            "partial_segment": {"low_max": 0.50, "medium_max": 0.95, "threshold": 0.95},
        },
    }


@lru_cache(maxsize=1)
def load_evidence_calibration() -> dict[str, Any]:
    path = release_root() / "config" / "evidence_calibration.json"
    if not path.is_file():
        return _default_calibration()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("axes"):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return _default_calibration()


def resolve_axis_key(axis: str) -> str:
    return AXIS_KEYS.get(axis.strip().lower(), axis.strip().lower())


def evidence_band(
    axis: str,
    probability: float | None,
    *,
    prediction_success: bool = True,
) -> str:
    if not prediction_success or probability is None:
        return STATE_INCONCLUSIVE
    try:
        p = float(probability)
    except (TypeError, ValueError):
        return STATE_INSUFFICIENT
    if not (0.0 <= p <= 1.0) or p != p:
        return STATE_INSUFFICIENT

    cfg = load_evidence_calibration()["axes"].get(resolve_axis_key(axis), {})
    low_max = float(cfg.get("low_max", 0.33))
    medium_max = float(cfg.get("medium_max", 0.66))
    if p <= low_max:
        return BAND_LOW
    if p <= medium_max:
        return BAND_MEDIUM
    return BAND_HIGH


def format_evidence_band_text(
    axis: str,
    probability: float | None,
    *,
    prediction_success: bool = True,
    prefix: str = "Evidence strength",
) -> str:
    band = evidence_band(axis, probability, prediction_success=prediction_success)
    return f"{prefix}: {band}"


def format_technical_raw_score(
    probability: float | None,
    *,
    label: str = "Uncalibrated model score",
) -> str:
    if probability is None or not isinstance(probability, (int, float)):
        return f"{label}: —"
    return f"{label}: {float(probability):.3f}"


def enrich_axis_evidence_display(
    evidence: dict[str, Any],
    *,
    axis: str,
) -> dict[str, Any]:
    """Add Phase 6 band fields without mutating model outputs."""
    out = dict(evidence)
    prob = out.get("probability")
    ok = bool(out.get("prediction_success"))
    out["evidence_strength_band"] = evidence_band(axis, prob, prediction_success=ok)
    out["evidence_strength_band_text"] = format_evidence_band_text(axis, prob, prediction_success=ok)
    out["technical_raw_score_text"] = format_technical_raw_score(prob)
    return out
