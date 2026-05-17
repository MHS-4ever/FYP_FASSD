"""
Phase 6: Generate explanations for the Phase 4 hybrid model on raw audio files.

Supports:
- Raw audio folder/file inference (e.g., `testing_audios/Trump`)
- Optional manifest mode (validate explanations on a labeled manifest with `filepath` column)

Core behavior:
- On-the-fly feature extraction per chunk:
  - Log-mel spectrogram: 64x400 using the SAME parameters as Phase 2 extraction
  - Environmental features: 12-D using `EnvironmentalFeatureExtractor`
- Chunking for long audio (defaults tuned to match training window: 4s chunks)
- Aggregate chunk predictions by mean spoof probability and mean attack probabilities
- Outputs per-file JSON explanations + overall CSV summary
"""

import argparse
import json
import os
import sys
from pathlib import Path

import librosa
import numpy as np
import torch
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from features.environmental_features import EnvironmentalFeatureExtractor


# Attack type mapping (must match Phase 4/5)
ATTACK_TYPE_NAMES = ["bonafide", "synthesis", "conversion", "replay"]


# Log-mel extraction parameters (must match Phase 2 extraction: `code/phase2/extract_spectrogram_features.py`)
SAMPLE_RATE = 16000
N_FFT = 512
HOP_LENGTH = 160  # 10ms at 16kHz
WIN_LENGTH = 400  # 25ms at 16kHz
N_MELS = 64
TARGET_FRAMES = 400  # fixed length for model input


def extract_logmel(
    y,
    sr=SAMPLE_RATE,
    n_mels=N_MELS,
    n_fft=N_FFT,
    hop_length=HOP_LENGTH,
    win_length=WIN_LENGTH,
    target_frames=TARGET_FRAMES,
):
    """
    Match Phase 2 log-mel extraction params (IMPORTANT for checkpoint compatibility).

    Returns:
        logmel_norm: [64, 400] float32 (per-sample normalized, same as Phase 4 dataset)
        logmel_raw:  [64, 400] float32 (no per-sample normalization; for optional analysis)
    """
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        n_mels=n_mels,
        power=2.0,
    )
    logmel = librosa.power_to_db(mel, ref=np.max).astype(np.float32)

    # Phase 2 behavior: truncate to first 400 frames (or pad)
    T = logmel.shape[1]
    if T < target_frames:
        logmel = np.pad(logmel, ((0, 0), (0, target_frames - T)), mode="constant", constant_values=0)
    elif T > target_frames:
        logmel = logmel[:, :target_frames]

    logmel_raw = logmel

    # per-sample norm (matches Phase 4 datasets)
    mean = float(logmel.mean())
    std = float(logmel.std()) + 1e-5
    logmel_norm = (logmel - mean) / std

    return logmel_norm.astype(np.float32), logmel_raw.astype(np.float32)


def _env_vector_from_dict(env_dict):
    # Must match EnvironmentalFeatureExtractor.extract_vector order
    return np.array(
        [
            env_dict.get("rt60", 0.0),
            env_dict.get("drr", 0.0),
            env_dict.get("snr", 0.0),
            env_dict.get("background_level", -100.0),
            env_dict.get("silence_ratio", 0.0),
            env_dict.get("spectral_tilt", 0.0),
            env_dict.get("spectral_flatness", 0.0),
            (env_dict.get("spectral_rolloff", 0.0) / 1000.0),
            env_dict.get("cleanliness_score", 0.0),
            env_dict.get("high_freq_content", 0.0),
            env_dict.get("background_consistency", 0.5),
            env_dict.get("env_stability", 0.5),
        ],
        dtype=np.float32,
    )


