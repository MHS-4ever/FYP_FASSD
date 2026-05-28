#!/usr/bin/env python3
"""
Assemble Phase 8E-0 datasets and leakage audit.

No model training, classifier fitting, or predictions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from progress_utils import iter_with_progress  # noqa: E402
from phase8e0_dataset_utils import (  # noqa: E402
    cleanup_merge_artifact_columns,
    check_required_columns,
    derive_file_targets,
    derive_segment_targets,
    drop_phase8b_placeholder_columns,
    ensure_schema_version_column,
    find_feature_columns,
    find_ssl_embedding_columns,
    infer_source_group_id,
    load_csv_required,
    make_leakage_audit,
    safe_join,
    summarize_dataset,
    write_markdown_report,
)

SCHEMA_VERSION = "phase8e0_v1"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Assemble Phase 8E-0 model-ready datasets.")
    p.add_argument("--file_table", default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv")
    p.add_argument("--segment_table", default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv")
    p.add_argument(
        "--file_acoustic_features",
        default="reports/phase8/features/phase8c_file_acoustic_features.csv",
    )
    p.add_argument(
        "--segment_acoustic_features",
        default="reports/phase8/features/phase8c_segment_acoustic_features.csv",
    )
    p.add_argument(
        "--file_ssl_embeddings",
        default="reports/phase8/embeddings/phase8d_file_ssl_embeddings.csv",
    )
    p.add_argument(
        "--segment_ssl_embeddings",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/models/phase8e0")
    p.add_argument("--report", default="reports/phase8/models/phase8e0/phase8e0_assembly_report.md")
    p.add_argument("--no_progress", action="store_true")
    p.add_argument("--progress_every", type=int, default=100)
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_ROOT / p).resolve()


def _apply_with_progress(
    df: pd.DataFrame,
    fn,
    *,
    desc: str,
    enabled: bool,
    progress_every: int,
) -> pd.DataFrame:
    records = []
    it = iter_with_progress(
        df.iterrows(),
        total=len(df),
        desc=desc,
        enabled=enabled,
        progress_every=progress_every,
        unit="row",
    )
    for _, row in it:
        records.append(fn(row))
    return pd.DataFrame(records)


def main() -> int:
    args = parse_args()
    show_progress = not args.no_progress

    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    file_tbl = load_csv_required(_resolve(args.file_table))
    seg_tbl = load_csv_required(_resolve(args.segment_table))
    file_feats = load_csv_required(_resolve(args.file_acoustic_features))
    seg_feats = load_csv_required(_resolve(args.segment_acoustic_features))
    file_emb = load_csv_required(_resolve(args.file_ssl_embeddings))
    seg_emb = load_csv_required(_resolve(args.segment_ssl_embeddings))

    if len(file_tbl) != 184:
        print(f"[warn] file table rows expected 184, found {len(file_tbl)}")
    if len(seg_tbl) != 4189:
        print(f"[warn] segment table rows expected 4189, found {len(seg_tbl)}")

    check_required_columns(file_tbl, ["file_id", "audio_path", "known_origin_label", "known_manipulation_labels"], "phase8b_file")
    check_required_columns(seg_tbl, ["file_id", "segment_id", "audio_path", "start_sec", "end_sec", "segment_duration_sec"], "phase8b_segment")
    check_required_columns(file_feats, ["file_id"], "phase8c_file_features")
    check_required_columns(seg_feats, ["file_id", "segment_id"], "phase8c_segment_features")
    check_required_columns(file_emb, ["file_id"], "phase8d_file_embeddings")
    check_required_columns(seg_emb, ["file_id", "segment_id"], "phase8d_segment_embeddings")

    # Keep only feature/embedding payload columns before joins.
    file_feature_cols = find_feature_columns(file_feats)
    seg_feature_cols = find_feature_columns(seg_feats)
    file_emb_cols = find_ssl_embedding_columns(file_emb)
    seg_emb_cols = find_ssl_embedding_columns(seg_emb)

    file_join_1 = safe_join(
        file_tbl,
        file_feats[["file_id"] + file_feature_cols],
        ["file_id"],
        "file_evidence_features",
    )
    file_master = safe_join(
        file_join_1,
        file_emb[["file_id"] + file_emb_cols],
        ["file_id"],
        "file_master_join",
    )
    file_master = cleanup_merge_artifact_columns(file_master)
    file_master = drop_phase8b_placeholder_columns(file_master)

    seg_join_1 = safe_join(
        seg_tbl,
        seg_feats[["file_id", "segment_id"] + seg_feature_cols],
        ["file_id", "segment_id"],
        "segment_evidence_features",
    )
    seg_master = safe_join(
        seg_join_1,
        seg_emb[["file_id", "segment_id"] + seg_emb_cols],
        ["file_id", "segment_id"],
        "segment_master_join",
    )
    seg_master = cleanup_merge_artifact_columns(seg_master)
    seg_master = drop_phase8b_placeholder_columns(seg_master)

    file_targets = _apply_with_progress(
        file_master,
        derive_file_targets,
        desc="derive file targets",
        enabled=show_progress,
        progress_every=args.progress_every,
    )
    file_master = pd.concat([file_master.reset_index(drop=True), file_targets], axis=1)
    file_master = ensure_schema_version_column(file_master, SCHEMA_VERSION)
    file_master["source_group_id"] = _apply_with_progress(
        file_master,
        infer_source_group_id,
        desc="infer source groups",
        enabled=show_progress,
        progress_every=args.progress_every,
    )
    file_master["leakage_group_id"] = file_master["source_group_id"]

    seg_master = seg_master.merge(
        file_master[
            [
                "file_id",
                "known_origin_label",
                "known_manipulation_labels",
                "source_group_id",
                "leakage_group_id",
            ]
        ].drop_duplicates("file_id"),
        on="file_id",
        how="left",
        suffixes=("", "_file"),
    )

    seg_targets = _apply_with_progress(
        seg_master,
        derive_segment_targets,
        desc="derive segment targets",
        enabled=show_progress,
        progress_every=args.progress_every,
    )
    seg_master = pd.concat([seg_master.reset_index(drop=True), seg_targets], axis=1)
    seg_master = ensure_schema_version_column(seg_master, SCHEMA_VERSION)
    seg_master = drop_phase8b_placeholder_columns(seg_master)

    origin_df = file_master[
        (file_master["eligible_origin_file_model"] == "true")
        & file_master["target_origin_multiclass"].isin(["human", "ai_synthetic"])
    ].copy()
    origin_df["eligible_origin_file_model"] = "true"

    replay_df = file_master[
        (file_master["eligible_replay_file_model"] == "true")
        & file_master["target_is_replay"].isin(["0", "1"])
    ].copy()
    replay_df = replay_df[
        ((replay_df["target_is_replay"] == "1") | (replay_df["target_is_clean"] == "1"))
        & (replay_df["target_is_mixer_channel"] == "0")
        & (replay_df["target_is_partial_fabrication_file"] == "0")
    ]

    mixer_df = file_master[
        (file_master["eligible_mixer_file_model"] == "true")
        & file_master["target_is_mixer_channel"].isin(["0", "1"])
    ].copy()
    mixer_df = mixer_df[
        ((mixer_df["target_is_mixer_channel"] == "1") | (mixer_df["target_is_clean"] == "1"))
        & (mixer_df["target_is_replay"] == "0")
        & (mixer_df["target_is_partial_fabrication_file"] == "0")
    ]

    partial_loc = seg_master[seg_master["inherited_target_is_partial_fabrication_file"] == "1"].copy()
    partial_loc["eligible_partial_segment_training"] = "false"
    partial_loc["reason_not_training_label"] = (
        "partial fabrication file label is inherited; true suspicious timestamps are required before supervised segment training"
    )

    origin_df = ensure_schema_version_column(origin_df, SCHEMA_VERSION)
    replay_df = ensure_schema_version_column(replay_df, SCHEMA_VERSION)
    mixer_df = ensure_schema_version_column(mixer_df, SCHEMA_VERSION)
    partial_loc = ensure_schema_version_column(partial_loc, SCHEMA_VERSION)
    origin_df = drop_phase8b_placeholder_columns(origin_df)
    replay_df = drop_phase8b_placeholder_columns(replay_df)
    mixer_df = drop_phase8b_placeholder_columns(mixer_df)
    partial_loc = drop_phase8b_placeholder_columns(partial_loc)

    audit_df = make_leakage_audit(file_master, seg_master)

    summary_rows = []
    for name, df in [
        ("file_master", file_master),
        ("segment_master", seg_master),
        ("origin_file_dataset", origin_df),
        ("replay_file_dataset", replay_df),
        ("mixer_file_dataset", mixer_df),
        ("partial_localization_prep", partial_loc),
    ]:
        s = summarize_dataset(
            df,
            [
                "target_origin_multiclass",
                "target_is_replay",
                "target_is_mixer_channel",
                "target_is_partial_fabrication_file",
                "eligible_origin_file_model",
                "eligible_replay_file_model",
                "eligible_mixer_file_model",
                "eligible_partial_segment_training",
            ],
        )
        s["dataset"] = name
        summary_rows.append(s)
    summary_df = pd.concat(summary_rows, ignore_index=True)

    missing_rows = [
        {"dataset": "file_master", "metric": "missing_acoustic_cells", "value": str(int(file_master[file_feature_cols].eq("").sum().sum()))},
        {"dataset": "file_master", "metric": "missing_embedding_cells", "value": str(int(file_master[file_emb_cols].eq("").sum().sum()))},
        {"dataset": "segment_master", "metric": "missing_acoustic_cells", "value": str(int(seg_master[seg_feature_cols].eq("").sum().sum()))},
        {"dataset": "segment_master", "metric": "missing_embedding_cells", "value": str(int(seg_master[seg_emb_cols].eq("").sum().sum()))},
        {
            "dataset": "leakage_audit",
            "metric": "blocking_items",
            "value": str(int((audit_df["severity"] == "blocking").sum())),
        },
    ]
    summary_df = pd.concat([summary_df, pd.DataFrame(missing_rows)], ignore_index=True)

    file_master.to_csv(out_dir / "phase8e0_file_level_master_dataset.csv", index=False)
    seg_master.to_csv(out_dir / "phase8e0_segment_level_master_dataset.csv", index=False)
    origin_df.to_csv(out_dir / "phase8e0_origin_file_dataset.csv", index=False)
    replay_df.to_csv(out_dir / "phase8e0_replay_file_dataset.csv", index=False)
    mixer_df.to_csv(out_dir / "phase8e0_mixer_file_dataset.csv", index=False)
    partial_loc.to_csv(out_dir / "phase8e0_partial_fabrication_localization_prep.csv", index=False)
    audit_df.to_csv(out_dir / "phase8e0_leakage_audit.csv", index=False)
    summary_df.to_csv(out_dir / "phase8e0_dataset_summary.csv", index=False)

    write_markdown_report(
        _resolve(args.report),
        summary_df,
        audit_df,
        file_master=file_master,
        origin_df=origin_df,
        replay_df=replay_df,
        mixer_df=mixer_df,
        partial_loc=partial_loc,
    )

    print("Phase 8E-0 assembly complete.")
    print(f"Output dir: {out_dir}")
    print("No training/prediction code executed.")
    print("Partial fabrication segment training blocked unless true timestamps exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
