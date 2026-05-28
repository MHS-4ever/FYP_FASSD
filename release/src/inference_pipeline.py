"""Inference pipeline skeleton for Phase 9A."""

from __future__ import annotations

from typing import Any

from .audio_io import load_audio, validate_audio_file
from .feature_extraction import extract_acoustic_features
from .fusion_rules import fuse_evidence_axes
from .report_generator import build_forensic_summary
from .schemas import default_forensic_response
from .segmentation import make_segments
from .ssl_embeddings import extract_ssl_embeddings
from .utils import make_case_id


def run_inference_pipeline(audio_path: str, case_id: str | None = None) -> dict[str, Any]:
    """Phase 9A orchestration skeleton.

    audio path -> audio validation -> segmentation -> acoustic features
    -> SSL embeddings -> model loading -> evidence outputs -> fusion -> report
    """
    resolved_case_id = case_id or make_case_id()
    response = default_forensic_response(case_id=resolved_case_id)

    ok, message = validate_audio_file(audio_path)
    if not ok:
        response["audio_metadata"] = {"path": audio_path, "validation_message": message}
        response["forensic_summary"] = (
            "Skeleton ready. Audio validation failed in placeholder mode."
        )
        return response

    waveform, audio_meta = load_audio(audio_path)
    response["audio_metadata"] = audio_meta
    segments = make_segments(waveform, sample_rate=16000, duration_sec=4.0, hop_sec=2.0)
    response["segment_candidates"] = segments
    _ = extract_acoustic_features(waveform, sample_rate=16000)
    _ = extract_ssl_embeddings(waveform, sample_rate=16000)

    # Models may be missing in Phase 9A; return placeholder-ready result.
    fused = fuse_evidence_axes(
        origin_evidence={"label": "pending_model_artifact", "confidence_indicator": None},
        replay_evidence={"label": "pending_model_artifact", "confidence_indicator": None},
        mixer_channel_evidence={"label": "pending_model_artifact", "confidence_indicator": None},
        partial_fabrication_evidence={
            "label": "pending_model_artifact",
            "confidence_indicator": None,
        },
    )
    response.update(fused)
    response["status"] = "skeleton_ready"
    response["message"] = "Phase 9B/9C required before full inference"
    response["forensic_summary"] = build_forensic_summary(response)
    return response