def extract_env_features(extractor: EnvironmentalFeatureExtractor, audio_path: str, y: np.ndarray | None = None):
    """
    Returns:
        env_raw_dict: dict with human-readable keys
        env_vec_norm: [12] float32 used for the model (per-sample normalized, like Phase 4)
    """
    if y is None:
        env_raw_dict = extractor.extract_all(audio_path)
    else:
        # Avoid duplicate file reads by reusing the loaded waveform.
        # EnvironmentalFeatureExtractor doesn't expose a direct method, so we emulate its behavior:
        # - This mirrors `extract_all()` but on waveform.
        # (Keeps Phase 6 fast without changing Phase 2/4 code.)
        # NOTE: This branch may diverge slightly from `extract_all()` if that method changes.
        env_raw_dict = {}
        env_raw_dict["rt60"] = extractor.compute_rt60(y)
        env_raw_dict["drr"] = extractor.compute_drr(y)
        env_raw_dict["snr"] = extractor.compute_snr(y)
        env_raw_dict["background_level"] = extractor.compute_background_level(y)
        env_raw_dict["silence_ratio"] = extractor.compute_silence_ratio(y)
        env_raw_dict["spectral_tilt"] = extractor.compute_spectral_tilt(y)
        env_raw_dict["spectral_flatness"] = extractor.compute_spectral_flatness(y)
        env_raw_dict["spectral_rolloff"] = extractor.compute_spectral_rolloff(y)
        env_raw_dict["cleanliness_score"] = extractor.compute_cleanliness(y)
        env_raw_dict["high_freq_content"] = extractor.compute_high_freq_content(y)
        env_raw_dict["background_consistency"] = extractor.compute_background_consistency(y)
        env_raw_dict["env_stability"] = extractor.compute_env_stability(y)

    env_vec = _env_vector_from_dict(env_raw_dict).astype(np.float32, copy=False)

    # per-sample norm (matches Phase 4 dataset normalization)
    mean = float(env_vec.mean())
    std = float(env_vec.std()) + 1e-5
    env_vec_norm = (env_vec - mean) / std

    return env_raw_dict, env_vec_norm.astype(np.float32)


def chunk_audio(y, sr, chunk_duration=4.0, overlap=1.0):
    chunk_len = int(chunk_duration * sr)
    hop = int((chunk_duration - overlap) * sr)
    if hop <= 0:
        hop = chunk_len
    if len(y) <= chunk_len:
        return [{"audio": y, "start_sec": 0.0, "end_sec": len(y) / max(sr, 1)}]
    chunks = []
    for start in range(0, len(y) - chunk_len + 1, hop):
        end = start + chunk_len
        chunks.append(
            {
                "audio": y[start:end],
                "start_sec": float(start / sr),
                "end_sec": float(end / sr),
            }
        )
    if not chunks:
        chunks = [{"audio": y, "start_sec": 0.0, "end_sec": len(y) / max(sr, 1)}]
    return chunks


def _speech_ratio_rms_threshold(chunk: np.ndarray, threshold_rms: float):
    """Ratio of chunk RMS frames above a fixed RMS threshold."""
    if chunk.size == 0:
        return 0.0
    rms = librosa.feature.rms(y=chunk, frame_length=WIN_LENGTH, hop_length=HOP_LENGTH)[0]
    if rms.size == 0:
        return 0.0
    return float(np.mean(rms > float(threshold_rms)))


def _speech_ratio_db_threshold(chunk: np.ndarray, db_threshold: float):
    """Ratio of chunk RMS frames above an absolute dB threshold."""
    if chunk.size == 0:
        return 0.0
    rms = librosa.feature.rms(y=chunk, frame_length=WIN_LENGTH, hop_length=HOP_LENGTH)[0]
    if rms.size == 0:
        return 0.0
    rms_db = librosa.amplitude_to_db(rms + 1e-12, ref=1.0)
    return float(np.mean(rms_db > float(db_threshold)))


def _trimmed_mean(values: np.ndarray, trim_frac: float):
    if values.size == 0:
        return 0.5
    if trim_frac <= 0.0:
        return float(values.mean())
    trim_n = int(round(trim_frac * values.size))
    if trim_n <= 0 or values.size <= 2 * trim_n:
        return float(values.mean())
    s = np.sort(values)
    return float(s[trim_n:-trim_n].mean())


def _aggregate_env_dicts(env_dicts: list[dict]):
    """Aggregate per-chunk env dicts with robust medians for file-level explanation."""
    if not env_dicts:
        return {}
    keys = list(env_dicts[0].keys())
    out = {}
    for k in keys:
        vals = [float(d.get(k, 0.0)) for d in env_dicts]
        out[k] = float(np.median(np.asarray(vals, dtype=np.float32)))
    return out


def _env_reasoning(env: dict):
    """
    Heuristic, human-readable reasoning based on EnvironmentalFeatureExtractor docs.
    These are explanations for users, not guaranteed to be the true model attribution.
    """
    reasons = []

    rt60 = float(env.get("rt60", 0.0))
    snr = float(env.get("snr", 0.0))
    bg = float(env.get("background_level", -100.0))
    clean = float(env.get("cleanliness_score", 0.0))
    silence_ratio = float(env.get("silence_ratio", 0.0))
    bg_cons = float(env.get("background_consistency", 0.5))

    # Suspicious “too clean” patterns
    if snr > 50:
        reasons.append(f"SNR is extremely high ({snr:.1f} dB) → audio is unusually clean (often suspicious).")
    elif snr > 40:
        reasons.append(f"SNR is high ({snr:.1f} dB) → audio is very clean compared to typical recordings.")

    if bg < -70:
        reasons.append(f"Background level is very low ({bg:.1f} dB) → near-silent ambience (often suspicious).")

    if clean >= 0.6:
        reasons.append(f"Cleanliness score is high ({clean:.2f}) → audio may be 'too perfect' for natural speech.")

    # Room acoustics plausibility
    if rt60 == 0.0:
        reasons.append("RT60 ≈ 0.0s → little/no measurable reverberation (can indicate synthetic or heavily processed audio).")
    elif rt60 < 0.15:
        reasons.append(f"RT60 is very low ({rt60:.2f}s) → unusually dry room response (potentially suspicious).")
    elif 0.2 <= rt60 <= 2.0:
        reasons.append(f"RT60 is in a natural range ({rt60:.2f}s) → consistent with real room acoustics.")

    # Consistency / stability
    if bg_cons < 0.6:
        reasons.append(f"Background consistency is low ({bg_cons:.2f}) → suggests edits or inconsistent environment.")

    if silence_ratio > 0.35:
        reasons.append(f"Silence ratio is high ({silence_ratio:.2%}) → unusual pauses/silence patterns.")

    if not reasons:
        reasons.append("Environmental features look broadly plausible; no strong anomalies detected.")

    return reasons


def _spec_reasoning(n_chunks: int, spoof_probs: np.ndarray):
    reasons = []
    if n_chunks <= 1:
        reasons.append("Audio fits into one chunk; decision is based on a single 4s window.")
        return reasons

    pmin = float(np.min(spoof_probs))
    pmax = float(np.max(spoof_probs))
    pstd = float(np.std(spoof_probs))

    reasons.append(f"Chunk consistency: spoof prob range [{pmin:.3f}, {pmax:.3f}] across {n_chunks} chunks.")
    if pstd > 0.15:
        reasons.append("Chunk scores vary a lot → the model is uncertain or the audio contains mixed-quality segments.")
    else:
        reasons.append("Chunk scores are consistent → model decision is stable across the file.")

    return reasons


