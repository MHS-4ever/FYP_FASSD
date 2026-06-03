"""
Phase 9E: Map Phase 9C inference output to P6 partial_fabrication report contract (release app).
"""

from __future__ import annotations

import html as html_module
import json
import sys
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

_RELEASE_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _RELEASE_ROOT.parent
_PARTIAL_PKG = _RELEASE_ROOT / "models" / "partial_fabrication_experimental_p5b"
_PARTIAL_REDESIGN = _REPO_ROOT / "code" / "phase9" / "partial_redesign"

if str(_PARTIAL_REDESIGN) not in sys.path:
    sys.path.insert(0, str(_PARTIAL_REDESIGN))

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

APP_PHASE = "Phase 9E-P2-P1"

# Dark-theme HTML card palette (explicit contrast for Gradio dark UI)
_CARD_BG = "#1f2937"
_CARD_BORDER_DEFAULT = "#374151"
_TEXT_PRIMARY = "#f9fafb"
_TEXT_SECONDARY = "#d1d5db"
_TEXT_MUTED = "#9ca3af"
_BORDER_DETECTED = "#f97316"
_BORDER_CANDIDATE = "#eab308"
_BORDER_CLEAR = "#22c55e"
_BORDER_UNAVAILABLE = "#94a3b8"
APP_NAME = "Deepfake Audio Detector — Local Demo"
RESEARCH_PROJECT_NAME = "Forensic Acoustic for Synthetic Speech Detection"
APP_SUBTITLE = "AI-generated, replayed, and partially manipulated audio evidence review."
_ELEVATED = frozenset({"moderate", "high", "elevated_partial_fabrication_indicator"})


def release_root() -> Path:
    return _RELEASE_ROOT


def repo_root() -> Path:
    return _REPO_ROOT


def gradio_output_dir(subdir: str = "") -> Path:
    """Writable paths under release/ for Gradio File/Image components (CWD-safe)."""
    base = _RELEASE_ROOT / "gradio_outputs"
    out = base / subdir if subdir else base
    out.mkdir(parents=True, exist_ok=True)
    return out


@lru_cache(maxsize=1)
def load_partial_report_contract() -> dict[str, Any]:
    path = _PARTIAL_PKG / "partial_report_contract.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_partial_module_metadata() -> dict[str, Any]:
    path = _PARTIAL_PKG / "partial_module_metadata.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_partial_validation_summary() -> dict[str, Any]:
    path = _PARTIAL_PKG / "partial_validation_summary.json"
    if not path.is_file():
        return dict(load_partial_module_metadata().get("validation_summary", {}))
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_model_inventory() -> dict[str, Any]:
    path = _RELEASE_ROOT / "models" / "model_inventory.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def safety_banner() -> dict[str, str]:
    return {
        "app_status": "experimental_forensic_demo",
        "partial_module_status": "experimental_manual_review_only",
        "manual_review_required": "true",
        "conclusive_authenticity_decision": "no",
        "operational_deployment_claim": "no",
        "legal_evidence_claim": "no",
        "wording": (
            "Experimental forensic evidence indicators only. "
            "Manual forensic review is recommended. "
            "Conclusive authenticity decision: no."
        ),
    }


def check_phase9c_models_available() -> tuple[bool, str]:
    try:
        from src.model_loader import load_all_active_models  # type: ignore

        load_all_active_models()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


def _html_escape(value: Any) -> str:
    return html_module.escape("" if value is None else str(value))


def _partial_segment_candidate_only(partial_section: dict[str, Any]) -> bool:
    if partial_section.get("segment_candidate_only") is True:
        return True
    return (
        partial_section.get("evidence_detected") is True
        and partial_section.get("file_gate_probability") is None
        and partial_section.get("full_p5b_cascade_available") is not True
    )


def _partial_full_cascade_detected(partial_section: dict[str, Any]) -> bool:
    return (
        partial_section.get("full_p5b_cascade_available") is True
        and partial_section.get("evidence_detected") is True
        and partial_section.get("file_gate_probability") is not None
    )


def _is_fusion_strongly_elevated(response: dict[str, Any]) -> bool:
    risk = str(response.get("forensic_risk_level", "")).lower()
    fusion = str(response.get("fusion_status", "")).lower()
    if risk == "high":
        return True
    return fusion.startswith("suspicious_")


def _has_candidate_segment(partial_section: dict[str, Any]) -> bool:
    cand = partial_section.get("candidate_segment") or {}
    if cand.get("start_sec") is not None and cand.get("end_sec") is not None:
        return True
    return bool(partial_section.get("top_segments"))


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
    """Map Phase 9C partial axis into P6 contract using packaged metadata/thresholds."""
    p6_meta = load_partial_module_metadata()
    p6_contract = load_partial_report_contract()
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
            "Phase 9C release pipeline segment partial axis mapped to P6 contract.",
        ],
    )
    section = contract["partial_fabrication"]
    section["module_status"] = str(p6_meta.get("status", MODULE_STATUS))
    contract_pf = p6_contract.get("partial_fabrication", p6_contract) if p6_contract else {}
    contract_limits = contract_pf.get("limitations", []) if isinstance(contract_pf, dict) else []
    merged = list(
        dict.fromkeys(
            list(p6_meta.get("limitations", []))
            + list(contract_limits)
            + list(section.get("limitations", []))
        )
    )
    section["limitations"] = merged
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

    fgp = section.get("file_gate_probability")
    section["source_mode"] = "phase9c_segment_axis_mapped_to_p6_contract"
    section["file_gate_available"] = fgp is not None
    section["full_p5b_cascade_available"] = False
    section["segment_candidate_only"] = bool(section.get("evidence_detected") is True and fgp is None)

    return section


def build_evidence_summary(phase9c_result: dict[str, Any], partial_section: dict[str, Any]) -> str:
    parts: list[str] = []
    fusion = str(phase9c_result.get("fusion_status", "not_evaluated"))
    parts.append(f"Fusion status (experimental): {fusion}")
    if _partial_segment_candidate_only(partial_section):
        parts.append(
            "Partial-fabrication: segment-level candidate highlighted for optional review "
            "(not strong suspicious evidence in this app path)."
        )
    elif partial_section.get("evidence_detected") is True:
        parts.append("Partial-fabrication experimental evidence: detected (manual review recommended).")
    elif partial_section.get("evidence_detected") is False:
        parts.append(
            "Partial-fabrication experimental evidence: not detected (does not prove authenticity)."
        )
    else:
        parts.append("Partial-fabrication experimental evidence: unavailable.")
    if fusion not in ("not_evaluated", "inconclusive", ""):
        parts.append(FORENSIC_SUMMARY_SAFE + " (conclusive authenticity decision: no).")
    parts.append("Conclusive authenticity decision: no.")
    return " ".join(parts)


def enrich_phase9c_response(
    phase9c_result: dict[str, Any],
    *,
    file_name: str = "",
    return_top_segments: bool = True,
) -> dict[str, Any]:
    """Add P6 partial_fabrication section and app fields to Phase 9C pipeline output."""
    partial_section = build_partial_fabrication_section(
        phase9c_result, return_top_segments=return_top_segments
    )
    meta = load_partial_module_metadata()
    limitations = list(phase9c_result.get("limitations", []))
    limitations.extend(partial_section.get("limitations", []))
    limitations.extend(meta.get("limitations", [])[:8])
    limitations = list(dict.fromkeys(limitations))

    out = dict(phase9c_result)
    out["partial_fabrication"] = partial_section
    out["evidence_summary"] = build_evidence_summary(phase9c_result, partial_section)
    out["manual_review_required"] = True
    out["conclusive_authenticity_decision"] = False
    out["app_phase"] = APP_PHASE
    if file_name:
        out["file_name"] = file_name
    out["request_id"] = str(uuid.uuid4())
    out["generated_at"] = out.get("generated_at") or _now_iso()
    out["safety"] = safety_banner()
    return out


