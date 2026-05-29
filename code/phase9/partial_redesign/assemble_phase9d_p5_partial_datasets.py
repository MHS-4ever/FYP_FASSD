#!/usr/bin/env python3
"""Assemble Phase 9D-P5 partial fabrication redesign datasets (no training)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

from phase9d_p5_partial_utils import (
    SAFE_LOCALIZATION_FEATURES,
    FILE_GATE_ELIGIBLE_CATEGORIES,
    FILE_GATE_METADATA_COLUMNS,
    SEGMENT_METADATA_COLUMNS,
    attach_model_feature_json,
    build_file_gate_feature_columns,
    build_leakage_audit,
    build_segment_localizer_feature_columns,
    compute_balance_summary,
    compute_live_localization_features,
    fabrication_direction_from_category,
    infer_file_category,
    is_partial_positive_category,
    load_timestamp_annotation_rows,
    map_replay_category,
    match_timestamp_to_files,
    progress,
    repo_root_from_here,
    row_has_features,
    sample_negative_segments,
    segment_overlap_metrics,
    segment_source_type_for_negative,
    select_file_acoustic_columns,
    select_segment_acoustic_columns,
    select_ssl_columns,
    timestamp_lookup_from_audit,
)


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P5 partial dataset assembly (dataset only, no training).")
    p.add_argument(
        "--file_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv"),
    )
    p.add_argument(
        "--segment_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv"),
    )
    p.add_argument(
        "--ai_timestamp_csv",
        default=str(root / "data/phase7c1/raw/ai_fabricated/insertion_stamps.csv"),
    )
    p.add_argument(
        "--human_timestamp_csv",
        default=str(root / "data/phase7c1/raw/human_fabricated/insertion_stamps.csv"),
    )
    p.add_argument(
        "--output_dir",
        default=str(root / "reports/phase9/partial_redesign"),
    )
    p.add_argument("--overlap_threshold", type=float, default=0.25)
    p.add_argument("--max_negative_segments_per_category", type=int, default=1000)
    p.add_argument(
        "--negative_sample_strategy",
        choices=["all", "balanced_by_positive", "cap_per_category"],
        default="cap_per_category",
    )
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _to_numeric_series(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def build_file_partial_gate_dataset(file_master: pd.DataFrame) -> pd.DataFrame:
    df = file_master.copy()
    df["file_category"] = df["audio_path"].map(infer_file_category)
    df = df[df["file_category"].isin(FILE_GATE_ELIGIBLE_CATEGORIES)].copy()

    acoustic_cols = select_file_acoustic_columns(df.columns)
    ssl_cols = select_ssl_columns(df.columns)

    rows: list[dict] = []
    for _, row in df.iterrows():
        cat = str(row["file_category"])
        is_positive = is_partial_positive_category(cat)
        target = 1 if is_positive else 0
        label_source = (
            "timestamp_controlled_partial_category" if is_positive else "controlled_negative_category"
        )

        feat_ac = row_has_features(row, acoustic_cols)
        feat_ssl = row_has_features(row, ssl_cols)
        if feat_ac and feat_ssl:
            allowed = "partial_file_gate_training_candidate"
        elif not feat_ac or not feat_ssl:
            allowed = "exclude_missing_features"
        else:
            allowed = "partial_file_gate_training_candidate"

        split_val = str(row.get("split", "")).strip().lower()
        if split_val in {"val", "validation", "test", "holdout"}:
            allowed = "holdout_candidate"

        rows.append(
            {
                "file_id": row.get("file_id", ""),
                "audio_path": row.get("audio_path", ""),
                "source_dataset": row.get("source_dataset", ""),
                "known_origin_label": row.get("known_origin_label", ""),
                "known_manipulation_labels": row.get("known_manipulation_labels", ""),
                "file_category": cat,
                "target_is_partial_fabrication_file": target,
                "partial_file_label_source": label_source,
                "feature_available_acoustic": str(feat_ac).lower(),
                "feature_available_ssl": str(feat_ssl).lower(),
                "split_group_id": row.get("leakage_group_id", row.get("source_group_id", "")),
                "leakage_group_id": row.get("leakage_group_id", ""),
                "allowed_use": allowed,
                **{c: row.get(c, "") for c in acoustic_cols},
                **{c: row.get(c, "") for c in ssl_cols},
            }
        )
    return pd.DataFrame(rows)


def build_segment_partial_localizer_dataset(
    segment_master: pd.DataFrame,
    timestamp_lookup: dict[str, dict[str, float]],
    *,
    overlap_threshold: float,
    negative_sample_strategy: str,
    max_negative_segments_per_category: int,
    random_seed: int,
    show_progress: bool,
) -> pd.DataFrame:
    seg = segment_master.copy()
    seg["file_category"] = seg["audio_path"].map(infer_file_category)
    seg = seg[seg["file_category"].isin(FILE_GATE_ELIGIBLE_CATEGORIES)].copy()

    acoustic_cols = select_segment_acoustic_columns(seg.columns)
    ssl_cols = select_ssl_columns(seg.columns)
    seg = _to_numeric_series(seg, acoustic_cols + ssl_cols + ["start_sec", "end_sec", "segment_duration_sec"])

    localized_parts: list[pd.DataFrame] = []
    file_ids = seg["file_id"].unique()
    for i, fid in enumerate(file_ids):
        if show_progress and i % 50 == 0:
            progress(f"  localization features: file {i + 1}/{len(file_ids)}", enabled=True)
        gx = seg[seg["file_id"] == fid].copy()
        localized_parts.append(compute_live_localization_features(gx))
    seg_loc = pd.concat(localized_parts, ignore_index=True) if localized_parts else seg.copy()

    rows: list[dict] = []
    for _, row in seg_loc.iterrows():
        cat = str(row["file_category"])
        cat = map_replay_category(cat)
        fid = str(row.get("file_id", ""))
        fab_dir = fabrication_direction_from_category(cat)

        try:
            seg_start = float(row["start_sec"])
            seg_end = float(row["end_sec"])
        except (TypeError, ValueError):
            continue

        if is_partial_positive_category(cat):
            ts = timestamp_lookup.get(fid)
            if ts:
                overlap = segment_overlap_metrics(
                    seg_start,
                    seg_end,
                    ts["fabricated_start_sec"],
                    ts["fabricated_end_sec"],
                    overlap_threshold,
                )
                is_positive = 1 if overlap["timestamp_region_label"] == "inside_fabricated_region" else 0
                source_type = "fabricated_inside" if is_positive else "fabricated_outside_same_file"
            else:
                overlap = {
                    "timestamp_overlap_sec": "",
                    "timestamp_overlap_ratio_segment": "",
                    "timestamp_region_label": "outside_fabricated_region",
                }
                is_positive = 0
                source_type = "fabricated_outside_same_file"
        else:
            overlap = {
                "timestamp_overlap_sec": "",
                "timestamp_overlap_ratio_segment": "",
                "timestamp_region_label": "non_partial_file_segment",
            }
            is_positive = 0
            source_type = segment_source_type_for_negative(cat) or "clean_direct_negative"

        rows.append(
            {
                "file_id": fid,
                "segment_id": row.get("segment_id", ""),
                "audio_path": row.get("audio_path", ""),
                "start_sec": row.get("start_sec", ""),
                "end_sec": row.get("end_sec", ""),
                "segment_duration_sec": row.get("segment_duration_sec", ""),
                "file_category": cat,
                "segment_source_type": source_type,
                "target_is_fabricated_segment": is_positive,
                "timestamp_overlap_sec": overlap["timestamp_overlap_sec"],
                "timestamp_overlap_ratio_segment": overlap["timestamp_overlap_ratio_segment"],
                "timestamp_region_label": overlap["timestamp_region_label"],
                "fabrication_direction": fab_dir,
                "split_group_id": row.get("leakage_group_id", row.get("source_group_id", "")),
                "leakage_group_id": row.get("leakage_group_id", ""),
                "allowed_use": "partial_segment_localizer_training_candidate",
                **{c: row.get(c, "") for c in acoustic_cols},
                **{c: row.get(c, "") for c in ssl_cols},
                **{c: row.get(c, "") for c in SAFE_LOCALIZATION_FEATURES if c in row.index},
            }
        )

    full_df = pd.DataFrame(rows)
    sampled = sample_negative_segments(
        full_df,
        strategy=negative_sample_strategy,
        max_negative_segments_per_category=max_negative_segments_per_category,
        random_seed=random_seed,
    )
    return sampled


def write_report(
    path: Path,
    *,
    balance: dict,
    timestamp_audit: pd.DataFrame,
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    matched = int((timestamp_audit["match_status"] == "matched").sum()) if not timestamp_audit.empty else 0
    total_ts = len(timestamp_audit)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    body = f"""# Phase 9D-P5 Partial Redesign Report

