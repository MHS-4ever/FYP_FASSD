"""
Phase 8B evidence table schema helpers.

Known labels (ground truth) are separate from evidence score columns.
Phase 8B leaves all evidence scores empty — filled later by 8C/8D/8E/8F.
"""

from __future__ import annotations

import hashlib
import re
import wave
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

SCHEMA_VERSION_DEFAULT = "phase8b_v1"

# --- Allowed vocabularies (frozen Phase 8A) ---

ALLOWED_ORIGIN_LABELS = frozenset({"human", "ai_synthetic", "mixed", "unknown", "na"})
ALLOWED_MANIPULATION_LABELS = frozenset(
    {
        "clean",
        "replay_rerecorded",
        "mixer_channel_processed",
        "partial_fabrication",
        "edited_spliced",
        "compressed_low_quality",
        "unknown_manipulation",
    }
)
ALLOWED_FINAL_FORENSIC_STATUS = frozenset(
    {
        "accept_human_clean",
        "suspicious_origin",
        "suspicious_manipulation",
        "suspicious_mixed",
        "inconclusive_manual_review",
    }
)
ALLOWED_FORENSIC_RISK_LEVEL = frozenset({"low", "medium", "high", "inconclusive"})
ALLOWED_MANUAL_REVIEW_REASON = frozenset(
    {
        "none",
        "weak_origin_evidence",
        "conflicting_origin_evidence",
        "strong_manipulation_weak_origin",
        "quality_limited",
        "suspicious_segment_file_conflict",
        "borderline_scores",
        "unknown_domain",
    }
)

FORBIDDEN_COLUMNS = frozenset({"evidence_origin_score", "origin_score"})

# Columns that must stay empty at Phase 8B (evidence + fusion placeholders)
FILE_EVIDENCE_SCORE_COLUMNS = [
    "evidence_origin_human_score",
    "evidence_origin_ai_score",
    "evidence_origin_mixed_score",
    "evidence_origin_unknown_score",
    "evidence_replay_score",
    "evidence_mixer_channel_score",
    "evidence_partial_fabrication_score",
    "evidence_splice_score",
    "evidence_quality_score",
]

FILE_FUSION_PLACEHOLDER_COLUMNS = [
    "calibrated_origin_label",
    "calibrated_manipulation_labels",
    "final_forensic_status",
    "forensic_risk_level",
    "manual_review_required",
    "manual_review_reason",
    "fusion_trace",
    "forensic_summary",
]

SEGMENT_SCORE_COLUMNS = [
    "segment_origin_human_score",
    "segment_origin_ai_score",
    "segment_origin_mixed_score",
    "segment_origin_unknown_score",
    "replay_score",
    "mixer_channel_score",
    "partial_fabrication_score",
    "splice_score",
    "quality_score",
]

SEGMENT_PLACEHOLDER_COLUMNS = [
    "suspicious_segment_flag",
    "segment_reason",
    "segment_evidence_source",
]

FILE_TABLE_COLUMNS = [
    "schema_version",
    "file_id",
    "audio_path",
    "original_manifest_path",
    "original_row_index",
    "duration_sec",
    "sample_rate",
    "source_dataset",
    "split",
    "known_origin_label",
    "known_manipulation_labels",
    "known_segment_labels_available",
    *FILE_EVIDENCE_SCORE_COLUMNS,
    *FILE_FUSION_PLACEHOLDER_COLUMNS,
    "evidence_source_paths",
]

SEGMENT_TABLE_COLUMNS = [
    "schema_version",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
    *SEGMENT_SCORE_COLUMNS,
    *SEGMENT_PLACEHOLDER_COLUMNS,
]

# Legacy / manifest label → frozen origin
ORIGIN_ALIASES: dict[str, str] = {
    "origin_ai": "ai_synthetic",
    "origin_human": "human",
    "ai": "ai_synthetic",
    "ai_likely": "ai_synthetic",
    "ai_synthetic": "ai_synthetic",
    "synthetic": "ai_synthetic",
    "fake": "ai_synthetic",
    "spoof": "ai_synthetic",
    "human": "human",
    "human_likely": "human",
    "bonafide": "human",
    "real": "human",
    "mixed": "mixed",
    "mixed_or_partial_ai": "mixed",
    "unknown": "unknown",
    "na": "na",
    "": "na",
}

# Legacy manipulation → frozen (never map direct_synthetic to manipulation)
MANIPULATION_ALIASES: dict[str, str] = {
    "manipulation_replay": "replay_rerecorded",
    "manipulation_mixer_channel": "mixer_channel_processed",
    "manipulation_partial_fabrication": "partial_fabrication",
    "manipulation_edited_spliced": "edited_spliced",
    "manipulation_compressed_low_quality": "compressed_low_quality",
    "manipulation_clean": "clean",
    "clean": "clean",
    "clean_original": "clean",
    "clean_direct": "clean",
    "replay": "replay_rerecorded",
    "replayed": "replay_rerecorded",
    "replayed_or_re-recorded": "replay_rerecorded",
    "replayed_or_re_recorded": "replay_rerecorded",
    "ai_replay": "replay_rerecorded",
    "human_replay": "replay_rerecorded",
    "mixer": "mixer_channel_processed",
    "mixer_processed": "mixer_channel_processed",
    "channel_processed": "mixer_channel_processed",
    "processed": "mixer_channel_processed",
    "partial": "partial_fabrication",
    "partial_fabrication": "partial_fabrication",
    "partial_ai_insert": "partial_fabrication",
    "edited": "edited_spliced",
    "edited_or_spliced": "edited_spliced",
    "spliced": "edited_spliced",
    "compressed": "compressed_low_quality",
    "low_quality": "compressed_low_quality",
    "unknown_manipulation": "unknown_manipulation",
}

