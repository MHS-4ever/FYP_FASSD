"""Audio IO skeleton for Phase 9A."""

from __future__ import annotations

from pathlib import Path


def validate_audio_file(audio_path: str) -> tuple[bool, str]:
    path = Path(audio_path)
    if not audio_path:
        return False, "Empty audio path."
    if not path.exists():
        return False, f"Audio file not found: {audio_path}"
    return True, "Audio file path looks valid."


def load_audio(audio_path: str):
    # TODO(Phase 9C): connect librosa/soundfile loader with robust error handling.
    return None, {"path": audio_path, "loaded": False, "note": "skeleton"}


def convert_to_mono(audio_waveform, sample_rate: int):
    # TODO(Phase 9C): convert multi-channel waveforms to mono.
    return audio_waveform, sample_rate


def resample_audio(audio_waveform, src_sr: int, target_sr: int):
    # TODO(Phase 9C): resample waveform to target sample rate.
    return audio_waveform, target_sr