Generated: {now}

**Training performed:** NO — dataset assembly only.

## Why P5 is needed

Phase 9D-P4 timestamp diagnostics showed that the current partial segment model carries ranking signal
(top-5 timestamp hit 36/46 fabricated files) but **localized_success_count = 0** and **broad_activation_count = 46/46**.
Broad activation across segments prevents reliable live localization. P5 introduces a two-stage design:

1. **File-level partial candidate gate** — does this file likely contain partial fabrication?
2. **Improved segment localizer v2** — which segments are fabricated, trained with stronger non-partial negatives.

## P4 diagnostic findings (reference)

| Metric | Value |
|--------|-------|
| Fabricated files tested | 46 |
| Top-5 timestamp hit | 36/46 |
| Localized success | 0 |
| Broad activation | 46/46 |
| Human fabricated top-5 | Better than AI fabricated |

## Two-stage design

### Stage 1: `partial_file_candidate_model`

- Dataset: `phase9d_p5_file_partial_gate_dataset.csv`
- Target: `target_is_partial_fabrication_file`
- Positives: ai_fabricated, human_fabricated
- Negatives: direct, replay/repeat, mixer controlled files
- Timestamps identify positives but **timestamp values are not file-model features**.

### Stage 2: `partial_segment_localizer_model_v2`

