"""Live fusion rules adapted from Phase 8F (axes remain separate)."""

from __future__ import annotations

import sys
from typing import Any

from .utils import repo_root

ELEVATED_STRENGTHS = frozenset({"moderate", "high"})

PARTIAL_FUSION_FIELDS = (
    "partial_fusion_eligible",
    "partial_evidence_strength_for_fusion",
    "partial_fusion_block_reason",
    "partial_arbitration_note",
    "broad_activation_warning",
    "localization_confidence_note",
)


def _import_phase8f():
    root = repo_root()
    fusion_dir = root / "code" / "phase8" / "fusion"
    if str(fusion_dir) not in sys.path:
        sys.path.insert(0, str(fusion_dir))
    try:
        import phase8f_fusion_rules as p8f  # type: ignore

        return p8f
    except Exception as exc:
        raise RuntimeError(f"Phase 8F fusion rules import failed: {exc}") from exc


def _axis_row(
    evidence: dict[str, Any],
    prob_key: str,
    th_key: str,
    available_key: str,
) -> dict[str, Any]:
    evaluated = bool(evidence.get("prediction_success", False))
    return {
        prob_key: evidence.get("probability"),
        th_key: evidence.get("threshold_candidate"),
        available_key: evaluated,
    }


def _classify_axis_strength(p8f: Any, evidence: dict[str, Any]) -> str:
    if not evidence.get("prediction_success"):
        return "not_evaluated"
    strength = evidence.get("evidence_strength")
    if strength and strength not in {"pending_fusion", "not_evaluated"}:
        return str(strength)
    return p8f.classify_evidence_strength(
        evidence.get("probability"),
        evidence.get("threshold_candidate"),
    )


def ensure_partial_arbitration_fields(partial_fabrication_evidence: dict[str, Any]) -> dict[str, Any]:
    """Ensure P3 partial arbitration fields exist (set in inference_pipeline when possible)."""
    out = dict(partial_fabrication_evidence)
    if out.get("partial_fusion_eligible") is None:
        out["partial_fusion_eligible"] = False
    if not out.get("partial_evidence_strength_for_fusion"):
        out["partial_evidence_strength_for_fusion"] = "not_evaluated"
    if not out.get("partial_fusion_block_reason"):
        out["partial_fusion_block_reason"] = "prediction_failed" if not out.get("prediction_success") else "none"
    if out.get("partial_arbitration_note") is None:
        out["partial_arbitration_note"] = ""
    if out.get("broad_activation_warning") is None:
        hsf = float(out.get("high_segment_fraction", 0.0) or 0.0)
        out["broad_activation_warning"] = hsf >= 0.60
    if not out.get("localization_confidence_note"):
        out["localization_confidence_note"] = "Partial localization not assessed."
    return out


def apply_partial_arbitration(
    partial_fabrication_evidence: dict[str, Any],
    origin_evidence: dict[str, Any],
    replay_evidence: dict[str, Any],
    mixer_channel_evidence: dict[str, Any],
    p8f: Any | None = None,
) -> dict[str, Any]:
    """Preserve inference-time arbitration; apply replay/mixer block only if not already finalized."""
    _ = origin_evidence
    p8f = p8f or _import_phase8f()
    out = ensure_partial_arbitration_fields(partial_fabrication_evidence)
    if out.get("partial_fusion_block_reason") in {
        "blocked_by_replay_or_mixer_context",
        "coexists_with_replay_or_mixer_context",
    }:
        return out

    replay_strength = _classify_axis_strength(p8f, replay_evidence)
    mixer_strength = _classify_axis_strength(p8f, mixer_channel_evidence)
    if replay_strength not in ELEVATED_STRENGTHS and mixer_strength not in ELEVATED_STRENGTHS:
        return out

    gate = str(out.get("partial_localization_gate", ""))
    hsf = float(out.get("high_segment_fraction", 1.0) or 1.0)
    topk_mr = float(out.get("topk_minus_rest_probability", 0.0) or 0.0)
    localized = gate == "localized_pattern_supported" and hsf <= 0.35 and topk_mr >= 0.20

    if localized:
        coexist_note = (
            "Localized partial segment pattern coexists with replay/mixer/channel context; "
            "segment candidates remain visible for review."
        )
        if out.get("partial_fusion_eligible") is not True:
            out["partial_fusion_eligible"] = True
        strength = str(out.get("partial_evidence_strength_for_fusion", "not_evaluated"))
        if strength in {"", "not_evaluated", "low"}:
            out["partial_evidence_strength_for_fusion"] = "borderline"
        out["partial_fusion_block_reason"] = "coexists_with_replay_or_mixer_context"
        out["partial_arbitration_note"] = coexist_note
        return out

    strict_ok = localized and topk_mr >= 0.35 and float(out.get("probability_std", 0.0) or 0.0) >= 0.25
    if strict_ok:
        return out

    arbitration_note = (
        "Partial segment activation may be explained by replay/mixer/channel effects; "
        "not used as elevated partial evidence in fusion."
    )
    out["partial_fusion_eligible"] = False
    out["partial_evidence_strength_for_fusion"] = "borderline"
    out["partial_fusion_block_reason"] = "blocked_by_replay_or_mixer_context"
    out["partial_arbitration_note"] = arbitration_note
    return out