# manipulation_direct_synthetic is origin-only signal
DIRECT_SYNTHETIC_TOKENS = frozenset(
    {
        "manipulation_direct_synthetic",
        "direct_synthetic",
        "direct_synthesis",
    }
)

COLUMN_RENAMES = {
    "filepath": "audio_path",
    "file_path": "audio_path",
    "path": "audio_path",
    "wav_path": "audio_path",
    "duration": "duration_sec",
    "duration_seconds": "duration_sec",
    "length_sec": "duration_sec",
    "sr": "sample_rate",
    "sample_rate_hz": "sample_rate",
    "ground_truth_origin": "ground_truth_origin",
    "ground_truth_manipulation": "ground_truth_manipulation",
    "origin_binary": "origin_binary",
    "manipulation_binary": "manipulation_binary",
}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase/strip headers and apply known renames."""
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    rename = {c: COLUMN_RENAMES[c] for c in out.columns if c in COLUMN_RENAMES}
    return out.rename(columns=rename)


def _slug(value: str, max_len: int = 80) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(value).strip())
    return s[:max_len].strip("_") or "row"


def make_file_id(row: pd.Series, manifest_path: Path, row_index: int) -> str:
    """Stable file_id from manifest identity + row content."""
    for key in ("sample_id", "row_id", "file_id", "filename"):
        if key in row.index and pd.notna(row[key]) and str(row[key]).strip():
            base = _slug(str(row[key]))
            prefix = _slug(manifest_path.stem)
            return f"{prefix}_{row_index:06d}_{base}"
    audio = infer_audio_path(row)
    if audio:
        h = hashlib.sha256(audio.encode("utf-8")).hexdigest()[:12]
        return f"{_slug(manifest_path.stem)}_{row_index:06d}_{h}"
    return f"{_slug(manifest_path.stem)}_{row_index:06d}"


def infer_audio_path(row: pd.Series) -> str | None:
    for key in ("audio_path", "filepath", "file_path", "path", "wav_path"):
        if key in row.index and pd.notna(row[key]) and str(row[key]).strip():
            return str(row[key]).strip()
    return None


def resolve_audio_path(audio_path: str | None) -> Path | None:
    if not audio_path:
        return None
    p = Path(audio_path)
    if p.is_file():
        return p.resolve()
    candidate = (REPO_ROOT / p).resolve()
    if candidate.is_file():
        return candidate
    return None


def get_audio_metadata(audio_path: str | None) -> tuple[float | None, int | None]:
    """Read duration (sec) and sample_rate from WAV via stdlib (no model inference)."""
    resolved = resolve_audio_path(audio_path)
    if resolved is None or resolved.suffix.lower() not in {".wav", ".wave"}:
        return None, None
    try:
        with wave.open(str(resolved), "rb") as wf:
            rate = wf.getframerate()
            frames = wf.getnframes()
            if rate <= 0:
                return None, rate or None
            return frames / float(rate), int(rate)
    except (wave.Error, OSError):
        return None, None


def normalize_origin_label(value: Any) -> str:
    """Map manifest origin fields to frozen vocabulary."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "na"
    token = str(value).strip().lower()
    if token in DIRECT_SYNTHETIC_TOKENS:
        return "ai_synthetic"
    if token in ORIGIN_ALIASES:
        return ORIGIN_ALIASES[token]
    if token in ALLOWED_ORIGIN_LABELS:
        return token
    return "unknown"


