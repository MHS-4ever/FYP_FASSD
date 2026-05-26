"""
Phase 7C2: Validate combined training manifests (leakage, holdout, labels, weights).

Does not train models.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.analyze_forensic_test_results import has_valid_suspicious_timestamps
from phase7.build_phase7c2_training_manifests import MANIFEST_COLUMNS, load_holdout_keys, _norm_path, _basename, _safe_str

VALID_ORIGIN_LABELS = {
    "human_likely",
    "ai_likely",
    "mixed_or_partial_ai",
    "uncertain",
}
VALID_MANIP_LABELS = {
    "clean_original",
    "replayed_or_re_recorded",
    "channel_processed",
    "edited_or_spliced",
    "platform_compressed",
    "noisy_low_quality",
    "uncertain",
}
VALID_ATTACK_HINTS = {
    "bonafide",
    "synthesis",
    "voice_conversion",
    "replay",
    "unknown",
}
VALID_ORIGIN_BINARY = {"human", "ai", "mixed", "unknown"}
VALID_MANIP_BINARY = {"clean", "manipulated", "uncertain"}
BOOL_TRUE = {"true", "1", "yes", "y"}
BOOL_FALSE = {"false", "0", "no", "n"}


def _parse_bool_str(val) -> bool | None:
    s = _safe_str(val).lower()
    if s in BOOL_TRUE:
        return True
    if s in BOOL_FALSE:
        return False
    return None


def _load_manifest(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path, low_memory=False)


def _check_required_columns(df: pd.DataFrame, split_name: str) -> list[str]:
    missing = [c for c in MANIFEST_COLUMNS if c not in df.columns]
    if missing:
        return [f"{split_name}: missing columns: {', '.join(missing)}"]
    return []


def _duplicate_within_split(df: pd.DataFrame, split_name: str) -> pd.DataFrame:
    if df.empty or "audio_path" not in df.columns:
        return pd.DataFrame()
    paths = df["audio_path"].astype(str).map(_norm_path)
    dup_mask = paths.duplicated(keep=False)
    if not dup_mask.any():
        return pd.DataFrame()
    sub = df.loc[dup_mask, ["row_id", "sample_id", "audio_path", "data_source"]].copy()
    sub["split"] = split_name
    sub["issue"] = "duplicate_audio_path_within_split"
    return sub


def _cross_split_overlap(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sets = {
        "train": set(train["audio_path"].astype(str).map(_norm_path)),
        "val": set(val["audio_path"].astype(str).map(_norm_path)),
        "test": set(test["audio_path"].astype(str).map(_norm_path)),
    }
    pairs = [("train", "val"), ("train", "test"), ("val", "test")]
    for a, b in pairs:
        inter = sets[a] & sets[b]
        inter.discard("")
        for p in sorted(inter):
            rows.append({"audio_path": p, "split_a": a, "split_b": b, "issue": "cross_split_path_overlap"})
    return pd.DataFrame(rows)


def _holdout_overlap(df: pd.DataFrame, holdout_keys: dict, split_name: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        path = _norm_path(row.get("audio_path", ""))
        base = _basename(path)
        sid = _safe_str(row.get("sample_id")).lower()
        if (
            (path and path in holdout_keys["paths"])
            or (base and base in holdout_keys["basenames"])
            or (sid and sid in holdout_keys["ids"])
        ):
            rows.append(
                {
                    "split": split_name,
                    "sample_id": row.get("sample_id"),
                    "audio_path": row.get("audio_path"),
                    "issue": "phase7a_holdout_overlap",
                }
            )
    return pd.DataFrame(rows)


def _p7c1_group_leakage(all_df: pd.DataFrame) -> list[str]:
    errors = []
    p7 = all_df[all_df["data_source"].astype(str) == "phase7c1"]
    if p7.empty:
        return errors
    for col in ("base_id", "split_group_id"):
        if col not in p7.columns:
            continue
        grp = p7.groupby(col)["split"].apply(lambda s: set(str(x).lower() for x in s))
        for gid, splits in grp.items():
            if len(splits) > 1:
                errors.append(f"CRITICAL: Phase 7C1 {col}={gid} appears in splits {splits}")
    return errors


def validate_manifests(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    holdout_path: Path | None,
    output_dir: Path,
    allow_missing_audio: bool,
) -> tuple[int, int, list[str], list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    critical: list[str] = []
    warnings: list[str] = []

    for name, df in [("train", train), ("val", val), ("test", test)]:
        critical.extend(_check_required_columns(df, name))

    dup_parts = []
    for name, df in [("train", train), ("val", val), ("test", test)]:
        dup_parts.append(_duplicate_within_split(df, name))
    dup_df = pd.concat(dup_parts, ignore_index=True) if dup_parts else pd.DataFrame()
    if not dup_df.empty:
        critical.append(f"Duplicate audio_path within split: {len(dup_df)} rows")

    leak_df = _cross_split_overlap(train, val, test)
    if not leak_df.empty:
        critical.append(f"Cross-split audio_path overlap: {len(leak_df)} paths")

    holdout_keys = load_holdout_keys(holdout_path)
    hold_parts = []
    for name, df in [("train", train), ("val", val), ("test", test)]:
        hold_parts.append(_holdout_overlap(df, holdout_keys, name))
    hold_df = pd.concat(hold_parts, ignore_index=True) if hold_parts else pd.DataFrame()
    if not hold_df.empty:
        critical.append(f"Phase 7A holdout overlap: {len(hold_df)} rows")

    all_df = pd.concat([train, val, test], ignore_index=True)
    critical.extend(_p7c1_group_leakage(all_df))

    # Old replay origin mask
    old_replay = all_df[
        (all_df["data_source"].astype(str) == "old")
        & (all_df["attack_hint"].astype(str).str.lower() == "replay")
    ]
    bad_replay = old_replay[old_replay["use_origin_loss"].astype(str).str.lower() != "false"]
    if len(bad_replay):
        critical.append(f"Old replay rows with use_origin_loss!=false: {len(bad_replay)}")

    # Weights
    weights = pd.to_numeric(all_df["sample_weight"], errors="coerce")
    bad_w = all_df[(weights < 0.1) | (weights > 4.0) | weights.isna()]
    if len(bad_w):
        critical.append(f"sample_weight out of range [0.1, 4.0] or NaN: {len(bad_w)}")

    # Loss masks
    for col in ("use_origin_loss", "use_manipulation_loss", "use_attack_loss", "use_partial_loss"):
        invalid = all_df[col].apply(_parse_bool_str).isna()
        if invalid.any():
            critical.append(f"Invalid boolean in {col}: {int(invalid.sum())} rows")

    # Labels
    bad_origin = ~all_df["origin_label"].astype(str).isin(VALID_ORIGIN_LABELS | {""})
    if bad_origin.any():
        warnings.append(f"Non-standard origin_label: {int(bad_origin.sum())} rows")

    bad_manip = ~all_df["manipulation_label"].astype(str).isin(VALID_MANIP_LABELS | {""})
    if bad_manip.any():
        warnings.append(f"Non-standard manipulation_label: {int(bad_manip.sum())} rows")

    # Fabricated timestamps
    fab = all_df[
        (all_df["data_source"].astype(str) == "phase7c1")
        & (pd.to_numeric(all_df["partial_fabrication_binary"], errors="coerce").fillna(0) == 1)
    ]
    for _, row in fab.iterrows():
        if not has_valid_suspicious_timestamps(
            row.get("suspicious_start_time"), row.get("suspicious_end_time")
        ):
            critical.append(f"Fabricated row missing timestamps: {row.get('sample_id')}")

    # Phase 7C1 size / old dominance
    for split_name, df in [("train", train), ("val", val), ("test", test)]:
        n = len(df)
        if n == 0:
            critical.append(f"{split_name} manifest is empty")
            continue
        p7_n = int((df["data_source"].astype(str) == "phase7c1").sum())
        old_n = int((df["data_source"].astype(str) == "old").sum())
        if p7_n < 10:
            warnings.append(f"{split_name}: Phase 7C1 only {p7_n} rows (very small)")
        if old_n > 0 and p7_n > 0 and old_n / n > 0.92:
            warnings.append(
                f"{split_name}: old data dominates ({old_n}/{n} = {100*old_n/n:.1f}% Phase 7C1)"
            )

    # Distribution CSVs
    label_dist = (
        all_df.groupby(["split", "origin_label", "manipulation_label"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    label_dist.to_csv(output_dir / "phase7c2_label_distribution.csv", index=False)

    source_dist = (
        all_df.groupby(["split", "data_source", "source_subset"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    source_dist.to_csv(output_dir / "phase7c2_source_distribution.csv", index=False)

    weight_dist = (
        all_df.groupby(["split", "data_source"], dropna=False)["sample_weight"]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
    )
    weight_dist.to_csv(output_dir / "phase7c2_weight_distribution.csv", index=False)

    leak_df.to_csv(output_dir / "phase7c2_split_leakage_report.csv", index=False)
    dup_df.to_csv(output_dir / "phase7c2_duplicate_path_report.csv", index=False)

    # Markdown report
    md_lines = [
        "# Phase 7C2 Training Manifest Validation Report",
        "",
        f"- Train rows: **{len(train)}**",
        f"- Val rows: **{len(val)}**",
        f"- Test rows: **{len(test)}**",
        f"- Critical errors: **{len(critical)}**",
        f"- Warnings: **{len(warnings)}**",
        "",
        "## Critical errors",
        "",
    ]
    md_lines.extend([f"- {e}" for e in critical] if critical else ["- None"])
    md_lines.extend(["", "## Warnings", ""])
    md_lines.extend([f"- {w}" for w in warnings] if warnings else ["- None"])
    md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `phase7c2_split_leakage_report.csv`",
            "- `phase7c2_duplicate_path_report.csv`",
            "- `phase7c2_label_distribution.csv`",
            "- `phase7c2_source_distribution.csv`",
            "- `phase7c2_weight_distribution.csv`",
            "",
        ]
    )
    verdict = "PASS" if not critical else "FAIL"
    md_lines.append(f"**Verdict:** {verdict}")
    report_path = output_dir / "phase7c2_training_manifest_validation_report.md"
    report_text = "\n".join(md_lines)
    report_path.write_text(report_text, encoding="utf-8")
    parent_report = output_dir.parent / "phase7c2_training_manifest_validation_report.md"
    parent_report.write_text(report_text, encoding="utf-8")
    print(f"[SAVE] {report_path}")

    return len(critical), len(warnings), critical, warnings


def main():
    p = argparse.ArgumentParser(description="Phase 7C2 — validate training manifests")
    p.add_argument("--train", type=str, required=True)
    p.add_argument("--val", type=str, required=True)
    p.add_argument("--test", type=str, required=True)
    p.add_argument("--phase7a_holdout", type=str, default="reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv")
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7c2_training_prep/validation")
    p.add_argument("--allow_missing_audio", action="store_true")
    p.add_argument("--allow_warnings", action="store_true")
    args = p.parse_args()

    train = _load_manifest(Path(args.train))
    val = _load_manifest(Path(args.val))
    test = _load_manifest(Path(args.test))
    holdout = Path(args.phase7a_holdout) if args.phase7a_holdout else None

    n_crit, n_warn, critical, warnings = validate_manifests(
        train, val, test, holdout, Path(args.output_dir), args.allow_missing_audio
    )

    print(f"Errors: {n_crit} | Warnings: {n_warn}")
    for e in critical[:10]:
        print(f"  [CRITICAL] {e}")
    for w in warnings[:10]:
        print(f"  [WARN] {w}")

    if n_crit > 0:
        print("[FAIL] Validation failed.")
        sys.exit(1)
    if n_warn > 0 and not args.allow_warnings:
        print("[FAIL] Warnings present (use --allow_warnings to pass).")
        sys.exit(1)
    print("[OK] Validation passed.")


if __name__ == "__main__":
    main()
