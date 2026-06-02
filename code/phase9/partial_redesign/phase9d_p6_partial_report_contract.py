"""
Phase 9D-P6: Partial-fabrication report contract helpers (experimental / manual review only).

Safe for Phase 9C/9E live pipelines — does not emit conclusive synthetic/authentic labels.
"""

from __future__ import annotations

from typing import Any

from phase9d_p5_training_utils import P5C_ACCEPTED_CASCADE_THRESHOLDS

MODULE_STATUS = "experimental_manual_review_only"

EVIDENCE_LABEL_DETECTED = "partial_fabrication_evidence_detected"
EVIDENCE_LABEL_NOT_DETECTED = "no_partial_fabrication_evidence_detected"
EVIDENCE_LABEL_UNAVAILABLE = "partial_fabrication_analysis_unavailable"

WORDING_DETECTED = (
    "Experimental partial-fabrication evidence was detected. The highlighted segment is a "
    "candidate region for manual forensic review; this is not a conclusive authenticity decision."
)
WORDING_NOT_DETECTED = (
    "No partial-fabrication evidence was detected by the experimental partial module. "
    "This does not prove the audio is authentic; subtle or unseen partial manipulations may still be missed."
)
WORDING_UNAVAILABLE = (
    "Partial-fabrication analysis was unavailable for this file. Manual forensic review is recommended "
    "if partial manipulation is suspected."
)

DEFAULT_LIMITATIONS = [
    "Experimental partial-fabrication evidence indicator only.",
    "Conclusive authenticity decision: no.",
    "Manual forensic review is recommended.",
    "Known false negatives and false positives remain in held-out testing.",
]

FORENSIC_SUMMARY_SAFE = "Forensic evidence indicators were observed"

INTEGRATION_NOTE_TAGS = (
    "experimental_partial_fabrication_evidence; manual_review_required; "
    "no_conclusive_authenticity_decision; no_operational_deployment_claim; no_legal_evidence_claim"
)


def default_partial_report_contract() -> dict[str, Any]:
    """JSON schema template for live pipeline `partial_fabrication` section."""
    th = dict(P5C_ACCEPTED_CASCADE_THRESHOLDS)
    return {
        "partial_fabrication": {
            "module_status": MODULE_STATUS,
            "evidence_detected": None,
            "evidence_label": EVIDENCE_LABEL_UNAVAILABLE,
            "file_gate_probability": None,
            "max_segment_probability": None,
            "high_segment_fraction": None,
            "topk_minus_rest_probability": None,
            "broad_activation_flag": None,
            "candidate_segment": {
                "start_sec": None,
                "end_sec": None,
                "probability": None,
                "rank": None,
            },
            "top_segments": [],
            "thresholds": {
                "file_gate_threshold": float(th["file_gate_threshold"]),
                "segment_threshold": float(th["segment_threshold"]),
                "contrast_threshold": float(th["contrast_threshold"]),
                "broad_limit": float(th["broad_limit"]),
            },
            "limitations": list(DEFAULT_LIMITATIONS),
            "user_facing_summary_detected": WORDING_DETECTED,
            "user_facing_summary_not_detected": WORDING_NOT_DETECTED,
            "user_facing_summary_unavailable": WORDING_UNAVAILABLE,
        }
    }


def format_partial_evidence_contract(
    *,
    analysis_ok: bool,
    evidence_detected: bool,
    file_gate_probability: float | None = None,
    max_segment_probability: float | None = None,
    high_segment_fraction: float | None = None,
    topk_minus_rest_probability: float | None = None,
    broad_activation_flag: bool | None = None,
    candidate_segment_start: float | None = None,
    candidate_segment_end: float | None = None,
    candidate_segment_probability: float | None = None,
    candidate_segment_rank: int | None = None,
    top_segments: list[dict[str, Any]] | None = None,
    extra_limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Build populated `partial_fabrication` contract section from cascade outputs."""
    base = default_partial_report_contract()
    section = base["partial_fabrication"]
    th = section["thresholds"]

    if not analysis_ok:
        section["evidence_label"] = EVIDENCE_LABEL_UNAVAILABLE
        section["evidence_detected"] = None
        section["user_facing_message"] = WORDING_UNAVAILABLE
        return base

    section["evidence_detected"] = bool(evidence_detected)
    section["evidence_label"] = (
        EVIDENCE_LABEL_DETECTED if evidence_detected else EVIDENCE_LABEL_NOT_DETECTED
    )
    section["user_facing_message"] = (
        WORDING_DETECTED if evidence_detected else WORDING_NOT_DETECTED
    )
    section["file_gate_probability"] = file_gate_probability
    section["max_segment_probability"] = max_segment_probability
    section["high_segment_fraction"] = high_segment_fraction
    section["topk_minus_rest_probability"] = topk_minus_rest_probability
    section["broad_activation_flag"] = broad_activation_flag
    section["candidate_segment"] = {
        "start_sec": candidate_segment_start,
        "end_sec": candidate_segment_end,
        "probability": candidate_segment_probability,
        "rank": candidate_segment_rank if candidate_segment_rank is not None else None,
    }
    normalized_top: list[dict[str, Any]] = []
    for row in top_segments or []:
        normalized_top.append(
            {
                "rank": int(row.get("rank", row.get("segment_rank", 0))),
                "start_sec": float(row["start_sec"]) if row.get("start_sec") is not None else None,
                "end_sec": float(row["end_sec"]) if row.get("end_sec") is not None else None,
                "probability": float(row["probability"]) if row.get("probability") is not None else None,
                "manual_review_recommended": True,
            }
        )
    section["top_segments"] = normalized_top
    section["thresholds"] = th
    lim = list(DEFAULT_LIMITATIONS)
    if extra_limitations:
        lim.extend(extra_limitations)
    section["limitations"] = lim
    return base


def build_partial_fabrication_report_section(contract: dict[str, Any]) -> dict[str, Any]:
    """
    Return a report-section dict for merging into Phase 9C forensic JSON.

    Keeps legacy `partial_fabrication_evidence` axis separate; adds `partial_fabrication`
    contract block for Phase 9E demo integration.
    """
    pf = contract.get("partial_fabrication", {})
    return {
        "partial_fabrication": pf,
        "partial_fabrication_integration_note": INTEGRATION_NOTE_TAGS,
    }