def predict_file(path, model, device, args, env_extractor: EnvironmentalFeatureExtractor):
    y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    chunks = chunk_audio(y, sr, args.chunk_duration, args.overlap)

    # VAD/speech gating to reduce long-audio pollution from non-speech chunks.
    # NOTE: chunk-local percentile thresholds produce near-constant ratios and weak filtering,
    # so we use either (a) file-level percentile RMS threshold, or (b) absolute dB threshold.
    speech_ratios = []
    vad_threshold_info = {}
    if args.vad_mode == "file_percentile":
        file_rms = librosa.feature.rms(y=y, frame_length=WIN_LENGTH, hop_length=HOP_LENGTH)[0]
        if file_rms.size == 0:
            file_thr = 0.0
        else:
            file_thr = float(np.percentile(file_rms, args.vad_rms_percentile))
        speech_ratios = [_speech_ratio_rms_threshold(c["audio"], file_thr) for c in chunks]
        vad_threshold_info = {
            "vad_mode": args.vad_mode,
            "vad_rms_percentile": float(args.vad_rms_percentile),
            "vad_file_rms_threshold": float(file_thr),
        }
    else:  # abs_db
        speech_ratios = [_speech_ratio_db_threshold(c["audio"], args.vad_db_threshold) for c in chunks]
        vad_threshold_info = {
            "vad_mode": args.vad_mode,
            "vad_db_threshold": float(args.vad_db_threshold),
        }

    keep_mask = np.asarray(speech_ratios, dtype=np.float32) >= float(args.vad_min_speech_ratio)
    chunks_used = [c for c, keep in zip(chunks, keep_mask) if keep]
    speech_used = [float(r) for r, keep in zip(speech_ratios, keep_mask) if keep]
    vad_fallback_all = False
    if len(chunks_used) == 0:
        # Fallback so we never return empty predictions.
        chunks_used = chunks
        speech_used = [float(r) for r in speech_ratios]
        vad_fallback_all = True

    spoof_probs = []
    spoof_logits = []
    attack_probs = []
    env_raw_chunks = []

    for i in range(0, len(chunks_used), args.batch_size):
        batch_chunks = chunks_used[i:i + args.batch_size]
        batch_audio = [c["audio"] for c in batch_chunks]
        logmels_norm = [extract_logmel(ca, sr=sr)[0] for ca in batch_audio]
        env_raw_norm = [extract_env_features(env_extractor, path, y=ca) for ca in batch_audio]
        env_raw_batch = [x[0] for x in env_raw_norm]
        env_norm_batch = [x[1] for x in env_raw_norm]
        env_raw_chunks.extend(env_raw_batch)

        spec = torch.from_numpy(np.stack(logmels_norm)).unsqueeze(1).float().to(device)
        env = torch.from_numpy(np.stack(env_norm_batch)).float().to(device)
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                bin_logits, mc_logits = model(spec, env)
                bin_probs = torch.softmax(bin_logits, dim=1)[:, 1]  # spoof prob per chunk
                mc_probs = torch.softmax(mc_logits, dim=1)          # attack probs
        spoof_probs.append(bin_probs.cpu().numpy())
        spoof_logits.append(bin_logits.detach().cpu().numpy())
        attack_probs.append(mc_probs.cpu().numpy())

    spoof_probs = np.concatenate(spoof_probs)
    spoof_logits = np.concatenate(spoof_logits)  # [N, 2]
    attack_probs = np.concatenate(attack_probs)

    spoof_mean = float(spoof_probs.mean())
    spoof_median = float(np.median(spoof_probs))
    spoof_trimmed = float(_trimmed_mean(spoof_probs, args.trim_fraction))
    pct_chunks_above_chunk_threshold = float(np.mean(spoof_probs >= args.chunk_threshold))
    # Logit-mean pooling: average logits across chunks, then softmax.
    mean_logits = spoof_logits.mean(axis=0)
    max_logit = float(np.max(mean_logits))
    exp_logits = np.exp(mean_logits - max_logit)
    spoof_logit_mean = float(exp_logits[1] / np.sum(exp_logits))

    if args.pooling == "mean":
        decision_score = spoof_mean
    elif args.pooling == "median":
        decision_score = spoof_median
    elif args.pooling == "trimmed_mean":
        decision_score = spoof_trimmed
    elif args.pooling == "logit_mean":
        decision_score = spoof_logit_mean
    elif args.pooling == "pct_vote":
        # Here decision_score is vote ratio [0, 1].
        decision_score = pct_chunks_above_chunk_threshold
    else:
        decision_score = spoof_median

    attack_mean = attack_probs.mean(axis=0)  # [4]
    attack_idx = int(np.argmax(attack_mean))
    attack_conf = float(attack_mean[attack_idx])
    attack_name = ATTACK_TYPE_NAMES[attack_idx] if 0 <= attack_idx < len(ATTACK_TYPE_NAMES) else str(attack_idx)

    effective_threshold = float(args.vote_threshold if args.pooling == "pct_vote" else args.threshold)
    prediction = "FAKE" if decision_score >= effective_threshold else "REAL"
    confidence = decision_score if prediction == "FAKE" else (1.0 - decision_score)

    env_raw = _aggregate_env_dicts(env_raw_chunks)
    env_reasons = _env_reasoning(env_raw)
    spec_reasons = _spec_reasoning(len(chunks_used), spoof_probs)
    spec_reasons.append(
        f"Pooling={args.pooling}: mean={spoof_mean:.3f}, median={spoof_median:.3f}, trimmed={spoof_trimmed:.3f}, "
        f"logit_mean={spoof_logit_mean:.3f}, pct_over_chunk_threshold={pct_chunks_above_chunk_threshold:.3f}"
    )
    if args.vad_min_speech_ratio > 0:
        spec_reasons.append(
            f"VAD({args.vad_mode}) kept {len(chunks_used)}/{len(chunks)} chunks (min speech ratio={args.vad_min_speech_ratio:.2f})."
        )
    if vad_fallback_all:
        spec_reasons.append("VAD fallback activated: no chunk passed gate, so all chunks were used.")
    if args.pooling == "pct_vote":
        spec_reasons.append(
            f"pct_vote thresholds: chunk_threshold={args.chunk_threshold:.3f}, vote_threshold={args.vote_threshold:.3f}."
        )

    # Overall explanation (simple + readable)
    if prediction == "FAKE":
        overall = (
            f"Model predicts FAKE (decision_score={decision_score:.3f}, pooling={args.pooling}, "
            f"threshold={effective_threshold:.3f}). "
            f"Most likely attack type: {attack_name} (conf={attack_conf:.3f})."
        )
    else:
        overall = (
            f"Model predicts REAL (bonafide) with confidence={confidence:.3f} "
            f"(pooling={args.pooling}, threshold={effective_threshold:.3f})."
        )

    chunk_timeline = []
    chunk_timeline_includes_all = False
    if getattr(args, "save_chunk_timeline", False):
        used_idx = 0
        for i, (c, keep, speech_ratio) in enumerate(zip(chunks, keep_mask, speech_ratios)):
            entry = {
                "chunk_index": int(i),
                "start_time": float(c["start_sec"]),
                "end_time": float(c["end_sec"]),
                "vad_kept": bool(keep),
                "speech_ratio": float(speech_ratio),
            }
            if keep:
                ap = attack_probs[used_idx]
                atk_idx = int(np.argmax(ap))
                entry.update(
                    {
                        "evaluated": True,
                        "spoof_probability": float(spoof_probs[used_idx]),
                        "attack_probs": [float(x) for x in ap.tolist()],
                        "attack_type": ATTACK_TYPE_NAMES[atk_idx]
                        if 0 <= atk_idx < len(ATTACK_TYPE_NAMES)
                        else str(atk_idx),
                        "env_features": env_raw_chunks[used_idx] if used_idx < len(env_raw_chunks) else {},
                    }
                )
                used_idx += 1
            else:
                entry.update(
                    {
                        "evaluated": False,
                        "spoof_probability": None,
                        "attack_probs": None,
                        "attack_type": None,
                        "env_features": None,
                    }
                )
            chunk_timeline.append(entry)
        chunk_timeline_includes_all = len(chunk_timeline) == len(chunks)

    if args.debug_chunk_stats:
        rt60_vals = np.array([float(d.get("rt60", 0.0)) for d in env_raw_chunks], dtype=np.float32)
        snr_vals = np.array([float(d.get("snr", 0.0)) for d in env_raw_chunks], dtype=np.float32)
        sil_vals = np.array([float(d.get("silence_ratio", 0.0)) for d in env_raw_chunks], dtype=np.float32)
        debug_stats = {
            "chunk_spoof_min": float(np.min(spoof_probs)),
            "chunk_spoof_p05": float(np.percentile(spoof_probs, 5)),
            "chunk_spoof_p50": float(np.percentile(spoof_probs, 50)),
            "chunk_spoof_p95": float(np.percentile(spoof_probs, 95)),
            "chunk_spoof_max": float(np.max(spoof_probs)),
            "chunk_spoof_std": float(np.std(spoof_probs)),
            "chunk_rt60_min": float(np.min(rt60_vals)) if rt60_vals.size else 0.0,
            "chunk_rt60_med": float(np.median(rt60_vals)) if rt60_vals.size else 0.0,
            "chunk_rt60_max": float(np.max(rt60_vals)) if rt60_vals.size else 0.0,
            "chunk_snr_min": float(np.min(snr_vals)) if snr_vals.size else 0.0,
            "chunk_snr_med": float(np.median(snr_vals)) if snr_vals.size else 0.0,
            "chunk_snr_max": float(np.max(snr_vals)) if snr_vals.size else 0.0,
            "chunk_silence_ratio_min": float(np.min(sil_vals)) if sil_vals.size else 0.0,
            "chunk_silence_ratio_med": float(np.median(sil_vals)) if sil_vals.size else 0.0,
            "chunk_silence_ratio_max": float(np.max(sil_vals)) if sil_vals.size else 0.0,
        }
    else:
        debug_stats = {}

    return {
        "filename": Path(path).name,
        "filepath": str(Path(path).resolve()),
        "prediction": prediction,
        "confidence": confidence,
        "spoof_prob": decision_score,  # score used for final decision
        "decision_score": decision_score,
        "pooling": args.pooling,
        "spoof_prob_mean": spoof_mean,
        "spoof_prob_median": spoof_median,
        "spoof_prob_trimmed": spoof_trimmed,
        "spoof_prob_logit_mean": spoof_logit_mean,
        "pct_chunks_above_chunk_threshold": pct_chunks_above_chunk_threshold,
        "threshold": float(args.threshold),  # legacy/default threshold for non-pct pooling
        "effective_threshold": float(effective_threshold),
        "chunk_threshold": float(args.chunk_threshold),
        "vote_threshold": float(args.vote_threshold),
        "attack_type": attack_name,
        "attack_type_idx": attack_idx,
        "attack_type_conf": attack_conf,
        "attack_probs": attack_mean.tolist(),
        "n_chunks": int(len(chunks_used)),
        "n_chunks_total": int(len(chunks)),
        "n_chunks_used": int(len(chunks_used)),
        "vad_min_speech_ratio": float(args.vad_min_speech_ratio),
        "vad_rms_percentile": float(args.vad_rms_percentile),
        "vad_mode": str(args.vad_mode),
        "vad_db_threshold": float(args.vad_db_threshold),
        "vad_fallback_all": bool(vad_fallback_all),
        "speech_ratio_mean_used": float(np.mean(speech_used)) if speech_used else 0.0,
        "speech_ratio_median_used": float(np.median(speech_used)) if speech_used else 0.0,
        **vad_threshold_info,
        **debug_stats,
        "chunk_timeline": chunk_timeline,
        "chunk_timeline_includes_all_chunks": chunk_timeline_includes_all,
        "chunk_timeline_note": (
            "All file chunks listed; model scores only on vad_kept/evaluated chunks."
            if chunk_timeline_includes_all
            else (
                "Timeline lists VAD-kept (evaluated) chunks only."
                if chunk_timeline
                else ""
            )
        ),
        "env_features": env_raw,  # raw values (interpretable)
        "env_reasons": env_reasons,
        "spec_reasons": spec_reasons,
        "overall_explanation": overall,
    }


