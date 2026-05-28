"""
Phase 8C acoustic/channel feature helpers.

Raw measurable features only — not evidence scores or forensic decisions.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_VERSION = "phase8c_v1"
FEATURE_SOURCE_LIBROSA = "phase8c_acoustic_librosa"
FEATURE_SOURCE_NUMPY = "phase8c_acoustic_numpy_fallback"

MIN_DURATION_SEC = 0.05
SILENCE_RMS_THRESHOLD = 1e-4
CLIP_THRESHOLD = 0.99

EXTRACTION_STATUSES = frozenset(
    {
        "ok",
        "missing_audio",
        "unreadable_audio",
        "too_short",
        "silent_or_invalid",
        "error",
    }
)

FILE_IDENTITY_COLUMNS = [
    "schema_version",
    "file_id",
    "audio_path",
    "source_dataset",
    "split",
    "known_origin_label",
    "known_manipulation_labels",
    "duration_sec",
    "sample_rate",
    "feature_source",
    "extraction_status",
    "warning_message",
]

FILE_FEATURE_NAMES = [
    "rms_mean",
    "rms_std",
    "rms_min",
    "rms_max",
    "peak_amplitude",
    "mean_amplitude",
    "std_amplitude",
    "dc_offset",
    "zero_crossing_rate_mean",
    "zero_crossing_rate_std",
    "clipping_ratio",
    "silence_ratio",
    "active_audio_ratio",
    "spectral_centroid_mean",
    "spectral_centroid_std",
    "spectral_bandwidth_mean",
    "spectral_bandwidth_std",
    "spectral_rolloff_mean",
    "spectral_rolloff_std",
    "spectral_flatness_mean",
    "spectral_flatness_std",
    "spectral_contrast_mean",
    "spectral_contrast_std",
    "low_band_energy_ratio",
    "mid_band_energy_ratio",
    "high_band_energy_ratio",
    "very_high_band_energy_ratio",
    "noise_floor_proxy",
    "snr_proxy",
    "dynamic_range_proxy",
    "spectral_entropy_mean",
    "spectral_entropy_std",
    "high_freq_rolloff_ratio",
    "bandwidth_occupied_95",
] + [f"mfcc_{i}_{stat}" for i in range(1, 14) for stat in ("mean", "std")]

FILE_TABLE_COLUMNS = FILE_IDENTITY_COLUMNS + FILE_FEATURE_NAMES

SEGMENT_IDENTITY_COLUMNS = [
    "schema_version",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
    "feature_source",
    "extraction_status",
    "warning_message",
]

SEGMENT_FEATURE_NAMES = [
    "rms_mean",
    "rms_std",
    "peak_amplitude",
    "zero_crossing_rate_mean",
    "clipping_ratio",
    "silence_ratio",
    "spectral_centroid_mean",
    "spectral_bandwidth_mean",
    "spectral_rolloff_mean",
    "spectral_flatness_mean",
    "spectral_contrast_mean",
    "low_band_energy_ratio",
    "mid_band_energy_ratio",
    "high_band_energy_ratio",
    "very_high_band_energy_ratio",
    "noise_floor_proxy",
    "snr_proxy",
    "dynamic_range_proxy",
    "spectral_entropy_mean",
    "bandwidth_occupied_95",
] + [f"mfcc_{i}_{stat}" for i in range(1, 14) for stat in ("mean", "std")]

SEGMENT_TABLE_COLUMNS = SEGMENT_IDENTITY_COLUMNS + SEGMENT_FEATURE_NAMES

# Left blank in fast segment mode (columns still present in CSV)
SEGMENT_FAST_BLANK_FEATURES = frozenset(
    {"spectral_contrast_mean"}
    | {f"mfcc_{i}_{stat}" for i in range(1, 14) for stat in ("mean", "std")}
)


def resolve_audio_path(audio_path: str | None) -> Path | None:
    if not audio_path or not str(audio_path).strip():
        return None
    p = Path(str(audio_path).strip())
    if p.is_file():
        return p.resolve()
    candidate = (REPO_ROOT / p).resolve()
    if candidate.is_file():
        return candidate
    return None


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


def load_audio_mono(
    audio_path: str | None,
    target_sample_rate: int = 16000,
) -> tuple[np.ndarray | None, int | None, str, str]:
    """
    Returns (y, sr, feature_source, error_message).
    error_message empty on success.
    """
    resolved = resolve_audio_path(audio_path)
    if resolved is None:
        return None, None, FEATURE_SOURCE_NUMPY, "missing_audio"

    y: np.ndarray | None = None
    sr: int | None = None
    source = FEATURE_SOURCE_NUMPY

    try:
        import soundfile as sf

        data, sr = sf.read(str(resolved), always_2d=False)
        y = _to_mono(np.asarray(data, dtype=np.float64))
        source = FEATURE_SOURCE_LIBROSA
    except Exception:
        pass

    if y is None:
        try:
            import librosa

            y, sr = librosa.load(str(resolved), sr=None, mono=True)
            y = np.asarray(y, dtype=np.float64)
            source = FEATURE_SOURCE_LIBROSA
        except Exception as exc:
            return None, None, FEATURE_SOURCE_NUMPY, f"unreadable_audio: {exc}"

    if sr is None or sr <= 0:
        return None, None, source, "unreadable_audio: invalid sample rate"

    if target_sample_rate > 0 and int(sr) != int(target_sample_rate):
        y = _resample(y, int(sr), int(target_sample_rate))
        sr = target_sample_rate

    if len(y) < max(int(MIN_DURATION_SEC * sr), 8):
        return y, sr, source, "too_short"

    if np.max(np.abs(y)) < 1e-8:
        return y, sr, source, "silent_or_invalid"

    return y, int(sr), source, ""


def safe_audio_slice(
    y: np.ndarray,
    sr: int,
    start_sec: float,
    end_sec: float,
) -> tuple[np.ndarray | None, str]:
    if y is None or len(y) == 0 or sr <= 0:
        return None, "silent_or_invalid"
    start = max(0, int(float(start_sec) * sr))
    end = min(len(y), int(float(end_sec) * sr))
    if end <= start:
        return None, "too_short"
    seg = y[start:end]
    if len(seg) < max(int(MIN_DURATION_SEC * sr), 4):
        return None, "too_short"
    if np.max(np.abs(seg)) < 1e-8:
        return None, "silent_or_invalid"
    return seg, ""


def _nan() -> float:
    return float("nan")


def empty_feature_dict(feature_names: list[str] | None = None) -> dict[str, float]:
    names = feature_names or FILE_FEATURE_NAMES
    return {k: _nan() for k in names}


def _frame_rms(y: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    if len(y) < frame_length:
        rms = np.sqrt(np.mean(y**2))
        return np.array([rms], dtype=np.float64)
    try:
        import librosa

        return librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    except Exception:
        frames = []
        for i in range(0, len(y) - frame_length + 1, hop_length):
            frame = y[i : i + frame_length]
            frames.append(np.sqrt(np.mean(frame**2)))
        return np.asarray(frames, dtype=np.float64) if frames else np.array([_nan()])


def compute_rms_features(y: np.ndarray) -> dict[str, float]:
    frame_length = min(2048, max(256, len(y) // 4))
    hop = max(256, frame_length // 4)
    rms_frames = _frame_rms(y, frame_length, hop)
    rms_frames = rms_frames[np.isfinite(rms_frames)]
    if len(rms_frames) == 0:
        return {k: _nan() for k in ("rms_mean", "rms_std", "rms_min", "rms_max")}
    return {
        "rms_mean": float(np.mean(rms_frames)),
        "rms_std": float(np.std(rms_frames)),
        "rms_min": float(np.min(rms_frames)),
        "rms_max": float(np.max(rms_frames)),
    }


def compute_amplitude_features(y: np.ndarray) -> dict[str, float]:
    peak = float(np.max(np.abs(y))) if len(y) else _nan()
    return {
        "peak_amplitude": peak,
        "mean_amplitude": float(np.mean(np.abs(y))) if len(y) else _nan(),
        "std_amplitude": float(np.std(y)) if len(y) else _nan(),
        "dc_offset": float(np.mean(y)) if len(y) else _nan(),
    }


def compute_zcr_features(y: np.ndarray) -> dict[str, float]:
    try:
        import librosa

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        return {
            "zero_crossing_rate_mean": float(np.mean(zcr)),
            "zero_crossing_rate_std": float(np.std(zcr)),
        }
    except Exception:
        signs = np.signbit(y[:-1]) != np.signbit(y[1:])
        rate = float(np.mean(signs)) if len(signs) else _nan()
        return {"zero_crossing_rate_mean": rate, "zero_crossing_rate_std": _nan()}


def compute_silence_features(y: np.ndarray, sr: int) -> dict[str, float]:
    frame_length = min(2048, max(256, len(y) // 4))
    hop = max(256, frame_length // 4)
    rms_frames = _frame_rms(y, frame_length, hop)
    silent = float(np.mean(rms_frames < SILENCE_RMS_THRESHOLD)) if len(rms_frames) else _nan()
    clip = float(np.mean(np.abs(y) >= CLIP_THRESHOLD)) if len(y) else _nan()
    return {
        "clipping_ratio": clip,
        "silence_ratio": silent,
        "active_audio_ratio": (1.0 - silent) if not math.isnan(silent) else _nan(),
    }


def _spectral_frames(y: np.ndarray, sr: int) -> dict[str, np.ndarray]:
    n_fft = min(2048, max(256, int(2 ** np.ceil(np.log2(len(y))))))
    hop = max(256, n_fft // 4)
    out: dict[str, np.ndarray] = {}
    try:
        import librosa

        out["centroid"] = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["rolloff"] = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["flatness"] = librosa.feature.spectral_flatness(y=y, n_fft=n_fft, hop_length=hop)[0]
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=n_fft, hop_length=hop)
        out["contrast"] = np.mean(contrast, axis=0)
        return out
    except Exception:
        return out


def compute_spectral_features(y: np.ndarray, sr: int) -> dict[str, float]:
    frames = _spectral_frames(y, sr)
    result: dict[str, float] = {}
    mapping = {
        "centroid": ("spectral_centroid_mean", "spectral_centroid_std"),
        "bandwidth": ("spectral_bandwidth_mean", "spectral_bandwidth_std"),
        "rolloff": ("spectral_rolloff_mean", "spectral_rolloff_std"),
        "flatness": ("spectral_flatness_mean", "spectral_flatness_std"),
        "contrast": ("spectral_contrast_mean", "spectral_contrast_std"),
    }
    for key, (m_key, s_key) in mapping.items():
        if key not in frames or len(frames[key]) == 0:
            result[m_key] = _nan()
            result[s_key] = _nan()
        else:
            arr = frames[key]
            result[m_key] = float(np.mean(arr))
            result[s_key] = float(np.std(arr))
    return result


def compute_band_energy_features(y: np.ndarray, sr: int) -> dict[str, float]:
    n_fft = min(4096, max(512, int(2 ** np.ceil(np.log2(len(y))))))
    try:
        import librosa

        S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=max(256, n_fft // 4))) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    except Exception:
        window = np.hanning(min(len(y), n_fft))
        seg = y[: len(window)] * window
        spec = np.abs(np.fft.rfft(seg, n=n_fft)) ** 2
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        S = spec.reshape(-1, 1)

    power = np.mean(S, axis=1)
    total = float(np.sum(power)) + 1e-12
    nyq = sr / 2.0
    bands = [
        ("low_band_energy_ratio", 0.0, 300.0),
        ("mid_band_energy_ratio", 300.0, 3000.0),
        ("high_band_energy_ratio", 3000.0, min(8000.0, nyq)),
        ("very_high_band_energy_ratio", min(8000.0, nyq), nyq),
    ]
    out: dict[str, float] = {}
    for name, lo, hi in bands:
        mask = (freqs >= lo) & (freqs < hi)
        out[name] = float(np.sum(power[mask]) / total) if np.any(mask) else _nan()
    return out


def compute_spectral_entropy(y: np.ndarray, sr: int) -> dict[str, float]:
    n_fft = min(2048, max(256, int(2 ** np.ceil(np.log2(len(y))))))
    hop = max(256, n_fft // 4)
    entropies: list[float] = []
    try:
        import librosa

        S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop)) ** 2
        for i in range(S.shape[1]):
            p = S[:, i]
            p = p / (np.sum(p) + 1e-12)
            ent = -np.sum(p * np.log(p + 1e-12))
            entropies.append(float(ent))
    except Exception:
        return {"spectral_entropy_mean": _nan(), "spectral_entropy_std": _nan()}
    if not entropies:
        return {"spectral_entropy_mean": _nan(), "spectral_entropy_std": _nan()}
    return {
        "spectral_entropy_mean": float(np.mean(entropies)),
        "spectral_entropy_std": float(np.std(entropies)),
    }


def compute_quality_proxy_features(
    y: np.ndarray,
    sr: int,
    spectral_rolloff_mean: float | None = None,
) -> dict[str, float]:
    frame_length = min(2048, max(256, len(y) // 4))
    hop = max(256, frame_length // 4)
    rms_frames = _frame_rms(y, frame_length, hop)
    rms_frames = rms_frames[np.isfinite(rms_frames)]
    if len(rms_frames) == 0:
        return {
            "noise_floor_proxy": _nan(),
            "snr_proxy": _nan(),
            "dynamic_range_proxy": _nan(),
            "high_freq_rolloff_ratio": _nan(),
            "bandwidth_occupied_95": _nan(),
        }
    noise_floor = float(np.percentile(rms_frames, 10))
    signal_level = float(np.percentile(rms_frames, 90))
    snr = signal_level / (noise_floor + 1e-12)
    dyn = float(np.max(rms_frames) - np.min(rms_frames))

    rolloff_mean = spectral_rolloff_mean
    if rolloff_mean is None or (isinstance(rolloff_mean, float) and math.isnan(rolloff_mean)):
        frames = _spectral_frames(y, sr)
        if "rolloff" in frames and len(frames["rolloff"]):
            rolloff_mean = float(np.mean(frames["rolloff"]))
        else:
            rolloff_mean = _nan()
    hf_ratio = rolloff_mean / (sr / 2.0) if sr > 0 and not math.isnan(rolloff_mean) else _nan()

    n_fft = min(4096, max(512, int(2 ** np.ceil(np.log2(len(y))))))
    try:
        import librosa

        S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=max(256, n_fft // 4))) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        power = np.mean(S, axis=1)
        cum = np.cumsum(power)
        total = cum[-1] + 1e-12
        idx = int(np.searchsorted(cum, 0.95 * total))
        bw95 = float(freqs[min(idx, len(freqs) - 1)] / (sr / 2.0))
    except Exception:
        bw95 = _nan()

    return {
        "noise_floor_proxy": noise_floor,
        "snr_proxy": float(snr),
        "dynamic_range_proxy": dyn,
        "high_freq_rolloff_ratio": float(hf_ratio) if not math.isnan(hf_ratio) else _nan(),
        "bandwidth_occupied_95": bw95,
    }


def compute_mfcc_summary(y: np.ndarray, sr: int, n_mfcc: int = 13) -> dict[str, float]:
    out: dict[str, float] = {}
    for i in range(1, n_mfcc + 1):
        out[f"mfcc_{i}_mean"] = _nan()
        out[f"mfcc_{i}_std"] = _nan()
    try:
        import librosa

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        for i in range(n_mfcc):
            out[f"mfcc_{i + 1}_mean"] = float(np.mean(mfcc[i]))
            out[f"mfcc_{i + 1}_std"] = float(np.std(mfcc[i]))
    except Exception:
        pass
    return out


def extract_file_feature_dict(y: np.ndarray, sr: int) -> dict[str, float]:
    feats: dict[str, float] = {}
    feats.update(compute_rms_features(y))
    feats.update(compute_amplitude_features(y))
    feats.update(compute_zcr_features(y))
    feats.update(compute_silence_features(y, sr))
    spec = compute_spectral_features(y, sr)
    feats.update(spec)
    feats.update(compute_band_energy_features(y, sr))
    rolloff = spec.get("spectral_rolloff_mean")
    feats.update(compute_quality_proxy_features(y, sr, spectral_rolloff_mean=rolloff))
    feats.update(compute_spectral_entropy(y, sr))
    feats.update(compute_mfcc_summary(y, sr))
    return feats


def _spectral_frames_fast(y: np.ndarray, sr: int) -> dict[str, np.ndarray]:
    """Spectral frames without contrast (faster for segment fast mode)."""
    n_fft = min(2048, max(256, int(2 ** np.ceil(np.log2(len(y))))))
    hop = max(256, n_fft // 4)
    out: dict[str, np.ndarray] = {}
    try:
        import librosa

        out["centroid"] = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["rolloff"] = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]
        out["flatness"] = librosa.feature.spectral_flatness(y=y, n_fft=n_fft, hop_length=hop)[0]
    except Exception:
        pass
    return out


def _spectral_means_fast(y: np.ndarray, sr: int) -> dict[str, float]:
    """Lightweight spectral means for segment fast mode (no contrast)."""
    frames = _spectral_frames_fast(y, sr)
    out: dict[str, float] = {
        "spectral_centroid_mean": _nan(),
        "spectral_bandwidth_mean": _nan(),
        "spectral_rolloff_mean": _nan(),
        "spectral_flatness_mean": _nan(),
        "spectral_contrast_mean": _nan(),
    }
    key_map = {
        "centroid": "spectral_centroid_mean",
        "bandwidth": "spectral_bandwidth_mean",
        "rolloff": "spectral_rolloff_mean",
        "flatness": "spectral_flatness_mean",
    }
    for k, col in key_map.items():
        if k in frames and len(frames[k]):
            out[col] = float(np.mean(frames[k]))
    return out


def extract_segment_feature_dict_fast(y: np.ndarray, sr: int) -> dict[str, float]:
    """
    Fast segment features: essential columns filled; heavy columns left blank.
    """
    feats: dict[str, float] = {k: _nan() for k in SEGMENT_FEATURE_NAMES}
    feats.update(compute_rms_features(y))
    peak = compute_amplitude_features(y).get("peak_amplitude", _nan())
    feats["peak_amplitude"] = peak
    zcr = compute_zcr_features(y)
    feats["zero_crossing_rate_mean"] = zcr.get("zero_crossing_rate_mean", _nan())
    feats.update(compute_silence_features(y, sr))
    spec_means = _spectral_means_fast(y, sr)
    feats.update(spec_means)
    feats.update(compute_band_energy_features(y, sr))
    ent = compute_spectral_entropy(y, sr)
    feats["spectral_entropy_mean"] = ent.get("spectral_entropy_mean", _nan())
    rolloff = spec_means.get("spectral_rolloff_mean")
    qual = compute_quality_proxy_features(y, sr, spectral_rolloff_mean=rolloff)
    for k in (
        "noise_floor_proxy",
        "snr_proxy",
        "dynamic_range_proxy",
        "bandwidth_occupied_95",
    ):
        feats[k] = qual.get(k, _nan())
    for blank_key in SEGMENT_FAST_BLANK_FEATURES:
        feats[blank_key] = _nan()
    return feats


def extract_segment_feature_dict(y: np.ndarray, sr: int, mode: str = "full") -> dict[str, float]:
    """Segment features; mode is 'fast' or 'full'."""
    if mode == "fast":
        return extract_segment_feature_dict_fast(y, sr)
    spec = compute_spectral_features(y, sr)
    feats: dict[str, float] = {k: _nan() for k in SEGMENT_FEATURE_NAMES}
    feats.update(compute_rms_features(y))
    feats["peak_amplitude"] = compute_amplitude_features(y).get("peak_amplitude", _nan())
    feats["zero_crossing_rate_mean"] = compute_zcr_features(y).get("zero_crossing_rate_mean", _nan())
    feats.update(compute_silence_features(y, sr))
    feats["spectral_centroid_mean"] = spec.get("spectral_centroid_mean", _nan())
    feats["spectral_bandwidth_mean"] = spec.get("spectral_bandwidth_mean", _nan())
    feats["spectral_rolloff_mean"] = spec.get("spectral_rolloff_mean", _nan())
    feats["spectral_flatness_mean"] = spec.get("spectral_flatness_mean", _nan())
    feats["spectral_contrast_mean"] = spec.get("spectral_contrast_mean", _nan())
    feats.update(compute_band_energy_features(y, sr))
    ent = compute_spectral_entropy(y, sr)
    feats["spectral_entropy_mean"] = ent.get("spectral_entropy_mean", _nan())
    qual = compute_quality_proxy_features(y, sr, spectral_rolloff_mean=spec.get("spectral_rolloff_mean"))
    for k in ("noise_floor_proxy", "snr_proxy", "dynamic_range_proxy", "bandwidth_occupied_95"):
        feats[k] = qual.get(k, _nan())
    feats.update(compute_mfcc_summary(y, sr))
    return feats


def validate_numeric_features(feature_dict: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key, val in feature_dict.items():
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue
        try:
            f = float(val)
            if not math.isfinite(f):
                warnings.append(f"{key}: non-finite value")
        except (TypeError, ValueError):
            warnings.append(f"{key}: non-numeric value")
    return warnings


def format_feature_value(val: float | None) -> str:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ""
    return f"{float(val):.8g}"
