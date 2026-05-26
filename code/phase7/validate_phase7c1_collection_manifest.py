"""
Phase 7C1: Validate Round-1 forensic collection manifest (8 variants per base_id).

Does not train models.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
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


def _resolve_audio(audio_path: str, repo_root: Path) -> Path | None:
    p = Path(audio_path)
    if p.is_file():
        return p
    c = repo_root / audio_path
    return c if c.is_file() else None


def validate_manifest(
    df: pd.DataFrame,
    repo_root: Path,
    *,
    strict: bool = False,
    allow_missing_audio: bool = False,
) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict = {"category_counts": Counter()}

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return errors, warnings, stats

    # Duplicate sample_id
    sids = df["sample_id"].astype(str).str.strip()
    dup_sid = sids[sids != ""].duplicated(keep=False)
    if dup_sid.any():
        errors.append(f"Duplicate sample_id: {int(dup_sid.sum())} rows")

    paths = df["audio_path"].astype(str).str.strip()
    dup_paths = paths[paths != ""].duplicated(keep=False)
    if dup_paths.any():
        errors.append(f"Duplicate audio_path: {int(dup_paths.sum())} rows")

    by_group: dict[str, list[dict]] = defaultdict(list)
    by_base: dict[str, set[str]] = defaultdict(set)
    base_to_split: dict[str, str] = {}
    group_to_split: dict[str, str] = {}

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
        audio_path = _safe_str(row.get("audio_path"))
        review = _safe_str(row.get("review_status")).lower()
        path_low = audio_path.lower()
        notes = _safe_str(row.get("notes")).lower()

        stats["category_counts"][variant or "unknown"] += 1

        if group:
            by_group[group].append(row)
        if base and variant:
            by_base[base].add(variant)

        if base and split:
            prev = base_to_split.get(base)
            if prev and prev != split:
                errors.append(f"base_id={base}: appears in multiple splits ({prev}, {split})")
            base_to_split[base] = split
        if group and split:
            prev = group_to_split.get(group)
            if prev and prev != split:
                errors.append(f"split_group_id={group}: appears in multiple splits ({prev}, {split})")
            group_to_split[group] = split

        path_blob = f"{path_low} {notes} {sid.lower()}"
        if any(m in path_blob for m in HOLDOUT_MARKERS):
            errors.append(f"{sid}: Phase 7A holdout path or marker in 7C1 manifest")

        if split and split not in ALLOWED_SPLIT:
            warnings.append(f"{sid}: unusual split value '{split}'")

        if gender and gender not in ALLOWED_GENDER:
            errors.append(f"{sid}: speaker_gender must be male/female/unknown (got {gender})")

        if lang and lang not in ALLOWED_LANGUAGE:
            errors.append(f"{sid}: language must be english/urdu/mixed/unknown (got {lang})")

        resolved = _resolve_audio(audio_path, repo_root)
        if not resolved:
            msg = f"{sid}: audio not found at {audio_path}"
            if allow_missing_audio:
                warnings.append(msg)
            else:
                errors.append(msg)
        elif not allow_missing_audio:
            pass

        dur = _duration_sec(row.get("duration"))
        if dur is not None:
            if dur < 8:
                errors.append(f"{sid}: duration {dur}s < 8s minimum")
            elif dur < 20:
                warnings.append(f"{sid}: duration {dur}s under 20s (recommended 30–60s)")
        else:
            warnings.append(f"{sid}: duration empty")

        is_fabricated = variant.endswith("_fabricated") or partial == 1
        has_ts = has_valid_suspicious_timestamps(
            row.get("suspicious_start_time"), row.get("suspicious_end_time")
        )

        if is_fabricated:
            if not has_ts:
                msg = f"{sid}: fabricated row missing suspicious timestamps (needs_review)"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                if review == "approved":
                    warnings.append(f"{sid}: fabricated row approved but timestamps missing")
            else:
                t0 = float(_safe_str(row.get("suspicious_start_time")))
                t1 = float(_safe_str(row.get("suspicious_end_time")))
                if t1 <= t0:
                    errors.append(f"{sid}: suspicious_end_time must be > suspicious_start_time")
                if t0 < 0:
                    errors.append(f"{sid}: suspicious_start_time must be >= 0")
                if dur is not None:
                    if t0 >= dur:
                        errors.append(
                            f"{sid}: suspicious_start_time {t0}s >= duration {dur}s"
                        )
                    if t1 > dur:
                        errors.append(
                            f"{sid}: suspicious_end_time {t1}s > duration {dur}s"
                        )
        elif partial == 1:
            if not has_ts:
                msg = f"{sid}: partial_fabrication_binary=1 but timestamps missing"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        if manip == "human_replay" and origin == "ai_likely":
            errors.append(f"{sid}: human_replay must not have origin_label=ai_likely")

        if manip == "mixer_processed" and _safe_str(row.get("source_origin")).lower() == "human":
            if attack == "voice_conversion":
                errors.append(f"{sid}: human_mixer_should_not_be_voice_conversion")

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

    for group, rows in by_group.items():
        splits = {_safe_str(r.get("split")).lower() for r in rows if _safe_str(r.get("split"))}
        if len(splits) > 1:
            errors.append(f"split_group_id={group}: multiple splits {splits}")

    for base, found in sorted(by_base.items()):
        missing = set(ROUND1_VARIANTS) - found
        if missing:
            warnings.append(f"base_id={base}: missing variants {sorted(missing)}")
        extra = found - set(ROUND1_VARIANTS)
        if extra:
            warnings.append(f"base_id={base}: extra variants {sorted(extra)}")

    stats["total_rows"] = len(df)
    stats["base_id_count"] = len(by_base)
    stats["expected_rows"] = len(by_base) * 8
    stats["split_counts"] = dict(df["split"].value_counts()) if "split" in df.columns else {}

    return errors, warnings, stats


def write_report(
    path: Path,
    errors: list[str],
    warnings: list[str],
    stats: dict,
    strict: bool,
) -> None:
    lines = [
        "# Phase 7C1 Collection Manifest Validation",
        "",
        f"**Rows:** {stats.get('total_rows', 0)}",
        f"**Base IDs:** {stats.get('base_id_count', 0)}",
        f"**Expected rows (bases × 8):** {stats.get('expected_rows', 0)}",
        f"**Strict mode:** {strict}",
        f"**Errors:** {len(errors)}",
        f"**Warnings:** {len(warnings)}",
        "",
        "## Split counts",
        "",
    ]
    for k, v in sorted(stats.get("split_counts", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Variant counts", ""])
    for k, v in stats.get("category_counts", Counter()).most_common():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {e}" for e in errors) if errors else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {w}" for w in warnings) if warnings else lines.append("- None")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser(description="Validate Phase 7C1 collection manifest")
    p.add_argument("--manifest", type=str, default=None, help="Manifest CSV path")
    p.add_argument("--input", type=str, default=None, help="Alias for --manifest")
    p.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7c1_collection/validation",
    )
    p.add_argument("--output", type=str, default=None, help="Single report path (legacy)")
    p.add_argument("--target_counts", type=str, default=None)
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    p.add_argument("--allow_warnings", action="store_true")
    p.add_argument("--allow_missing_audio", action="store_true")
    p.add_argument("--strict", action="store_true", help="Treat missing fabricated timestamps as errors")
    return p.parse_args()


def main():
    args = parse_args()
    manifest_path = args.manifest or args.input
    if not manifest_path:
        print("ERROR: provide --manifest or --input")
        sys.exit(1)
    path = Path(manifest_path)
    if not path.is_file():
        print(f"ERROR: manifest not found: {path}")
        sys.exit(1)

    df = pd.read_csv(path, low_memory=False)
    errors, warnings, stats = validate_manifest(
        df,
        Path(args.repo_root),
        strict=args.strict,
        allow_missing_audio=args.allow_missing_audio,
    )

    if args.output:
        out = Path(args.output)
    else:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "phase7c1_validation_report.md"

    write_report(out, errors, warnings, stats, args.strict)
    print(f"[SAVE] {out}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    print(f"Rows: {stats.get('total_rows')} | base_ids: {stats.get('base_id_count')}")
    if errors:
        for e in errors[:15]:
            print(f"  ERROR: {e}")
        sys.exit(1)
    if warnings and not args.allow_warnings:
        for w in warnings[:15]:
            print(f"  WARN: {w}")
        sys.exit(2)
    print("[OK] Validation passed.")


if __name__ == "__main__":
    main()
