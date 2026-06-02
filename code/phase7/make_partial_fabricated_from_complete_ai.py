import argparse
import csv
import math
import random
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


SUPPORTED_EXTS = {".wav", ".flac", ".ogg", ".mp3"}


def get_audio_files(folder: Path):
    files = []
    for ext in SUPPORTED_EXTS:
        files.extend(folder.rglob(f"*{ext}"))
    return sorted(files)


def read_audio(path: Path):
    audio, sr = sf.read(str(path), always_2d=True)
    return audio.astype(np.float32), sr


def write_audio(path: Path, audio: np.ndarray, sr: int):
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(path), audio, sr)


def resample_audio(audio: np.ndarray, src_sr: int, target_sr: int):
    if src_sr == target_sr:
        return audio

    gcd = math.gcd(src_sr, target_sr)
    up = target_sr // gcd
    down = src_sr // gcd

    channels = []
    for ch in range(audio.shape[1]):
        channels.append(resample_poly(audio[:, ch], up, down))

    return np.stack(channels, axis=1).astype(np.float32)


def match_channels(audio: np.ndarray, target_channels: int):
    current_channels = audio.shape[1]

    if current_channels == target_channels:
        return audio

    if target_channels == 1:
        return np.mean(audio, axis=1, keepdims=True).astype(np.float32)

    if current_channels == 1 and target_channels > 1:
        return np.repeat(audio, target_channels, axis=1).astype(np.float32)

    return audio[:, :target_channels].astype(np.float32)


def rms(x: np.ndarray):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-9))


def match_rms(ai_chunk: np.ndarray, real_region: np.ndarray):
    real_rms = rms(real_region)
    ai_rms = rms(ai_chunk)

    gain = real_rms / max(ai_rms, 1e-9)
    gain = max(0.25, min(gain, 4.0))

    return ai_chunk * gain


def get_random_chunk_from_complete_ai(
    ai_files,
    required_samples,
    target_sr,
    target_channels,
):
    ai_path = random.choice(ai_files)
    ai_audio, ai_sr = read_audio(ai_path)

    ai_audio = resample_audio(ai_audio, ai_sr, target_sr)
    ai_audio = match_channels(ai_audio, target_channels)

    if len(ai_audio) < required_samples:
        repeat_count = math.ceil(required_samples / len(ai_audio))
        ai_audio = np.tile(ai_audio, (repeat_count, 1))

    max_ai_start = len(ai_audio) - required_samples
    ai_start_sample = random.randint(0, max_ai_start)
    ai_end_sample = ai_start_sample + required_samples

    ai_chunk = ai_audio[ai_start_sample:ai_end_sample]

    return ai_chunk.astype(np.float32), ai_path, ai_start_sample, ai_end_sample


def replace_with_crossfade(
    real_audio,
    ai_chunk,
    start_sample,
    crossfade_samples,
):
    output = real_audio.copy()

    fake_len = len(ai_chunk)
    end_sample = start_sample + fake_len

    real_region = real_audio[start_sample:end_sample]
    fabricated_region = ai_chunk.copy()

    fade = min(
        crossfade_samples,
        fake_len // 4,
        len(real_region) // 4,
    )

    if fade > 0:
        fade_in = np.linspace(0.0, 1.0, fade, dtype=np.float32).reshape(-1, 1)
        fade_out = np.linspace(1.0, 0.0, fade, dtype=np.float32).reshape(-1, 1)

        fabricated_region[:fade] = (
            real_region[:fade] * (1.0 - fade_in)
            + fabricated_region[:fade] * fade_in
        )

        fabricated_region[-fade:] = (
            fabricated_region[-fade:] * fade_out
            + real_region[-fade:] * (1.0 - fade_out)
        )

    output[start_sample:end_sample] = fabricated_region

    return output