- Dataset: `phase9d_p5_segment_partial_localizer_dataset.csv`
- Target: `target_is_fabricated_segment`
- Positives: segments overlapping fabricated timestamp region
- Negatives: outside segments from partial files + direct + replay + mixer segments
- Negative sampling: `{args.negative_sample_strategy}` (max {args.max_negative_segments_per_category} per category)

## File-level gate dataset summary

| Metric | Count |
|--------|------:|
| Total rows | {balance['file_gate_total_rows']} |
| Positive (partial) | {balance['file_gate_positive_count']} |
| Negative (controlled) | {balance['file_gate_negative_count']} |

## Segment localizer dataset summary

| Metric | Count |
|--------|------:|
| Total rows | {balance['segment_total_rows']} |
| Positive segments | {balance['segment_positive_count']} |
| Negative segments | {balance['segment_negative_count']} |
| Outside same partial negatives | {balance['segment_negative_outside_same_partial_count']} |
| Clean direct negatives | {balance['segment_negative_clean_count']} |
| Replay negatives | {balance['segment_negative_replay_count']} |
| Mixer negatives | {balance['segment_negative_mixer_count']} |
| AI fabricated positives | {balance['ai_fabricated_positive_segment_count']} |
| Human fabricated positives | {balance['human_fabricated_positive_segment_count']} |

## Timestamp usage policy

- Timestamps loaded from Phase 7C1 insertion_stamps.csv (AI + human fabricated).
- Used **only** for target construction (`target_is_fabricated_segment`, audit labels) and evaluation metadata.
- Timestamp overlap fields are metadata columns, **excluded** from `model_feature_columns_json`.
- Timestamp match audit: {matched}/{total_ts} matched rows.

## Leakage prevention

- Forbidden columns audited in `phase9d_p5_feature_leakage_audit.csv`.
- Separate feature column JSON files for file gate and segment localizer.
- No `fake_score`, `real_score`, fusion outputs, or prior model probabilities as features.

## Class balance warnings

{balance.get('warnings') or 'none'}

## Risks and limitations

- Segment localizer still depends on file-level gate in live pipeline (not trained here).
- Negative sampling caps may exclude rare edge segments; adjust `--max_negative_segments_per_category` if needed.
- Unmatched timestamp rows reduce positive segment labels for affected files.
- Broad activation issue may persist until v2 model is trained and evaluated in P5B.

## Next recommended phase