def _partial_row_for_fusion(
    partial_fabrication_evidence: dict[str, Any],
    p8f: Any,
) -> dict[str, Any]:
    """Partial counts as elevated only when fusion-eligible with fusion strength moderate/high."""
    eligible = partial_fabrication_evidence.get("partial_fusion_eligible") is True
    strength = str(partial_fabrication_evidence.get("partial_evidence_strength_for_fusion", "not_evaluated"))
    label = str(partial_fabrication_evidence.get("evidence_label", "not_evaluated"))

    if (
        not eligible
        or not partial_fabrication_evidence.get("prediction_success")
        or strength not in ELEVATED_STRENGTHS
    ):
        return {
            "partial_max_segment_probability": 0.0,
            "partial_model_available": bool(partial_fabrication_evidence.get("prediction_success")),
            "partial_evidence_strength": strength if strength != "pending_fusion" else "borderline",
            "partial_evidence_label": label,
        }

    gated_prob = float(partial_fabrication_evidence.get("gated_partial_probability", 0.0) or 0.0)
    th = partial_fabrication_evidence.get("threshold_candidate")
    fused_label = p8f._evidence_label_from_prob(gated_prob, th, "elevated_partial_fabrication_indicator")
    return {
        "partial_max_segment_probability": gated_prob,
        "partial_model_available": True,
        "partial_evidence_strength": strength,
        "partial_evidence_label": fused_label,
    }


def _resolve_live_fusion_status(
    row: dict[str, Any],
    partial_fabrication_evidence: dict[str, Any],
) -> str:
    """Live fusion rule E: partial elevated only when partial_fusion_eligible."""
    origin_s = str(row.get("origin_evidence_strength", "not_evaluated"))
    replay_s = str(row.get("replay_evidence_strength", "not_evaluated"))
    mixer_s = str(row.get("mixer_evidence_strength", "not_evaluated"))
    partial_elevated = (
        partial_fabrication_evidence.get("partial_fusion_eligible") is True
        and str(partial_fabrication_evidence.get("partial_evidence_strength_for_fusion", "")) in ELEVATED_STRENGTHS
    )
    file_elevated = {
        "origin": origin_s in ELEVATED_STRENGTHS,
        "replay": replay_s in ELEVATED_STRENGTHS,
        "mixer": mixer_s in ELEVATED_STRENGTHS,
        "partial": partial_elevated,
    }
    elevated_count = sum(1 for v in file_elevated.values() if v)

    if elevated_count >= 2:
        return "suspicious_mixed_evidence_experimental"
    if file_elevated["partial"]:
        return "suspicious_partial_fabrication_experimental"
    if file_elevated["replay"]:
        return "suspicious_replay_experimental"
    if file_elevated["mixer"]:
        return "suspicious_mixer_channel_experimental"
    if file_elevated["origin"]:
        return "suspicious_origin_experimental"
    return str(row.get("experimental_fusion_status", "inconclusive_manual_review_experimental"))


