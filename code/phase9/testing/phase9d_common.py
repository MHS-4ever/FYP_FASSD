"""Shared helpers for Phase 9D end-to-end testing scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}

DEFAULT_CATEGORY_FOLDERS: tuple[str, ...] = (
    "ai_direct",
    "human_direct",
    "human_clean",
    "ai_repeat",
    "human_repeat",
    "ai_replay",
    "human_replay",
    "ai_replay_laptop_mobile",
    "human_replay_laptop_mobile",
    "ai_mixer",
    "human_mixer",
    "ai_mixer_processed",
    "human_mixer_processed",
    "ai_fabricated",
    "human_fabricated",
    "replay",
    "mixer",
    "fabricated",
    "direct",
    "clean",
)

SKIP_DIR_NAME_PARTS: frozenset[str] = frozenset(
    {
        "augmented",
        "rir",
        "noise",
        "features",
        "embeddings",
        "cache",
        "__pycache__",
        "reports",
        "musan",
        "statistics",
        "manifests",
        "features_augmented",
        "features_merged",
        "noise_rir",
    }
)

FOLDER_CATEGORY_MAP: dict[str, str] = {
    "ai_direct": "ai_direct",
    "human_direct": "human_direct",
    "human_clean": "human_direct",
    "ai_repeat": "ai_replay",
    "human_repeat": "human_replay",
    "ai_replay": "ai_replay",
    "human_replay": "human_replay",
    "ai_replay_laptop_mobile": "ai_replay",
    "human_replay_laptop_mobile": "human_replay",
    "ai_mixer": "ai_mixer",
    "human_mixer": "human_mixer",
    "ai_mixer_processed": "ai_mixer",
    "human_mixer_processed": "human_mixer",
    "ai_fabricated": "ai_fabricated",
    "human_fabricated": "human_fabricated",
    "replay": "replay",
    "mixer": "mixer_channel",
    "fabricated": "unknown",
    "direct": "unknown",
    "clean": "human_direct",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_repo_on_path() -> Path:
    root = repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    """Resolve a path relative to base (or repo root). Never returns base alone."""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    root = base or repo_root()
    return (root / p).resolve()


def progress(msg: str, no_progress: bool) -> None:
    if not no_progress:
        print(msg, flush=True)


def detect_expected_category(audio_path: Path) -> str:
    """Infer test category from folder/file name (Phase 9D heuristic)."""
    text = str(audio_path).lower().replace("\\", "/")
    name = audio_path.name.lower()
    parts = "/".join([text, name])

    if "bad_audio_short" in parts or name.startswith("bad_short"):
        return "bad_audio_short"
    if "bad_audio_silent" in parts or name.startswith("bad_silent"):
        return "bad_audio_silent"
    if "bad_audio_invalid" in parts or name.endswith(".wav.txt") or name == "bad_invalid.wav":
        return "bad_audio_invalid"

    if "ai_fabricated" in parts or ("ai" in parts and "fabricated" in parts):
        return "ai_fabricated"
    if "human_fabricated" in parts or ("human" in parts and "fabricated" in parts):
        return "human_fabricated"

    if "human_clean" in parts:
        return "human_direct"
    if "ai_replay" in parts or "ai_repeat" in parts:
        return "ai_replay"
    if "human_replay" in parts or "human_repeat" in parts:
        return "human_replay"

    if "ai_mixer" in parts or "ai_mixer_processed" in parts:
        return "ai_mixer"
    if "human_mixer" in parts or "human_mixer_processed" in parts:
        return "human_mixer"
    if "mixer" in parts or "channel" in parts or "mixer_processed" in parts:
        if "human" in parts:
            return "human_mixer"
        if "ai" in parts:
            return "ai_mixer"
        return "mixer_channel"

    if any(tok in parts for tok in ("replay", "repeat", "rerecord", "rerecorded")):
        if "human" in parts:
            return "human_replay"
        if "ai" in parts:
            return "ai_replay"
        return "replay"

    if "ai_direct" in parts or re.search(r"ai[^/]*direct", parts):
        return "ai_direct"
    if "human_direct" in parts or "human_clean" in parts or re.search(r"human[^/]*direct", parts):
        return "human_direct"
    if re.search(r"\bai\b", parts) and "direct" in name:
        return "ai_direct"
    if re.search(r"\bhuman\b", parts) and "direct" in name:
        return "human_direct"

    return "unknown"


CATEGORY_EXPECTATIONS: dict[str, dict[str, str]] = {
    "ai_direct": {
        "expected_primary_axis": "origin",
        "expected_fusion_behavior": "suspicious_origin_experimental (or inconclusive if low confidence)",
        "expected_manual_review": "true",
        "notes": "Clean AI/direct-origin behavior check; not final proof.",
    },
    "human_direct": {
        "expected_primary_axis": "clean_human",
        "expected_fusion_behavior": "accept_human_clean_experimental or low-risk inconclusive",
        "expected_manual_review": "false_or_true_if_borderline",
        "notes": "Clean human/direct behavior check.",
    },
    "ai_replay": {
        "expected_primary_axis": "replay",
        "expected_fusion_behavior": "suspicious_replay_experimental",
        "expected_manual_review": "true",
        "notes": "Replay/rerecord chain on AI source.",
    },
    "human_replay": {
        "expected_primary_axis": "replay",
        "expected_fusion_behavior": "suspicious_replay_experimental or low if clean human dominates",
        "expected_manual_review": "true",
        "notes": "Human replay may still show replay indicators.",
    },
    "replay": {
        "expected_primary_axis": "replay",
        "expected_fusion_behavior": "suspicious_replay_experimental",
        "expected_manual_review": "true",
        "notes": "Generic replay category.",
    },
    "ai_mixer": {
        "expected_primary_axis": "mixer_channel",
        "expected_fusion_behavior": "suspicious_mixer_channel_experimental",
        "expected_manual_review": "true",
        "notes": "Mixer/channel processing; partial should be gated under mixer context.",
    },
    "human_mixer": {
        "expected_primary_axis": "mixer_channel",
        "expected_fusion_behavior": "suspicious_mixer_channel_experimental or clean if weak",
        "expected_manual_review": "true",
        "notes": "Human mixer-processed audio.",
    },
    "mixer_channel": {
        "expected_primary_axis": "mixer_channel",
        "expected_fusion_behavior": "suspicious_mixer_channel_experimental",
        "expected_manual_review": "true",
        "notes": "Generic mixer/channel category.",
    },
    "ai_fabricated": {
        "expected_primary_axis": "partial_or_origin_with_partial_review",
        "expected_fusion_behavior": "suspicious_partial_fabrication_experimental or needs_review if broad activation",
        "expected_manual_review": "true",
        "notes": "Partial fabrication localization is experimental; broad activation is a known limitation.",
    },
    "human_fabricated": {
        "expected_primary_axis": "partial_or_origin_with_partial_review",
        "expected_fusion_behavior": "partial review expected; may be inconclusive",
        "expected_manual_review": "true",
        "notes": "Human-fabricated partial cases for architecture verification only.",
    },
    "bad_audio_short": {
        "expected_primary_axis": "error_or_manual_review",
        "expected_fusion_behavior": "safe error or inconclusive_manual_review_experimental",
        "expected_manual_review": "true",
        "notes": "Very short audio should not crash pipeline.",
    },
    "bad_audio_silent": {
        "expected_primary_axis": "error_or_manual_review",
        "expected_fusion_behavior": "safe error or inconclusive_manual_review_experimental",
        "expected_manual_review": "true",
        "notes": "Silent audio should be handled safely.",
    },
    "bad_audio_invalid": {
        "expected_primary_axis": "error_or_manual_review",
        "expected_fusion_behavior": "safe load/prediction error without unhandled crash",
        "expected_manual_review": "true",
        "notes": "Invalid audio placeholder for robustness check.",
    },
    "unknown": {
        "expected_primary_axis": "manual_review",
        "expected_fusion_behavior": "inconclusive_manual_review_experimental",
        "expected_manual_review": "true",
        "notes": "Category uncertain from path; manual review expected.",
    },
}


def expectations_for_category(category: str) -> dict[str, str]:
    return dict(CATEGORY_EXPECTATIONS.get(category, CATEGORY_EXPECTATIONS["unknown"]))


def make_case_id(category: str, index: int, stem: str) -> str:
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", stem)[:40]
    return f"phase9d_{category}_{index:03d}_{safe_stem}"


def category_for_folder_name(folder_name: str) -> str:
    """Map controlled folder name to expected test category."""
    key = folder_name.strip().lower()
    mapped = FOLDER_CATEGORY_MAP.get(key)
    if mapped and mapped != "unknown":
        return mapped
    return detect_expected_category(Path(folder_name))


def should_skip_dir_name(name: str) -> bool:
    lower = name.lower()
    return any(part in lower for part in SKIP_DIR_NAME_PARTS)


def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTS
