"""
Phase 7B: Validate forensic_labeled_master.csv against label schema rules.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))
from phase7.analyze_forensic_test_results import has_valid_suspicious_timestamps, parse_bool

ALLOWED = {
    "origin_label": {"human_likely", "ai_likely", "mixed_or_partial_ai", "uncertain"},
    "manipulation_label": {
        "clean_original",
        "replayed_or_re_recorded",
        "channel_processed",
        "platform_compressed",
        "edited_or_spliced",
        "environment_mismatch",
        "noisy_low_quality",
        "uncertain",
    },
    "attack_hint": {"bonafide", "synthesis", "voice_conversion", "replay", "unknown"},
    "risk_level": {"low", "medium", "high", "inconclusive"},
    "origin_binary": {"human", "ai", "mixed", "unknown"},
    "manipulation_binary": {"clean", "manipulated", "uncertain"},
    "review_status": {"approved", "needs_review", "rejected"},
    "label_confidence": {"high", "medium", "low"},
    "dataset_role": {"controlled_holdout", "training_pool", "evaluation_only", "unknown"},
    "training_readiness": {
        "not_ready_for_training",
        "ready_for_training_preview",
        "ready_for_training",
        "unknown",
    },
}

REQUIRED_COLUMNS = [
    "test_id",
    "audio_path",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "origin_binary",
    "manipulation_binary",
    "review_status",
    "label_confidence",
    "use_for_training",
    "dataset_role",
    "training_readiness",
    "training_warning",
]


def _resolve_audio(audio_path: str, repo_root: Path) -> Path:
    p = Path(audio_path)
    if p.is_file():
        return p.resolve()
    c = (repo_root / audio_path).resolve()
    return c if c.is_file() else p.resolve()


def _check_label_conflicts(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for _, r in df.iterrows():
        tid = str(r.get("test_id", ""))
        manip = str(r.get("manipulation_type", "")).strip().lower()
        gt_origin = str(r.get("ground_truth_origin", "")).strip().lower()
        origin = str(r.get("origin_label", "")).strip().lower()
        mlabel = str(r.get("manipulation_label", "")).strip().lower()
        ahint = str(r.get("attack_hint", "")).strip().lower()
        partial_bin = int(_partial_bin(r.get("partial_fabrication_binary")))

        if manip == "partial_ai_insert":
            if origin != "mixed_or_partial_ai":
                errors.append(f"{tid}: partial_ai_insert requires origin_label=mixed_or_partial_ai (got {origin})")
            if mlabel != "edited_or_spliced":
                errors.append(f"{tid}: partial_ai_insert requires manipulation_label=edited_or_spliced (got {mlabel})")
            if partial_bin != 1:
                errors.append(f"{tid}: partial_ai_insert requires partial_fabrication_binary=1")
            if parse_bool(r.get("use_for_training")):
                if not has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time")):
                    errors.append(f"{tid}: use_for_training=true but partial timestamps missing")

        if manip == "human_replay":
            if origin != "human_likely":
                errors.append(f"{tid}: human_replay requires origin_label=human_likely (got {origin})")
            if mlabel != "replayed_or_re_recorded":
                errors.append(f"{tid}: human_replay requires manipulation_label=replayed_or_re_recorded (got {mlabel})")

        if manip == "ai_replay":
            if origin != "ai_likely":
                errors.append(f"{tid}: ai_replay requires origin_label=ai_likely (got {origin})")
            if mlabel != "replayed_or_re_recorded":
                errors.append(f"{tid}: ai_replay requires manipulation_label=replayed_or_re_recorded (got {mlabel})")

        if manip == "mixer_processed" and gt_origin == "human":
            if origin != "human_likely":
                errors.append(f"{tid}: human mixer requires origin_label=human_likely (got {origin})")
            if mlabel != "channel_processed":
                errors.append(f"{tid}: human mixer requires manipulation_label=channel_processed (got {mlabel})")
            if ahint == "voice_conversion":
                warnings.append(f"{tid}: human_mixer_should_not_be_voice_conversion")

        if manip == "clean_direct" and gt_origin == "human":
            if origin != "human_likely":
                errors.append(f"{tid}: clean_direct human requires origin_label=human_likely (got {origin})")
            if mlabel != "clean_original":
                errors.append(f"{tid}: clean_direct human requires manipulation_label=clean_original (got {mlabel})")

        if manip == "clean_direct" and gt_origin == "ai":
            if origin != "ai_likely":
                errors.append(f"{tid}: clean_direct ai requires origin_label=ai_likely (got {origin})")
            if mlabel != "clean_original":
                errors.append(f"{tid}: clean_direct ai requires manipulation_label=clean_original (got {mlabel})")

        if str(r.get("dataset_role", "")).strip().lower() == "controlled_holdout":
            if parse_bool(r.get("use_for_training")):
                errors.append(f"{tid}: controlled_holdout must have use_for_training=false")

    return errors, warnings


def _partial_bin(value) -> int:
    if parse_bool(value) is True:
        return 1
    if parse_bool(value) is False:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def validate_master(df: pd.DataFrame, repo_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    for field, allowed in ALLOWED.items():
        if field not in df.columns:
            continue
        bad = df[~df[field].astype(str).str.lower().isin(allowed)][field].unique()
        if len(bad):
            errors.append(f"Invalid {field} values: {list(bad)[:10]}")

    if "test_id" in df.columns:
        dup_ids = df[df["test_id"].duplicated(keep=False)]["test_id"].unique()
        if len(dup_ids):
            errors.append(f"Duplicate test_id: {list(dup_ids)}")

    if "audio_path" in df.columns:
        dup_paths = df[df["audio_path"].duplicated(keep=False)]["audio_path"].unique()
        if len(dup_paths):
            warnings.append(f"Duplicate audio_path: {len(dup_paths)} entries")

        missing = []
        for p in df["audio_path"].astype(str):
            if not _resolve_audio(p, repo_root).is_file():
                missing.append(p)
        if missing:
            warnings.append(f"Missing audio files: {len(missing)} ({missing[:3]}...)")

    for col in ("duration", "sample_rate"):
        if col in df.columns:
            empty = df[col].isna() | (df[col].astype(str).str.strip() == "")
            if empty.any():
                warnings.append(f"Missing {col} on {int(empty.sum())} rows")

    if "use_for_training" in df.columns:
        n_train = int((df["use_for_training"] == True).sum())
        if n_train > 0:
            errors.append(f"use_for_training=true on {n_train} rows (must be 0 for controlled holdout)")

    if "manipulation_type" in df.columns:
        partial = df[df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert"]
        for _, r in partial.iterrows():
            has_ts = has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time"))
            if not has_ts:
                warnings.append(f"{r.get('test_id')}: partial_ai_insert without suspicious timestamps")

    train_bad = df[(df["use_for_training"] == True) & (df["review_status"].astype(str) != "approved")]
    if len(train_bad):
        errors.append(f"use_for_training=true with review_status!=approved: {len(train_bad)} rows")

    conflict_errors, conflict_warnings = _check_label_conflicts(df)
    errors.extend(conflict_errors)
    warnings.extend(conflict_warnings)

    return errors, warnings


def write_validation_report(
    path: Path,
    df: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
    repo_root: Path,
) -> None:
    total = len(df)
    approved = int((df["review_status"].astype(str) == "approved").sum()) if "review_status" in df.columns else 0
    needs = int((df["review_status"].astype(str) == "needs_review").sum()) if "review_status" in df.columns else 0
    rejected = int((df["review_status"].astype(str) == "rejected").sum()) if "review_status" in df.columns else 0
    n_train = int((df["use_for_training"] == True).sum()) if "use_for_training" in df.columns else -1
    n_holdout = int((df["dataset_role"].astype(str).str.lower() == "controlled_holdout").sum()) if "dataset_role" in df.columns else 0

    lines = [
        "# Forensic Dataset Validation Report — Phase 7B",
        "",
        f"**Input rows:** {total}  ",
        f"**Critical errors:** {len(errors)}  ",
        f"**Warnings:** {len(warnings)}  ",
        "",
        "---",
        "",
        "## 1. Summary counts",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total files | {total} |",
        f"| Approved | {approved} |",
        f"| Needs review | {needs} |",
        f"| Rejected | {rejected} |",
        f"| dataset_role=controlled_holdout | {n_holdout} |",
        f"| use_for_training=true | {n_train} |",
        "",
    ]

    if "origin_label" in df.columns:
        lines.append("## 2. Count by origin_label\n")
        for k, v in df["origin_label"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    if "manipulation_label" in df.columns:
        lines.append("## 3. Count by manipulation_label\n")
        for k, v in df["manipulation_label"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    if "attack_hint" in df.columns:
        lines.append("## 4. Count by attack_hint\n")
        for k, v in df["attack_hint"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    if "risk_level" in df.columns:
        lines.append("## 5. Count by risk_level\n")
        for k, v in df["risk_level"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    if "language" in df.columns:
        lines.append("## 6. Count by language\n")
        for k, v in df["language"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    if "platform" in df.columns:
        lines.append("## 7. Count by platform\n")
        for k, v in df["platform"].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    partial = df[df.get("manipulation_type", pd.Series(dtype=str)).astype(str).str.lower() == "partial_ai_insert"]
    partial_no_ts = sum(
        1
        for _, r in partial.iterrows()
        if not has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time"))
    )
    lines.extend(
        [
            "## 8. Partial fabrication timestamps",
            "",
            f"- partial_ai_insert rows: {len(partial)}",
            f"- Missing suspicious timestamps: {partial_no_ts}",
            "",
            "## 9. Training readiness verdict",
            "",
            "**Phase 7A/T1–T5 is `controlled_holdout` — NOT used for training.**",
            "",
            "- All rows must have `use_for_training=false` (current: "
            f"**{n_train}** with true — must be **0**).",
            "- `forensic_training_manifest_preview.csv` is a **future CSV format preview** only.",
            "- Approved rows may use `use_for_validation=true` and `use_for_testing=true`.",
            "",
            "Phase 7C fine-tuning requires a **larger collected dataset** (see gap analysis).",
            "",
            "---",
            "",
            "## 10. Errors",
            "",
        ]
    )
    if errors:
        lines.extend(f"- {e}" for e in errors)
    else:
        lines.append("- None")
    lines.extend(["", "## 11. Warnings", ""])
    if warnings:
        lines.extend(f"- {w}" for w in warnings)
    else:
        lines.append("- None")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7B — validate forensic labels")
    p.add_argument("--input", type=str, required=True)
    p.add_argument("--output", type=str, default="reports/phase7_dataset/forensic_dataset_validation_report.md")
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    p.add_argument("--allow_warnings", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.input, low_memory=False)
    errors, warnings = validate_master(df, Path(args.repo_root))
    write_validation_report(Path(args.output), df, errors, warnings, Path(args.repo_root))
    print(f"[SAVE] {args.output}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    if "use_for_training" in df.columns:
        print(f"use_for_training=true rows: {int((df['use_for_training'] == True).sum())}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    if warnings and not args.allow_warnings:
        for w in warnings:
            print(f"  WARN: {w}")
        sys.exit(2)
    print("[OK] Validation passed.")


if __name__ == "__main__":
    main()