def parse_args():
    p = argparse.ArgumentParser("Phase 6 - Explain Hybrid Model Predictions on Raw Audio")
    p.add_argument("--ckpt", type=str, required=True, help="Phase 4 best checkpoint")
    p.add_argument("--audio_dir", type=str, default="E:/FYP/testing_audios", help="Directory of audio files")
    p.add_argument("--audio_path", type=str, default=None, help="Single audio file (overrides --audio_dir)")
    p.add_argument("--test_manifest", type=str, default=None, help="Optional: CSV manifest with `filepath` column for bulk validation run")
    p.add_argument("--manifest_audio_col", type=str, default="filepath", help="Which column contains audio paths in --test_manifest (default: filepath)")
    p.add_argument("--max_files", type=int, default=None, help="Optional: limit number of files processed (useful for quick tests)")
    p.add_argument("--output_dir", type=str, default="reports/explanation_examples")
    p.add_argument("--chunk_duration", type=float, default=4.0, help="Chunk size in seconds (default 4s to match training window)")
    p.add_argument("--overlap", type=float, default=1.0, help="Chunk overlap in seconds")
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--threshold", type=float, default=0.65, help="Decision threshold (recommend ~0.65 for long real-world audio)")
    p.add_argument(
        "--pooling",
        type=str,
        default="median",
        choices=["median", "trimmed_mean", "mean", "logit_mean", "pct_vote"],
        help="Chunk-to-file pooling strategy for binary spoof score",
    )
    p.add_argument(
        "--trim_fraction",
        type=float,
        default=0.10,
        help="Trim fraction for trimmed_mean pooling (0.10 = drop top/bottom 10%)",
    )
    p.add_argument(
        "--vad_min_speech_ratio",
        type=float,
        default=0.40,
        help="Min speech ratio to keep a chunk (0 disables gating).",
    )
    p.add_argument(
        "--vad_rms_percentile",
        type=float,
        default=30.0,
        help="Percentile used to compute file-level RMS threshold in vad_mode=file_percentile.",
    )
    p.add_argument(
        "--vad_mode",
        type=str,
        default="file_percentile",
        choices=["file_percentile", "abs_db"],
        help="VAD thresholding mode: file-level percentile RMS or absolute dB.",
    )
    p.add_argument(
        "--vad_db_threshold",
        type=float,
        default=-45.0,
        help="Absolute RMS dB threshold when vad_mode=abs_db.",
    )
    p.add_argument(
        "--chunk_threshold",
        type=float,
        default=0.65,
        help="Chunk spoof-prob threshold used by pct_vote pooling.",
    )
    p.add_argument(
        "--vote_threshold",
        type=float,
        default=0.50,
        help="Vote-ratio threshold used by pct_vote pooling.",
    )
    p.add_argument(
        "--debug_chunk_stats",
        action="store_true",
        help="Include per-file chunk distribution stats in CSV/JSON.",
    )
    p.add_argument(
        "--save_chunk_timeline",
        action="store_true",
        help="Include per-chunk timeline (times, spoof prob, attack probs) in JSON output.",
    )
    p.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"])
    return p.parse_args()


