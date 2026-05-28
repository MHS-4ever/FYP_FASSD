"""
Phase 8F fusion rules for multi-axis experimental forensic synthesis.
"""

from __future__ import annotations

from typing import Any

ALLOWED_EVIDENCE_STRENGTH = {
    "not_evaluated",
    "low",
    "borderline",
    "moderate",
    "high",
    "unknown",
}

ALLOWED_EXPERIMENTAL_STATUSES = {
    "accept_human_clean_experimental",
    "suspicious_origin_experimental",
    "suspicious_replay_experimental",
    "suspicious_mixer_channel_experimental",
    "suspicious_partial_fabrication_experimental",
    "suspicious_mixed_evidence_experimental",
    "inconclusive_manual_review_experimental",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "inconclusive"}


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        txt = str(value).strip()
        if txt == "":
            return None
        return float(txt)
    except Exception:
        return None


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def classify_evidence_strength(probability: Any, threshold: Any, margin: float = 0.10) -> str:
    prob = _to_float(probability)
    th = _to_float(threshold)
    if prob is None:
        return "not_evaluated"
    if th is None:
        return "unknown"
    if prob < max(0.0, th - margin):
        return "low"
    if abs(prob - th) <= margin:
        return "borderline"
    if prob >= th + (2.0 * margin):
        return "high"
    return "moderate"


def _evidence_label_from_prob(probability: Any, threshold: Any, positive_label: str) -> str:
    prob = _to_float(probability)
    th = _to_float(threshold)
    if prob is None or th is None:
        return "not_evaluated"
    return positive_label if prob >= th else "low_indicator"


def _axis_not_evaluated(model_available: Any, probability: Any) -> bool:
    return (not _to_bool(model_available)) or (_to_float(probability) is None)


def fuse_origin_evidence(row: dict[str, Any]) -> dict[str, Any]:
    if _axis_not_evaluated(row.get("origin_model_available"), row.get("origin_ai_probability")):
        return {
            "origin_evidence_strength": "not_evaluated",
            "origin_evidence_label": "not_evaluated",
        }
    strength = classify_evidence_strength(
        row.get("origin_ai_probability"),
        row.get("origin_threshold_candidate"),
    )
    label = _evidence_label_from_prob(
        row.get("origin_ai_probability"),
        row.get("origin_threshold_candidate"),
        "elevated_ai_origin_indicator",
    )
    return {
        "origin_evidence_strength": strength,
        "origin_evidence_label": label,
    }


def fuse_replay_evidence(row: dict[str, Any]) -> dict[str, Any]:
    if _axis_not_evaluated(row.get("replay_model_available"), row.get("replay_probability")):
        return {
            "replay_evidence_strength": "not_evaluated",
            "replay_evidence_label": "not_evaluated",
        }
    strength = classify_evidence_strength(
        row.get("replay_probability"),
        row.get("replay_threshold_candidate"),
    )
    label = _evidence_label_from_prob(
        row.get("replay_probability"),
        row.get("replay_threshold_candidate"),
        "elevated_replay_rerecording_indicator",
    )
    return {
        "replay_evidence_strength": strength,
        "replay_evidence_label": label,
    }


def fuse_mixer_evidence(row: dict[str, Any]) -> dict[str, Any]:
    if _axis_not_evaluated(row.get("mixer_model_available"), row.get("mixer_probability")):
        return {
            "mixer_evidence_strength": "not_evaluated",
            "mixer_evidence_label": "not_evaluated",
        }
    strength = classify_evidence_strength(
        row.get("mixer_probability"),
        row.get("mixer_threshold_candidate"),
    )
    label = _evidence_label_from_prob(
        row.get("mixer_probability"),
        row.get("mixer_threshold_candidate"),
        "elevated_mixer_channel_indicator",
    )
    return {
        "mixer_evidence_strength": strength,
        "mixer_evidence_label": label,
    }


def fuse_partial_evidence(row: dict[str, Any]) -> dict[str, Any]:
    if _axis_not_evaluated(row.get("partial_model_available"), row.get("partial_max_segment_probability")):
        return {
            "partial_evidence_strength": "not_evaluated",
            "partial_evidence_label": "not_evaluated",
        }
    strength = classify_evidence_strength(
        row.get("partial_max_segment_probability"),
        row.get("partial_segment_threshold_candidate"),
    )
    label = _evidence_label_from_prob(
        row.get("partial_max_segment_probability"),
        row.get("partial_segment_threshold_candidate"),
        "elevated_partial_fabrication_indicator",
    )
    return {
        "partial_evidence_strength": strength,
        "partial_evidence_label": label,
    }