def build_api_analyze_response(
    *,
    file_name: str,
    phase9c_result: dict[str, Any],
    return_top_segments: bool = True,
    save_report_path: str | None = None,
) -> dict[str, Any]:
    enriched = enrich_phase9c_response(
        phase9c_result,
        file_name=file_name,
        return_top_segments=return_top_segments,
    )
    duration = None
    audio_meta = phase9c_result.get("audio_metadata") or {}
    if isinstance(audio_meta, dict):
        duration = audio_meta.get("duration_sec")

    user_summary = build_user_result_summary(enriched)
    evidence_cards = build_evidence_axis_cards(enriched)

    return {
        "request_id": enriched.get("request_id"),
        "phase": APP_PHASE,
        "file_name": file_name,
        "duration_sec": duration,
        "processing_status": "ok" if phase9c_result.get("status") != "error" else "error",
        "case_id": phase9c_result.get("case_id"),
        "phase9c_report": phase9c_result,
        "partial_fabrication": enriched.get("partial_fabrication"),
        "partial_fabrication_evidence_legacy_axis": phase9c_result.get("partial_fabrication_evidence"),
        "evidence_summary": enriched.get("evidence_summary"),
        "limitations": enriched.get("limitations", []),
        "manual_review_required": True,
        "conclusive_authenticity_decision": False,
        "generated_at": enriched.get("generated_at"),
        "safety": safety_banner(),
        "saved_report_path": save_report_path,
        "user_summary": user_summary,
        "evidence_axis_cards": evidence_cards,
        "visual_summary_available": True,
        "report_download_hint": "Use Gradio download buttons or save_report=true for JSON path.",
    }


def gradio_segment_table(response: dict[str, Any]) -> list[list[Any]]:
    return gradio_suspicious_segments_table(response)


