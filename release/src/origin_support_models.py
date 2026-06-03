"""Shadow origin-support models (AASIST / HybridResNet) — audit and inference only.

Phase 9E-P4A: These models support voice-origin shadow evaluation only.
They must NOT drive replay, mixer, partial, or active release fusion decisions.
"""

from __future__ import annotations

import json
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from .utils import repo_root, release_root

ORIGIN_AI_THRESHOLD = 0.5
ORIGIN_HUMAN_MARGIN = 0.10
AASIST_SPOOF_CLASS_INDEX = 0
HYBRID_CHUNK_SEC = 4.0
HYBRID_OVERLAP_SEC = 1.0


def _reference_root() -> Path:
    return release_root() / "models" / "reference"


def _code_root() -> Path:
    return repo_root() / "code"


def _resolve_device(device: str = "auto") -> str:
    if device != "auto":
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _origin_label_from_score(score_ai: float | None, threshold: float = ORIGIN_AI_THRESHOLD) -> str:
    if score_ai is None or score_ai != score_ai:
        return "unavailable"
    if score_ai >= threshold:
        return "likely_ai_generated"
    if score_ai <= threshold - ORIGIN_HUMAN_MARGIN:
        return "likely_human"
    return "inconclusive"


def _model_result(
    *,
    available: bool,
    runnable: bool,
    status: str,
    score_ai: float | None = None,
    label: str = "unavailable",
    error: str | None = None,
    runtime_sec: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "available": available,
        "runnable": runnable,
        "status": status,
        "score_ai": score_ai,
        "label": label,
        "error": error,
    }
    if runtime_sec is not None:
        out["runtime_sec"] = runtime_sec
    if extra:
        out.update(extra)
    return out


def _aasist_paths() -> dict[str, Path]:
    root = _reference_root()
    repo = repo_root()
    vendor = repo / "code" / "phase7" / "aasist" / "vendor" / "AASIST"
    config = vendor / "config" / "AASIST-L.conf"
    weights = root / "aasist" / "aasist_l_official_pretrained_reference.pth"
    if not weights.is_file():
        alt = root / "aasist" / "aasist_official_pretrained_reference.pth"
        if alt.is_file():
            weights = alt
    return {
        "package_path": root / "aasist",
        "vendor_src": vendor,
        "config": config,
        "weights": weights,
        "metadata": root / "aasist" / "metadata.json",
    }


def _hybrid_paths() -> dict[str, Path]:
    root = _reference_root()
    weights = root / "hybrid_resnet" / "hybrid_resnet_environmental_best.pth"
    if not weights.is_file():
        alt = repo_root() / "models_saved" / "hybrid_resnet_environmental_best.pth"
        if alt.is_file():
            weights = alt
    return {
        "package_path": root / "hybrid_resnet",
        "weights": weights,
        "metadata": root / "hybrid_resnet" / "metadata.json",
        "inference_code": _code_root() / "phase3" / "hybrid_resnet_environmental.py",
    }


def _audit_single_model(model_name: str) -> dict[str, Any]:
    if model_name == "aasist":
        paths = _aasist_paths()
        weights_found = paths["weights"].is_file()
        config_found = paths["config"].is_file()
        inference_found = (paths["vendor_src"] / "models" / "AASIST.py").is_file()
        expected_input = "mono float32 waveform @16kHz, fixed-length windows (nb_samp from AASIST-L config)"
        gpu_risk = "medium (windowed inference; batch size 1 default)"
        runtime_risk = "medium (sliding windows on long files)"
        if not weights_found:
            reason = "reference weights missing under release/models/reference/aasist/"
            action = "audit_only"
            runnable = False
        elif not config_found or not inference_found:
            reason = "AASIST vendor source or config missing under code/phase7/aasist/vendor/AASIST/"
            action = "audit_only"
            runnable = False
        else:
            reason = ""
            action = "runnable_shadow_eval"
            runnable = True
    else:
        paths = _hybrid_paths()
        weights_found = paths["weights"].is_file()
        config_found = paths["metadata"].is_file()
        inference_found = paths["inference_code"].is_file()
        expected_input = "mono @16kHz → log-mel [64x400] + 12-D environmental features per 4s chunk"
        gpu_risk = "low-medium (chunked 4s windows)"
        runtime_risk = "medium (librosa feature extraction per chunk)"
        if not weights_found:
            reason = "HybridResNet reference weights missing"
            action = "audit_only"
            runnable = False
        elif not inference_found:
            reason = "HybridResNet architecture code missing under code/phase3/"
            action = "audit_only"
            runnable = False
        else:
            reason = ""
            action = "runnable_shadow_eval"
            runnable = True

    return {
        "model_name": model_name,
        "package_path": str(paths["package_path"]),
        "weights_found": weights_found,
        "config_found": config_found,
        "inference_code_found": inference_found,
        "expected_input_format": expected_input,
        "runnable_in_release": runnable,
        "reason_if_not_runnable": reason,
        "estimated_runtime_risk": runtime_risk,
        "gpu_memory_risk": gpu_risk,
        "action": action,
        "weight_path": str(paths["weights"]) if weights_found else "",
    }


def audit_origin_support_models() -> dict[str, Any]:
    """Detailed P4A audit for AASIST and HybridResNet reference packages."""
    aasist = _audit_single_model("aasist")
    hybrid = _audit_single_model("hybrid_resnet")
    any_runnable = aasist["runnable_in_release"] or hybrid["runnable_in_release"]
    if any_runnable:
        summary = "one or more reference origin-support models runnable for shadow eval"
    elif aasist["weights_found"] or hybrid["weights_found"]:
        summary = "reference weights present but shadow wrappers not runnable (missing vendor/code)"
    else:
        summary = "reference origin-support models unavailable (audit only)"

    compact_aasist = {
        "available": aasist["weights_found"],
        "runnable": aasist["runnable_in_release"],
        "status": "shadow_runnable" if aasist["runnable_in_release"] else "audit_only",
    }
    compact_hybrid = {
        "available": hybrid["weights_found"],
        "runnable": hybrid["runnable_in_release"],
        "status": "shadow_runnable" if hybrid["runnable_in_release"] else "audit_only",
    }
    return {
        "audit_status": summary,
        "reference_root": str(_reference_root()),
        "used_as_active_decision": False,
        "policy": "shadow_support_only_unless_validation_proves_improvement",
        "aasist": compact_aasist,
        "hybrid_resnet": compact_hybrid,
        "models": [aasist, hybrid],
        "model_details": {"aasist": aasist, "hybrid_resnet": hybrid},
    }


def audit_reference_models() -> dict[str, Any]:
    """Backward-compatible audit wrapper used by Phase 9E-P3 eval."""
    audit = audit_origin_support_models()
    models: list[dict[str, Any]] = []
    for key in ("aasist", "hybrid_resnet"):
        detail = audit["model_details"][key]
        models.append(
            {
                "model_name": key,
                "status": "shadow_runnable" if detail["runnable_in_release"] else "present_not_runnable",
                "metadata_path": str(_reference_root() / key / "metadata.json"),
                "weight_files": [detail["weight_path"]] if detail.get("weight_path") else [],
                "active_in_fusion": False,
                "safe_wrapper_available": detail["runnable_in_release"],
            }
        )
    out = dict(audit)
    out["models"] = models
    out["inventory_present"] = (_reference_root() / "reference_model_inventory.json").is_file()
    return out


