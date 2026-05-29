"""Forensic-safe report generation for Phase 9C."""

from __future__ import annotations

from typing import Any


def generate_partial_axis_text(evidence: dict[str, Any]) -> str:
    if evidence.get("broad_activation_warning") is True:
        return (
            "Partial fabrication: partial segment activation was broad across the file, "
            "so it is not treated as localized partial-fabrication evidence."
        )
    if str(evidence.get("partial_fusion_block_reason", "")) == "blocked_by_replay_or_mixer_context":
        return (
            "Partial fabrication: partial segment activation was not used as elevated "
            "partial-fabrication evidence because stronger replay/mixer/channel evidence may explain "
            "the segment-level changes."
        )
    if evidence.get("partial_fusion_eligible") is False and evidence.get("partial_arbitration_note"):
        return (
            "Partial fabrication: partial segment indicators were not used as elevated "
            "partial-fabrication evidence because stronger replay/mixer/channel evidence may explain "
            "the segment-level activation."
        )
    gate = evidence.get("partial_localization_gate", "")
    if gate == "global_activation_not_localized":
        return (
            "Partial fabrication: segment-level partial model activation was broad across the file, "
            "so it is not treated as localized partial-fabrication evidence. Manual review may inspect "
            "the audio, but this output does not identify a localized fabricated region."
        )
    if gate == "localized_pattern_supported" and evidence.get("partial_fusion_eligible") is True:
        return (
            "Partial fabrication: localized partial-fabrication evidence indicators were found in "
            "candidate timestamp regions. Manual review is recommended. This is not final forensic proof."
        )
    return generate_axis_text("Partial fabrication", evidence)


def generate_axis_text(axis_name: str, evidence: dict[str, Any]) -> str:
    label = evidence.get("evidence_label") or evidence.get("label", "not_evaluated")
    strength = evidence.get("evidence_strength", "not_evaluated")
    prob = evidence.get("probability")
    prob_txt = f"{prob:.3f}" if isinstance(prob, (int, float)) else "n/a"
    return (
        f"{axis_name}: experimental evidence indicator '{label}' "
        f"(strength={strength}, probability={prob_txt}). "
        "This is not a final forensic proof."
    )


def generate_segment_candidate_text(segment_candidates: list[dict[str, Any]]) -> str:
    if not segment_candidates:
        return "No candidate segments ranked."
    top = segment_candidates[:3]
    parts = []
    for seg in top:
        parts.append(
            f"candidate segment {seg.get('segment_id')} "
            f"({seg.get('start_sec')}s-{seg.get('end_sec')}s) "
            f"partial indicator={seg.get('partial_probability', 'n/a')}"
        )
    return "Top candidate segments: " + "; ".join(parts) + ". Manual review recommended."


def generate_limitations() -> list[str]:
    return [
        "experimental_forensic_prototype",
        "evidence indicators only; not final forensic proof",
        "manual review recommended",
        "replay/mixer indicators do not mean AI-generated",
        "reference models (AASIST/HybridResNet) are inactive in this pipeline",
        "no single binary authenticity score produced",
    ]


def generate_safe_report(result_dict: dict[str, Any]) -> str:
    lines = [
        "# Experimental Forensic Analysis Report",
        "",
        f"Case ID: {result_dict.get('case_id')}",
        f"Status: {result_dict.get('status')}",
        "",
        "## Summary",
        result_dict.get("forensic_summary", ""),
        "",
        "## Evidence axes (separate indicators)",
        generate_axis_text("Origin", result_dict.get("origin_evidence", {})),
        generate_axis_text("Replay", result_dict.get("replay_evidence", {})),
        generate_axis_text("Mixer/channel", result_dict.get("mixer_channel_evidence", {})),
        generate_partial_axis_text(result_dict.get("partial_fabrication_evidence", {})),
        "",
        "## Candidate segments",
        generate_segment_candidate_text(result_dict.get("segment_candidates", [])),
        "",
        "## Fusion",
        f"Fusion status: {result_dict.get('fusion_status')}",
        f"Risk level: {result_dict.get('forensic_risk_level', 'inconclusive')}",
        f"Manual review required: {result_dict.get('manual_review_required')}",
        "",
        "## Limitations",
    ]
    for item in result_dict.get("limitations", generate_limitations()):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_forensic_summary(response_payload: dict[str, Any]) -> str:
    fusion = response_payload.get("fusion_status", "inconclusive")
    review = response_payload.get("manual_review_required", True)
    n_seg = len(response_payload.get("segment_candidates", []))
    axes = [
        response_payload.get("origin_evidence", {}),
        response_payload.get("replay_evidence", {}),
        response_payload.get("mixer_channel_evidence", {}),
        response_payload.get("partial_fabrication_evidence", {}),
    ]
    ok_count = sum(1 for a in axes if a.get("prediction_success"))
    if ok_count == 0:
        return (
            "Experimental prototype run completed, but active model predictions did not succeed. "
            "Manual review required. This output is not final forensic proof."
        )
    return (
        "Experimental prototype evidence indicators generated from packaged Phase 9B models. "
        f"Fusion status: {fusion}. Successful axis predictions: {ok_count}/4. "
        f"Candidate segments: {n_seg}. "
        f"Manual review {'required' if review else 'not required by default rule set'}. "
        "Output is consistent with multi-axis review workflow support only."
    )
