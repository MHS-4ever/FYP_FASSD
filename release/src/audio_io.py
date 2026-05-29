"""Audio IO for Phase 9C live inference."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import numpy as np


TARGET_SAMPLE_RATE = 16000
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}


class AudioLoadError(Exception):
    pass


def validate_audio_path(path: str) -> tuple[bool, str]:
    if not path or not str(path).strip():
        return False, "Empty audio path."
    p = Path(path)
    if not p.is_file():
        return False, f"Audio file not found: {path}"
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported extension '{p.suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
    return True, "ok"


def _to_mono(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        return y
    if y.ndim == 2:
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = y.T
        return np.mean(y, axis=1)
    return y.reshape(-1)


def _resample(y: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr or len(y) < 2:
        return y
    try:
        import librosa

        return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)
    except Exception:
        duration = len(y) / float(orig_sr)
        n = max(int(duration * target_sr), 1)
        x_old = np.linspace(0, 1, num=len(y), endpoint=False)
        x_new = np.linspace(0, 1, num=n, endpoint=False)
        return np.interp(x_new, x_old, y).astype(np.float64)


def normalize_audio(y: np.ndarray) -> np.ndarray:
    y = _to_mono(np.asarray(y, dtype=np.float64))
    peak = np.max(np.abs(y)) if len(y) else 0.0
    if peak > 1.0:
        y = y / peak
    return y


def load_audio(path: str, target_sample_rate: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, int]:
    ok, msg = validate_audio_path(path)
    if not ok:
        raise AudioLoadError(msg)

    resolved = Path(path).resolve()
    y: np.ndarray | None = None
    sr: int | None = None

    try:
        import soundfile as sf

        data, sr = sf.read(str(resolved), always_2d=False)
        y = _to_mono(np.asarray(data, dtype=np.float64))
    except Exception:
        pass

    if y is None:
        try:
            import librosa

            y, sr = librosa.load(str(resolved), sr=None, mono=True)
            y = np.asarray(y, dtype=np.float64)
        except Exception as exc:
            raise AudioLoadError(f"Could not read audio: {exc}") from exc

    if sr is None or int(sr) <= 0:
        raise AudioLoadError("Invalid sample rate after load.")

    y = normalize_audio(y)
    if int(sr) != int(target_sample_rate):
        y = _resample(y, int(sr), int(target_sample_rate))
        sr = target_sample_rate

    if len(y) < int(0.05 * sr):
        raise AudioLoadError("Audio too short for analysis.")
    if np.max(np.abs(y)) < 1e-8:
        raise AudioLoadError("Audio appears silent or invalid.")

    return y, int(sr)


def audio_metadata(path: str, y: np.ndarray, sr: int) -> dict[str, Any]:
    duration = float(len(y) / sr) if sr > 0 else 0.0
    return {
        "path": str(Path(path).resolve()),
        "sample_rate": sr,
        "duration_sec": round(duration, 4),
        "num_samples": int(len(y)),
        "channels": "mono",
        "loaded": True,
    }


def save_temp_wav_if_needed(y: np.ndarray, sr: int) -> str:
    try:
        import soundfile as sf
    except Exception as exc:
        raise AudioLoadError(f"soundfile required for temp wav: {exc}") from exc
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    sf.write(tmp.name, y, sr)
    return tmp.name