def compact_origin_support_audit(audit: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    if audit is None:
        audit = audit_origin_support_models()
    out: dict[str, dict[str, Any]] = {}
    for key in ("aasist", "hybrid_resnet"):
        detail = (audit.get("model_details") or {}).get(key) or {}
        if not detail and audit.get(key):
            compact = audit[key]
            out[key] = {
                "available": compact.get("available", False),
                "runnable": compact.get("runnable", False),
                "status": compact.get("status", "audit_only"),
            }
            continue
        runnable = bool(detail.get("runnable_in_release"))
        out[key] = {
            "available": bool(detail.get("weights_found")),
            "runnable": runnable,
            "status": "shadow_runnable" if runnable else "audit_only",
        }
    return out


def format_reference_audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Reference Origin-Support Model Audit",
        "",
        f"**Summary:** {audit.get('audit_status', '')}",
        "",
        "| Model | Weights | Config | Code | Runnable | Action |",
        "|-------|---------|--------|------|----------|--------|",
    ]
    details = audit.get("model_details") or {}
    for key in ("aasist", "hybrid_resnet"):
        d = details.get(key, {})
        lines.append(
            f"| {key} | {d.get('weights_found', False)} | {d.get('config_found', False)} | "
            f"{d.get('inference_code_found', False)} | {d.get('runnable_in_release', False)} | "
            f"{d.get('action', 'audit_only')} |"
        )
    lines.extend(
        [
            "",
            "Shadow models are **not** used for active voice-origin, replay, mixer, or partial decisions.",
        ]
    )
    return "\n".join(lines) + "\n"


def format_p4a_audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Phase 9E-P4A Reference Model Audit",
        "",
        f"**Summary:** {audit.get('audit_status', '')}",
        "",
    ]
    for d in audit.get("models") or []:
        lines.extend(
            [
                f"## {d.get('model_name')}",
                "",
                f"- package_path: `{d.get('package_path')}`",
                f"- weights_found: {d.get('weights_found')}",
                f"- config_found: {d.get('config_found')}",
                f"- inference_code_found: {d.get('inference_code_found')}",
                f"- expected_input_format: {d.get('expected_input_format')}",
                f"- runnable_in_release: {d.get('runnable_in_release')}",
                f"- reason_if_not_runnable: {d.get('reason_if_not_runnable') or '—'}",
                f"- estimated_runtime_risk: {d.get('estimated_runtime_risk')}",
                f"- gpu_memory_risk: {d.get('gpu_memory_risk')}",
                f"- action: {d.get('action')}",
                "",
            ]
        )
    lines.append("Active release fusion unchanged; shadow eval only.")
    return "\n".join(lines) + "\n"


@lru_cache(maxsize=1)
def load_origin_support_models(device: str = "auto") -> dict[str, Any]:
    """Load shadow origin-support models once per process (cached)."""
    dev = _resolve_device(device)
    audit = audit_origin_support_models()
    loaded: dict[str, Any] = {"device": dev, "aasist": None, "hybrid_resnet": None, "errors": {}}

    if audit["model_details"]["aasist"]["runnable_in_release"]:
        try:
            loaded["aasist"] = _load_aasist_model(dev)
        except Exception as exc:
            loaded["errors"]["aasist"] = str(exc)

    if audit["model_details"]["hybrid_resnet"]["runnable_in_release"]:
        try:
            loaded["hybrid_resnet"] = _load_hybrid_model(dev)
        except Exception as exc:
            loaded["errors"]["hybrid_resnet"] = str(exc)

    return loaded


def _load_aasist_model(device: str) -> dict[str, Any]:
    paths = _aasist_paths()
    integration = repo_root() / "code" / "phase7" / "aasist" / "integration"
    if str(integration) not in sys.path:
        sys.path.insert(0, str(integration))
    from aasist_eval_common import load_aasist_model  # type: ignore

    model, meta = load_aasist_model(
        paths["vendor_src"],
        paths["config"],
        paths["weights"],
        device,
        spoof_class_index=AASIST_SPOOF_CLASS_INDEX,
    )
    return {"model": model, "meta": meta, "device": meta.get("device", device)}


def _load_hybrid_model(device: str) -> dict[str, Any]:
    import torch

    paths = _hybrid_paths()
    code = _code_root()
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))
    from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental  # type: ignore

    dev = device if device == "cuda" and torch.cuda.is_available() else "cpu"
    ckpt = torch.load(str(paths["weights"]), map_location=dev, weights_only=False)
    state = ckpt.get("model_state_dict", ckpt)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(dev)
    model.load_state_dict(state, strict=False)
    model.eval()
    return {"model": model, "device": dev, "weight_path": str(paths["weights"])}