def _axis_card_from_evidence(
    axis_name: str,
    evidence: dict[str, Any],
    *,
    partial_section: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if partial_section is not None:
        if (
            partial_section.get("evidence_detected") is None
            or partial_section.get("evidence_label") == EVIDENCE_LABEL_UNAVAILABLE
        ):
            return {
                "axis_name": axis_name,
                "status": "Unavailable",
                "user_text": partial_section.get("user_facing_message") or WORDING_UNAVAILABLE,
                "score_text": "",
                "severity": "unavailable",
            }
        if _partial_full_cascade_detected(partial_section):
            max_seg = partial_section.get("max_segment_probability")
            score_text = (
                f"Max segment score: {max_seg:.3f}" if isinstance(max_seg, (int, float)) else ""
            )
            return {
                "axis_name": axis_name,
                "status": "Detected",
                "user_text": partial_section.get("user_facing_message") or WORDING_DETECTED,
                "score_text": score_text,
                "severity": "review",
            }
        if _partial_segment_candidate_only(partial_section):
            max_seg = partial_section.get("max_segment_probability")
            score_text = (
                f"Candidate segment score: {max_seg:.3f}" if isinstance(max_seg, (int, float)) else ""
            )
            return {
                "axis_name": axis_name,
                "status": "Review candidate",
                "user_text": (
                    "A segment-level candidate was highlighted by the experimental partial module. "
                    "This alone is not enough to mark the full audio as suspicious."
                ),
                "score_text": score_text,
                "severity": "candidate",
            }
        detected = partial_section.get("evidence_detected")
        if detected is False:
            status, severity = "Not detected", "clear"
            user_text = partial_section.get("user_facing_message") or WORDING_NOT_DETECTED
        else:
            status, severity = "Unavailable", "unavailable"
            user_text = partial_section.get("user_facing_message") or WORDING_UNAVAILABLE
        max_seg = partial_section.get("max_segment_probability")
        score_text = f"Max segment score: {max_seg:.3f}" if isinstance(max_seg, (int, float)) else ""
        return {
            "axis_name": axis_name,
            "status": status,
            "user_text": user_text,
            "score_text": score_text,
            "severity": severity,
        }

    if not evidence.get("prediction_success"):
        return {
            "axis_name": axis_name,
            "status": "Unavailable",
            "user_text": "This evidence axis was not available in the current analysis output.",
            "score_text": "",
            "severity": "unavailable",
        }

    label = str(evidence.get("evidence_label") or evidence.get("label", "")).lower()
    strength = str(evidence.get("evidence_strength", "")).lower()
    prob = evidence.get("probability")
    score_text = f"Evidence score: {prob:.3f}" if isinstance(prob, (int, float)) else ""

    elevated = (
        "elevated" in label
        or strength in _ELEVATED
        or label in ("elevated_indicator", "suspicious_mixer_channel_experimental")
    )
    if elevated:
        status, severity = "Detected", "review"
        user_text = (
            f"Experimental indicators were observed on this axis. "
            f"This is not conclusive proof; manual review is recommended."
        )
    else:
        status, severity = "Not detected", "clear"
        user_text = (
            f"No strong experimental indicators were highlighted on this axis. "
            f"This does not prove authenticity."
        )
    return {
        "axis_name": axis_name,
        "status": status,
        "user_text": user_text,
        "score_text": score_text,
        "severity": severity,
    }


def build_evidence_axis_cards(response: dict[str, Any]) -> list[dict[str, Any]]:
    pf = response.get("partial_fabrication") or {}
    return [
        _axis_card_from_evidence("AI-origin evidence", response.get("origin_evidence") or {}),
        _axis_card_from_evidence("Replay evidence", response.get("replay_evidence") or {}),
        _axis_card_from_evidence("Channel/mixer evidence", response.get("mixer_channel_evidence") or {}),
        _axis_card_from_evidence(
            "Partial-fabrication evidence",
            {},
            partial_section=pf,
        ),
    ]


def _highlight_segment_text(
    response: dict[str, Any], *, candidate_only: bool = False
) -> tuple[str, float | None, float | None]:
    from src.app_visualization import format_time_mmss

    pf = response.get("partial_fabrication") or {}
    cand = pf.get("candidate_segment") or {}
    start = cand.get("start_sec")
    end = cand.get("end_sec")
    if start is not None and end is not None:
        prefix = (
            "Candidate segment available for review"
            if candidate_only
            else "Highlighted segment"
        )
        return (
            f"{prefix}: {format_time_mmss(start)} – {format_time_mmss(end)}",
            float(start),
            float(end),
        )
    if candidate_only and _has_candidate_segment(pf):
        return "Candidate segment available for review: see table below", None, None
    if not candidate_only and any(
        c.get("status") == "Detected"
        for c in build_evidence_axis_cards(response)
        if c.get("axis_name") != "Partial-fabrication evidence"
    ):
        return "Highlighted segment: see segments table", None, None
    return "Highlighted segment: none", None, None


def build_user_result_summary(response: dict[str, Any]) -> dict[str, Any]:
    """Concise user-facing result lines for dashboard and PDF."""
    status = str(response.get("status", ""))
    processing_error = (
        status == "error"
        or response.get("processing_status") == "error"
        or bool(response.get("error_message"))
    )

    pf = response.get("partial_fabrication") or {}
    cards = build_evidence_axis_cards(response)
    segment_candidate_only = _partial_segment_candidate_only(pf)
    strong_evidence_detected = any(
        c.get("status") == "Detected"
        for c in cards
        if c.get("axis_name") != "Partial-fabrication evidence"
    ) or _partial_full_cascade_detected(pf)
    if _is_fusion_strongly_elevated(response):
        strong_evidence_detected = True

    base_unavailable = {
        "status_title": "Analysis incomplete",
        "finding_title": "Analysis unavailable",
        "highlighted_segment_text": "Highlighted segment: unavailable",
        "recommendation_text": "Try another supported file or perform manual review",
        "plain_language_explanation": (
            "The system could not produce a reliable analysis output."
        ),
        "severity_level": "unavailable",
        "evidence_detected_any": False,
        "strong_evidence_detected": False,
        "segment_candidate_only": False,
    }

    if processing_error:
        return base_unavailable

    if strong_evidence_detected:
        highlight_text, _, _ = _highlight_segment_text(response, candidate_only=False)
        return {
            "status_title": "Analysis completed",
            "finding_title": "Suspicious audio indicators found",
            "highlighted_segment_text": highlight_text,
            "recommendation_text": "Manual review recommended",
            "plain_language_explanation": (
                "A section of the audio was highlighted for closer review."
            ),
            "severity_level": "review",
            "evidence_detected_any": True,
            "strong_evidence_detected": True,
            "segment_candidate_only": False,
        }

    if segment_candidate_only and _has_candidate_segment(pf):
        highlight_text, _, _ = _highlight_segment_text(response, candidate_only=True)
        return {
            "status_title": "Analysis completed",
            "finding_title": "No strong manipulation indicators detected",
            "highlighted_segment_text": highlight_text,
            "recommendation_text": "Manual review optional for the highlighted segment",
            "plain_language_explanation": (
                "A segment-level candidate was highlighted, but this alone is not enough "
                "to flag the full audio."
            ),
            "severity_level": "clear_candidate",
            "evidence_detected_any": False,
            "strong_evidence_detected": False,
            "segment_candidate_only": True,
        }

    highlight_text, _, _ = _highlight_segment_text(response, candidate_only=False)
    return {
        "status_title": "Analysis completed",
        "finding_title": "No strong manipulation indicators detected",
        "highlighted_segment_text": highlight_text,
        "recommendation_text": "Manual review may still be needed for sensitive cases",
        "plain_language_explanation": (
            "The system did not highlight a strong suspicious region."
        ),
        "severity_level": "clear",
        "evidence_detected_any": False,
        "strong_evidence_detected": False,
        "segment_candidate_only": False,
    }


def gradio_segments_table_title(response: dict[str, Any]) -> str:
    summary = build_user_result_summary(response)
    if summary.get("strong_evidence_detected") or summary.get("severity_level") == "review":
        return "Suspicious segments for review"
    return "Candidate segments for review"


def gradio_segments_section_heading(response: dict[str, Any]) -> str:
    return f"### {gradio_segments_table_title(response)}"


def _json_output_dir() -> Path:
    out = _REPO_ROOT / "reports" / "phase9" / "app" / "sample_outputs" / "json"
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_json_report(app_response: dict[str, Any], output_dir: str | Path | None = None) -> str:
    out_dir = Path(output_dir) if output_dir else _json_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    case = app_response.get("case_id") or app_response.get("request_id") or "report"
    safe_case = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(case))[:48]
    path = out_dir / f"{safe_case}_analysis.json"
    path.write_text(json.dumps(app_response, indent=2, default=str), encoding="utf-8")
    return str(path)


