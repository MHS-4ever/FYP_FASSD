"""Schema helpers for Phase 9A response structure."""

from __future__ import annotations

from typing import Any


def default_forensic_response(case_id: str | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "skeleton_ready",
        "audio_metadata": {},
        "origin_evidence": {"label": "pending", "confidence_indicator": None, "notes": []},
        "replay_evidence": {"label": "pending", "confidence_indicator": None, "notes": []},
        "mixer_channel_evidence": {
            "label": "pending",
            "confidence_indicator": None,
            "notes": [],
        },
        "partial_fabrication_evidence": {
            "label": "pending",
            "confidence_indicator": None,
            "notes": [],
        },
        "segment_candidates": [],
        "fusion_status": "pending_phase9b_phase9c",
        "forensic_summary": (
            "Skeleton ready. Phase 9B/9C required before full inference."
        ),
        "manual_review_required": True,
        "limitations": [
            "experimental_forensic_prototype",
            "no model packaging executed in Phase 9A",
            "no live inference executed in Phase 9A",
        ],
    }
