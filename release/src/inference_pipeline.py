"""Phase 9C live single-audio inference pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .audio_io import AudioLoadError, audio_metadata, load_audio
from .feature_extraction import (
    align_features_to_metadata,
    compute_live_localization_features,
    ensure_ssl_embedding_columns,
    extract_file_acoustic_features,
    extract_segment_acoustic_features,
)
from .fusion_rules import fuse_live_evidence
from .model_loader import get_model_input_feature_names, get_threshold, load_all_active_models
from .report_generator import build_forensic_summary, generate_safe_report
from .schemas import default_forensic_response
from .segmentation import make_segments
from .ssl_embeddings import (
    extract_file_ssl_embedding,
    extract_segment_ssl_embeddings,
    load_ssl_extractor,
)
from .utils import make_case_id, now_iso, read_yaml_safe, release_root

ELEVATED_STRENGTHS = frozenset({"moderate", "high"})


def _file_axis_strength(evidence: dict[str, Any]) -> str:
    """Classify file-axis strength for partial arbitration (before Phase 8F fusion)."""
    if not evidence.get("prediction_success"):
        return "not_evaluated"
    prob = evidence.get("probability")
    if prob is None:
        return "not_evaluated"
    th = float(evidence.get("threshold_candidate", 0.5) or 0.5)
    p = float(prob)
    if p >= th + 0.20:
        return "high"
    if p >= th:
        return "moderate"
    if p >= th - 0.10:
        return "borderline"
    return "low"


def _alignment_debug(features: dict[str, Any], expected_features: list[str]) -> dict[str, Any]:
    provided_keys = set(features.keys())
    missing = []
    for name in expected_features:
        if name not in provided_keys:
            missing.append(name)
            continue
        val = features.get(name)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            missing.append(name)
    preview = missing[:12]
    return {
        "expected_feature_count": len(expected_features),
        "provided_feature_count": len(provided_keys),
        "missing_feature_count": len(missing),
        "missing_feature_preview": preview,
    }


def _predict_axis(model, meta: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    th = get_threshold(meta)
    expected_features = get_model_input_feature_names(model, meta)
    if not expected_features:
        return {
            "model_available": True,
            "prediction_success": False,
            "probability": None,
            "threshold_candidate": th,
            "label": "prediction_error",
            "evidence_label": "prediction_error",
            "evidence_strength": "not_evaluated",
            "notes": ["could not resolve fit-time input feature names"],
            "alignment_debug": {},
        }

    aligned_features = ensure_ssl_embedding_columns(features) if any(
        n.startswith("ssl_emb_") for n in expected_features
    ) else dict(features)
    align_debug = _alignment_debug(aligned_features, expected_features)
    x = align_features_to_metadata(aligned_features, expected_features)

    if align_debug["missing_feature_count"] > 0:
        ratio = align_debug["missing_feature_count"] / max(1, align_debug["expected_feature_count"])
        missing_note = (
            f"missing_or_nan_features={align_debug['missing_feature_count']}/"
            f"{align_debug['expected_feature_count']}"
        )
    else:
        ratio = 0.0
        missing_note = ""

    try:
        proba = float(model.predict_proba(x)[0, 1])
        label = "elevated_indicator" if proba >= th else "low_indicator"
        notes = []
        if ratio > 0.25:
            notes.append(f"warning: {missing_note}; imputer will fill gaps")
        return {
            "model_available": True,
            "prediction_success": True,
            "probability": proba,
            "threshold_candidate": th,
            "label": label,
            "evidence_label": label,
            "evidence_strength": "pending_fusion",
            "expected_feature_count": align_debug["expected_feature_count"],
            "provided_feature_count": align_debug["provided_feature_count"],
            "missing_feature_count": align_debug["missing_feature_count"],
            "missing_feature_preview": align_debug["missing_feature_preview"],
            "selected_feature_names_doc": list(meta.get("feature_names", [])),
            "notes": notes,
            "alignment_debug": {**align_debug, "prediction_success": True},
        }
    except Exception as exc:
        err_txt = str(exc)
        return {
            "model_available": True,
            "prediction_success": False,
            "probability": None,
            "threshold_candidate": th,
            "label": "prediction_error",
            "evidence_label": "prediction_error",
            "evidence_strength": "not_evaluated",
            "expected_feature_count": align_debug.get("expected_feature_count", 0),
            "provided_feature_count": align_debug.get("provided_feature_count", 0),
            "missing_feature_count": align_debug.get("missing_feature_count", 0),
            "missing_feature_preview": align_debug.get("missing_feature_preview", []),
            "selected_feature_names_doc": list(meta.get("feature_names", [])),
            "notes": [f"prediction_error: {err_txt}", missing_note] if missing_note else [f"prediction_error: {err_txt}"],
            "alignment_debug": {**align_debug, "prediction_success": False, "error": err_txt},
        }


def _run_file_axis(
    models: dict[str, dict[str, Any]],
    key: str,
    file_features: dict[str, Any],
) -> dict[str, Any]:
    return _predict_axis(models[key]["model"], models[key]["metadata"], dict(file_features))


def _partial_segment_diagnostics(
    seg_df: pd.DataFrame,
    threshold: float,
    high_segment_fraction: float,
) -> dict[str, Any]:
    top_ranges: list[str] = []
    high_ranges: list[str] = []
    if len(seg_df) > 0 and "partial_probability" in seg_df.columns:
        ordered = seg_df.sort_values("partial_probability", ascending=False, na_position="last")
        for _, row in ordered.head(5).iterrows():
            p = row.get("partial_probability")
            if p is None or (isinstance(p, float) and np.isnan(p)):
                continue
            top_ranges.append(
                f"{row.get('start_sec', '?')}s-{row.get('end_sec', '?')}s (p={float(p):.3f})"
            )
        for _, row in seg_df.iterrows():
            p = row.get("partial_probability")
            if p is None or (isinstance(p, float) and np.isnan(p)):
                continue
            if float(p) >= threshold:
                high_ranges.append(f"{row.get('start_sec', '?')}s-{row.get('end_sec', '?')}s")
    broad = bool(high_segment_fraction >= 0.60)
    return {
        "top_segment_ranges": top_ranges,
        "high_probability_ranges": high_ranges,
        "broad_activation_warning": broad,
        "localization_confidence_note": (
            "Broad high activation; not enough contrast to identify localized partial region."
            if broad
            else "Segment contrast assessed for localization support (experimental)."
        ),
    }


def _compute_partial_segment_metrics(
    valid_probs: list[float],
    threshold: float,
    prediction_success: bool,
) -> dict[str, Any]:
    """Compute segment-level partial metrics (no fusion eligibility yet)."""
    segment_count = len(valid_probs)
    if not prediction_success or segment_count == 0:
        return {
            "segment_count": segment_count,
            "high_segment_count": 0,
            "high_segment_fraction": 0.0,
            "max_segment_probability": 0.0,
            "raw_max_segment_probability": 0.0,
            "mean_segment_probability": 0.0,
            "median_segment_probability": 0.0,
            "top_k_mean_probability": 0.0,
            "rest_mean_probability": 0.0,
            "topk_minus_rest_probability": 0.0,
            "probability_std": 0.0,
            "localized_pattern_score": 0.0,
            "gated_partial_probability": 0.0,
            "gating_note": "partial predictions unavailable",
            "label": "prediction_error",
            "evidence_label": "prediction_error",
            "evidence_strength": "not_evaluated",
            "probability": None,
        }

    arr = np.asarray(valid_probs, dtype=float)
    max_prob = float(np.max(arr))
    mean_prob = float(np.mean(arr))
    median_prob = float(np.median(arr))
    std_prob = float(np.std(arr)) if len(arr) > 1 else 0.0
    high_count = int(np.sum(arr >= threshold))
    high_fraction = float(high_count / segment_count) if segment_count else 0.0

    k = min(5, segment_count)
    sorted_probs = np.sort(arr)[::-1]
    top_k_mean = float(np.mean(sorted_probs[:k]))
    rest_mean = float(np.mean(sorted_probs[k:])) if len(sorted_probs) > k else 0.0
    topk_minus_rest = float(top_k_mean - rest_mean)
    localized_pattern_score = float(topk_minus_rest + std_prob)

    return {
        "segment_count": segment_count,
        "high_segment_count": high_count,
        "high_segment_fraction": round(high_fraction, 4),
        "max_segment_probability": max_prob,
        "raw_max_segment_probability": max_prob,
        "mean_segment_probability": round(mean_prob, 4),
        "median_segment_probability": round(median_prob, 4),
        "top_k_mean_probability": round(top_k_mean, 4),
        "rest_mean_probability": round(rest_mean, 4),
        "topk_minus_rest_probability": round(topk_minus_rest, 4),
        "probability_std": round(std_prob, 4),
        "localized_pattern_score": round(localized_pattern_score, 4),
        "gated_partial_probability": max_prob,
        "gating_note": "segment metrics computed",
        "label": "partial_segment_metrics",
        "evidence_label": "partial_segment_metrics",
        "evidence_strength": "pending_fusion",
        "probability": max_prob,
    }


def _apply_partial_fusion_fields(metrics: dict[str, Any], threshold: float, prediction_success: bool) -> dict[str, Any]:
    """Apply conservative partial gate + fusion eligibility (Phase 9C-P3-FIX rule C)."""
    out = dict(metrics)
    segment_count = int(out.get("segment_count", 0) or 0)
    broad = False
    loc_note = "Segment contrast assessed for localization support (experimental)."

    if not prediction_success:
        out.update(
            {
                "partial_localization_gate": "insufficient_segments",
                "partial_fusion_eligible": False,
                "partial_evidence_strength_for_fusion": "not_evaluated",
                "partial_fusion_block_reason": "prediction_failed",
                "partial_arbitration_note": "",
                "broad_activation_warning": False,
                "localization_confidence_note": "Partial segment prediction failed.",
                "gated_partial_probability": 0.0,
                "evidence_label": "prediction_error",
                "evidence_strength": "not_evaluated",
            }
        )
        return out

    hsf = float(out.get("high_segment_fraction", 0.0) or 0.0)
    max_prob = float(out.get("max_segment_probability", 0.0) or 0.0)
    topk_mr = float(out.get("topk_minus_rest_probability", 0.0) or 0.0)

    if segment_count < 3:
        out.update(
            {
                "partial_localization_gate": "insufficient_segments",
                "partial_fusion_eligible": False,
                "partial_evidence_strength_for_fusion": "not_evaluated",
                "partial_fusion_block_reason": "insufficient_segments",
                "partial_arbitration_note": "",
                "broad_activation_warning": False,
                "localization_confidence_note": "Too few segments for localization assessment.",
                "gated_partial_probability": max_prob,
                "gating_note": "too few segments for localization pattern assessment",
                "evidence_label": "insufficient_segments_for_partial_localization",
                "evidence_strength": "not_evaluated",
            }
        )
        return out

    if hsf >= 0.60:
        broad = True
        loc_note = "Broad high activation; not enough contrast to identify localized partial region."
        out.update(
            {
                "partial_localization_gate": "global_activation_not_localized",
                "partial_fusion_eligible": False,
                "partial_evidence_strength_for_fusion": "borderline",
                "partial_fusion_block_reason": "global_activation_not_localized",
                "partial_arbitration_note": "",
                "broad_activation_warning": True,
                "localization_confidence_note": loc_note,
                "gated_partial_probability": min(max_prob, threshold - 0.01) if threshold > 0.01 else 0.0,
                "gating_note": "broad segment activation across file; not treated as localized partial-fabrication evidence",
                "evidence_label": "global_partial_model_activation_not_localized",
                "evidence_strength": "borderline",
            }
        )
        return out

    if max_prob >= threshold and topk_mr >= 0.15:
        fusion_strength = "high" if max_prob >= threshold + 0.20 else "moderate"
        out.update(
            {
                "partial_localization_gate": "localized_pattern_supported",
                "partial_fusion_eligible": True,
                "partial_evidence_strength_for_fusion": fusion_strength,
                "partial_fusion_block_reason": "none",
                "partial_arbitration_note": "",
                "broad_activation_warning": False,
                "localization_confidence_note": loc_note,
                "gated_partial_probability": max_prob,
                "gating_note": "localized contrast between top candidate segments and remainder",
                "evidence_label": "localized_partial_fabrication_indicator",
                "evidence_strength": fusion_strength,
            }
        )
        return out

    if max_prob >= threshold and topk_mr < 0.15:
        out.update(
            {
                "partial_localization_gate": "weak_localization_contrast",
                "partial_fusion_eligible": False,
                "partial_evidence_strength_for_fusion": "borderline",
                "partial_fusion_block_reason": "weak_localization_contrast",
                "partial_arbitration_note": "",
                "broad_activation_warning": False,
                "localization_confidence_note": loc_note,
                "gated_partial_probability": max_prob,
                "gating_note": "high segment scores without strong localization contrast",
                "evidence_label": "weak_or_nonlocalized_partial_indicator",
                "evidence_strength": "borderline",
            }
        )
        return out

    out.update(
        {
            "partial_localization_gate": "low_partial_indicator",
            "partial_fusion_eligible": False,
            "partial_evidence_strength_for_fusion": "low",
            "partial_fusion_block_reason": "none",
            "partial_arbitration_note": "",
            "broad_activation_warning": False,
            "localization_confidence_note": loc_note,
            "gated_partial_probability": max_prob,
            "gating_note": "segment scores below partial threshold",
            "evidence_label": "low_indicator",
            "evidence_strength": "low",
        }
    )
    return out


def _apply_replay_mixer_partial_arbitration(
    partial: dict[str, Any],
    replay_evidence: dict[str, Any],
    mixer_channel_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Replay/mixer context arbitration — Phase 4: do not hide localized partial."""
    out = dict(partial)
    replay_strength = _file_axis_strength(replay_evidence)
    mixer_strength = _file_axis_strength(mixer_channel_evidence)
    if replay_strength not in ELEVATED_STRENGTHS and mixer_strength not in ELEVATED_STRENGTHS:
        return out

    gate = str(out.get("partial_localization_gate", ""))
    hsf = float(out.get("high_segment_fraction", 1.0) or 1.0)
    topk_mr = float(out.get("topk_minus_rest_probability", 0.0) or 0.0)
    pstd = float(out.get("probability_std", 0.0) or 0.0)
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
        out["gating_note"] = "; ".join([s for s in [str(out.get("gating_note", "")), coexist_note] if s])
        return out

    strict_ok = localized and topk_mr >= 0.35 and pstd >= 0.25
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
    out["gating_note"] = "; ".join([s for s in [str(out.get("gating_note", "")), arbitration_note] if s])
    return out