def _severity_border(severity: str) -> str:
    return {
        "review": _BORDER_DETECTED,
        "candidate": _BORDER_CANDIDATE,
        "clear_candidate": _BORDER_CANDIDATE,
        "unavailable": _BORDER_UNAVAILABLE,
        "clear": _BORDER_CLEAR,
        "warning": _BORDER_CANDIDATE,
    }.get(severity, _BORDER_CLEAR)


def _card_status_border(status: str) -> str:
    return {
        "Detected": _BORDER_DETECTED,
        "Review candidate": _BORDER_CANDIDATE,
        "Not detected": _BORDER_CLEAR,
        "Unavailable": _BORDER_UNAVAILABLE,
    }.get(status, _CARD_BORDER_DEFAULT)


def render_main_result_card(summary: dict[str, Any]) -> str:
    severity = str(summary.get("severity_level", "clear"))
    border = _severity_border(severity)
    return f"""
<div style="border-left:4px solid {border};padding:12px 16px;background:{_CARD_BG};border-radius:8px;color:{_TEXT_PRIMARY};">
  <div style="font-size:0.85rem;color:{_TEXT_MUTED};">{_html_escape(summary.get('status_title',''))}</div>
  <div style="font-size:1.25rem;font-weight:600;margin:6px 0;color:{_TEXT_PRIMARY};">{_html_escape(summary.get('finding_title',''))}</div>
  <div style="margin:4px 0;color:{_TEXT_SECONDARY};">{_html_escape(summary.get('highlighted_segment_text',''))}</div>
  <div style="margin:4px 0;color:{_TEXT_SECONDARY};">{_html_escape(summary.get('recommendation_text',''))}</div>
  <div style="font-size:0.9rem;color:{_TEXT_MUTED};margin-top:8px;">{_html_escape(summary.get('plain_language_explanation',''))}</div>
</div>
"""