def _predict_aasist(audio_path: str, bundle: dict[str, Any] | None, device: str) -> dict[str, Any]:
    if bundle is None:
        return _model_result(
            available=_aasist_paths()["weights"].is_file(),
            runnable=False,
            status="audit_only",
            error="AASIST not loaded",
        )
    t0 = time.perf_counter()
    try:
        integration = repo_root() / "code" / "phase7" / "aasist" / "integration"
        if str(integration) not in sys.path:
            sys.path.insert(0, str(integration))
        from aasist_eval_common import (  # type: ignore
            extract_window,
            generate_window_starts,
            infer_window_probabilities,
            load_audio_mono_16k,
        )

        model = bundle["model"]
        meta = bundle["meta"]
        dev = bundle.get("device", device)
        nb_samp = int(meta.get("nb_samp", 64600))
        hop = max(1, nb_samp // 2)
        wav, _ = load_audio_mono_16k(Path(audio_path))
        starts, _ = generate_window_starts(len(wav), nb_samp, hop)
        windows = [extract_window(wav, s, nb_samp) for s in starts]
        probs = infer_window_probabilities(
            model, windows, dev, batch_size=8, spoof_class_index=AASIST_SPOOF_CLASS_INDEX
        )
        if not probs:
            raise RuntimeError("no_aasist_windows")
        spoof_scores = [p["spoof_score"] for p in probs]
        score_ai = float(max(spoof_scores))
        label = _origin_label_from_score(score_ai)
        return _model_result(
            available=True,
            runnable=True,
            status="shadow_runnable",
            score_ai=score_ai,
            label=label,
            error=None,
            runtime_sec=time.perf_counter() - t0,
            extra={"n_windows": len(windows), "mean_spoof_score": float(np.mean(spoof_scores))},
        )
    except Exception as exc:
        return _model_result(
            available=True,
            runnable=True,
            status="error",
            error=str(exc),
            runtime_sec=time.perf_counter() - t0,
        )


def _predict_hybrid(audio_path: str, bundle: dict[str, Any] | None, device: str) -> dict[str, Any]:
    if bundle is None:
        return _model_result(
            available=_hybrid_paths()["weights"].is_file(),
            runnable=False,
            status="audit_only",
            error="HybridResNet not loaded",
        )
    t0 = time.perf_counter()
    try:
        import librosa
        import torch

        code = _code_root()
        if str(code) not in sys.path:
            sys.path.insert(0, str(code))
        if str(code / "features") not in sys.path:
            sys.path.insert(0, str(code / "features"))
        from environmental_features import EnvironmentalFeatureExtractor  # type: ignore

        from .audio_io import load_audio

        y, sr = load_audio(audio_path)
        dev = bundle.get("device", device)
        model = bundle["model"]
        extractor = EnvironmentalFeatureExtractor(sr=16000)

        chunk_len = int(HYBRID_CHUNK_SEC * sr)
        hop = int((HYBRID_CHUNK_SEC - HYBRID_OVERLAP_SEC) * sr)
        if hop <= 0:
            hop = chunk_len
        chunks: list[np.ndarray] = []
        if len(y) <= chunk_len:
            chunks = [y]
        else:
            for start in range(0, len(y) - chunk_len + 1, hop):
                chunks.append(y[start : start + chunk_len])
            if not chunks:
                chunks = [y]

        fake_probs: list[float] = []
        with torch.no_grad():
            for chunk in chunks:
                mel = librosa.feature.melspectrogram(
                    y=chunk.astype(np.float32),
                    sr=sr,
                    n_fft=512,
                    hop_length=160,
                    win_length=400,
                    n_mels=64,
                    power=2.0,
                )
                logmel = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
                if logmel.shape[1] < 400:
                    logmel = np.pad(logmel, ((0, 0), (0, 400 - logmel.shape[1])))
                elif logmel.shape[1] > 400:
                    logmel = logmel[:, :400]
                mean, std = float(logmel.mean()), float(logmel.std()) + 1e-5
                spec = ((logmel - mean) / std).astype(np.float32)
                spec_t = torch.from_numpy(spec).unsqueeze(0).unsqueeze(0).to(dev)

                env_dict = extractor.extract_all(audio_path) if len(chunks) == 1 else {}
                if not env_dict:
                    env_vec = np.array(
                        [
                            extractor.compute_rt60(chunk),
                            extractor.compute_drr(chunk),
                            extractor.compute_snr(chunk),
                            extractor.compute_background_level(chunk),
                            extractor.compute_silence_ratio(chunk),
                            extractor.compute_spectral_tilt(chunk),
                            extractor.compute_spectral_flatness(chunk),
                            extractor.compute_spectral_rolloff(chunk) / 1000.0,
                            extractor.compute_cleanliness(chunk),
                            extractor.compute_high_freq_content(chunk),
                            extractor.compute_background_consistency(chunk),
                            extractor.compute_env_stability(chunk),
                        ],
                        dtype=np.float32,
                    )
                else:
                    env_vec = np.array(
                        [
                            env_dict.get("rt60", 0.0),
                            env_dict.get("drr", 0.0),
                            env_dict.get("snr", 0.0),
                            env_dict.get("background_level", -100.0),
                            env_dict.get("silence_ratio", 0.0),
                            env_dict.get("spectral_tilt", 0.0),
                            env_dict.get("spectral_flatness", 0.0),
                            env_dict.get("spectral_rolloff", 0.0) / 1000.0,
                            env_dict.get("cleanliness_score", 0.0),
                            env_dict.get("high_freq_content", 0.0),
                            env_dict.get("background_consistency", 0.5),
                            env_dict.get("env_stability", 0.5),
                        ],
                        dtype=np.float32,
                    )
                em, es = float(env_vec.mean()), float(env_vec.std()) + 1e-5
                env_t = torch.from_numpy((env_vec - em) / es).unsqueeze(0).to(dev)
                binary_logits, _ = model(spec_t, env_t)
                prob_fake = torch.softmax(binary_logits, dim=1)[0, 1].item()
                fake_probs.append(float(prob_fake))

        score_ai = float(np.mean(fake_probs)) if fake_probs else None
        label = _origin_label_from_score(score_ai)
        return _model_result(
            available=True,
            runnable=True,
            status="shadow_runnable",
            score_ai=score_ai,
            label=label,
            error=None,
            runtime_sec=time.perf_counter() - t0,
            extra={"n_chunks": len(chunks), "max_prob_fake": float(max(fake_probs)) if fake_probs else None},
        )
    except Exception as exc:
        return _model_result(
            available=True,
            runnable=True,
            status="error",
            error=str(exc),
            runtime_sec=time.perf_counter() - t0,
        )


def predict_origin_support(audio_path: str, device: str = "auto") -> dict[str, Any]:
    """Run shadow AASIST/HybridResNet origin-support predictors (does not alter release output)."""
    dev = _resolve_device(device)
    bundles = load_origin_support_models(dev)
    return {
        "used_for_voice_origin": False,
        "shadow_only": True,
        "device": dev,
        "aasist": _predict_aasist(audio_path, bundles.get("aasist"), dev),
        "hybrid_resnet": _predict_hybrid(audio_path, bundles.get("hybrid_resnet"), dev),
        "load_errors": bundles.get("errors", {}),
    }


def run_shadow_origin_support(audio_path: str, *, device: str = "auto") -> dict[str, Any]:
    """Legacy entry point — returns shadow predictions without activating fusion."""
    pred = predict_origin_support(audio_path, device=device)
    return {
        "status": "shadow_complete",
        "used_for_voice_origin": False,
        "aasist_shadow": pred.get("aasist"),
        "hybrid_resnet_shadow": pred.get("hybrid_resnet"),
        "device": pred.get("device"),
    }