def _risk_for_status(status: str, row: dict[str, Any]) -> str:
    if status == "accept_human_clean_experimental":
        return "low"
    if status.startswith("suspicious_"):
        if status == "suspicious_mixed_evidence_experimental":
            return "high"
        partial_s = str(row.get("partial_evidence_strength", ""))
        if partial_s == "high":
            return "high"
        return "medium"
    return "inconclusive"


def fuse_live_evidence(
    origin_evidence: dict[str, Any],
    replay_evidence: dict[str, Any],
    mixer_channel_evidence: dict[str, Any],
    partial_fabrication_evidence: dict[str, Any],
    segment_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    p8f = _import_phase8f()
    partial_fabrication_evidence = apply_partial_arbitration(
        partial_fabrication_evidence,
        origin_evidence,
        replay_evidence,
        mixer_channel_evidence,
        p8f,
    )

    row: dict[str, Any] = {}
    row.update(_axis_row(origin_evidence, "origin_ai_probability", "origin_threshold_candidate", "origin_model_available"))
    row.update(_axis_row(replay_evidence, "replay_probability", "replay_threshold_candidate", "replay_model_available"))
    row.update(
        _axis_row(
            mixer_channel_evidence,
            "mixer_probability",
            "mixer_threshold_candidate",
            "mixer_model_available",
        )
    )

    partial_partial = _partial_row_for_fusion(partial_fabrication_evidence, p8f)
    row.update(
        {
            "partial_max_segment_probability": partial_partial["partial_max_segment_probability"],
            "partial_segment_threshold_candidate": partial_fabrication_evidence.get("threshold_candidate"),
            "partial_model_available": partial_partial["partial_model_available"],
        }
    )

    row.update(p8f.fuse_origin_evidence(row))
    row.update(p8f.fuse_replay_evidence(row))
    row.update(p8f.fuse_mixer_evidence(row))

    row["partial_evidence_strength"] = partial_partial["partial_evidence_strength"]
    row["partial_evidence_label"] = partial_partial["partial_evidence_label"]

    provisional = p8f.apply_multi_axis_fusion(row)
    row.update(provisional)

    resolved_status = _resolve_live_fusion_status(row, partial_fabrication_evidence)
    row["experimental_fusion_status"] = resolved_status
    row["forensic_risk_level"] = _risk_for_status(resolved_status, row)
    row["manual_review_required"] = "true" if resolved_status.startswith("suspicious_") else row.get(
        "manual_review_required", "true"
    )
    row["fusion_trace"] = p8f.build_fusion_trace(row)

    return {
        "experimental_fusion_status": row.get("experimental_fusion_status"),
        "forensic_risk_level": row.get("forensic_risk_level"),
        "manual_review_required": row.get("manual_review_required") == "true",
        "manual_review_reason": row.get("manual_review_reason", "none"),
        "fusion_trace": row.get("fusion_trace", ""),
        "origin_evidence": {
            **origin_evidence,
            "evidence_strength": row.get("origin_evidence_strength"),
            "evidence_label": row.get("origin_evidence_label"),
        },
        "replay_evidence": {
            **replay_evidence,
            "evidence_strength": row.get("replay_evidence_strength"),
            "evidence_label": row.get("replay_evidence_label"),
        },
        "mixer_channel_evidence": {
            **mixer_channel_evidence,
            "evidence_strength": row.get("mixer_evidence_strength"),
            "evidence_label": row.get("mixer_evidence_label"),
        },
        "partial_fabrication_evidence": {
            **partial_fabrication_evidence,
            "evidence_strength": partial_partial["partial_evidence_strength"],
            "evidence_label": partial_partial["partial_evidence_label"],
        },
        "segment_candidates": segment_candidates,
    }


def fuse_evidence_axes(
    origin_evidence: dict[str, Any],
    replay_evidence: dict[str, Any],
    mixer_channel_evidence: dict[str, Any],
    partial_fabrication_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible wrapper for API skeleton."""
    return fuse_live_evidence(
        origin_evidence,
        replay_evidence,
        mixer_channel_evidence,
        partial_fabrication_evidence,
        [],
    )