def build_manual_review_reason(row: dict[str, Any]) -> str:
    reasons: list[str] = []
    strengths = {
        "origin": row.get("origin_evidence_strength", "unknown"),
        "replay": row.get("replay_evidence_strength", "unknown"),
        "mixer": row.get("mixer_evidence_strength", "unknown"),
        "partial": row.get("partial_evidence_strength", "unknown"),
    }
    for axis, strength in strengths.items():
        if strength == "borderline":
            reasons.append(f"{axis}_borderline")
        if axis == "origin" and strength in {"moderate", "high"}:
            reasons.append("origin_ai_evidence_review")
        if axis == "replay" and strength in {"moderate", "high"}:
            reasons.append("replay_rerecording_evidence_review")
        if axis == "mixer" and strength in {"moderate", "high"}:
            reasons.append("mixer_channel_evidence_review")
    if strengths["partial"] in {"moderate", "high"}:
        reasons.append("partial_segment_evidence_review")
    if row.get("experimental_fusion_status") == "suspicious_mixed_evidence_experimental":
        reasons.append("multi_axis_evidence_review")
    if row.get("experimental_fusion_status") == "inconclusive_manual_review_experimental":
        reasons.append("insufficient_evidence_review")
    if not reasons:
        return "none"
    return ";".join(sorted(set(reasons)))


def build_fusion_trace(row: dict[str, Any]) -> str:
    return (
        f"origin={row.get('origin_evidence_strength','unknown')}"
        f"|replay={row.get('replay_evidence_strength','unknown')}"
        f"|mixer={row.get('mixer_evidence_strength','unknown')}"
        f"|partial={row.get('partial_evidence_strength','unknown')}"
        f"|status={row.get('experimental_fusion_status','unknown')}"
        f"|risk={row.get('forensic_risk_level','inconclusive')}"
    )


def apply_multi_axis_fusion(row: dict[str, Any]) -> dict[str, Any]:
    origin_strength = row.get("origin_evidence_strength", "not_evaluated")
    replay_strength = row.get("replay_evidence_strength", "not_evaluated")
    mixer_strength = row.get("mixer_evidence_strength", "not_evaluated")
    partial_strength = row.get("partial_evidence_strength", "not_evaluated")

    elevated_axes = {
        "origin": origin_strength in {"high", "moderate"},
        "replay": replay_strength in {"high", "moderate"},
        "mixer": mixer_strength in {"high", "moderate"},
        "partial": partial_strength in {"high", "moderate"},
    }
    elevated_count = sum(1 for v in elevated_axes.values() if v)
    borderline_present = any(
        x == "borderline" for x in [origin_strength, replay_strength, mixer_strength, partial_strength]
    )
    evaluated_count = sum(
        1
        for x in [origin_strength, replay_strength, mixer_strength, partial_strength]
        if x not in {"not_evaluated", "unknown"}
    )

    status = "inconclusive_manual_review_experimental"
    risk = "inconclusive"
    manual_review = True

    if evaluated_count == 0:
        status = "inconclusive_manual_review_experimental"
        risk = "inconclusive"
        manual_review = True
    elif elevated_count == 0 and not borderline_present and origin_strength == "low":
        if replay_strength in {"low", "not_evaluated"} and mixer_strength in {"low", "not_evaluated"} and partial_strength in {"low", "not_evaluated"}:
            status = "accept_human_clean_experimental"
            risk = "low"
            manual_review = False
    elif elevated_axes["partial"] and elevated_count > 1:
        status = "suspicious_mixed_evidence_experimental"
        risk = "high"
        manual_review = True
    elif elevated_axes["partial"]:
        status = "suspicious_partial_fabrication_experimental"
        risk = "high" if partial_strength == "high" else "medium"
        manual_review = True
    elif elevated_count > 1:
        status = "suspicious_mixed_evidence_experimental"
        risk = "high"
        manual_review = True
    elif elevated_axes["replay"]:
        status = "suspicious_replay_experimental"
        risk = "high" if replay_strength == "high" else "medium"
        manual_review = True
    elif elevated_axes["mixer"]:
        status = "suspicious_mixer_channel_experimental"
        risk = "high" if mixer_strength == "high" else "medium"
        manual_review = True
    elif elevated_axes["origin"]:
        status = "suspicious_origin_experimental"
        risk = "high" if origin_strength == "high" else "medium"
        manual_review = True
    elif evaluated_count > 0 and not borderline_present:
        status = "inconclusive_manual_review_experimental"
        risk = "inconclusive"
        manual_review = True

    if borderline_present:
        manual_review = True
        if elevated_count == 0:
            risk = "inconclusive"
            status = "inconclusive_manual_review_experimental"

    provisional = {
        "experimental_fusion_status": status,
        "forensic_risk_level": risk,
        "manual_review_required": "true" if manual_review else "false",
    }
    reason = build_manual_review_reason({**row, **provisional})
    has_elevated = elevated_count > 0
    is_suspicious = status.startswith("suspicious_")
    must_review = (
        status == "inconclusive_manual_review_experimental"
        or risk == "inconclusive"
        or "insufficient_evidence_review" in reason
        or borderline_present
        or elevated_count > 1
        or partial_strength in {"moderate", "high"}
        or is_suspicious
    )
    allow_clean_auto_false = (
        status == "accept_human_clean_experimental"
        and risk == "low"
        and (not has_elevated)
        and (not borderline_present)
        and reason == "none"
    )
    final_manual = True if must_review else (False if allow_clean_auto_false else bool(manual_review))
    out = {
        "experimental_fusion_status": status,
        "forensic_risk_level": risk,
        "manual_review_required": "true" if final_manual else "false",
        "manual_review_reason": reason,
    }
    out["fusion_trace"] = build_fusion_trace({**row, **out})
    return out