def fabricate_file(
    real_path,
    ai_files,
    out_dir,
    fake_ratio,
    crossfade_ms,
    use_rms_match,
):
    real_audio, sr = read_audio(real_path)

    total_samples = len(real_audio)
    channels = real_audio.shape[1]

    fake_samples = int(total_samples * fake_ratio)

    if fake_samples <= 0:
        raise ValueError(f"Audio too short: {real_path}")

    max_real_start = total_samples - fake_samples
    real_start_sample = random.randint(0, max_real_start)
    real_end_sample = real_start_sample + fake_samples

    real_region = real_audio[real_start_sample:real_end_sample]

    ai_chunk, ai_path, ai_start_sample, ai_end_sample = get_random_chunk_from_complete_ai(
        ai_files=ai_files,
        required_samples=fake_samples,
        target_sr=sr,
        target_channels=channels,
    )

    if use_rms_match:
        ai_chunk = match_rms(ai_chunk, real_region)

    crossfade_samples = int((crossfade_ms / 1000.0) * sr)

    fabricated_audio = replace_with_crossfade(
        real_audio=real_audio,
        ai_chunk=ai_chunk,
        start_sample=real_start_sample,
        crossfade_samples=crossfade_samples,
    )

    output_name = f"{real_path.stem}_partial_fake_20pct.wav"
    output_path = out_dir / output_name

    write_audio(output_path, fabricated_audio, sr)

    duration_sec = total_samples / sr

    row = {
        "output_path": str(output_path),
        "real_source_path": str(real_path),
        "ai_source_path": str(ai_path),

        "label": "partial_fake",
        "fabrication_type": "random_ai_chunk_replacement",

        "duration_sec": round(duration_sec, 6),
        "target_fake_ratio": fake_ratio,
        "actual_fake_ratio": round(fake_samples / total_samples, 6),

        "fabricated_start_sec": round(real_start_sample / sr, 6),
        "fabricated_end_sec": round(real_end_sample / sr, 6),
        "fabricated_duration_sec": round(fake_samples / sr, 6),

        "fabricated_start_sample": real_start_sample,
        "fabricated_end_sample": real_end_sample,

        "ai_chunk_start_sec": round(ai_start_sample / sr, 6),
        "ai_chunk_end_sec": round(ai_end_sample / sr, 6),
        "ai_chunk_start_sample": ai_start_sample,
        "ai_chunk_end_sample": ai_end_sample,

        "sample_rate": sr,
        "channels": channels,
        "crossfade_ms": crossfade_ms,
        "rms_matched": use_rms_match,
    }

    return row


def main():
    parser = argparse.ArgumentParser(
        description="Create partial fake audios by cutting random chunks from complete AI audios."
    )

    parser.add_argument("--real_dir", required=True)
    parser.add_argument("--ai_complete_dir", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--manifest", required=True)

    parser.add_argument("--fake_ratio", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--crossfade_ms", type=float, default=30.0)
    parser.add_argument("--no_rms_match", action="store_true")

    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    real_dir = Path(args.real_dir)
    ai_complete_dir = Path(args.ai_complete_dir)
    out_dir = Path(args.out_dir)
    manifest_path = Path(args.manifest)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    real_files = get_audio_files(real_dir)
    ai_files = get_audio_files(ai_complete_dir)

    if not real_files:
        raise RuntimeError(f"No real audio found in: {real_dir}")

    if not ai_files:
        raise RuntimeError(f"No complete AI audio found in: {ai_complete_dir}")

    rows = []

    for real_path in real_files:
        print(f"[PROCESSING] {real_path.name}")

        row = fabricate_file(
            real_path=real_path,
            ai_files=ai_files,
            out_dir=out_dir,
            fake_ratio=args.fake_ratio,
            crossfade_ms=args.crossfade_ms,
            use_rms_match=not args.no_rms_match,
        )

        rows.append(row)

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"[DONE] Fabricated files saved in: {out_dir}")
    print(f"[DONE] Timestamp CSV saved at: {manifest_path}")
    print(f"[DONE] Total fabricated files: {len(rows)}")


if __name__ == "__main__":
    main()