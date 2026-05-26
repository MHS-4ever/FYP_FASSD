"""
Phase 7C1: Build collection manifest from recorded audio filenames.

Scans audio_dir, assigns labels/splits, loads fabricated timestamps from sidecar JSON/CSV.
Does not train models.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
SIDECAR_EXTS = {".json", ".csv"}

FILENAME_RE = re.compile(
    r"^(human|ai)_(\d{3})_(clean|replay_laptop_mobile|mixer_processed|fabricated|direct)$",
    re.IGNORECASE,
)

ROUND1_VARIANTS = [
    "human_clean",
    "human_replay_laptop_mobile",
    "human_mixer_processed",
    "human_fabricated",
    "ai_direct",
    "ai_replay_laptop_mobile",
    "ai_mixer_processed",
    "ai_fabricated",
]

START_TIME_KEYS = frozenset({
    "suspicious_start_time",
    "start_time",
    "fake_start_time",
    "ai_start_time",
    "insert_start_time",
    "insert_start_sec",
    "start",
    "start_sec",
    "start_seconds",
})

END_TIME_KEYS = frozenset({
    "suspicious_end_time",
    "end_time",
    "fake_end_time",
    "ai_end_time",
    "insert_end_time",
    "insert_end_sec",
    "end",
    "end_sec",
    "end_seconds",
})

# Per fabricated variant folder (human_fabricated / ai_fabricated): sample_id -> metadata row
_BULK_INSERTION_CACHE: dict[str, dict[str, dict]] = {}

BULK_SIDECAR_NAMES = (
    "insertion_stamps.json",
    "insertion_stamps.csv",
    "timestamps.json",
    "timestamps.csv",
    "fabrication_timestamps.json",
    "fabrication_timestamps.csv",
)

NOTES_KEYS = frozenset({
    "notes",
    "description",
    "fabrication_notes",
    "edit_notes",
})

MANIFEST_COLUMNS = [
    "sample_id",
    "audio_path",
    "base_id",
    "variant_id",
    "speaker_id",
    "speaker_gender",
    "speaker_type",
    "language",
    "script_id",
    "source_origin",
    "manipulation_type",
    "platform",
    "device_chain",
    "recording_condition",
    "ground_truth_origin",
    "ground_truth_manipulation",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "duration",
    "sample_rate",
    "channels",
    "split_group_id",
    "split",
    "collection_date",
    "collector",
    "quality_status",
    "review_status",
    "notes",
]

HUMAN_MIXER_NOTE = (
    "Human audio played from laptop, mixer/equalizer changed during playback, recorded on mobile."
)
AI_MIXER_NOTE = (
    "AI audio played from laptop, mixer/equalizer changed during playback, recorded on mobile."
)
HUMAN_FAB_NOTE = (
    "Mostly human/real audio with AI-generated inserted/replaced segment."
)
AI_FAB_NOTE = (
    "Fabricated mixed file. If mostly AI with human inserted, mention in notes manually."
)
SIDECAR_NOTE_PREFIX = "Timestamps loaded from sidecar:"


@dataclass
class SidecarStats:
    total_fabricated: int = 0
    auto_filled: int = 0
    still_missing: int = 0
    invalid: int = 0
    sidecars_used: list[str] = field(default_factory=list)
    sidecars_not_matched: list[str] = field(default_factory=list)
    invalid_details: list[str] = field(default_factory=list)


@dataclass
class TimestampLoadResult:
    start: float | None = None
    end: float | None = None
    notes: str = ""
    source_path: str = ""
    found: bool = False
    valid: bool = False
    error: str = ""


def _norm_key(key: str) -> str:
    return str(key).strip().lower().replace(" ", "_").replace("-", "_")


def _to_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        v = float(s)
        return v if v == v else None  # NaN check
    except (TypeError, ValueError):
        return None


def _extract_times_from_mapping(data: dict) -> tuple[float | None, float | None, str]:
    norm: dict[str, object] = {}
    for k, v in data.items():
        norm[_norm_key(k)] = v

    start = end = None
    for key in START_TIME_KEYS:
        if key in norm:
            start = _to_float(norm[key])
            if start is not None:
                break
    for key in END_TIME_KEYS:
        if key in norm:
            end = _to_float(norm[key])
            if end is not None:
                break

    if start is None and "insert_start_ms" in norm:
        ms = _to_float(norm["insert_start_ms"])
        if ms is not None:
            start = ms / 1000.0
    if end is None and "insert_end_ms" in norm:
        ms = _to_float(norm["insert_end_ms"])
        if ms is not None:
            end = ms / 1000.0

    notes = ""
    for key in NOTES_KEYS:
        if key in norm and _to_float(norm.get(key)) is None:
            notes = str(norm[key]).strip()
            if notes:
                break
    return start, end, notes


def _flatten_dicts(obj, out: list[dict]) -> None:
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _flatten_dicts(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _flatten_dicts(item, out)


def _sample_id_from_output_value(value: str) -> str:
    """Normalize output_file / filename to manifest sample_id stem."""
    s = str(value).strip().replace("\\", "/")
    if not s:
        return ""
    return Path(s).stem.lower()


def _entry_matches_sample(entry: dict, sample_id: str) -> bool:
    sid = sample_id.lower()
    for key in ("output_file", "filename", "file", "audio_path", "sample_id", "output", "name"):
        if key not in entry:
            continue
        val = _sample_id_from_output_value(str(entry.get(key, "")))
        if val == sid:
            return True
    return False


def _output_file_key_from_entry(entry: dict) -> str:
    for key in ("output_file", "filename", "file", "audio_path", "sample_id"):
        if key in entry:
            k = _sample_id_from_output_value(str(entry[key]))
            if k:
                return k
    return ""


def _load_bulk_insertion_lookup(folder: Path) -> dict[str, dict]:
    """Load insertion_stamps.json/csv for a variant folder (human_fabricated / ai_fabricated)."""
    cache_key = str(folder.resolve())
    if cache_key in _BULK_INSERTION_CACHE:
        return _BULK_INSERTION_CACHE[cache_key]

    lookup: dict[str, dict] = {}
    for name in BULK_SIDECAR_NAMES:
        path = folder / name
        if not path.is_file():
            continue
        try:
            if path.suffix.lower() == ".json":
                raw = json.loads(path.read_text(encoding="utf-8"))
                rows = raw.get("insertions", [])
                if isinstance(rows, list):
                    for entry in rows:
                        if isinstance(entry, dict):
                            key = _output_file_key_from_entry(entry)
                            if key:
                                lookup[key] = entry
                else:
                    candidates: list[dict] = []
                    _flatten_dicts(raw, candidates)
                    for entry in candidates:
                        key = _output_file_key_from_entry(entry)
                        if key and key not in lookup:
                            lookup[key] = entry
            else:
                df = pd.read_csv(path, low_memory=False)
                for _, row in df.iterrows():
                    entry = row.to_dict()
                    key = _output_file_key_from_entry(entry)
                    if key:
                        lookup[key] = entry
        except Exception:
            continue

    _BULK_INSERTION_CACHE[cache_key] = lookup
    return lookup


def _timestamp_from_entry(entry: dict, source_path: str) -> TimestampLoadResult:
    result = TimestampLoadResult(source_path=source_path)
    start, end, notes = _extract_times_from_mapping(entry)
    if start is not None and end is not None:
        result.start, result.end = start, end
        result.notes = notes
        result.found = True
    else:
        result.error = "No start/end pair in metadata entry"
    return result


def _parse_json_sidecar(path: Path, sample_id: str) -> TimestampLoadResult:
    result = TimestampLoadResult(source_path=str(path))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        result.error = f"JSON read error: {e}"
        return result

    insertions = raw.get("insertions")
    if isinstance(insertions, list):
        for entry in insertions:
            if isinstance(entry, dict) and _entry_matches_sample(entry, sample_id):
                parsed = _timestamp_from_entry(entry, str(path))
                if parsed.found:
                    return parsed

    candidates: list[dict] = []
    _flatten_dicts(raw, candidates)
    for mapping in candidates:
        if _entry_matches_sample(mapping, sample_id):
            parsed = _timestamp_from_entry(mapping, str(path))
            if parsed.found:
                return parsed
        start, end, notes = _extract_times_from_mapping(mapping)
        if start is not None and end is not None:
            result.start, result.end, result.notes = start, end, notes
            result.found = True
            return result

    result.error = "No start/end pair found in JSON"
    return result


def _parse_csv_sidecar(path: Path, sample_id: str) -> TimestampLoadResult:
    result = TimestampLoadResult(source_path=str(path))
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        result.error = f"CSV read error: {e}"
        return result

    if df.empty:
        result.error = "CSV is empty"
        return result

    col_map = {_norm_key(c): c for c in df.columns}
    id_cols = [
        c
        for nk, c in col_map.items()
        if nk
        in {
            "sample_id",
            "filename",
            "file",
            "audio",
            "name",
            "id",
            "output_file",
            "output",
        }
    ]

    sample_low = sample_id.lower()
    row_idx = None
    for i, row in df.iterrows():
        row_dict = row.to_dict()
        if _entry_matches_sample(row_dict, sample_id):
            row_idx = i
            break
        for ic in id_cols:
            val = _sample_id_from_output_value(str(row.get(ic, "")))
            if val and (val == sample_low):
                row_idx = i
                break
        if row_idx is not None:
            break

    if row_idx is None:
        result.error = f"No row for sample_id {sample_id}"
        return result

    return _timestamp_from_entry(df.loc[row_idx].to_dict(), str(path))


def _discover_sidecar_paths(audio_path: Path) -> list[Path]:
    """Stem JSON/CSV, bulk insertion_stamps, folder matches, parent folder."""
    stem = audio_path.stem
    folder = audio_path.parent
    seen: set[Path] = set()
    ordered: list[Path] = []

    def add(p: Path) -> None:
        if not p.is_file():
            return
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            ordered.append(rp)

    for name in BULK_SIDECAR_NAMES:
        add(folder / name)

    for ext in (".json", ".csv"):
        add(folder / f"{stem}{ext}")

    if folder.is_dir():
        for p in sorted(folder.iterdir()):
            if p.suffix.lower() in SIDECAR_EXTS:
                if stem.lower() in p.stem.lower() or p.stem.lower() in {
                    "insertion_stamps",
                    "timestamps",
                    "fabrication_timestamps",
                }:
                    add(p)

    parent = folder.parent
    if parent.is_dir() and parent != folder:
        for name in BULK_SIDECAR_NAMES:
            add(parent / name)
        for p in sorted(parent.iterdir()):
            if p.is_file() and p.suffix.lower() in SIDECAR_EXTS and stem.lower() in p.stem.lower():
                add(p)

    return ordered


def _validate_timestamp_range(
    start: float, end: float, duration: float | None
) -> tuple[bool, str]:
    if start < 0:
        return False, "negative start time"
    if end <= start:
        return False, "end must be > start"
    if duration is not None:
        if start >= duration:
            return False, f"start {start}s >= duration {duration}s"
        if end > duration:
            return False, f"end {end}s > duration {duration}s"
    return True, ""


def _load_fabricated_timestamps(audio_path: Path, sample_id: str, duration: float | None) -> TimestampLoadResult:
    folder = audio_path.parent
    bulk = _load_bulk_insertion_lookup(folder)
    sid = sample_id.lower()
    if sid in bulk:
        parsed = _timestamp_from_entry(bulk[sid], f"{folder}/insertion_stamps (bulk)")
        if parsed.found:
            ok, reason = _validate_timestamp_range(parsed.start, parsed.end, duration)
            parsed.valid = ok
            if ok:
                return parsed
            parsed.error = reason

    candidates = _discover_sidecar_paths(audio_path)
    if not candidates and sid not in bulk:
        return TimestampLoadResult(error="no sidecar file found")

    last = TimestampLoadResult(error="no sidecar file found")
    for sidecar in candidates:
        if sidecar.suffix.lower() == ".json":
            parsed = _parse_json_sidecar(sidecar, sample_id)
        else:
            parsed = _parse_csv_sidecar(sidecar, sample_id)

        if not parsed.found:
            last = parsed
            continue

        ok, reason = _validate_timestamp_range(parsed.start, parsed.end, duration)
        parsed.valid = ok
        if ok:
            return parsed
        parsed.error = reason
        last = parsed

    return last


def _apply_fabricated_sidecar(row: dict, audio_path: Path, stats: SidecarStats) -> None:
    stats.total_fabricated += 1
    sample_id = row["sample_id"]
    dur_raw = row.get("duration", "")
    duration = _to_float(dur_raw) if dur_raw != "" else None

    loaded = _load_fabricated_timestamps(audio_path, sample_id, duration)
    base_note = row.get("notes", "")

    if not loaded.found:
        stats.still_missing += 1
        stats.sidecars_not_matched.append(sample_id)
        row["review_status"] = "needs_review"
        row["quality_status"] = "needs_review"
        row["notes"] = (
            f"{base_note} Fill suspicious_start_time and suspicious_end_time. "
            f"(No sidecar metadata found.)"
        ).strip()
        return

    if not loaded.valid:
        stats.invalid += 1
        stats.still_missing += 1
        detail = f"{sample_id}: invalid timestamps from {loaded.source_path} — {loaded.error}"
        stats.invalid_details.append(detail)
        row["review_status"] = "needs_review"
        row["quality_status"] = "needs_review"
        row["notes"] = f"{base_note} Sidecar invalid: {loaded.error}".strip()
        return

    row["suspicious_start_time"] = round(loaded.start, 3)
    row["suspicious_end_time"] = round(loaded.end, 3)
    stats.auto_filled += 1
    rel_sidecar = loaded.source_path
    try:
        rel_sidecar = str(Path(loaded.source_path).resolve())
    except OSError:
        pass
    stats.sidecars_used.append(f"{sample_id}: {rel_sidecar}")

    sidecar_note = f"{SIDECAR_NOTE_PREFIX} {Path(loaded.source_path).name}"
    if loaded.notes:
        sidecar_note += f" | {loaded.notes}"
    row["notes"] = f"{base_note} {sidecar_note}".strip()

    if duration is not None and duration < 8:
        row["review_status"] = "needs_review"
        row["quality_status"] = "needs_review"
        row["notes"] += f" Duration {duration}s below 8s minimum."
    else:
        row["review_status"] = "approved"
        row["quality_status"] = "approved"


def _suffix_to_variant_id(prefix: str, suffix: str) -> str | None:
    prefix = prefix.lower()
    suffix = suffix.lower()
    if suffix == "clean" and prefix == "human":
        return "human_clean"
    if suffix == "direct" and prefix == "ai":
        return "ai_direct"
    if suffix == "replay_laptop_mobile":
        return f"{prefix}_replay_laptop_mobile"
    if suffix == "mixer_processed":
        return f"{prefix}_mixer_processed"
    if suffix == "fabricated":
        return f"{prefix}_fabricated"
    return None


def _split_for_base_num(n: int) -> str:
    if 1 <= n <= 16:
        return "train"
    if 17 <= n <= 19:
        return "val"
    if 20 <= n <= 23:
        return "test"
    return "unassigned"


def _language_from_name(stem: str) -> str:
    low = stem.lower()
    if "english" in low:
        return "english"
    if "urdu" in low:
        return "urdu"
    if "mixed" in low:
        return "mixed"
    return "unknown"


def _probe_audio(path: Path) -> dict:
    out = {"duration": "", "sample_rate": "", "channels": ""}
    if not path.is_file():
        return out
    try:
        import soundfile as sf

        info = sf.info(path)
        out["duration"] = round(float(info.duration), 3)
        out["sample_rate"] = int(info.samplerate)
        out["channels"] = int(info.channels)
        return out
    except Exception:
        pass
    try:
        import librosa

        duration = float(librosa.get_duration(path=path))
        out["duration"] = round(duration, 3)
        y, sr = librosa.load(path, sr=None, mono=False, duration=0.01)
        out["sample_rate"] = int(sr)
        out["channels"] = 1 if getattr(y, "ndim", 1) == 1 else int(y.shape[0])
    except Exception:
        pass
    return out


def _label_row(
    prefix: str,
    variant_id: str,
    base_num: int,
    audio_path: str,
    sample_id: str,
    meta: dict,
) -> dict:
    split_group = f"base_{base_num:03d}"
    base_id = split_group
    speaker_id = f"speaker_{base_num:03d}"
    split = _split_for_base_num(base_num)
    is_fabricated = variant_id.endswith("_fabricated")
    dur = meta.get("duration", "")
    dur_f = _to_float(dur)

    row = {
        "sample_id": sample_id,
        "audio_path": audio_path,
        "base_id": base_id,
        "variant_id": variant_id,
        "speaker_id": speaker_id,
        "speaker_gender": "unknown",
        "speaker_type": "local_speaker" if prefix == "human" else "ai_voice",
        "language": _language_from_name(sample_id),
        "script_id": "unknown",
        "platform": "none",
        "partial_fabrication_binary": 0,
        "suspicious_start_time": "",
        "suspicious_end_time": "",
        "duration": dur,
        "sample_rate": meta.get("sample_rate", ""),
        "channels": meta.get("channels", ""),
        "split_group_id": split_group,
        "split": split,
        "collection_date": date.today().isoformat(),
        "collector": "build_phase7c1_manifest_from_audio",
        "notes": "",
    }

    if variant_id == "human_clean":
        row.update(
            {
                "source_origin": "human",
                "manipulation_type": "clean_direct",
                "device_chain": "direct_recording",
                "recording_condition": "clean_human",
                "ground_truth_origin": "human",
                "ground_truth_manipulation": "clean",
                "origin_label": "human_likely",
                "manipulation_label": "clean_original",
                "attack_hint": "bonafide",
                "risk_level": "low",
            }
        )
    elif variant_id == "human_replay_laptop_mobile":
        row.update(
            {
                "source_origin": "human",
                "manipulation_type": "human_replay",
                "device_chain": "laptop_speaker_to_mobile_recording",
                "recording_condition": "replayed_human_audio",
                "ground_truth_origin": "human",
                "ground_truth_manipulation": "replayed",
                "origin_label": "human_likely",
                "manipulation_label": "replayed_or_re_recorded",
                "attack_hint": "replay",
                "risk_level": "medium",
            }
        )
    elif variant_id == "human_mixer_processed":
        row.update(
            {
                "source_origin": "human",
                "manipulation_type": "mixer_processed",
                "device_chain": "laptop_mixer_mobile_recording",
                "recording_condition": "mixer_changed_during_playback_and_mobile_recording",
                "ground_truth_origin": "human",
                "ground_truth_manipulation": "processed",
                "origin_label": "human_likely",
                "manipulation_label": "channel_processed",
                "attack_hint": "unknown",
                "risk_level": "medium",
                "notes": HUMAN_MIXER_NOTE,
            }
        )
    elif variant_id == "human_fabricated":
        row.update(
            {
                "source_origin": "mixed",
                "manipulation_type": "partial_ai_insert",
                "device_chain": "edited_real_plus_ai",
                "recording_condition": "partial_ai_insert",
                "ground_truth_origin": "mixed",
                "ground_truth_manipulation": "mixed",
                "origin_label": "mixed_or_partial_ai",
                "manipulation_label": "edited_or_spliced",
                "attack_hint": "synthesis",
                "risk_level": "high",
                "partial_fabrication_binary": 1,
                "notes": HUMAN_FAB_NOTE,
            }
        )
    elif variant_id == "ai_direct":
        row.update(
            {
                "source_origin": "ai",
                "manipulation_type": "clean_direct",
                "device_chain": "direct_ai_file",
                "recording_condition": "direct_ai",
                "ground_truth_origin": "ai",
                "ground_truth_manipulation": "clean",
                "origin_label": "ai_likely",
                "manipulation_label": "clean_original",
                "attack_hint": "synthesis",
                "risk_level": "high",
            }
        )
    elif variant_id == "ai_replay_laptop_mobile":
        row.update(
            {
                "source_origin": "ai",
                "manipulation_type": "ai_replay",
                "device_chain": "laptop_speaker_to_mobile_recording",
                "recording_condition": "replayed_ai_audio",
                "ground_truth_origin": "ai",
                "ground_truth_manipulation": "replayed",
                "origin_label": "ai_likely",
                "manipulation_label": "replayed_or_re_recorded",
                "attack_hint": "replay",
                "risk_level": "high",
            }
        )
    elif variant_id == "ai_mixer_processed":
        row.update(
            {
                "source_origin": "ai",
                "manipulation_type": "mixer_processed",
                "device_chain": "laptop_mixer_mobile_recording",
                "recording_condition": "mixer_changed_during_playback_and_mobile_recording",
                "ground_truth_origin": "ai",
                "ground_truth_manipulation": "processed",
                "origin_label": "ai_likely",
                "manipulation_label": "channel_processed",
                "attack_hint": "synthesis",
                "risk_level": "high",
                "notes": AI_MIXER_NOTE,
            }
        )
    elif variant_id == "ai_fabricated":
        row.update(
            {
                "source_origin": "mixed",
                "manipulation_type": "partial_ai_insert",
                "device_chain": "edited_mixed_ai_or_human_insert",
                "recording_condition": "partial_fabrication",
                "ground_truth_origin": "mixed",
                "ground_truth_manipulation": "mixed",
                "origin_label": "mixed_or_partial_ai",
                "manipulation_label": "edited_or_spliced",
                "attack_hint": "synthesis",
                "risk_level": "high",
                "partial_fabrication_binary": 1,
                "notes": AI_FAB_NOTE,
            }
        )

    if is_fabricated:
        # Status set by _apply_fabricated_sidecar
        pass
    elif dur_f is None:
        row["review_status"] = "needs_review"
        row["quality_status"] = "needs_review"
        row["notes"] = (row["notes"] + " " if row["notes"] else "") + "Could not read audio metadata."
    elif dur_f < 8:
        row["review_status"] = "needs_review"
        row["quality_status"] = "needs_review"
        row["notes"] = (row["notes"] + " " if row["notes"] else "") + f"Duration {dur_f}s below 8s minimum."
    else:
        row["review_status"] = "approved"
        row["quality_status"] = "approved"

    return row


def scan_audio_dir(audio_dir: Path) -> tuple[list[Path], list[str]]:
    found: list[Path] = []
    unexpected: list[str] = []
    if not audio_dir.is_dir():
        return found, [f"audio_dir not found: {audio_dir}"]
    for p in sorted(audio_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in AUDIO_EXTS:
            continue
        found.append(p)
        stem = p.stem
        if not FILENAME_RE.match(stem):
            unexpected.append(str(p.relative_to(audio_dir)))
    return found, unexpected


def build_manifest_rows(
    audio_files: list[Path],
    audio_dir: Path,
    repo_root: Path,
    sidecar_stats: SidecarStats,
) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    unexpected: list[str] = []
    for apath in audio_files:
        stem = apath.stem
        m = FILENAME_RE.match(stem)
        if not m:
            unexpected.append(str(apath))
            continue
        prefix, num_s, suffix = m.group(1).lower(), m.group(2), m.group(3).lower()
        base_num = int(num_s)
        variant_id = _suffix_to_variant_id(prefix, suffix)
        if not variant_id:
            unexpected.append(str(apath))
            continue
        try:
            rel = apath.relative_to(repo_root).as_posix()
        except ValueError:
            rel = apath.as_posix()
        meta = _probe_audio(apath)
        row = _label_row(prefix, variant_id, base_num, rel, stem, meta)
        if variant_id.endswith("_fabricated"):
            _apply_fabricated_sidecar(row, apath, sidecar_stats)
        rows.append(row)
    rows.sort(key=lambda r: (r["base_id"], r["variant_id"]))
    return rows, unexpected


def _fabricated_needs_template(row: dict) -> bool:
    start = _to_float(row.get("suspicious_start_time"))
    end = _to_float(row.get("suspicious_end_time"))
    dur = _to_float(row.get("duration"))
    if start is None or end is None:
        return True
    ok, _ = _validate_timestamp_range(start, end, dur)
    return not ok


def write_build_report(
    path: Path,
    *,
    audio_found: int,
    manifest_rows: int,
    base_ids: set[str],
    missing_by_base: dict[str, list[str]],
    unexpected: list[str],
    duration_warnings: list[str],
    split_counts: dict[str, int],
    sidecar: SidecarStats,
) -> None:
    expected = len(base_ids) * 8
    lines = [
        "# Phase 7C1 Manifest Build Report",
        "",
        f"**Audio files found:** {audio_found}",
        f"**Manifest rows created:** {manifest_rows}",
        f"**Base ID count:** {len(base_ids)}",
        f"**Expected rows (bases × 8):** {expected}",
        "",
        "## Fabricated timestamp sidecars",
        "",
        f"- **Total fabricated rows:** {sidecar.total_fabricated}",
        f"- **Timestamps auto-filled:** {sidecar.auto_filled}",
        f"- **Still missing or invalid:** {sidecar.still_missing}",
        f"- **Invalid timestamp parses:** {sidecar.invalid}",
        "",
        "### Sidecar files used",
        "",
    ]
    if sidecar.sidecars_used:
        lines.extend(f"- {u}" for u in sidecar.sidecars_used)
    else:
        lines.append("- None")
    lines.extend(["", "### Fabricated rows with no sidecar matched", ""])
    if sidecar.sidecars_not_matched:
        lines.extend(f"- `{s}`" for s in sidecar.sidecars_not_matched)
    else:
        lines.append("- None")
    lines.extend(["", "### Invalid fabricated timestamps", ""])
    if sidecar.invalid_details:
        lines.extend(f"- {d}" for d in sidecar.invalid_details)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "**Sidecar formats:** JSON/CSV per-file, plus bulk `insertion_stamps.json` / `insertion_stamps.csv` in variant folders (`human_fabricated`, `ai_fabricated`) matched by `output_file`.",
            "",
            "**Supported start keys:** "
            + ", ".join(sorted(START_TIME_KEYS)),
            "",
            "**Supported end keys:** "
            + ", ".join(sorted(END_TIME_KEYS)),
            "",
            "## Split counts",
            "",
        ]
    )
    for k, v in sorted(split_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Missing variants per base_id", ""])
    if missing_by_base:
        for base, missing in sorted(missing_by_base.items()):
            lines.append(f"- `{base}`: {', '.join(missing)}")
    else:
        lines.append("- None (all bases complete)")
    lines.extend(["", "## Unexpected filename patterns", ""])
    if unexpected:
        for u in unexpected[:50]:
            lines.append(f"- {u}")
        if len(unexpected) > 50:
            lines.append(f"- ... and {len(unexpected) - 50} more")
    else:
        lines.append("- None")
    lines.extend(["", "## Duration warnings (< 20s recommended)", ""])
    if duration_warnings:
        lines.extend(f"- {w}" for w in duration_warnings[:30])
    else:
        lines.append("- None")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser(description="Build Phase 7C1 manifest from audio files")
    p.add_argument("--audio_dir", type=str, default="data/phase7c1/raw")
    p.add_argument(
        "--output_manifest",
        type=str,
        default="reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv",
    )
    p.add_argument(
        "--timestamp_template",
        type=str,
        default="reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv",
    )
    p.add_argument(
        "--build_report",
        type=str,
        default="reports/phase7/phase7c1_collection/validation/phase7c1_manifest_build_report.md",
    )
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    return p.parse_args()


def main():
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    audio_dir = (repo_root / args.audio_dir).resolve()
    sidecar_stats = SidecarStats()

    audio_files, scan_unexpected = scan_audio_dir(audio_dir)
    rows, parse_unexpected = build_manifest_rows(
        audio_files, audio_dir, repo_root, sidecar_stats
    )
    unexpected = list(dict.fromkeys(scan_unexpected + parse_unexpected))

    df = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    out_manifest = repo_root / args.output_manifest
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_manifest, index=False)

    fab = df[df["variant_id"].astype(str).str.endswith("_fabricated")]
    ts_cols = [
        "sample_id",
        "audio_path",
        "base_id",
        "variant_id",
        "suspicious_start_time",
        "suspicious_end_time",
        "notes",
    ]
    fab_needs_fill = fab[fab.apply(lambda r: _fabricated_needs_template(r.to_dict()), axis=1)]
    ts_path = repo_root / args.timestamp_template
    fab_needs_fill[ts_cols].to_csv(ts_path, index=False)

    by_base: dict[str, set[str]] = defaultdict(set)
    for _, r in df.iterrows():
        by_base[str(r["base_id"])].add(str(r["variant_id"]))
    missing_by_base = {
        b: sorted(set(ROUND1_VARIANTS) - v)
        for b, v in sorted(by_base.items())
        if set(ROUND1_VARIANTS) - v
    }
    for n in range(1, 24):
        bid = f"base_{n:03d}"
        if bid not in by_base:
            missing_by_base[bid] = list(ROUND1_VARIANTS)

    duration_warnings = []
    for _, r in df.iterrows():
        try:
            d = float(r["duration"])
            if d < 20:
                duration_warnings.append(f"{r['sample_id']}: {d}s")
        except (TypeError, ValueError):
            pass

    split_counts = df["split"].value_counts().to_dict() if len(df) else {}

    write_build_report(
        repo_root / args.build_report,
        audio_found=len(audio_files),
        manifest_rows=len(df),
        base_ids=set(df["base_id"].astype(str)) if len(df) else set(),
        missing_by_base=missing_by_base,
        unexpected=unexpected,
        duration_warnings=duration_warnings,
        split_counts=split_counts,
        sidecar=sidecar_stats,
    )

    print(f"[SAVE] Manifest -> {out_manifest} ({len(df)} rows)")
    print(f"[SAVE] Timestamp template (missing/invalid only) -> {ts_path} ({len(fab_needs_fill)} rows)")
    print(f"[SAVE] Build report -> {repo_root / args.build_report}")
    print(f"Audio files scanned: {len(audio_files)}")
    print(f"Fabricated: {sidecar_stats.total_fabricated} | auto-filled: {sidecar_stats.auto_filled} | still missing/invalid: {sidecar_stats.still_missing}")
    print("")
    print("Sidecar formats supported: JSON, CSV")
    print("Build command:")
    print(
        "python code/phase7/build_phase7c1_manifest_from_audio.py "
        "--audio_dir data/phase7c1/raw "
        "--output_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv "
        "--timestamp_template reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv"
    )
    print("Validation command:")
    print(
        "python code/phase7/validate_phase7c1_collection_manifest.py "
        "--manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv "
        "--output_dir reports/phase7/phase7c1_collection/validation --allow_missing_audio --allow_warnings"
    )


if __name__ == "__main__":
    main()