**Phase 9D-P5B** — train and evaluate file-level partial gate and segment localizer v2 using these datasets.
Do **not** start Phase 9E apps until P5B validation passes.
"""
    path.write_text(body, encoding="utf-8")


def main() -> int:
    args = parse_args()
    show = not args.no_progress
    root = repo_root_from_here(Path(__file__))
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading Phase 8E0 master datasets...", enabled=show)
    file_master = pd.read_csv(args.file_master, low_memory=False)
    segment_master = pd.read_csv(args.segment_master, low_memory=False)

    progress("Loading and matching timestamp annotations...", enabled=show)
    ai_ts = load_timestamp_annotation_rows(Path(args.ai_timestamp_csv), "ai_fabricated")
    human_ts = load_timestamp_annotation_rows(Path(args.human_timestamp_csv), "human_fabricated")
    timestamp_raw = pd.concat([ai_ts, human_ts], ignore_index=True)

    file_gate_pre = file_master.copy()
    file_gate_pre["file_category"] = file_gate_pre["audio_path"].map(infer_file_category)
    file_gate_pre = file_gate_pre[file_gate_pre["file_category"].isin(FILE_GATE_ELIGIBLE_CATEGORIES)]

    timestamp_audit = match_timestamp_to_files(timestamp_raw, file_gate_pre)
    timestamp_lookup = timestamp_lookup_from_audit(timestamp_audit)

    progress("Building file-level partial gate dataset...", enabled=show)
    file_gate_df = build_file_partial_gate_dataset(file_master)
    file_feature_cols = build_file_gate_feature_columns(file_gate_df.columns)
    file_gate_df = attach_model_feature_json(file_gate_df, file_feature_cols)

    progress("Building segment partial localizer dataset...", enabled=show)
    segment_df = build_segment_partial_localizer_dataset(
        segment_master,
        timestamp_lookup,
        overlap_threshold=args.overlap_threshold,
        negative_sample_strategy=args.negative_sample_strategy,
        max_negative_segments_per_category=args.max_negative_segments_per_category,
        random_seed=args.random_seed,
        show_progress=show,
    )
    segment_feature_cols = build_segment_localizer_feature_columns(segment_df.columns)
    segment_df = attach_model_feature_json(segment_df, segment_feature_cols)

    progress("Running leakage audit and balance summary...", enabled=show)
    leakage_file = build_leakage_audit("file_partial_gate", file_gate_df.columns, file_feature_cols)
    leakage_seg = build_leakage_audit("segment_partial_localizer", segment_df.columns, segment_feature_cols)
    leakage_audit = pd.concat([leakage_file, leakage_seg], ignore_index=True)

    balance = compute_balance_summary(file_gate_df, segment_df)
    balance_df = pd.DataFrame([balance])

    file_gate_path = out_dir / "phase9d_p5_file_partial_gate_dataset.csv"
    segment_path = out_dir / "phase9d_p5_segment_partial_localizer_dataset.csv"
    timestamp_audit_path = out_dir / "phase9d_p5_timestamp_target_audit.csv"
    leakage_path = out_dir / "phase9d_p5_feature_leakage_audit.csv"
    balance_path = out_dir / "phase9d_p5_dataset_balance_summary.csv"
    report_path = out_dir / "phase9d_p5_partial_redesign_report.md"
    file_feat_json_path = out_dir / "phase9d_p5_file_gate_feature_columns.json"
    seg_feat_json_path = out_dir / "phase9d_p5_segment_localizer_feature_columns.json"

    file_gate_df.to_csv(file_gate_path, index=False)
    segment_df.to_csv(segment_path, index=False)
    timestamp_audit.to_csv(timestamp_audit_path, index=False)
    leakage_audit.to_csv(leakage_path, index=False)
    balance_df.to_csv(balance_path, index=False)
    file_feat_json_path.write_text(json.dumps(file_feature_cols, indent=2), encoding="utf-8")
    seg_feat_json_path.write_text(json.dumps(segment_feature_cols, indent=2), encoding="utf-8")
    write_report(
        report_path,
        balance=balance,
        timestamp_audit=timestamp_audit,
        file_gate_df=file_gate_df,
        segment_df=segment_df,
        args=args,
    )

    progress(f"Wrote file gate dataset: {file_gate_path}", enabled=show)
    progress(f"Wrote segment localizer dataset: {segment_path}", enabled=show)
    progress(f"Wrote timestamp audit: {timestamp_audit_path}", enabled=show)
    progress(f"Wrote leakage audit: {leakage_path}", enabled=show)
    progress(f"Wrote balance summary: {balance_path}", enabled=show)
    progress(f"Wrote report: {report_path}", enabled=show)
    progress("Phase 9D-P5A assembly complete (no training performed).", enabled=show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
