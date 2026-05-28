"""
Phase 8F report text generator with forensic-safe wording.
"""

from __future__ import annotations

from typing import Any


def _safe_str(value: Any, default: str = "not available") -> str:
    txt = str(value).strip() if value is not None else ""
    if txt.lower() in {"nan", "none"}:
        return default
    return txt if txt else default


def generate_file_summary(row: dict[str, Any]) -> str:
    status = _safe_str(row.get("experimental_fusion_status"), "inconclusive_manual_review_experimental")
    risk = _safe_str(row.get("forensic_risk_level"), "inconclusive")
    return (
        f"Experimental multi-axis fusion status is `{status}` with risk level `{risk}`. "
        "This is an evidence indicator and does not by itself prove fabrication."
    )


def generate_axis_explanation(row: dict[str, Any]) -> str:
    origin = _safe_str(row.get("origin_evidence_strength"), "not_evaluated")
    replay = _safe_str(row.get("replay_evidence_strength"), "not_evaluated")
    mixer = _safe_str(row.get("mixer_evidence_strength"), "not_evaluated")
    partial = _safe_str(row.get("partial_evidence_strength"), "not_evaluated")

    def _axis_line(name: str, strength: str, suffix: str) -> str:
        if strength == "not_evaluated":
            return (
                f"- {name} evidence strength: `not_evaluated`. "
                "This evidence axis was not evaluated in the current retrospective fusion record. "
                "No conclusion is drawn from this missing axis."
            )
        return f"- {name} evidence strength: `{strength}` ({suffix})."

    lines = [
        _axis_line("Origin", origin, "experimental model output"),
        _axis_line("Replay", replay, "replay does not imply AI-generated origin"),
        _axis_line("Mixer/channel", mixer, "mixer indicators do not imply AI-generated origin"),
        _axis_line("Partial fabrication", partial, "timestamp/segment based candidate evidence"),
    ]
    return "\n".join(lines)


def generate_segment_summary(row: dict[str, Any], segment_rows: list[dict[str, Any]] | None = None) -> str:
    if not segment_rows:
        ranges = _safe_str(row.get("partial_top_segment_ranges"), "")
        if not ranges:
            return "No segment candidate ranges are available for this file."
        return f"Candidate segment ranges from fusion summary: `{ranges}`."
    top = sorted(
        segment_rows,
        key=lambda r: float(str(r.get("partial_segment_probability", "0") or "0")),
        reverse=True,
    )[:3]
    snippets = []
    for rec in top:
        snippets.append(
            f"{_safe_str(rec.get('segment_id'),'segment')} "
            f"[{_safe_str(rec.get('start_sec'),'?')}, {_safe_str(rec.get('end_sec'),'?')}] "
            f"p={_safe_str(rec.get('partial_segment_probability'),'')}"
        )
    if not snippets:
        return "No segment candidate ranges are available for this file."
    return "Top candidate segments: " + "; ".join(snippets) + "."


def generate_limitations(row: dict[str, Any]) -> str:
    return (
        "These outputs are experimental model outputs across separate evidence axes. "
        "They are consistent with candidate forensic patterns but do not by themselves prove or disprove fabrication. "
        "Manual review is recommended when evidence is borderline, conflicting, or incomplete."
    )


def generate_safe_report(row: dict[str, Any], segment_rows: list[dict[str, Any]] | None = None) -> str:
    status = str(row.get("experimental_fusion_status", "")).strip().lower()
    manual = str(row.get("manual_review_required", "false")).lower() == "true"
    if status == "inconclusive_manual_review_experimental":
        review_stmt = (
            "Manual review is recommended because the evidence is incomplete, borderline, or inconclusive."
        )
    else:
        review_stmt = "manual review recommended." if manual else "manual review may still be helpful."
    parts = [
        generate_file_summary(row),
        generate_axis_explanation(row),
        generate_segment_summary(row, segment_rows),
        generate_limitations(row),
        f"Final note: {review_stmt}",
    ]
    return "\n\n".join(parts)
