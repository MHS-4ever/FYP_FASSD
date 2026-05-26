"""
Shared helpers for Phase 7E2/7E3A AASIST pretrained evaluation.

Controls: model loading, class convention, audio/windowing, partial-region metrics,
status mapping, path resolution.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

from _common import REPO_ROOT, add_aasist_src_to_path, resolve_path, utc_now_iso, write_json, write_markdown

OFFICIAL_MODEL_MODULE = "models.AASIST"
OFFICIAL_MODEL_CLASS = "Model"
TARGET_SAMPLE_RATE = 16000

# Official ASVspoof training labels (vendor/AASIST/data_utils.py):
#   d_meta[key] = 1 if label == "bonafide" else 0
OFFICIAL_SPOOF_CLASS_INDEX = 0
OFFICIAL_BONAFIDE_CLASS_INDEX = 1

MANIPULATION_DETECT_SCORE = 0.65
SEGMENT_SUSPICIOUS_MAX_SPOOF = 0.95
SEGMENT_SUSPICIOUS_RATIO = 0.30
BORDERLINE_MARGIN = 0.05
PARTIAL_REGION_DELTA_MIN = 0.10


def load_selected_paths(audit_json: Path | None = None) -> dict[str, str]:
    path = audit_json or (REPO_ROOT / "reports/phase7/phase7e_aasist_experiment/audit/phase7e0_selected_paths.json")
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for k, v in data.get("paths", {}).items():
        if isinstance(v, dict) and v.get("selected_path"):
            out[k] = v["selected_path"]
    return out


def resolve_audio_path(audio_path: str) -> Path | None:
    p = Path(audio_path)
    if p.is_file():
        return p.resolve()
    candidate = REPO_ROOT / audio_path
    if candidate.is_file():
        return candidate.resolve()
    return None


def verify_official_class_mapping(aasist_src: Path) -> dict[str, Any]:
    """
    Trace class index meaning from vendor source (read-only, no import side effects required).
    """
    notes: list[str] = []
    verified = False
    aasist_src = Path(aasist_src)

    data_utils = aasist_src / "data_utils.py"
    main_py = aasist_src / "main.py"

    if data_utils.is_file():
        text = data_utils.read_text(encoding="utf-8", errors="replace")
        if re.search(r'label\s*==\s*["\']bonafide["\']', text) and re.search(
            r"1\s+if\s+label\s*==\s*[\"']bonafide[\"']", text
        ):
            notes.append("data_utils.py: training label 1=bonafide, 0=spoof")
            verified = True

    if main_py.is_file():
        text = main_py.read_text(encoding="utf-8", errors="replace")
        if "batch_out[:, 1]" in text and "produce_evaluation_file" in text:
            notes.append("main.py produce_evaluation_file: evaluation score = logits[:, 1] (bonafide)")
            verified = True

    return {
        "verified": verified,
        "official_spoof_class_index": OFFICIAL_SPOOF_CLASS_INDEX,
        "official_bonafide_class_index": OFFICIAL_BONAFIDE_CLASS_INDEX,
        "notes": notes,
        "class_convention_source": "official_aasist_label_mapping" if verified else "",
        "class_convention_warning": "" if verified else "unverified_class_mapping",
    }


def build_class_convention_fields(
    spoof_class_index: int,
    aasist_src: Path,
    user_override: bool = False,
) -> dict[str, Any]:
    """Build traceable class-convention metadata for CSV/JSON outputs."""
    audit = verify_official_class_mapping(aasist_src)
    bonafide_class_index = 1 - spoof_class_index

    if user_override and spoof_class_index != OFFICIAL_SPOOF_CLASS_INDEX:
        source = "cli_override"
        warning = "cli_spoof_class_index_differs_from_official_default_0"
    elif audit["verified"] and spoof_class_index == OFFICIAL_SPOOF_CLASS_INDEX:
        source = audit["class_convention_source"] or "official_aasist_label_mapping"
        warning = ""
    elif audit["verified"]:
        source = "cli_override_with_official_mapping_on_disk"
        warning = f"spoof_class_index={spoof_class_index}_not_official_default_0"
    else:
        source = ""
        warning = audit["class_convention_warning"] or "unverified_class_mapping"

    # Index 0/1 are fixed model output positions; names follow which index is spoof.
    class_names_by_index = {
        0: "spoof" if spoof_class_index == 0 else "bonafide",
        1: "bonafide" if spoof_class_index == 0 else "spoof",
    }

    return {
        "spoof_class_index_used": spoof_class_index,
        "bonafide_class_index_used": bonafide_class_index,
        "class_0_name": class_names_by_index[0],
        "class_1_name": class_names_by_index[1],
        "class_convention_source": source,
        "class_convention_warning": warning,
        "class_convention_audit_notes": "; ".join(audit.get("notes", [])),
        "official_eval_bonafide_index": OFFICIAL_BONAFIDE_CLASS_INDEX,
        "spoof_score_definition": f"softmax(class_{spoof_class_index})",
        "bonafide_score_definition": f"softmax(class_{bonafide_class_index})",
    }


def load_aasist_config(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    if "model_config" not in config:
        raise ValueError("config missing model_config")
    return config, config["model_config"]


def load_aasist_model(
    aasist_src: Path,
    config_path: Path,
    checkpoint_path: Path | None,
    device: str,
    spoof_class_index: int = OFFICIAL_SPOOF_CLASS_INDEX,
) -> tuple[Any, dict[str, Any]]:
    import torch

    config, model_config = load_aasist_config(config_path)
    convention = build_class_convention_fields(spoof_class_index, aasist_src, user_override=False)

    meta: dict[str, Any] = {
        "config_path": str(config_path),
        "checkpoint_path": str(checkpoint_path) if checkpoint_path else None,
        "class_convention": convention,
    }
    path_notes = add_aasist_src_to_path(aasist_src)
    meta["sys_path_notes"] = path_notes

    mod = importlib.import_module(OFFICIAL_MODEL_MODULE)
    ModelCls = getattr(mod, OFFICIAL_MODEL_CLASS)
    model = ModelCls(model_config)

    dev = device if device == "cuda" and torch.cuda.is_available() else "cpu"
    model = model.to(dev)
    model.eval()
    meta["device"] = dev
    meta["nb_samp"] = int(model_config.get("nb_samp", 64600))

    if checkpoint_path and checkpoint_path.is_file():
        try:
            try:
                ckpt = torch.load(str(checkpoint_path), map_location=dev, weights_only=False)
            except TypeError:
                ckpt = torch.load(str(checkpoint_path), map_location=dev)
            state = ckpt
            if isinstance(ckpt, dict):
                for key in ("model_state_dict", "state_dict", "model"):
                    if key in ckpt and isinstance(ckpt[key], dict):
                        state = ckpt[key]
                        meta["checkpoint_state_key"] = key
                        break
            incompatible = model.load_state_dict(state, strict=False)
            meta["checkpoint_load"] = {
                "status": "loaded",
                "missing_keys_count": len(incompatible.missing_keys),
                "unexpected_keys_count": len(incompatible.unexpected_keys),
            }
        except Exception as e:  # noqa: BLE001
            meta["checkpoint_load"] = {"status": "failed", "error": repr(e)}
    else:
        meta["checkpoint_load"] = {"status": "not_provided"}

    return model, meta


def _resample_waveform(wav: np.ndarray, sr: int, target_sr: int, meta: dict[str, Any]) -> np.ndarray:
    if int(sr) == int(target_sr):
        return wav.astype(np.float32)
    try:
        import torch
        import torchaudio  # type: ignore[import-untyped]

        wav_t = torch.from_numpy(wav.astype(np.float32))
        out = torchaudio.functional.resample(wav_t, int(sr), int(target_sr))
        meta["resampled"] = True
        return out.cpu().numpy().astype(np.float32)
    except Exception as e:  # noqa: BLE001
        meta["resample_note"] = repr(e)
        ratio = target_sr / float(sr)
        new_len = int(len(wav) * ratio)
        return np.interp(
            np.linspace(0, len(wav) - 1, new_len),
            np.arange(len(wav)),
            wav.astype(np.float64),
        ).astype(np.float32)


def load_audio_mono_16k(audio_path: Path, target_sr: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Load mono float32 waveform at target_sr.

    Fallback order: torchaudio -> librosa -> soundfile.
    On failure raises ValueError with loader_error_chain in the message.
    """
    meta: dict[str, Any] = {"path": str(audio_path), "loader_error_chain": []}
    wav: np.ndarray | None = None
    sr: int | None = None

    # 1) torchaudio (handles many formats including MP4 when ffmpeg backend available)
    try:
        import torchaudio  # type: ignore[import-untyped]

        x, sr_in = torchaudio.load(str(audio_path))
        if x.shape[0] > 1:
            x = x.mean(dim=0, keepdim=True)
        wav = x.squeeze(0).cpu().numpy().astype(np.float32)
        sr = int(sr_in)
        meta["loader"] = "torchaudio"
        meta["loader_error_chain"].append("torchaudio:ok")
    except Exception as e:  # noqa: BLE001
        meta["loader_error_chain"].append(f"torchaudio:{e!r}")

    # 2) librosa (strong MP4 / codec fallback)
    if wav is None:
        try:
            import librosa  # type: ignore[import-untyped]

            y, sr_in = librosa.load(str(audio_path), sr=target_sr, mono=True)
            wav = np.asarray(y, dtype=np.float32)
            sr = int(sr_in)
            meta["loader"] = "librosa"
            meta["resampled"] = True
            meta["loader_error_chain"].append("librosa:ok")
        except Exception as e:  # noqa: BLE001
            meta["loader_error_chain"].append(f"librosa:{e!r}")

    # 3) soundfile (WAV/FLAC/OGG; often fails on MP4)
    if wav is None:
        try:
            import soundfile as sf

            data, sr_in = sf.read(str(audio_path), dtype="float32")
            if data.ndim > 1:
                data = data.mean(axis=1)
            wav = data.astype(np.float32)
            sr = int(sr_in)
            meta["loader"] = "soundfile"
            meta["loader_error_chain"].append("soundfile:ok")
        except Exception as e:  # noqa: BLE001
            meta["loader_error_chain"].append(f"soundfile:{e!r}")

    if wav is None or sr is None:
        chain = " -> ".join(meta["loader_error_chain"])
        raise ValueError(f"audio_load_failed:{audio_path}: {chain}")

    if meta.get("loader") != "librosa":
        wav = _resample_waveform(wav, sr, target_sr, meta)
        meta["original_sample_rate"] = int(sr)
    else:
        meta["original_sample_rate"] = int(sr)

    meta["sample_rate"] = target_sr
    meta["num_samples"] = int(len(wav))
    meta["duration_sec"] = len(wav) / target_sr
    meta["loader_error_chain"] = " -> ".join(meta["loader_error_chain"])
    return wav, meta


def load_audio_for_aasist(audio_path: Path, target_sr: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, dict[str, Any]]:
    """Alias for AASIST integration entry point."""
    return load_audio_mono_16k(audio_path, target_sr=target_sr)


def generate_window_starts(
    num_samples: int,
    nb_samp: int,
    hop: int,
    suspicious_start: float | None = None,
    suspicious_end: float | None = None,
    sample_rate: int = TARGET_SAMPLE_RATE,
) -> tuple[list[int], dict[str, Any]]:
    """
    Sliding windows plus optional suspicious-region coverage.
    Returns (start_indexes, meta) where meta includes suspicious_region_window_included.
    """
    window_meta: dict[str, Any] = {
        "suspicious_region_window_included": False,
        "suspicious_extra_starts_added": [],
    }

    if num_samples <= 0:
        return [0], window_meta
    if num_samples <= nb_samp:
        return [0], window_meta

    base_starts = list(range(0, max(1, num_samples - nb_samp + 1), hop))
    if not base_starts:
        base_starts = [0]
    last = num_samples - nb_samp
    if last > 0 and base_starts[-1] != last:
        base_starts.append(last)

    starts = list(base_starts)

    if suspicious_start is not None and suspicious_end is not None:
        try:
            s_sec = float(suspicious_start)
            e_sec = float(suspicious_end)
            if e_sec > s_sec:
                center = int(((s_sec + e_sec) / 2.0) * sample_rate)
                center_start = max(0, min(center - nb_samp // 2, max(0, num_samples - nb_samp)))
                region_start = max(0, int(s_sec * sample_rate))
                region_start = min(region_start, max(0, num_samples - nb_samp))

                for extra_start, label in (
                    (center_start, "center"),
                    (region_start, "region_start"),
                ):
                    if extra_start not in starts:
                        starts.append(extra_start)
                        window_meta["suspicious_extra_starts_added"].append(
                            {"start_sample": extra_start, "anchor": label}
                        )
                        window_meta["suspicious_region_window_included"] = True
        except (TypeError, ValueError):
            pass

    starts = sorted(set(starts))
    return starts, window_meta


def extract_window(wav: np.ndarray, start: int, nb_samp: int) -> np.ndarray:
    end = start + nb_samp
    if start >= len(wav):
        chunk = np.zeros(nb_samp, dtype=np.float32)
    else:
        chunk = wav[start:end]
        if len(chunk) < nb_samp:
            chunk = np.pad(chunk, (0, nb_samp - len(chunk)))
    return chunk.astype(np.float32)


def extract_aasist_logits(model_output: Any) -> Any:
    """
    Official AASIST forward returns (last_hidden, logits); classifier logits are the last item.
    """
    if isinstance(model_output, (tuple, list)):
        logits = model_output[-1]
    else:
        logits = model_output
    if logits.ndim != 2 or logits.shape[1] != 2:
        raise ValueError(f"AASIST classifier output shape invalid: {tuple(logits.shape)}")
    return logits


def infer_window_probabilities(
    model: Any,
    windows: list[np.ndarray],
    device: str,
    batch_size: int,
    spoof_class_index: int = OFFICIAL_SPOOF_CLASS_INDEX,
) -> list[dict[str, float]]:
    """Per-window softmax probabilities and derived spoof/bonafide scores."""
    import torch

    bonafide_class_index = 1 - spoof_class_index
    dev = device if device == "cuda" and torch.cuda.is_available() else "cpu"
    out: list[dict[str, float]] = []
    model.eval()

    with torch.no_grad():
        for i in range(0, len(windows), batch_size):
            batch = windows[i : i + batch_size]
            x = torch.stack([torch.from_numpy(w) for w in batch]).to(dev)
            logits = extract_aasist_logits(model(x))
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()
            for row in probs:
                p0 = float(row[0])
                p1 = float(row[1])
                spoof_score = p0 if spoof_class_index == 0 else p1
                bonafide_score = p1 if bonafide_class_index == 1 else p0
                out.append(
                    {
                        "prob_class_0": p0,
                        "prob_class_1": p1,
                        "spoof_score": spoof_score,
                        "bonafide_score": bonafide_score,
                    }
                )
    return out


def compute_partial_region_metrics(
    windows: list[dict],
    suspicious_start: float | None,
    suspicious_end: float | None,
    threshold: float,
) -> dict[str, Any]:
    """
    Partial fabrication metrics using ALL windows (not threshold-filtered).
    """
    empty = {
        "n_windows_inside_region": 0,
        "n_windows_outside_region": 0,
        "inside_region_avg_spoof": "",
        "outside_region_avg_spoof": "",
        "inside_region_max_spoof": "",
        "outside_region_max_spoof": "",
        "region_delta": "",
        "partial_region_detected": None,
    }
    if suspicious_start is None or suspicious_end is None:
        return empty
    try:
        s_sec = float(suspicious_start)
        e_sec = float(suspicious_end)
    except (TypeError, ValueError):
        return empty
    if e_sec <= s_sec:
        return empty

    inside = [w for w in windows if w["end_time"] > s_sec and w["start_time"] < e_sec]
    outside = [w for w in windows if w["end_time"] <= s_sec or w["start_time"] >= e_sec]

    if not inside:
        return {
            **empty,
            "n_windows_inside_region": 0,
            "n_windows_outside_region": len(outside),
            "partial_region_detected": False,
        }

    inside_scores = [float(w["spoof_score"]) for w in inside]
    outside_scores = [float(w["spoof_score"]) for w in outside] if outside else []

    inside_avg = float(np.mean(inside_scores))
    inside_max = float(np.max(inside_scores))
    outside_avg = float(np.mean(outside_scores)) if outside_scores else 0.0
    outside_max = float(np.max(outside_scores)) if outside_scores else 0.0
    region_delta = inside_avg - outside_avg

    detected = (
        inside_max >= threshold
        or region_delta >= PARTIAL_REGION_DELTA_MIN
        or inside_avg >= outside_avg + PARTIAL_REGION_DELTA_MIN
    )

    return {
        "n_windows_inside_region": len(inside),
        "n_windows_outside_region": len(outside),
        "inside_region_avg_spoof": inside_avg,
        "outside_region_avg_spoof": outside_avg,
        "inside_region_max_spoof": inside_max,
        "outside_region_max_spoof": outside_max,
        "region_delta": region_delta,
        "partial_region_detected": bool(detected),
    }


def check_run_readiness(
    *,
    aasist_src: Path,
    config_path: Path,
    checkpoint_path: Path,
    eval_manifest: Path,
    output_dir: Path,
    spoof_class_index: int,
) -> tuple[bool, dict[str, Any]]:
    """Pre-flight checks before inference loop."""
    report: dict[str, Any] = {
        "checks": {},
        "class_convention": build_class_convention_fields(
            spoof_class_index, aasist_src, user_override=(spoof_class_index != OFFICIAL_SPOOF_CLASS_INDEX)
        ),
    }
    checks = report["checks"]

    checks["aasist_src_exists"] = aasist_src.is_dir()
    checks["config_exists"] = config_path.is_file()
    checks["checkpoint_exists"] = checkpoint_path.is_file()
    checks["eval_manifest_exists"] = eval_manifest.is_file()
    checks["output_dir_writable"] = False
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["output_dir_writable"] = True
    except OSError:
        checks["output_dir_writable"] = False

    convention = report["class_convention"]
    checks["class_convention_detected"] = bool(
        convention.get("class_convention_source") or convention.get("class_convention_audit_notes")
    )
    checks["class_convention_verified"] = convention.get("class_convention_source") == "official_aasist_label_mapping"

    critical = [
        "aasist_src_exists",
        "config_exists",
        "checkpoint_exists",
        "eval_manifest_exists",
        "output_dir_writable",
    ]
    ready = all(checks.get(k) for k in critical)
    report["ready"] = ready
    return ready, report


def _to_float(value, default=None):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    s = str(value).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _parse_bool(value) -> bool | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y"):
        return True
    if s in ("0", "false", "no", "n"):
        return False
    return None


def evaluate_aasist_status(row: dict) -> str:
    """Mirror Phase 7C1 baseline status logic using AASIST spoof scores."""
    err = row.get("error")
    if err is not None and str(err).strip() != "":
        return "unknown_review_required"

    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    spoof_score = _to_float(row.get("mean_spoof_score"), 0.0) or 0.0
    threshold = _to_float(row.get("threshold_used"), 0.5) or 0.5
    max_spoof = _to_float(row.get("max_spoof_score", row.get("max_window_spoof")))
    ratio = _to_float(row.get("suspicious_window_ratio"), 0.0) or 0.0
    borderline = abs(spoof_score - threshold) <= BORDERLINE_MARGIN
    partial_bin = _parse_bool(row.get("partial_fabrication_binary"))

    pred_fake = spoof_score >= threshold
    manipulation_detected = (
        spoof_score >= MANIPULATION_DETECT_SCORE
        or (max_spoof is not None and max_spoof >= SEGMENT_SUSPICIOUS_MAX_SPOOF)
        or ratio >= SEGMENT_SUSPICIOUS_RATIO
    )
    segment_suspicious = (max_spoof is not None and max_spoof >= SEGMENT_SUSPICIOUS_MAX_SPOOF) or (
        ratio >= SEGMENT_SUSPICIOUS_RATIO
    )

    if partial_bin is True or manip == "partial_ai_insert":
        s_start = _to_float(row.get("suspicious_start_time"))
        s_end = _to_float(row.get("suspicious_end_time"))
        if s_start is None or s_end is None or s_end <= s_start:
            return "partial_fabrication_not_evaluable"
        if _parse_bool(row.get("partial_region_detected")) is True:
            return "partial_fabrication_detected"
        return "partial_fabrication_missed"

    if manip == "clean_direct" and gt_origin == "human":
        if borderline:
            return "clean_human_borderline"
        if not pred_fake:
            return "clean_human_accepted"
        return "clean_human_false_alarm"

    if manip == "clean_direct" and gt_origin == "ai":
        if pred_fake:
            return "direct_ai_detected"
        if not pred_fake and segment_suspicious:
            return "direct_ai_file_level_missed_but_segment_suspicious"
        if not pred_fake:
            return "direct_ai_missed"
        return "borderline_needs_review"

    if manip == "human_replay":
        return "human_replay_manipulation_detected" if manipulation_detected else "human_replay_missed"

    if manip == "ai_replay":
        if pred_fake or spoof_score >= MANIPULATION_DETECT_SCORE:
            return "ai_replay_detected"
        if segment_suspicious:
            return "ai_replay_file_level_missed_but_segment_suspicious"
        return "ai_replay_missed"

    if manip == "mixer_processed" and gt_origin == "human":
        return "human_mixer_manipulation_detected" if manipulation_detected else "human_mixer_missed"

    if manip == "mixer_processed" and gt_origin == "ai":
        if pred_fake or spoof_score >= MANIPULATION_DETECT_SCORE:
            return "ai_mixer_detected"
        if segment_suspicious:
            return "ai_mixer_file_level_missed_but_segment_suspicious"
        return "ai_mixer_missed"

    # Phase 7A channel/processed variants
    processed_manips = ("whatsapp_compressed", "youtube_broadcast", "phone_recorded", "noisy_room")
    if manip in processed_manips:
        if gt_origin == "human":
            return "human_processed_detected" if manipulation_detected else "human_processed_missed"
        if gt_origin == "ai":
            if pred_fake or spoof_score >= MANIPULATION_DETECT_SCORE:
                return "ai_processed_detected"
            if segment_suspicious:
                return "ai_processed_file_level_missed_but_segment_suspicious"
            return "ai_processed_missed"

    if borderline:
        return "borderline_needs_review"
    return "unknown_review_required"


def map_expected_risk_fields(
    manipulation_type: str,
    source_origin: str,
    ground_truth_manipulation: str,
    partial_fabrication_binary: Any = None,
) -> tuple[str, str, str]:
    manip = str(manipulation_type or "").strip().lower()
    origin = str(source_origin or "").strip().lower()
    gt_manip = str(ground_truth_manipulation or "").strip().lower()
    partial = _parse_bool(partial_fabrication_binary)

    if partial is True or manip in ("partial_ai_insert", "edited_spliced", "edited_or_spliced"):
        return "1", "partial_fabrication", "forensic-risk positive; partial/splice — not pure origin label"

    if manip == "clean_direct" and origin == "human" and gt_manip in ("clean", ""):
        return "0", "clean_human", "low-risk clean human speech"

    if manip == "clean_direct" and origin == "ai":
        return "1", "direct_ai", "direct synthetic/spoof evidence"

    if manip == "human_replay":
        return "1", "human_replay", "human-origin replay/rerecording risk"

    if manip == "ai_replay":
        return "1", "ai_replay", "AI-origin with replay chain risk"

    if manip == "mixer_processed":
        return "1", "human_mixer" if origin == "human" else "ai_mixer", "channel/mixer processing risk"

    if manip in ("whatsapp_compressed", "youtube_broadcast", "phone_recorded", "noisy_room"):
        if origin == "ai":
            return "1", "ai_processed", "AI with channel/platform processing"
        return "1", "human_processed", "human-origin with channel/platform processing"

    if manip in ("edited_spliced", "spliced"):
        return "1", "edited_spliced", "editing/splice risk"

    if gt_manip in ("clean",) and origin == "human":
        return "0", "clean_human", "inferred clean human"

    if gt_manip in ("replayed", "processed", "mixed"):
        return "1", "manipulation_risk", f"inferred from ground_truth_manipulation={gt_manip}"

    return "", "needs_review", "could not infer expected risk — manual review"
