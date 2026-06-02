"""
Phase 9E-P1: Format Phase 9C inference output + P6 partial contract for API/Gradio.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parent
_PARTIAL_REDESIGN = _APP_DIR.parent / "partial_redesign"
for _p in (_APP_DIR, _PARTIAL_REDESIGN):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app_config import (  # noqa: E402
    APP_PHASE,
    load_partial_module_metadata,
    load_partial_report_contract_template,
    safety_banner,
)

from phase9d_p6_partial_report_contract import (  # noqa: E402
    EVIDENCE_LABEL_DETECTED,
    EVIDENCE_LABEL_NOT_DETECTED,
    EVIDENCE_LABEL_UNAVAILABLE,
    FORENSIC_SUMMARY_SAFE,
    MODULE_STATUS,
    WORDING_DETECTED,
    WORDING_NOT_DETECTED,
    WORDING_UNAVAILABLE,
    format_partial_evidence_contract,
)

_ELEVATED = frozenset({"moderate", "high", "elevated_partial_fabrication_indicator"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


def _partial_evidence_detected_from_phase9c(partial_axis: dict[str, Any]) -> bool:
    if not partial_axis.get("prediction_success"):
        return False
    if partial_axis.get("partial_fusion_eligible") is True:
        strength = str(partial_axis.get("partial_evidence_strength_for_fusion", ""))
        if strength in _ELEVATED:
            return True
    label = str(partial_axis.get("evidence_label", "")).lower()
    if "elevated" in label or "localized" in label:
        gate = str(partial_axis.get("partial_localization_gate", ""))
        if gate == "localized_pattern_supported":
            return True
    return False


def build_partial_fabrication_section(
    phase9c_result: dict[str, Any],
    *,
    return_top_segments: bool = True,
) -> dict[str, Any]:
    """
    Map Phase 9C `partial_fabrication_evidence` into P6 `partial_fabrication` report contract.

    Phase 9C live inference uses the packaged segment partial axis; P6 metadata/thresholds
    define the experimental manual-review report contract for apps.
    """
    p6_meta = load_partial_module_metadata()
    partial_axis = dict(phase9c_result.get("partial_fabrication_evidence") or {})
    analysis_ok = bool(partial_axis.get("prediction_success"))

    max_seg = partial_axis.get("max_segment_probability")
    if max_seg is None:
        max_seg = partial_axis.get("gated_partial_probability")
    hsf = partial_axis.get("high_segment_fraction")
    topk = partial_axis.get("topk_minus_rest_probability")
    broad = partial_axis.get("broad_activation_warning")

    candidates = list(phase9c_result.get("segment_candidates") or [])
    cand_start = cand_end = cand_prob = cand_rank = None
    if candidates:
        top = candidates[0]
        cand_start = top.get("start_sec")
        cand_end = top.get("end_sec")
        cand_prob = top.get("partial_probability")
        cand_rank = top.get("candidate_rank", 1)

    top_segments: list[dict[str, Any]] = []
    if return_top_segments:
        for row in candidates[:10]:
            p = row.get("partial_probability")
            top_segments.append(
                {
                    "rank": int(row.get("candidate_rank", 0)),
                    "start_sec": row.get("start_sec"),
                    "end_sec": row.get("end_sec"),
                    "probability": None if p is None else float(p),
                    "manual_review_recommended": True,
                }
            )

    evidence_detected = _partial_evidence_detected_from_phase9c(partial_axis)

    contract = format_partial_evidence_contract(
        analysis_ok=analysis_ok,
        evidence_detected=evidence_detected,
        file_gate_probability=None,
        max_segment_probability=float(max_seg) if max_seg is not None else None,
        high_segment_fraction=float(hsf) if hsf is not None else None,
        topk_minus_rest_probability=float(topk) if topk is not None else None,
        broad_activation_flag=bool(broad) if broad is not None else None,
        candidate_segment_start=float(cand_start) if cand_start is not None else None,
        candidate_segment_end=float(cand_end) if cand_end is not None else None,
        candidate_segment_probability=float(cand_prob) if cand_prob is not None else None,
        candidate_segment_rank=int(cand_rank) if cand_rank is not None else None,
        top_segments=top_segments,
        extra_limitations=[
            "Phase 9C live pipeline segment partial axis mapped to P6 contract (P5B file gate not run in 9C path).",
        ],
    )
    section = contract["partial_fabrication"]
    section["module_status"] = str(p6_meta.get("status", MODULE_STATUS))
    p6_limits = list(p6_meta.get("limitations", []))
    merged_limits = list(dict.fromkeys(p6_limits + list(section.get("limitations", []))))
    section["limitations"] = merged_limits
    th = dict(p6_meta.get("thresholds", section.get("thresholds", {})))
    if th:
        section["thresholds"] = th

    if not analysis_ok:
        section["evidence_label"] = EVIDENCE_LABEL_UNAVAILABLE
        section["user_facing_message"] = WORDING_UNAVAILABLE
    elif evidence_detected:
        section["evidence_label"] = EVIDENCE_LABEL_DETECTED
        section["user_facing_message"] = WORDING_DETECTED
    else:
        section["evidence_label"] = EVIDENCE_LABEL_NOT_DETECTED
        section["user_facing_message"] = WORDING_NOT_DETECTED

    return section


def build_evidence_summary(phase9c_result: dict[str, Any], partial_section: dict[str, Any]) -> str:
    parts: list[str] = []
    fusion = str(phase9c_result.get("fusion_status", "not_evaluated"))
    parts.append(f"Fusion status (experimental): {fusion}")
    if partial_section.get("evidence_detected") is True:
        parts.append("Partial-fabrication experimental evidence: detected (manual review recommended).")
    elif partial_section.get("evidence_detected") is False:
        parts.append("Partial-fabrication experimental evidence: not detected (does not prove authenticity).")
    else:
        parts.append("Partial-fabrication experimental evidence: unavailable.")
    if fusion not in ("not_evaluated", "inconclusive", ""):
        parts.append(FORENSIC_SUMMARY_SAFE + " (not a conclusive authenticity decision).")
    parts.append("Conclusive authenticity decision: no.")
    return " ".join(parts)


def build_app_analyze_response(
    *,
    file_name: str,
    phase9c_result: dict[str, Any],
    return_top_segments: bool = True,
    save_report_path: str | None = None,
) -> dict[str, Any]:
    partial_section = build_partial_fabrication_section(
        phase9c_result, return_top_segments=return_top_segments
    )
    meta = load_partial_module_metadata()
    limitations = list(phase9c_result.get("limitations", []))
    limitations.extend(partial_section.get("limitations", []))
    limitations.extend(meta.get("limitations", [])[:6])
    limitations = list(dict.fromkeys(limitations))

    duration = None
    audio_meta = phase9c_result.get("audio_metadata") or {}
    if isinstance(audio_meta, dict):
        duration = audio_meta.get("duration_sec")

    processing_status = "ok" if phase9c_result.get("status") != "error" else "error"

    out: dict[str, Any] = {
        "request_id": str(uuid.uuid4()),
        "phase": APP_PHASE,
        "file_name": file_name,
        "duration_sec": duration,
        "processing_status": processing_status,
        "case_id": phase9c_result.get("case_id"),
        "phase9c_report": phase9c_result,
        "partial_fabrication": partial_section,
        "partial_fabrication_evidence_legacy_axis": phase9c_result.get("partial_fabrication_evidence"),
        "evidence_summary": build_evidence_summary(phase9c_result, partial_section),
        "limitations": limitations,
        "manual_review_required": True,
        "conclusive_authenticity_decision": False,
        "generated_at": _now_iso(),
        "safety": safety_banner(),
    }
    if save_report_path:
        out["saved_report_path"] = save_report_path
    template = load_partial_report_contract_template()
    if template:
        out["partial_fabrication_contract_reference"] = "release/models/partial_fabrication_experimental_p5b/partial_report_contract.json"
    return out


def gradio_user_summary(app_response: dict[str, Any]) -> str:
    pf = app_response.get("partial_fabrication") or {}
    lines = [
        "## Summary",
        "",
        app_response.get("evidence_summary", ""),
        "",
        "### Partial-fabrication (experimental)",
        "",
        f"- Module status: {pf.get('module_status', MODULE_STATUS)}",
        f"- Evidence label: {pf.get('evidence_label', EVIDENCE_LABEL_UNAVAILABLE)}",
        f"- Evidence detected: {pf.get('evidence_detected')}",
        f"- User message: {pf.get('user_facing_message', '')}",
        "",
        "#### Candidate segment",
        "",
    ]
    cand = pf.get("candidate_segment") or {}
    lines.append(f"- Start (sec): {cand.get('start_sec')}")
    lines.append(f"- End (sec): {cand.get('end_sec')}")
    lines.append(f"- Probability: {cand.get('probability')}")
    lines.append(f"- Rank: {cand.get('rank')}")
    lines.append("")
    lines.append("- Manual review recommended: yes")
    lines.append("- Conclusive authenticity decision: no")
    lines.append("")
    lines.append("### Limitations")
    lines.append("")
    for lim in app_response.get("limitations", [])[:12]:
        lines.append(f"- {lim}")
    return "\n".join(lines)


def gradio_segment_table(app_response: dict[str, Any]) -> list[list[Any]]:
    pf = app_response.get("partial_fabrication") or {}
    rows: list[list[Any]] = []
    for seg in pf.get("top_segments") or []:
        rows.append(
            [
                seg.get("rank"),
                seg.get("start_sec"),
                seg.get("end_sec"),
                seg.get("probability"),
                seg.get("manual_review_recommended", True),
            ]
        )
    return rows
