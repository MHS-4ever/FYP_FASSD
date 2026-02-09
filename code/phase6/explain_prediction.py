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
        return [y]
    chunks = []
    for start in range(0, len(y) - chunk_len + 1, hop):
        end = start + chunk_len
        chunks.append(y[start:end])
    if not chunks:
        chunks = [y]
    return chunks


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

    env_raw, env_feats_norm = extract_env_features(env_extractor, path, y=y)
    env_tensor = torch.from_numpy(env_feats_norm).unsqueeze(0).float().to(device)

    spoof_probs = []
    attack_probs = []

    for i in range(0, len(chunks), args.batch_size):
        batch_chunks = chunks[i:i + args.batch_size]
        logmels_norm = [extract_logmel(c, sr=sr)[0] for c in batch_chunks]
        spec = torch.from_numpy(np.stack(logmels_norm)).unsqueeze(1).float().to(device)
        # repeat env for each chunk
        env = env_tensor.repeat(spec.size(0), 1)
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                bin_logits, mc_logits = model(spec, env)
                bin_probs = torch.softmax(bin_logits, dim=1)[:, 1]  # spoof prob
                mc_probs = torch.softmax(mc_logits, dim=1)          # attack probs
        spoof_probs.append(bin_probs.cpu().numpy())
        attack_probs.append(mc_probs.cpu().numpy())

    spoof_probs = np.concatenate(spoof_probs)
    attack_probs = np.concatenate(attack_probs)

    spoof_mean = float(spoof_probs.mean())
    attack_mean = attack_probs.mean(axis=0)  # [4]
    attack_idx = int(np.argmax(attack_mean))
    attack_conf = float(attack_mean[attack_idx])
    attack_name = ATTACK_TYPE_NAMES[attack_idx] if 0 <= attack_idx < len(ATTACK_TYPE_NAMES) else str(attack_idx)

    prediction = "FAKE" if spoof_mean >= args.threshold else "REAL"
    confidence = spoof_mean if prediction == "FAKE" else (1.0 - spoof_mean)

    env_reasons = _env_reasoning(env_raw)
    spec_reasons = _spec_reasoning(len(chunks), spoof_probs)

    # Overall explanation (simple + readable)
    if prediction == "FAKE":
        overall = (
            f"Model predicts FAKE (spoof_prob={spoof_mean:.3f}). "
            f"Most likely attack type: {attack_name} (conf={attack_conf:.3f})."
        )
    else:
        overall = f"Model predicts REAL (bonafide) with confidence={confidence:.3f}."

    return {
        "filename": Path(path).name,
        "filepath": str(Path(path).resolve()),
        "prediction": prediction,
        "confidence": confidence,
        "spoof_prob": spoof_mean,
        "threshold": float(args.threshold),
        "attack_type": attack_name,
        "attack_type_idx": attack_idx,
        "attack_type_conf": attack_conf,
        "attack_probs": attack_mean.tolist(),
        "n_chunks": int(len(chunks)),
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
    p.add_argument("--threshold", type=float, default=0.5)
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


