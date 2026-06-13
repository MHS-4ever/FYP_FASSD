"""Train-only synthetic manipulation examples for Phase 4 two-stage v3.

No new recordings — edits and codec transforms applied in memory to existing
Phase 7 train files only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from retrain_mixer_channel_experimental import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    augmentation_rows,
    channel_degrade,
    resolve_audio,
)

from train_two_stage_manipulation_prototype import (  # noqa: E402
    extract_file_acoustic_features,
)

from phase3_common import tqdm_iter  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"


def synthetic_edited_splice(y: np.ndarray, sr: int, *, seed: int = 42) -> np.ndarray:
    """Insert a reversed mid-file patch to mimic edited/spliced content."""
    rng = np.random.default_rng(seed)
    z = np.asarray(y, dtype=np.float64).copy()
    n = len(z)
    if n < int(2.5 * sr):
        return z
    seg_len = int(n * rng.uniform(0.12, 0.22))
    seg_len = max(seg_len, int(0.25 * sr))
    mid = n // 2
    dst_start = max(0, mid - seg_len // 2)
    dst_end = min(n, dst_start + seg_len)
    seg_len = dst_end - dst_start
    src_start = int(rng.integers(int(0.08 * n), max(int(0.08 * n) + 1, int(0.55 * n))))
    patch = z[src_start : src_start + seg_len].copy()
    if len(patch) < seg_len:
        patch = np.pad(patch, (0, seg_len - len(patch)))
    patch = patch[::-1]
    fade = min(int(0.015 * sr), seg_len // 4)
    for i in range(fade):
        alpha = (i + 1) / max(fade, 1)
        z[dst_start + i] = (1 - alpha) * z[dst_start + i] + alpha * patch[i]
        z[dst_end - 1 - i] = (1 - alpha) * z[dst_end - 1 - i] + alpha * patch[seg_len - 1 - i]
    z[dst_start + fade : dst_end - fade] = patch[fade : seg_len - fade]
    peak = float(np.max(np.abs(z))) if len(z) else 0.0
    if peak > 0.99:
        z = z / peak * 0.99
    return z.astype(np.float64)


def synthetic_platform_modes() -> list[str]:
    return ["whatsapp_8k", "codec_8k", "mobile_11k", "codec_12k", "dynamic_compress_noise"]


def build_edited_splice_rows(
    train_df: pd.DataFrame,
    *,
    max_rows: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Human clean train files -> edited_spliced positives."""
    import sys

    if str(RELEASE) not in sys.path:
        sys.path.insert(0, str(RELEASE))
    from src.audio_io import load_audio  # noqa: E402

    sources = train_df[
        train_df["feature_status"].eq("ok")
        & train_df["manipulation_type"].astype(str).eq("clean_direct")
        & train_df["ground_truth_origin"].astype(str).eq("human")
    ].head(max_rows)
    rows: list[dict] = []
    for idx, (_, row) in enumerate(
        tqdm_iter(list(sources.iterrows()), desc="4A edited/splice synth", unit="file"),
        start=1,
    ):
        audio = resolve_audio(str(row["audio_path"]))
        if audio is None or audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            y, sr = load_audio(str(audio), target_sample_rate=16000)
            z = synthetic_edited_splice(y, sr, seed=seed + idx)
            out = row.to_dict()
            out.update(extract_file_acoustic_features(z, sr))
            out["sample_id"] = f"{row.get('sample_id', 'row')}__synth_edited_splice"
            out["feature_status"] = "ok"
            out["eval_split"] = "train"
            out["leakage_safe_split"] = "train"
            out["stage1_target_manipulated"] = 1
            out["stage2_target_type"] = "edited_spliced"
            out["synthetic_kind"] = "edited_splice"
            rows.append(out)
        except Exception:
            continue
    return pd.DataFrame(rows)


def build_platform_compression_rows(
    train_df: pd.DataFrame,
    *,
    max_rows: int,
) -> pd.DataFrame:
    """AI clean train files -> platform_compression positives."""
    import sys

    if str(RELEASE) not in sys.path:
        sys.path.insert(0, str(RELEASE))
    from src.audio_io import load_audio  # noqa: E402

    sources = train_df[
        train_df["feature_status"].eq("ok")
        & train_df["manipulation_type"].astype(str).eq("clean_direct")
        & train_df["ground_truth_origin"].astype(str).eq("ai")
    ].head(max_rows)
    rows: list[dict] = []
    modes = synthetic_platform_modes()
    for idx, (_, row) in enumerate(
        tqdm_iter(list(sources.iterrows()), desc="4A platform synth", unit="file"),
        start=1,
    ):
        if len(rows) >= max_rows:
            break
        audio = resolve_audio(str(row["audio_path"]))
        if audio is None or audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            y, sr = load_audio(str(audio), target_sample_rate=16000)
        except Exception:
            continue
        mode = modes[(idx - 1) % len(modes)]
        z = channel_degrade(y, sr, mode)
        out = row.to_dict()
        out.update(extract_file_acoustic_features(z, sr))
        out["sample_id"] = f"{row.get('sample_id', 'row')}__synth_platform_{mode}"
        out["feature_status"] = "ok"
        out["eval_split"] = "train"
        out["leakage_safe_split"] = "train"
        out["stage1_target_manipulated"] = 1
        out["stage2_target_type"] = "platform_compression"
        out["synthetic_kind"] = f"platform_{mode}"
        rows.append(out)
    return pd.DataFrame(rows)


def build_mixer_codec_augmentation_rows(
    train_df: pd.DataFrame,
    *,
    max_rows: int,
    policy: str = "v3_targeted",
    progress_every: int = 1,
) -> pd.DataFrame:
    """Reuse mixer retrain augmentation; map positives into stage2 labels."""
    aug = augmentation_rows(
        train_df,
        max_rows=max_rows,
        progress_every=progress_every,
        policy=policy,
    )
    if aug.empty:
        return aug
    out = aug.copy()
    out["stage1_target_manipulated"] = out["target_is_mixer_channel"].astype(int)
    out["stage2_target_type"] = np.where(
        out["target_is_mixer_channel"].astype(int).eq(1),
        "mixer_channel",
        "unknown_channel_artifact",
    )
    out["synthetic_kind"] = "codec_aug_" + out["augmentation_mode"].astype(str)
    return out
