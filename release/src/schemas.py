"""Schema helpers for Phase 9C response structure."""

from __future__ import annotations

from typing import Any


def empty_axis() -> dict[str, Any]:
    return {
        "label": "not_evaluated",
        "evidence_label": "not_evaluated",
        "evidence_strength": "not_evaluated",
        "probability": None,
        "threshold_candidate": None,
        "model_available": False,
        "prediction_success": False,
        "notes": [],
    }


def default_forensic_response(case_id: str | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "experimental_forensic_prototype",
        "audio_metadata": {},
        "origin_evidence": empty_axis(),
        "replay_evidence": empty_axis(),
        "mixer_channel_evidence": empty_axis(),
        "partial_fabrication_evidence": empty_axis(),
        "segment_candidates": [],
        "fusion_status": "not_evaluated",
        "forensic_risk_level": "inconclusive",
        "forensic_summary": "",
        "manual_review_required": True,
        "manual_review_reason": "none",
        "limitations": [
            "experimental_forensic_prototype",
            "evidence indicators only",
        ],
        "debug_info": None,
    }


def debug_partial_segment_score_schema() -> dict[str, Any]:
    """Optional debug-only rows under debug_info.partial_segment_scores (return_debug=True)."""
    return {
        "case_id": "string",
        "segment_id": "string|int",
        "start_sec": "float",
        "end_sec": "float",
        "partial_probability": "float|null",
        "partial_rank": "int",
        "partial_above_threshold": "bool",
        "candidate_type": "partial_segment_score",
        "partial_localization_gate": "string",
    }