def _split_tokens(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[;|,]+", text)
    return [p.strip().lower() for p in parts if p.strip()]


def _collect_manipulation_tokens(row: pd.Series) -> list[str]:
    tokens: list[str] = []
    for col in (
        "known_manipulation_labels",
        "ground_truth_manipulation",
        "manipulation_label",
        "manipulation_type",
        "manipulation_binary",
        "attack_type_original",
        "recording_condition",
    ):
        if col in row.index:
            tokens.extend(_split_tokens(row[col]))
    return tokens


def normalize_manipulation_labels(row: pd.Series) -> str:
    """
    Return semicolon-separated frozen manipulation labels.
    manipulation_direct_synthetic contributes to origin only (handled separately).
    """
    raw_tokens = _collect_manipulation_tokens(row)
    labels: list[str] = []
    seen: set[str] = set()

    for token in raw_tokens:
        if token in DIRECT_SYNTHETIC_TOKENS:
            continue
        mapped = MANIPULATION_ALIASES.get(token, token)
        if mapped in ALLOWED_MANIPULATION_LABELS and mapped not in seen:
            labels.append(mapped)
            seen.add(mapped)

    if not labels:
        return "na"

    if "clean" in seen and len(seen) > 1:
        labels = [x for x in labels if x != "clean"]

    return ";".join(labels)


def infer_origin_from_row(row: pd.Series) -> str:
    """Pick best available origin ground truth from row columns."""
    candidates: list[Any] = []
    for col in (
        "known_origin_label",
        "ground_truth_origin",
        "origin_label",
        "source_origin",
        "origin_binary",
        "label_original",
    ):
        if col in row.index and pd.notna(row[col]):
            candidates.append(row[col])

    for token in _collect_manipulation_tokens(row):
        if token in DIRECT_SYNTHETIC_TOKENS:
            return "ai_synthetic"

    for val in candidates:
        label = normalize_origin_label(val)
        if label != "na":
            return label
    return "na"


def infer_source_dataset(row: pd.Series, manifest_path: Path) -> str:
    for col in ("source_dataset", "data_source", "dataset", "domain"):
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            return _slug(str(row[col]), 40)
    name = manifest_path.stem.lower()
    if "phase7c1" in name or "7c1" in name:
        return "phase7c1"
    if "phase7c2" in name or "7c2" in name:
        return "phase7c2"
    if "asvspoof" in name:
        return "asvspoof"
    if "features" in name:
        return "features"
    return _slug(manifest_path.stem, 40)


def infer_split(row: pd.Series, manifest_path: Path) -> str:
    allowed = {"train", "val", "test", "holdout", "eval_only", "none"}
    if "split" in row.index and pd.notna(row["split"]):
        s = str(row["split"]).strip().lower()
        if s in allowed:
            return s
        if s in {"validation", "valid"}:
            return "val"
        if s in {"eval", "evaluation"}:
            return "eval_only"
    name = manifest_path.stem.lower()
    if "train" in name:
        return "train"
    if "val" in name:
        return "val"
    if "test" in name:
        return "test"
    return "none"


def infer_segment_labels_available(row: pd.Series) -> bool:
    pf = row.get("partial_fabrication_binary")
    if pf is not None and str(pf).strip() in {"1", "1.0", "true", "True", "yes"}:
        start = row.get("suspicious_start_time")
        end = row.get("suspicious_end_time")
        if pd.notna(start) and pd.notna(end) and str(start).strip() and str(end).strip():
            return True
    if row.get("known_segment_labels_available") in (True, "true", "True", 1, "1"):
        return True
    return False


def parse_optional_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def create_segments(
    duration_sec: float,
    segment_length_sec: float,
    segment_hop_sec: float,
) -> list[dict[str, float]]:
    """Non-overlapping or hop-based windows covering [0, duration_sec)."""
    if duration_sec <= 0 or segment_length_sec <= 0:
        return []
    segments: list[dict[str, float]] = []
    start = 0.0
    idx = 0
    hop = segment_hop_sec if segment_hop_sec > 0 else segment_length_sec
    while start < duration_sec:
        end = min(start + segment_length_sec, duration_sec)
        if end <= start:
            break
        segments.append(
            {
                "start_sec": round(start, 6),
                "end_sec": round(end, 6),
                "segment_duration_sec": round(end - start, 6),
                "segment_index": idx,
            }
        )
        idx += 1
        if end >= duration_sec:
            break
        start += hop
    return segments


def segment_overlaps_ground_truth(
    start_sec: float,
    end_sec: float,
    gt_start: float | None,
    gt_end: float | None,
) -> bool:
    if gt_start is None or gt_end is None:
        return False
    return start_sec < gt_end and end_sec > gt_start


def empty_file_evidence_scores() -> dict[str, str]:
    return {col: "" for col in FILE_EVIDENCE_SCORE_COLUMNS}


def empty_file_fusion_placeholders() -> dict[str, str]:
    return {col: "" for col in FILE_FUSION_PLACEHOLDER_COLUMNS}


def empty_segment_scores() -> dict[str, str]:
    return {col: "" for col in SEGMENT_SCORE_COLUMNS}


def empty_segment_placeholders() -> dict[str, str]:
    return {col: "" for col in SEGMENT_PLACEHOLDER_COLUMNS}


def validate_allowed_labels(
    known_origin: str,
    known_manipulation: str,
) -> list[str]:
    """Return list of validation warnings for known labels."""
    warnings: list[str] = []
    if known_origin not in ALLOWED_ORIGIN_LABELS:
        warnings.append(f"unknown origin label: {known_origin}")
    if known_manipulation == "na":
        return warnings
    for part in known_manipulation.split(";"):
        part = part.strip()
        if part and part not in ALLOWED_MANIPULATION_LABELS:
            warnings.append(f"unknown manipulation label: {part}")
        if part in DIRECT_SYNTHETIC_TOKENS:
            warnings.append(f"forbidden manipulation token (use origin): {part}")
    return warnings