def main():
    args = parse_args()

    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"[DEVICE] {device}")
    if device.type == "cuda":
        print(f"[GPU] {torch.cuda.get_device_name(0)}")
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load model
    ckpt = torch.load(args.ckpt, map_location=device, weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    print(f"[OK] Loaded checkpoint: {args.ckpt}")

    # Collect files (priority: --test_manifest > --audio_path > --audio_dir)
    files = []
    manifest_df = None
    if args.test_manifest:
        import pandas as pd

        if not os.path.isfile(args.test_manifest):
            print(f"[ERROR] Manifest not found: {args.test_manifest}")
            return
        manifest_df = pd.read_csv(args.test_manifest, low_memory=False)
        if args.manifest_audio_col not in manifest_df.columns:
            print(f"[ERROR] Manifest missing column: {args.manifest_audio_col}. Available: {list(manifest_df.columns)}")
            return
        filepaths = manifest_df[args.manifest_audio_col].astype(str).tolist()
        files = [Path(fp) for fp in filepaths]
    elif args.audio_path:
        if os.path.isfile(args.audio_path):
            files = [Path(args.audio_path)]
        else:
            print(f"[ERROR] File not found: {args.audio_path}")
            return
    else:
        audio_dir = Path(args.audio_dir)
        # Recursively discover files (users often keep nested folders), case-insensitive on suffix.
        if audio_dir.exists() and audio_dir.is_dir():
            for p in audio_dir.rglob("*"):
                if p.is_file() and p.suffix.lower() in [".wav", ".mp3", ".flac", ".m4a"]:
                    files.append(p)

    if args.max_files is not None:
        files = files[: int(args.max_files)]
        if manifest_df is not None:
            manifest_df = manifest_df.iloc[: int(args.max_files)].reset_index(drop=True)

    if not files:
        print("[ERROR] No audio found. Check --test_manifest / --audio_dir or --audio_path.")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    results = []
    env_extractor = EnvironmentalFeatureExtractor(sr=SAMPLE_RATE)

    for idx, f in enumerate(tqdm(files, desc="Explaining", colour="cyan")):
        try:
            if not f.exists():
                # In manifest mode, filepaths might be unavailable on this machine; skip gracefully.
                print(f"[WARN] Missing audio file, skipping: {f}")
                continue

            res = predict_file(str(f), model, device, args, env_extractor=env_extractor)

            # Attach labels (manifest mode) for validation/analysis
            if manifest_df is not None and idx < len(manifest_df):
                row = manifest_df.iloc[idx].to_dict()
                if "label" in row:
                    res["true_label"] = str(row["label"])
                if "attack_type" in row:
                    res["true_attack_type"] = str(row["attack_type"])
                if "dataset" in row:
                    res["domain"] = str(row["dataset"])

            results.append(res)
            # save per-file JSON
            json_path = os.path.join(args.output_dir, f"{f.stem}.json")
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(res, jf, indent=2)
        except Exception as e:
            print(f"[ERROR] {f.name}: {e}")

    # Save CSV
    if results:
        import pandas as pd
        df = pd.DataFrame(results)
        csv_path = os.path.join(args.output_dir, "results.csv")
        df.to_csv(csv_path, index=False)
        print(f"[SAVE] CSV -> {csv_path}")
    else:
        print("[WARN] No results to save.")


if __name__ == "__main__":
    main()