def _segment_candidates_from_partial(
    seg_df: pd.DataFrame,
    model,
    meta: dict[str, Any],
    top_k: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    expected_features = get_model_input_feature_names(model, meta)
    th = get_threshold(meta)
    probs: list[float] = []
    errors = 0
    for _, row in seg_df.iterrows():
        row_dict = row.to_dict()
        if any(n.startswith("ssl_emb_") for n in expected_features):
            row_dict = ensure_ssl_embedding_columns(row_dict)
        x = align_features_to_metadata(row_dict, expected_features)
        try:
            probs.append(float(model.predict_proba(x)[0, 1]))
        except Exception:
            probs.append(float("nan"))
            errors += 1

    seg_df = seg_df.copy()
    seg_df["partial_probability"] = probs
    seg_df = seg_df.sort_values("partial_probability", ascending=False, na_position="last")
    valid_probs = [p for p in probs if p is not None and not np.isnan(p)]
    max_prob = float(max(valid_probs)) if valid_probs else None
    prediction_success = len(valid_probs) > 0

    candidates: list[dict[str, Any]] = []
    for rank, (_, row) in enumerate(seg_df.head(top_k).iterrows(), start=1):
        p = row.get("partial_probability")
        candidates.append(
            {
                "segment_id": row.get("segment_id"),
                "start_sec": row.get("start_sec"),
                "end_sec": row.get("end_sec"),
                "partial_probability": None if p is None or (isinstance(p, float) and np.isnan(p)) else float(p),
                "candidate_rank": rank,
                "candidate_wording": "candidate_segment_for_manual_review",
                "above_threshold": bool(p is not None and not np.isnan(p) and float(p) >= th),
            }
        )

    metrics = _compute_partial_segment_metrics(valid_probs, th, prediction_success)
    partial_core = _apply_partial_fusion_fields(metrics, th, prediction_success)
    diagnostics = _partial_segment_diagnostics(
        seg_df,
        th,
        float(partial_core.get("high_segment_fraction", 0.0) or 0.0),
    )

    partial_evidence = {
        "model_available": True,
        "prediction_success": prediction_success,
        "threshold_candidate": th,
        "selected_feature_names_doc": list(meta.get("feature_names", [])),
        "notes": [
            "segment-level partial fabrication localization support only (not a general file-level partial detector)",
        ]
        + ([f"segment_prediction_errors={errors}"] if errors else []),
        "expected_feature_count": len(expected_features),
        "provided_feature_count": len(set(seg_df.columns)),
        "missing_feature_count": None,
        "missing_feature_preview": [],
        "alignment_debug": {
            "expected_feature_count": len(expected_features),
            "segment_count": len(seg_df),
            "prediction_success": prediction_success,
        },
        **diagnostics,
        **partial_core,
    }
    all_segment_scores = _build_all_partial_segment_scores(
        seg_df,
        th,
        partial_core.get("partial_localization_gate"),
    )
    return candidates, partial_evidence, all_segment_scores


def _build_all_partial_segment_scores(
    seg_df: pd.DataFrame,
    threshold: float,
    partial_localization_gate: Any,
) -> list[dict[str, Any]]:
    """All segment partial scores for debug/diagnostic use only (not normal API output)."""
    if "partial_probability" not in seg_df.columns:
        return []
    ordered = seg_df.sort_values("partial_probability", ascending=False, na_position="last")
    rows: list[dict[str, Any]] = []
    gate = str(partial_localization_gate or "")
    for rank, (_, row) in enumerate(ordered.iterrows(), start=1):
        p = row.get("partial_probability")
        if p is None or (isinstance(p, float) and np.isnan(p)):
            prob_val = None
            above = False
        else:
            prob_val = float(p)
            above = prob_val >= threshold
        rows.append(
            {
                "segment_id": row.get("segment_id"),
                "start_sec": row.get("start_sec"),
                "end_sec": row.get("end_sec"),
                "partial_probability": prob_val,
                "partial_rank": rank,
                "partial_above_threshold": above,
                "candidate_type": "partial_segment_score",
                "partial_localization_gate": gate,
            }
        )
    return rows


def analyze_audio_file(
    audio_path: str,
    case_id: str | None = None,
    output_dir: str | Path | None = None,
    device: str = "auto",
    return_debug: bool = False,
) -> dict[str, Any]:
    resolved_case_id = case_id or make_case_id()
    result = default_forensic_response(case_id=resolved_case_id)
    debug: dict[str, Any] = {"steps": []}

    runtime = read_yaml_safe(release_root() / "config" / "runtime_config.yaml")
    seg_dur = float(runtime.get("segment_duration_sec", 4.0))
    seg_hop = float(runtime.get("segment_hop_sec", 2.0))
    target_sr = int(runtime.get("target_sample_rate", 16000))

    try:
        y, sr = load_audio(audio_path, target_sample_rate=target_sr)
        result["audio_metadata"] = audio_metadata(audio_path, y, sr)
        debug["steps"].append("audio_loaded")
    except AudioLoadError as exc:
        result["status"] = "error"
        result["forensic_summary"] = f"Audio load failed: {exc}"
        result["limitations"].append(str(exc))
        if return_debug:
            result["debug_info"] = debug
        return result

    segments = make_segments(y, sr, segment_duration_sec=seg_dur, hop_sec=seg_hop)
    debug["steps"].append(f"segments:{len(segments)}")

    file_acoustic = extract_file_acoustic_features(y, sr)
    seg_acoustic = extract_segment_acoustic_features(segments, y, sr, mode="full")

    ssl_model, ssl_processor, ssl_device = load_ssl_extractor(device=device)
    file_ssl = extract_file_ssl_embedding(y, sr, ssl_model, ssl_processor, ssl_device)
    file_features = ensure_ssl_embedding_columns({**file_acoustic, **file_ssl})
    seg_ssl = extract_segment_ssl_embeddings(segments, y, sr, ssl_model, ssl_processor, ssl_device)

    ssl_cols = [c for c in seg_ssl.columns if c.startswith("ssl_emb_") or c == "ssl_extraction_status"]
    seg_df = seg_acoustic.merge(seg_ssl[["segment_id"] + ssl_cols], on="segment_id", how="left")
    seg_df = compute_live_localization_features(seg_df)
    debug["steps"].append("features_extracted")

    models = load_all_active_models()
    debug["steps"].append("models_loaded")

    origin = _run_file_axis(models, "origin", file_features)
    replay = _run_file_axis(models, "replay", file_features)
    mixer = _run_file_axis(models, "mixer", file_features)

    if origin.get("prediction_success"):
        origin["notes"] = list(origin.get("notes", [])) + [
            "origin indicator is not a final fake/real decision"
        ]
    if replay.get("prediction_success"):
        replay["notes"] = list(replay.get("notes", [])) + [
            "replay indicator does not mean AI-generated"
        ]
    if mixer.get("prediction_success"):
        mixer["notes"] = list(mixer.get("notes", [])) + [
            "mixer/channel indicator does not mean AI-generated"
        ]

    segment_candidates, partial, all_partial_segment_scores = _segment_candidates_from_partial(
        seg_df, models["partial_segment"]["model"], models["partial_segment"]["metadata"]
    )
    partial = _apply_replay_mixer_partial_arbitration(partial, replay, mixer)

    fused = fuse_live_evidence(origin, replay, mixer, partial, segment_candidates)

    result["origin_evidence"] = fused["origin_evidence"]
    result["replay_evidence"] = fused["replay_evidence"]
    result["mixer_channel_evidence"] = fused["mixer_channel_evidence"]
    result["partial_fabrication_evidence"] = fused["partial_fabrication_evidence"]
    result["segment_candidates"] = fused["segment_candidates"]
    result["fusion_status"] = fused.get("experimental_fusion_status")
    result["forensic_risk_level"] = fused.get("forensic_risk_level")
    result["manual_review_required"] = fused.get("manual_review_required", True)
    result["manual_review_reason"] = fused.get("manual_review_reason", "none")
    result["status"] = "experimental_forensic_prototype"
    result["limitations"] = [
        "experimental_forensic_prototype",
        "multi-axis evidence only; no single binary authenticity score",
        "AASIST/HybridResNet reference models inactive",
        "manual review recommended for elevated or mixed indicators",
    ]
    result["forensic_summary"] = build_forensic_summary(result)
    result["report_markdown"] = generate_safe_report(result)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        from .utils import write_json, write_markdown

        write_json(out / f"{resolved_case_id}_analysis.json", result)
        write_markdown(out / f"{resolved_case_id}_report.md", result["report_markdown"])

    result["generated_at"] = now_iso()
    if return_debug:
        for row in all_partial_segment_scores:
            row["case_id"] = resolved_case_id
        debug["partial_segment_scores"] = all_partial_segment_scores
        result["debug_info"] = debug
    return result


def run_inference_pipeline(audio_path: str, case_id: str | None = None) -> dict[str, Any]:
    """Compatibility wrapper for FastAPI/Gradio skeleton."""
    return analyze_audio_file(audio_path=audio_path, case_id=case_id)