def render_audio_overview(response: dict[str, Any]) -> str:
    audio_meta = response.get("audio_metadata") or {}
    duration = audio_meta.get("duration_sec")
    dur_txt = f"{float(duration):.1f} s" if duration is not None else "—"
    manual = "yes" if response.get("manual_review_required", True) else "no"
    case_id = response.get("case_id") or "—"
    fname = response.get("file_name") or "—"
    proc = "ok" if response.get("status") != "error" else "error"
    cell = (
        f'<div style="padding:10px;background:{_CARD_BG};border:1px solid {_CARD_BORDER_DEFAULT};'
        f'border-radius:6px;color:{_TEXT_PRIMARY};"><b style="color:{_TEXT_SECONDARY};">%s</b><br>%s</div>'
    )
    return f"""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;">
  {cell % ("File", _html_escape(fname))}
  {cell % ("Duration", _html_escape(dur_txt))}
  {cell % ("Analysis status", _html_escape(proc))}
  {cell % ("Manual review", _html_escape(manual))}
  {cell % ("Case ID", _html_escape(case_id))}
</div>
"""


def render_evidence_cards_html(cards: list[dict[str, Any]]) -> str:
    parts = [
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">'
    ]
    for card in cards:
        st = str(card.get("status", "Unavailable"))
        border = _card_status_border(st)
        score = card.get("score_text") or ""
        score_html = (
            f'<div style="font-size:0.8rem;color:{_TEXT_MUTED};">{_html_escape(score)}</div>'
            if score
            else ""
        )
        parts.append(
            f'<div style="padding:12px;background:{_CARD_BG};border:2px solid {border};'
            f'border-radius:8px;color:{_TEXT_PRIMARY};">'
            f'<div style="font-weight:600;color:{_TEXT_PRIMARY};">{_html_escape(card.get("axis_name",""))}</div>'
            f'<div style="margin:6px 0;font-weight:500;color:{_TEXT_SECONDARY};">{_html_escape(st)}</div>'
            f'<div style="font-size:0.88rem;color:{_TEXT_SECONDARY};">{_html_escape(card.get("user_text",""))}</div>'
            f"{score_html}</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def render_technical_details(response: dict[str, Any]) -> str:
    meta = load_partial_module_metadata()
    pf = response.get("partial_fabrication") or {}
    lines = [
        "### Technical details",
        "",
        f"- App phase: {response.get('app_phase', APP_PHASE)}",
        f"- Partial source mode: {pf.get('source_mode', 'phase9c_segment_axis_mapped_to_p6_contract')}",
        f"- Partial module status: {pf.get('module_status', meta.get('status', MODULE_STATUS))}",
        f"- File gate available in this app path: {pf.get('file_gate_available', False)}",
        f"- Full P5B cascade available in this app path: {pf.get('full_p5b_cascade_available', False)}",
        f"- Segment candidate only: {pf.get('segment_candidate_only', False)}",
        f"- Fusion status: {response.get('fusion_status', 'not_evaluated')}",
        f"- Forensic risk level: {response.get('forensic_risk_level', 'inconclusive')}",
        "",
        "The current release app maps the Phase 9C segment partial axis into the P6 report "
        "contract. The full P5B file-gate cascade is not used in this app path yet.",
        "",
        "**Thresholds (experimental package)**",
        "",
    ]
    th = pf.get("thresholds") or meta.get("thresholds", {})
    for k, v in th.items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "**Limitations (sample)**", ""])
    for lim in (response.get("limitations") or [])[:8]:
        lines.append(f"- {lim}")
    return "\n".join(lines)


def gradio_suspicious_segments_table(response: dict[str, Any]) -> list[list[Any]]:
    from src.app_visualization import format_time_mmss

    pf = response.get("partial_fabrication") or {}
    rows: list[list[Any]] = []
    for seg in pf.get("top_segments") or []:
        start = seg.get("start_sec")
        end = seg.get("end_sec")
        prob = seg.get("probability")
        prob_txt = f"{prob:.3f}" if isinstance(prob, (int, float)) else "—"
        rows.append(
            [
                seg.get("rank"),
                f"{format_time_mmss(start)} – {format_time_mmss(end)}",
                prob_txt,
                "Recommended" if seg.get("manual_review_recommended", True) else "Optional",
            ]
        )
    return rows


def gradio_user_summary(response: dict[str, Any]) -> str:
    """Legacy wrapper — prefer render_main_result_card(build_user_result_summary(...))."""
    summary = build_user_result_summary(response)
    return render_main_result_card(summary)
