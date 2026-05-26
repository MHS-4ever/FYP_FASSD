"""
Phase 7C1: Summarize collection manifest status (counts, gaps, next actions).

Does not train models.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]

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


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _has_timestamps(row) -> bool:
    return bool(_safe_str(row.get("suspicious_start_time"))) and bool(
        _safe_str(row.get("suspicious_end_time"))
    )


def summarize(df: pd.DataFrame, target_counts_path: Path | None) -> str:
    lines = ["# Phase 7C1 Collection Status", ""]
    n = len(df)
    lines.append(f"**Total manifest rows:** {n}")
    if n:
        lines.append(f"**Unique base_id:** {df['base_id'].nunique()}")
        lines.append(f"**Unique variant_id:** {df['variant_id'].nunique()}")
    lines.append(f"**Expected (23 × 8):** 184")
    lines.append("")

    if n == 0:
        lines.append("_Empty manifest._")
        return "\n".join(lines)

    def section(title: str, col: str):
        lines.append(f"## {title}")
        lines.append("")
        for k, v in df[col].value_counts().items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    section("By split", "split")
    section("By source_origin", "source_origin")
    section("By manipulation_type", "manipulation_type")
    section("By origin_label", "origin_label")
    section("By manipulation_label", "manipulation_label")
    section("By review_status", "review_status")
    section("By quality_status", "quality_status")

    by_base: dict[str, set[str]] = defaultdict(set)
    for _, r in df.iterrows():
        by_base[_safe_str(r["base_id"])].add(_safe_str(r["variant_id"]))

    missing = []
    for base, found in sorted(by_base.items()):
        miss = set(ROUND1_VARIANTS) - found
        if miss:
            missing.append(f"- `{base}`: {', '.join(sorted(miss))}")
    lines.append("## Missing variants per base_id")
    lines.append("")
    lines.extend(missing if missing else ["- None"])
    lines.append("")

    fab = df[df["variant_id"].astype(str).str.endswith("_fabricated")]
    fab_no_ts = fab[~fab.apply(_has_timestamps, axis=1)]
    lines.append("## Fabricated files missing timestamps")
    lines.append("")
    lines.append(f"- Total fabricated rows: {len(fab)}")
    lines.append(f"- Missing timestamps: {len(fab_no_ts)}")
    if len(fab_no_ts):
        for sid in fab_no_ts["sample_id"].head(20):
            lines.append(f"  - {sid}")
        if len(fab_no_ts) > 20:
            lines.append(f"  - ... and {len(fab_no_ts) - 20} more")
    lines.append("")

    needs = df[df["review_status"].astype(str) == "needs_review"]
    lines.append(f"## Rows with review_status=needs_review: {len(needs)}")
    lines.append("")

    lines.append("## Next required actions")
    lines.append("")
    actions = []
    if len(fab_no_ts):
        actions.append(
            "1. Fill `phase7c1_fabricated_timestamps_to_fill.csv` and merge into manifest "
            "(suspicious_start_time / suspicious_end_time)."
        )
    if missing:
        actions.append("2. Record missing variant files for incomplete base_ids.")
    if len(df) < 184:
        actions.append(f"3. Collection incomplete: {n}/184 rows in manifest.")
    actions.append("4. Run `validate_phase7c1_collection_manifest.py` with `--allow_missing_audio` if paths differ.")
    actions.append("5. After validation passes, plan Phase 7C feature extraction (not in this step).")
    lines.extend(actions)
    lines.append("")

    if target_counts_path and target_counts_path.is_file():
        lines.append(f"Target counts reference: `{target_counts_path.name}`")
        lines.append("")

    return "\n".join(lines)


def parse_args():
    p = argparse.ArgumentParser(description="Summarize Phase 7C1 collection manifest")
    p.add_argument("--manifest", type=str, required=True)
    p.add_argument("--target_counts", type=str, default="reports/phase7/phase7c1_collection/phase7c1_target_counts.csv")
    p.add_argument("--output_md", type=str, default="reports/phase7/phase7c1_collection/phase7c1_collection_status.md")
    return p.parse_args()


def main():
    args = parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(f"ERROR: manifest not found: {manifest}")
        raise SystemExit(1)
    df = pd.read_csv(manifest, low_memory=False)
    tc = Path(args.target_counts) if args.target_counts else None
    md = summarize(df, tc)
    out = Path(args.output_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"[SAVE] {out}")
    print(f"Rows: {len(df)} | base_ids: {df['base_id'].nunique() if len(df) else 0}")
    fab = df[df["variant_id"].astype(str).str.endswith("_fabricated")]
    no_ts = sum(1 for _, r in fab.iterrows() if not _has_timestamps(r))
    print(f"Fabricated missing timestamps: {no_ts}/{len(fab)}")


if __name__ == "__main__":
    main()
