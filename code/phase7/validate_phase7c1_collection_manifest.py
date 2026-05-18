"""
Phase 7C1: Validate Round-1 forensic collection manifest (8 variants per base_id).

Does not train models. Checks schema, labels, splits, and partial timestamps.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))
from phase7.analyze_forensic_test_results import has_valid_suspicious_timestamps, parse_bool

REQUIRED_COLUMNS = [
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

ALLOWED_GENDER = {"male", "female", "unknown"}
ALLOWED_LANGUAGE = {"english", "urdu", "mixed", "unknown"}
ALLOWED_SPLIT = {"train", "val", "test", "holdout", "unassigned"}

# Phase 7A holdout markers — must not appear as 7C1 training rows
HOLDOUT_MARKERS = (
    "controlled_holdout",
    "phase7_forensic_tests",
    "testing_audios/t1",
    "testing_audios/t2",
    "testing_audios/t3",
    "testing_audios/t4",
    "testing_audios/t5",
    "testing_audios/fabricated",
)

VARIANT_LABEL_RULES: dict[str, dict] = {
    "human_clean": {
        "manipulation_type": "clean_direct",
        "origin_label": "human_likely",
        "manipulation_label": "clean_original",
        "attack_hint": "bonafide",
        "partial_fabrication_binary": 0,
    },
    "human_replay_laptop_mobile": {
        "manipulation_type": "human_replay",
        "origin_label": "human_likely",
        "manipulation_label": "replayed_or_re_recorded",
        "partial_fabrication_binary": 0,
    },
    "human_mixer_processed": {
        "manipulation_type": "mixer_processed",
        "origin_label": "human_likely",
        "manipulation_label": "channel_processed",
        "forbidden_attack_hint": {"voice_conversion"},
        "partial_fabrication_binary": 0,
    },
    "human_fabricated": {
        "manipulation_type": "partial_ai_insert",
        "origin_label": "mixed_or_partial_ai",
        "manipulation_label": "edited_or_spliced",
        "partial_fabrication_binary": 1,
        "requires_timestamps": True,
    },
    "ai_direct": {
        "manipulation_type": "clean_direct",
        "origin_label": "ai_likely",
        "manipulation_label": "clean_original",
        "partial_fabrication_binary": 0,
    },
    "ai_replay_laptop_mobile": {
        "manipulation_type": "ai_replay",
        "origin_label": "ai_likely",
        "manipulation_label": "replayed_or_re_recorded",
        "partial_fabrication_binary": 0,
    },
    "ai_mixer_processed": {
        "manipulation_type": "mixer_processed",
        "origin_label": "ai_likely",
        "manipulation_label": "channel_processed",
        "partial_fabrication_binary": 0,
    },
    "ai_fabricated": {
        "manipulation_type": "partial_ai_insert",
        "origin_label": "mixed_or_partial_ai",
        "manipulation_label": "edited_or_spliced",
        "partial_fabrication_binary": 1,
        "requires_timestamps": True,
    },
}


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _partial_bin(val) -> int:
    if parse_bool(val) is True:
        return 1
    if parse_bool(val) is False:
        return 0
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def _duration_sec(val) -> float | None:
    s = _safe_str(val)
    if not s:
        return None
    try:
        d = float(s)
        return d if d >= 0 else None
    except ValueError:
        return None


def validate_manifest(df: pd.DataFrame, repo_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return errors, warnings

    # Duplicate paths
    paths = df["audio_path"].astype(str).str.strip()
    dup_paths = paths[paths != ""].duplicated(keep=False)
    if dup_paths.any():
        errors.append(f"Duplicate audio_path: {int(dup_paths.sum())} rows")

    by_group: dict[str, list[dict]] = defaultdict(list)
    by_base: dict[str, set[str]] = defaultdict(set)

    for _, r in df.iterrows():
        row = r.to_dict()
        sid = _safe_str(row.get("sample_id"))
        variant = _safe_str(row.get("variant_id")).lower()
        base = _safe_str(row.get("base_id"))
        group = _safe_str(row.get("split_group_id"))
        split = _safe_str(row.get("split")).lower()
        gender = _safe_str(row.get("speaker_gender")).lower()
        lang = _safe_str(row.get("language")).lower()
        manip = _safe_str(row.get("manipulation_type")).lower()
        origin = _safe_str(row.get("origin_label")).lower()
        attack = _safe_str(row.get("attack_hint")).lower()
        partial = _partial_bin(row.get("partial_fabrication_binary"))
        audio_path = _safe_str(row.get("audio_path")).lower()
        notes = _safe_str(row.get("notes")).lower()

        if group:
            by_group[group].append(row)
        if base and variant:
            by_base[base].add(variant)

        # Holdout / 7A leakage
        path_blob = f"{audio_path} {notes} {sid.lower()}"
        if any(m in path_blob for m in HOLDOUT_MARKERS):
            errors.append(f"{sid}: Phase 7A holdout path or marker in 7C1 manifest")

        if split and split not in ALLOWED_SPLIT:
            warnings.append(f"{sid}: unusual split value '{split}'")

        if gender and gender not in ALLOWED_GENDER:
            errors.append(f"{sid}: speaker_gender must be male/female/unknown (got {gender})")

        if lang and lang not in ALLOWED_LANGUAGE:
            errors.append(f"{sid}: language must be english/urdu/mixed/unknown (got {lang})")

        # Duration
        dur = _duration_sec(row.get("duration"))
        if dur is not None:
            if dur < 8:
                errors.append(f"{sid}: duration {dur}s < 8s minimum")
            elif dur < 20:
                warnings.append(f"{sid}: duration {dur}s under 20s (recommended 30–60s)")
        elif _safe_str(row.get("duration")) == "":
            warnings.append(f"{sid}: duration empty")

        # Partial timestamps
        if partial == 1:
            if not has_valid_suspicious_timestamps(
                row.get("suspicious_start_time"), row.get("suspicious_end_time")
            ):
                errors.append(f"{sid}: partial_fabrication_binary=1 but timestamps missing/invalid")
            else:
                t0 = float(_safe_str(row.get("suspicious_start_time")) or 0)
                t1 = float(_safe_str(row.get("suspicious_end_time")) or 0)
                if t1 <= t0:
                    errors.append(f"{sid}: suspicious_end_time must be > suspicious_start_time")

        # Human replay origin
        if manip == "human_replay" and origin == "ai_likely":
            errors.append(f"{sid}: human_replay must not have origin_label=ai_likely")

        # Human mixer attack hint
        if manip == "mixer_processed" and _safe_str(row.get("source_origin")).lower() == "human":
            if attack == "voice_conversion":
                errors.append(f"{sid}: human_mixer_should_not_be_voice_conversion")

        # Variant-specific rules
        rules = VARIANT_LABEL_RULES.get(variant, {})
        if rules:
            for key, expected in rules.items():
                if key == "forbidden_attack_hint":
                    if attack in expected:
                        errors.append(f"{sid}: attack_hint={attack} forbidden for {variant}")
                    continue
                if key == "requires_timestamps":
                    continue
                if key in row:
                    actual = _safe_str(row.get(key)).lower()
                    exp = str(expected).lower() if not isinstance(expected, int) else expected
                    if key == "partial_fabrication_binary":
                        if _partial_bin(row.get(key)) != expected:
                            errors.append(f"{sid}: {variant} expects partial_fabrication_binary={expected}")
                    elif actual != exp:
                        errors.append(f"{sid}: {variant} expects {key}={expected} (got {actual})")
        elif variant:
            warnings.append(f"{sid}: unknown variant_id '{variant}' (not in Round-1 set)")

        # Audio exists (warning only)
        if audio_path:
            p = Path(audio_path)
            if not p.is_file() and not (repo_root / audio_path).is_file():
                warnings.append(f"{sid}: audio not found at {audio_path}")

    # Split consistency per split_group_id
    for group, rows in by_group.items():
        splits = {_safe_str(r.get("split")).lower() for r in rows if _safe_str(r.get("split"))}
        if len(splits) > 1:
            errors.append(f"split_group_id={group}: multiple splits {splits} — paired variants must match")

    # Expected variants per base_id (warning if incomplete)
    for base, found in sorted(by_base.items()):
        missing = set(ROUND1_VARIANTS) - found
        if missing:
            warnings.append(f"base_id={base}: missing variants {sorted(missing)}")
        extra = found - set(ROUND1_VARIANTS)
        if extra:
            warnings.append(f"base_id={base}: extra variants {sorted(extra)}")

    return errors, warnings


def write_report(path: Path, errors: list[str], warnings: list[str], n_rows: int) -> None:
    lines = [
        "# Phase 7C1 Collection Manifest Validation",
        "",
        f"**Rows:** {n_rows}",
        f"**Errors:** {len(errors)}",
        f"**Warnings:** {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {e}" for e in errors) if errors else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {w}" for w in warnings) if warnings else lines.append("- None")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser(description="Validate Phase 7C1 collection manifest")
    p.add_argument("--input", type=str, required=True)
    p.add_argument("--output", type=str, default="reports/phase7c1_collection/phase7c1_validation_report.md")
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    p.add_argument("--allow_warnings", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    path = Path(args.input)
    if not path.is_file():
        print(f"ERROR: manifest not found: {path}")
        sys.exit(1)
    df = pd.read_csv(path, low_memory=False)
    errors, warnings = validate_manifest(df, Path(args.repo_root))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_report(out, errors, warnings, len(df))
    print(f"[SAVE] {out}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    if errors:
        for e in errors[:20]:
            print(f"  ERROR: {e}")
        sys.exit(1)
    if warnings and not args.allow_warnings:
        for w in warnings[:20]:
            print(f"  WARN: {w}")
        sys.exit(2)
    print("[OK] Validation passed.")


if __name__ == "__main__":
    main()
