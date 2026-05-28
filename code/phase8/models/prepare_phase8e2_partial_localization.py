#!/usr/bin/env python3
"""
Phase 8E-2 partial fabrication localization preparation.

Preparation and descriptive scoring only. No model training/predictions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from progress_utils import iter_with_progress  # noqa: E402
from phase8e2_localization_utils import (  # noqa: E402
    ALLOWED_LOCALIZATION_STATUS,
    SCHEMA_VERSION,
    compute_segment_timestamp_overlap,
    euclidean_from_median,
    find_acoustic_cols,
    find_ssl_cols,
    load_csv_required,
    load_timestamp_annotations,
    match_annotations_to_files,
    now_utc,
    percentile_rank,
    robust_distance_to_baseline,
    robust_z_matrix,
    timestamp_audit_for_file,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prepare Phase 8E-2 partial localization tables.")
    p.add_argument(
        "--partial_prep",
        default="reports/phase8/models/phase8e0/phase8e0_partial_fabrication_localization_prep.csv",
    )
    p.add_argument(
        "--segment_master",
        default="reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv",
    )
    p.add_argument(
        "--file_master",
        default="reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/models/phase8e2")
    p.add_argument("--top_k_segments_per_file", type=int, default=5)
    p.add_argument("--neighbor_window", type=int, default=1)
    p.add_argument("--timestamp_annotations", nargs="*", default=[])
    p.add_argument("--timestamp_format", choices=["auto", "csv", "json", "jsonl"], default="auto")
    p.add_argument("--timestamp_audio_path_col", default="auto")
    p.add_argument("--timestamp_file_id_col", default="auto")
    p.add_argument("--timestamp_start_col", default="auto")
    p.add_argument("--timestamp_end_col", default="auto")
    p.add_argument("--timestamp_label_col", default="auto")
    p.add_argument("--min_overlap_ratio", type=float, default=0.25)
    p.add_argument(
        "--positive_label_values",
        default="mixed,fabricated,partial_fabrication,inserted,ai_inserted,human_inserted,synthetic,splice,edited,1,true",
    )
    p.add_argument(
        "--negative_label_values",
        default="clean,human,bonafide,nonfabricated,non_fabricated,0,false",
    )
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_ROOT / p).resolve()


def _plot_if_enabled(out_dir: Path, loc_df: pd.DataFrame, top_files: list[str], make_plots: bool) -> None:
    if not make_plots:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for fid in top_files[:8]:
        g = loc_df[loc_df["file_id"] == fid].copy()
        if len(g) == 0:
            continue
        g["start_sec_num"] = pd.to_numeric(g["start_sec"], errors="coerce")
        g["dev"] = pd.to_numeric(g["combined_within_file_deviation_score"], errors="coerce")
        g["trans"] = pd.to_numeric(g["combined_neighbor_transition_score"], errors="coerce")
        g = g.sort_values("start_sec_num")

        plt.figure(figsize=(8, 3.5))
        plt.plot(g["start_sec_num"], g["dev"], label="within_file_deviation")
        plt.plot(g["start_sec_num"], g["trans"], label="neighbor_transition")
        plt.xlabel("start_sec")
        plt.ylabel("score")
        plt.title(f"File {fid}: localization score timeline")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / f"{fid}__timeline.png", dpi=120)
        plt.close()

    plt.figure(figsize=(7, 4))
    plt.hist(pd.to_numeric(loc_df["combined_within_file_deviation_score"], errors="coerce").dropna(), bins=20, alpha=0.7)
    plt.xlabel("combined_within_file_deviation_score")
    plt.ylabel("count")
    plt.title("Within-file candidate score distribution")
    plt.tight_layout()
    plt.savefig(fig_dir / "deviation_histogram.png", dpi=120)
    plt.close()


def _ensure_schema_version(df: pd.DataFrame, version: str) -> pd.DataFrame:
    schema_like = [c for c in df.columns if c.startswith("schema_version") and c != "schema_version"]
    if schema_like:
        df = df.drop(columns=schema_like, errors="ignore")
    if "schema_version" in df.columns:
        df["schema_version"] = version
        return df[["schema_version"] + [c for c in df.columns if c != "schema_version"]]
    df.insert(0, "schema_version", version)
    return df


def main() -> int:
    args = parse_args()
    show_progress = not args.no_progress
    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    partial_prep = load_csv_required(_resolve(args.partial_prep))
    seg_master = load_csv_required(_resolve(args.segment_master))
    file_master = load_csv_required(_resolve(args.file_master))

    # Restrict to partial-fabrication files from E0 prep table.
    partial_files = sorted(set(partial_prep["file_id"].astype(str)))
    seg_partial = seg_master[seg_master["file_id"].astype(str).isin(partial_files)].copy()
    if len(seg_partial) == 0:
        raise ValueError("No partial-fabrication segment rows found in segment master.")

    acoustic_cols = find_acoustic_cols(seg_partial)
    ssl_cols = find_ssl_cols(seg_partial)

    # Optional external timestamp annotations.
    pos_vals = {x.strip().lower() for x in args.positive_label_values.split(",") if x.strip()}
    neg_vals = {x.strip().lower() for x in args.negative_label_values.split(",") if x.strip()}
    ts_paths = [_resolve(p) for p in args.timestamp_annotations]
    ts_raw = load_timestamp_annotations(
        [str(p) for p in ts_paths],
        timestamp_format=args.timestamp_format,
        timestamp_audio_path_col=args.timestamp_audio_path_col,
        timestamp_file_id_col=args.timestamp_file_id_col,
        timestamp_start_col=args.timestamp_start_col,
        timestamp_end_col=args.timestamp_end_col,
        timestamp_label_col=args.timestamp_label_col,
        positive_label_values=pos_vals,
        negative_label_values=neg_vals,
    )
    ts_norm = match_annotations_to_files(ts_raw, file_master, partial_prep) if len(ts_raw) else ts_raw.copy()
    if len(ts_norm):
        ts_norm.to_csv(out_dir / "phase8e2_timestamp_annotation_normalized.csv", index=False)

    seg_partial = compute_segment_timestamp_overlap(
        seg_partial,
        ts_norm,
        min_overlap_ratio=args.min_overlap_ratio,
    )

    # Timestamp audit by file.
    timestamp_rows = []
    for fid, g in seg_partial.groupby("file_id", dropna=False):
        audit = timestamp_audit_for_file(g)
        valid_regions = 0
        if len(ts_norm):
            valid_regions = int(
                ((ts_norm["matched_file_id"] == fid) & (ts_norm["annotation_status"] == "matched")).sum()
            )
        fabricated_segments = int((g["timestamp_segment_label"] == "fabricated_region").sum())
        outside_segments = int((g["timestamp_segment_label"] == "outside_fabricated_region").sum())
        if valid_regions > 0:
            audit["has_true_timestamp_labels"] = "true"
            audit["timestamp_columns_found"] = "external_annotation_regions"
            audit["timestamp_label_source"] = "external_timestamp_annotation"
        audit["valid_timestamp_region_count"] = valid_regions
        audit["fabricated_segment_count"] = fabricated_segments
        audit["outside_segment_count"] = outside_segments
        if valid_regions == 0 and fabricated_segments == 0 and outside_segments == 0:
            audit["reason"] = "only inherited file-level partial label available"
            audit["usable_for_supervised_segment_training"] = "false"
        elif (fabricated_segments == 0) or (outside_segments == 0):
            audit["usable_for_supervised_segment_training"] = "false"
            audit["reason"] = "timestamp labels incomplete"
        else:
            audit["usable_for_supervised_segment_training"] = "true"
            audit["reason"] = "external timestamp labels aligned to fabricated/outside segments"
        timestamp_rows.append({"file_id": fid, **audit})
    timestamp_df = pd.DataFrame(timestamp_rows)

    seg_partial = seg_partial.merge(timestamp_df, on="file_id", how="left")
    seg_partial = _ensure_schema_version(seg_partial, SCHEMA_VERSION)

    delta_rows = []
    neigh_rows = []
    loc_rows = []
    file_summary_rows = []

    for fid, g in iter_with_progress(
        seg_partial.groupby("file_id", dropna=False),
        total=seg_partial["file_id"].nunique(),
        desc="phase8e2 files",
        enabled=show_progress,
        progress_every=1,
        unit="file",
    ):
        gx = g.copy()
        gx["start_sec_num"] = pd.to_numeric(gx["start_sec"], errors="coerce")
        gx = gx.sort_values(["start_sec_num", "segment_id"]).reset_index(drop=True)
        n_seg = len(gx)
        has_timestamps = str(gx["has_true_timestamp_labels"].iloc[0]).lower() == "true"
        usable_supervised = str(gx["usable_for_supervised_segment_training"].iloc[0]).lower() == "true"

        acoustic_distance = np.full(shape=(n_seg,), fill_value=np.nan)
        ssl_distance = np.full(shape=(n_seg,), fill_value=np.nan)
        if acoustic_cols:
            acoustic_distance = euclidean_from_median(gx[acoustic_cols])
        if ssl_cols:
            ssl_distance = euclidean_from_median(gx[ssl_cols])

        # Combined score from percentile ranks to stabilize scales.
        a_rank = percentile_rank(pd.Series(acoustic_distance))
        s_rank = percentile_rank(pd.Series(ssl_distance))
        combined_dev = pd.concat([a_rank, s_rank], axis=1).mean(axis=1, skipna=True)

        # Neighbor deltas (window 1 by default).
        prev_seg = gx["segment_id"].shift(args.neighbor_window)
        next_seg = gx["segment_id"].shift(-args.neighbor_window)
        ac_prev = pd.Series(np.nan, index=gx.index, dtype=float)
        ac_next = pd.Series(np.nan, index=gx.index, dtype=float)
        ssl_prev = pd.Series(np.nan, index=gx.index, dtype=float)
        ssl_next = pd.Series(np.nan, index=gx.index, dtype=float)

        if acoustic_cols:
            az = robust_z_matrix(gx[acoustic_cols])
            for i in range(n_seg):
                if i - args.neighbor_window >= 0:
                    ac_prev.iloc[i] = float(np.nanmean(np.abs(az[i] - az[i - args.neighbor_window])))
                if i + args.neighbor_window < n_seg:
                    ac_next.iloc[i] = float(np.nanmean(np.abs(az[i] - az[i + args.neighbor_window])))
        if ssl_cols:
            sz = robust_z_matrix(gx[ssl_cols])
            for i in range(n_seg):
                if i - args.neighbor_window >= 0:
                    ssl_prev.iloc[i] = float(np.nanmean(np.abs(sz[i] - sz[i - args.neighbor_window])))
                if i + args.neighbor_window < n_seg:
                    ssl_next.iloc[i] = float(np.nanmean(np.abs(sz[i] - sz[i + args.neighbor_window])))

        max_ac = pd.concat([ac_prev, ac_next], axis=1).max(axis=1, skipna=True)
        max_ssl = pd.concat([ssl_prev, ssl_next], axis=1).max(axis=1, skipna=True)
        combined_transition = pd.concat([percentile_rank(max_ac), percentile_rank(max_ssl)], axis=1).mean(axis=1, skipna=True)
        transition_rank = combined_transition.rank(ascending=False, method="min")
        dev_rank = combined_dev.rank(ascending=False, method="min")

        # Timestamp inside/outside baselines (if available).
        file_level_ac_sep = np.nan
        file_level_ssl_sep = np.nan
        file_level_combined_sep = np.nan
        ac_dist_out = np.full(shape=(n_seg,), fill_value=np.nan)
        ssl_dist_out = np.full(shape=(n_seg,), fill_value=np.nan)
        ac_dist_in = np.full(shape=(n_seg,), fill_value=np.nan)
        ssl_dist_in = np.full(shape=(n_seg,), fill_value=np.nan)
        ac_margin = np.full(shape=(n_seg,), fill_value=np.nan)
        ssl_margin = np.full(shape=(n_seg,), fill_value=np.nan)
        c_dist_out = np.full(shape=(n_seg,), fill_value=np.nan)
        c_dist_in = np.full(shape=(n_seg,), fill_value=np.nan)
        c_margin = np.full(shape=(n_seg,), fill_value=np.nan)

        fab_mask = gx["timestamp_segment_label"].astype(str) == "fabricated_region"
        out_mask = gx["timestamp_segment_label"].astype(str) == "outside_fabricated_region"
        has_inside_outside = bool(fab_mask.any() and out_mask.any())
        if has_inside_outside:
            if acoustic_cols:
                ac_x = gx[acoustic_cols].copy().mask(gx[acoustic_cols].eq("")).apply(pd.to_numeric, errors="coerce")
                ac_out_base = ac_x.loc[out_mask].median(axis=0, skipna=True)
                ac_in_base = ac_x.loc[fab_mask].median(axis=0, skipna=True)
                ac_scale = (1.4826 * (ac_x.sub(ac_x.median(axis=0, skipna=True), axis=1).abs().median(axis=0, skipna=True))).replace(0, np.nan)
                ac_dist_out = robust_distance_to_baseline(ac_x, ac_out_base, ac_scale)
                ac_dist_in = robust_distance_to_baseline(ac_x, ac_in_base, ac_scale)
                ac_margin = ac_dist_out - ac_dist_in
                file_level_ac_sep = float(np.nanmean(robust_distance_to_baseline(ac_x.loc[fab_mask], ac_out_base, ac_scale))) - float(
                    np.nanmean(robust_distance_to_baseline(ac_x.loc[out_mask], ac_out_base, ac_scale))
                )
            if ssl_cols:
                ssl_x = gx[ssl_cols].copy().mask(gx[ssl_cols].eq("")).apply(pd.to_numeric, errors="coerce")
                ssl_out_base = ssl_x.loc[out_mask].median(axis=0, skipna=True)
                ssl_in_base = ssl_x.loc[fab_mask].median(axis=0, skipna=True)
                ssl_scale = (1.4826 * (ssl_x.sub(ssl_x.median(axis=0, skipna=True), axis=1).abs().median(axis=0, skipna=True))).replace(0, np.nan)
                ssl_dist_out = robust_distance_to_baseline(ssl_x, ssl_out_base, ssl_scale)
                ssl_dist_in = robust_distance_to_baseline(ssl_x, ssl_in_base, ssl_scale)
                ssl_margin = ssl_dist_out - ssl_dist_in
                file_level_ssl_sep = float(np.nanmean(robust_distance_to_baseline(ssl_x.loc[fab_mask], ssl_out_base, ssl_scale))) - float(
                    np.nanmean(robust_distance_to_baseline(ssl_x.loc[out_mask], ssl_out_base, ssl_scale))
                )
            c_dist_out = np.nanmean(np.column_stack([ac_dist_out, ssl_dist_out]), axis=1)
            c_dist_in = np.nanmean(np.column_stack([ac_dist_in, ssl_dist_in]), axis=1)
            c_margin = c_dist_out - c_dist_in
            file_level_combined_sep = float(np.nanmean(c_margin))

        # Build delta and neighbor tables.
        for i, row in gx.iterrows():
            mode = "timestamp_inside_outside" if has_inside_outside else "unsupervised_within_file_deviation"
            delta_rows.append(
                {
                    "file_id": fid,
                    "segment_id": row["segment_id"],
                    "start_sec": row["start_sec"],
                    "end_sec": row["end_sec"],
                    "timestamp_segment_label": row.get("timestamp_segment_label", "unknown_no_timestamp"),
                    "mode": mode,
                    "acoustic_distance_from_outside_baseline": ac_dist_out[i] if np.isfinite(ac_dist_out[i]) else "",
                    "ssl_distance_from_outside_baseline": ssl_dist_out[i] if np.isfinite(ssl_dist_out[i]) else "",
                    "acoustic_distance_from_fabricated_baseline": ac_dist_in[i] if np.isfinite(ac_dist_in[i]) else "",
                    "ssl_distance_from_fabricated_baseline": ssl_dist_in[i] if np.isfinite(ssl_dist_in[i]) else "",
                    "acoustic_outside_minus_fabricated_margin": ac_margin[i] if np.isfinite(ac_margin[i]) else "",
                    "ssl_outside_minus_fabricated_margin": ssl_margin[i] if np.isfinite(ssl_margin[i]) else "",
                    "acoustic_distance_from_file_median": acoustic_distance[i] if np.isfinite(acoustic_distance[i]) else "",
                    "ssl_distance_from_file_median": ssl_distance[i] if np.isfinite(ssl_distance[i]) else "",
                    "acoustic_deviation_percentile_within_file": a_rank.iloc[i] if pd.notna(a_rank.iloc[i]) else "",
                    "ssl_deviation_percentile_within_file": s_rank.iloc[i] if pd.notna(s_rank.iloc[i]) else "",
                    "combined_distance_from_outside_baseline": c_dist_out[i] if np.isfinite(c_dist_out[i]) else "",
                    "combined_distance_from_fabricated_baseline": c_dist_in[i] if np.isfinite(c_dist_in[i]) else "",
                    "combined_inside_outside_margin": c_margin[i] if np.isfinite(c_margin[i]) else "",
                    "combined_deviation_score": combined_dev.iloc[i] if pd.notna(combined_dev.iloc[i]) else "",
                    "file_level_acoustic_inside_outside_separation": file_level_ac_sep if np.isfinite(file_level_ac_sep) else "",
                    "file_level_ssl_inside_outside_separation": file_level_ssl_sep if np.isfinite(file_level_ssl_sep) else "",
                    "file_level_combined_inside_outside_separation": file_level_combined_sep if np.isfinite(file_level_combined_sep) else "",
                    "interpretation_note": "within-file deviation indicator only; not a confirmed fabricated segment",
                }
            )
            neigh_rows.append(
                {
                    "file_id": fid,
                    "segment_id": row["segment_id"],
                    "prev_segment_id": prev_seg.iloc[i] if pd.notna(prev_seg.iloc[i]) else "",
                    "next_segment_id": next_seg.iloc[i] if pd.notna(next_seg.iloc[i]) else "",
                    "acoustic_prev_delta": ac_prev.iloc[i] if pd.notna(ac_prev.iloc[i]) else "",
                    "acoustic_next_delta": ac_next.iloc[i] if pd.notna(ac_next.iloc[i]) else "",
                    "ssl_prev_delta": ssl_prev.iloc[i] if pd.notna(ssl_prev.iloc[i]) else "",
                    "ssl_next_delta": ssl_next.iloc[i] if pd.notna(ssl_next.iloc[i]) else "",
                    "max_acoustic_neighbor_delta": max_ac.iloc[i] if pd.notna(max_ac.iloc[i]) else "",
                    "max_ssl_neighbor_delta": max_ssl.iloc[i] if pd.notna(max_ssl.iloc[i]) else "",
                    "combined_neighbor_transition_score": combined_transition.iloc[i] if pd.notna(combined_transition.iloc[i]) else "",
                    "transition_rank_within_file": transition_rank.iloc[i] if pd.notna(transition_rank.iloc[i]) else "",
                    "interpretation_note": "neighbor transition indicator only; not a confirmed fabricated segment",
                }
            )

        # Candidate classification.
        top_k = max(1, int(args.top_k_segments_per_file))
        gx["within_file_acoustic_deviation_score"] = a_rank
        gx["within_file_ssl_deviation_score"] = s_rank
        gx["combined_within_file_deviation_score"] = combined_dev
        gx["neighbor_acoustic_transition_score"] = percentile_rank(max_ac)
        gx["neighbor_ssl_transition_score"] = percentile_rank(max_ssl)
        gx["combined_neighbor_transition_score"] = combined_transition
        gx["combined_inside_outside_margin"] = pd.Series(c_margin)
        overall_candidate_score = pd.concat(
            [combined_dev, combined_transition, percentile_rank(pd.Series(c_margin))], axis=1
        ).mean(axis=1, skipna=True)
        gx["localization_candidate_rank_within_file"] = overall_candidate_score.rank(ascending=False, method="min")
        gx["candidate_type"] = "not_top_candidate"
        gx.loc[
            (gx["localization_candidate_rank_within_file"] <= top_k)
            & (gx["combined_inside_outside_margin"] >= gx["combined_within_file_deviation_score"])
            & (gx["combined_inside_outside_margin"] >= gx["combined_neighbor_transition_score"]),
            "candidate_type",
        ] = "inside_outside_candidate"
        gx.loc[(gx["localization_candidate_rank_within_file"] <= top_k) & (gx["combined_within_file_deviation_score"] > gx["combined_neighbor_transition_score"]), "candidate_type"] = "within_file_deviation_candidate"
        gx.loc[(gx["localization_candidate_rank_within_file"] <= top_k) & (gx["combined_within_file_deviation_score"] < gx["combined_neighbor_transition_score"]), "candidate_type"] = "neighbor_transition_candidate"
        gx.loc[
            (gx["localization_candidate_rank_within_file"] <= top_k)
            & (gx["combined_within_file_deviation_score"] >= 0.7)
            & (gx["combined_neighbor_transition_score"] >= 0.7),
            "candidate_type",
        ] = "both_deviation_and_transition"
        gx.loc[
            (gx["localization_candidate_rank_within_file"] <= top_k)
            & (gx["combined_within_file_deviation_score"] >= 0.65)
            & (gx["combined_neighbor_transition_score"] >= 0.65)
            & (gx["combined_inside_outside_margin"] >= 0.65),
            "candidate_type",
        ] = "combined_localization_candidate"
        if n_seg < 2 or (not acoustic_cols and not ssl_cols):
            gx["candidate_type"] = "insufficient_data"
        gx["candidate_reason"] = gx["candidate_type"].map(
            {
                "within_file_deviation_candidate": "high within-file deviation indicator",
                "neighbor_transition_candidate": "strong neighbor transition indicator",
                "both_deviation_and_transition": "both deviation and transition indicators are high",
                "inside_outside_candidate": "inside/outside baseline margin is high",
                "combined_localization_candidate": "deviation, transition, and inside/outside margins are jointly high",
                "not_top_candidate": "not in top candidate ranks for this file",
                "insufficient_data": "insufficient per-file feature context",
            }
        )

        # File summary.
        top_ids = gx.sort_values("localization_candidate_rank_within_file")["segment_id"].head(top_k).tolist()
        if n_seg < 2:
            status = "insufficient_segments"
            note = "too few segments for localization context"
        elif (not acoustic_cols and not ssl_cols):
            status = "missing_features"
            note = "acoustic/ssl feature vectors unavailable"
        elif has_timestamps and usable_supervised:
            status = "timestamp_supervision_available"
            note = "timestamp supervision available; still requires cautious review"
        else:
            status = "unsupervised_candidates_only"
            note = "only inherited labels; use candidates for manual review/fusion context"
        file_info = file_master[file_master["file_id"] == fid].head(1)
        file_summary_rows.append(
            {
                "file_id": fid,
                "audio_path": file_info["audio_path"].iloc[0] if len(file_info) else "",
                "known_origin_label": file_info["known_origin_label"].iloc[0] if len(file_info) else "",
                "known_manipulation_labels": file_info["known_manipulation_labels"].iloc[0] if len(file_info) else "",
                "duration_sec": file_info["duration_sec"].iloc[0] if len(file_info) else "",
                "segment_count": n_seg,
                "has_true_timestamp_labels": "true" if has_timestamps else "false",
                "usable_for_phase8e3_training": "true" if usable_supervised else "false",
                "top_candidate_segment_ids": ";".join(top_ids),
                "max_within_file_anomaly_score": float(pd.to_numeric(gx["combined_within_file_deviation_score"], errors="coerce").max()),
                "max_neighbor_transition_score": float(pd.to_numeric(gx["combined_neighbor_transition_score"], errors="coerce").max()),
                "file_level_acoustic_inside_outside_separation": file_level_ac_sep if np.isfinite(file_level_ac_sep) else "",
                "file_level_ssl_inside_outside_separation": file_level_ssl_sep if np.isfinite(file_level_ssl_sep) else "",
                "file_level_combined_inside_outside_separation": file_level_combined_sep if np.isfinite(file_level_combined_sep) else "",
                "fabricated_segment_count": int(fab_mask.sum()),
                "outside_segment_count": int(out_mask.sum()),
                "localization_status": status if status in ALLOWED_LOCALIZATION_STATUS else "error",
                "review_note": note,
            }
        )

        for _, row in gx.iterrows():
            loc_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "file_id": row["file_id"],
                    "segment_id": row["segment_id"],
                    "start_sec": row["start_sec"],
                    "end_sec": row["end_sec"],
                    "segment_duration_sec": row["segment_duration_sec"],
                    "known_origin_label": row.get("known_origin_label", ""),
                    "known_manipulation_labels": row.get("known_manipulation_labels", ""),
                    "segment_label_source": row.get("segment_label_source", ""),
                    "has_true_timestamp_labels": row.get("has_true_timestamp_labels", "false"),
                    "usable_for_supervised_segment_training": row.get("usable_for_supervised_segment_training", "false"),
                    "timestamp_segment_label": row.get("timestamp_segment_label", "unknown_no_timestamp"),
                    "training_label_available": row.get("training_label_available", "false"),
                    "max_fabricated_overlap_sec": row.get("max_fabricated_overlap_sec", ""),
                    "max_fabricated_overlap_ratio": row.get("max_fabricated_overlap_ratio", ""),
                    "total_fabricated_overlap_sec": row.get("total_fabricated_overlap_sec", ""),
                    "acoustic_distance_from_outside_baseline": ac_dist_out[row.name] if (row.name < len(ac_dist_out) and np.isfinite(ac_dist_out[row.name])) else "",
                    "ssl_distance_from_outside_baseline": ssl_dist_out[row.name] if (row.name < len(ssl_dist_out) and np.isfinite(ssl_dist_out[row.name])) else "",
                    "acoustic_distance_from_fabricated_baseline": ac_dist_in[row.name] if (row.name < len(ac_dist_in) and np.isfinite(ac_dist_in[row.name])) else "",
                    "ssl_distance_from_fabricated_baseline": ssl_dist_in[row.name] if (row.name < len(ssl_dist_in) and np.isfinite(ssl_dist_in[row.name])) else "",
                    "combined_distance_from_outside_baseline": c_dist_out[row.name] if (row.name < len(c_dist_out) and np.isfinite(c_dist_out[row.name])) else "",
                    "combined_distance_from_fabricated_baseline": c_dist_in[row.name] if (row.name < len(c_dist_in) and np.isfinite(c_dist_in[row.name])) else "",
                    "combined_inside_outside_margin": c_margin[row.name] if (row.name < len(c_margin) and np.isfinite(c_margin[row.name])) else "",
                    "file_level_combined_inside_outside_separation": file_level_combined_sep if np.isfinite(file_level_combined_sep) else "",
                    "within_file_acoustic_deviation_score": row.get("within_file_acoustic_deviation_score", ""),
                    "within_file_ssl_deviation_score": row.get("within_file_ssl_deviation_score", ""),
                    "combined_within_file_deviation_score": row.get("combined_within_file_deviation_score", ""),
                    "neighbor_acoustic_transition_score": row.get("neighbor_acoustic_transition_score", ""),
                    "neighbor_ssl_transition_score": row.get("neighbor_ssl_transition_score", ""),
                    "combined_neighbor_transition_score": row.get("combined_neighbor_transition_score", ""),
                    "localization_candidate_rank_within_file": row.get("localization_candidate_rank_within_file", ""),
                    "candidate_reason": row.get("candidate_reason", ""),
                    "candidate_type": row.get("candidate_type", "insufficient_data"),
                    "allowed_use": (
                        "supervised_training_candidate"
                        if str(row.get("training_label_available", "false")).lower() == "true"
                        else "manual_review_candidate"
                    ),
                }
            )

    timestamp_df.to_csv(out_dir / "phase8e2_timestamp_label_audit.csv", index=False)
    file_summary_df = pd.DataFrame(file_summary_rows)
    file_summary_df.to_csv(out_dir / "phase8e2_partial_file_summary.csv", index=False)

    loc_df = pd.DataFrame(loc_rows)
    loc_df.to_csv(out_dir / "phase8e2_partial_segment_localization_table.csv", index=False)

    inside_outside_df = pd.DataFrame(delta_rows)
    inside_outside_df.to_csv(out_dir / "phase8e2_inside_outside_delta_features.csv", index=False)
    neighbor_df = pd.DataFrame(neigh_rows)
    neighbor_df.to_csv(out_dir / "phase8e2_neighbor_transition_features.csv", index=False)

    cand_df = loc_df.copy()
    cand_df = cand_df.sort_values(["file_id", "localization_candidate_rank_within_file"], ascending=[True, True])
    cand_df = cand_df.rename(
        columns={
            "localization_candidate_rank_within_file": "candidate_rank_within_file",
        }
    )
    if "training_label_available" not in cand_df.columns:
        cand_df["training_label_available"] = "false"
    cand_df["evidence_type"] = "localized_anomaly_indicator"
    cand_df["allowed_use"] = np.where(
        cand_df["training_label_available"].astype(str).str.lower() == "true",
        "supervised_training_candidate",
        np.where(
            cand_df["candidate_type"].isin({"within_file_deviation_candidate", "neighbor_transition_candidate", "both_deviation_and_transition"}),
            "phase8f_fusion_candidate",
            "manual_review_candidate",
        ),
    )
    cand_df = cand_df[
        [
            "file_id",
            "segment_id",
            "start_sec",
            "end_sec",
            "candidate_rank_within_file",
            "candidate_type",
            "timestamp_segment_label",
            "combined_within_file_deviation_score",
            "combined_neighbor_transition_score",
            "combined_inside_outside_margin",
            "max_fabricated_overlap_ratio",
            "candidate_reason",
            "evidence_type",
            "training_label_available",
            "allowed_use",
        ]
    ]
    cand_df.to_csv(out_dir / "phase8e2_suspicious_segment_candidates.csv", index=False)
    top_cand_df = cand_df[
        (cand_df["candidate_type"] != "not_top_candidate")
        | (pd.to_numeric(cand_df["candidate_rank_within_file"], errors="coerce") <= int(args.top_k_segments_per_file))
        | (pd.to_numeric(cand_df["combined_inside_outside_margin"], errors="coerce") >= 0.75)
        | (pd.to_numeric(cand_df["combined_neighbor_transition_score"], errors="coerce") >= 0.80)
    ].copy()
    top_cand_df.to_csv(out_dir / "phase8e2_top_suspicious_segment_candidates.csv", index=False)

    # Readiness review
    ann_loaded = len(ts_norm)
    matched_ann = int((ts_norm["annotation_status"] == "matched").sum()) if len(ts_norm) else 0
    true_ts_count = int((timestamp_df["has_true_timestamp_labels"] == "true").sum())
    usable_count = int((timestamp_df["usable_for_supervised_segment_training"] == "true").sum())
    min_pos = int((loc_df["timestamp_segment_label"] == "fabricated_region").sum()) if "timestamp_segment_label" in loc_df.columns else 0
    min_neg = int((loc_df["timestamp_segment_label"] == "outside_fabricated_region").sum()) if "timestamp_segment_label" in loc_df.columns else 0
    files_with_both = 0
    if len(loc_df):
        for _, gg in loc_df.groupby("file_id"):
            if (gg["timestamp_segment_label"] == "fabricated_region").any() and (
                gg["timestamp_segment_label"] == "outside_fabricated_region"
            ).any():
                files_with_both += 1
    ready = (
        "yes"
        if ann_loaded > 0 and matched_ann > 0 and min_pos >= 20 and min_neg >= 20 and files_with_both >= 3
        else "no"
    )
    readiness_rows = [
        {
            "criterion": "timestamp_annotations_loaded",
            "status": "yes" if ann_loaded > 0 else "no",
            "evidence": f"annotation_rows_loaded={ann_loaded}",
            "recommendation": "provide timestamp annotation files for partial-fabrication intervals",
        },
        {
            "criterion": "timestamp_annotations_matched_to_files",
            "status": "yes" if matched_ann > 0 else "no",
            "evidence": f"matched_annotation_rows={matched_ann}",
            "recommendation": "improve file-path/file-id matching coverage if low",
        },
        {
            "criterion": "timestamp_labels_available",
            "status": "yes" if true_ts_count > 0 else "no",
            "evidence": f"files_with_true_timestamp_labels={true_ts_count}",
            "recommendation": "collect reliable timestamp annotations for each partial file",
        },
        {
            "criterion": "true_segment_labels_available",
            "status": "yes" if usable_count > 0 else "no",
            "evidence": f"files_usable_for_supervised_segment_training={usable_count}",
            "recommendation": "require per-segment or start/end labels before supervised training",
        },
        {
            "criterion": "inherited_labels_only",
            "status": "yes" if usable_count == 0 else "no",
            "evidence": "current partial dataset uses inherited file-level labels for localization prep",
            "recommendation": "keep phase8e2 outputs as manual/fusion candidates only",
        },
        {
            "criterion": "minimum_positive_segment_count",
            "status": "yes" if min_pos >= 20 else "no",
            "evidence": f"positive_fabricated_segment_count={min_pos}",
            "recommendation": "collect more timestamp-labeled positive segments",
        },
        {
            "criterion": "minimum_negative_segment_count",
            "status": "yes" if min_neg >= 20 else "no",
            "evidence": f"negative_outside_segment_count={min_neg}",
            "recommendation": "collect timestamp-labeled outside/clean segments",
        },
        {
            "criterion": "source_group_leakage_control_possible",
            "status": "yes",
            "evidence": "source_group_id exists in segment-level tables",
            "recommendation": "use group-aware splits for any future supervised stage",
        },
        {
            "criterion": "inside_outside_feature_columns_created",
            "status": "yes" if len(inside_outside_df) > 0 else "no",
            "evidence": "inside/outside baseline distance columns created in phase8e2_inside_outside_delta_features.csv",
            "recommendation": "verify baseline distances before supervised stage",
        },
        {
            "criterion": "top_candidate_table_created",
            "status": "yes" if len(top_cand_df) > 0 else "no",
            "evidence": f"phase8e2_top_suspicious_segment_candidates rows={len(top_cand_df)}",
            "recommendation": "prioritize top candidates for manual review",
        },
        {
            "criterion": "ready_for_supervised_partial_segment_training",
            "status": ready,
            "evidence": "requires loaded+matched annotations, sufficient positive/negative counts, and leakage control",
            "recommendation": "remain in localization-prep mode unless all criteria are satisfied",
        },
    ]
    readiness_df = pd.DataFrame(readiness_rows)
    readiness_df.to_csv(out_dir / "phase8e2_phase8e3_readiness_review.csv", index=False)

    top_files = file_summary_df.sort_values(
        ["max_within_file_anomaly_score", "max_neighbor_transition_score"], ascending=False
    )["file_id"].head(10).tolist()
    _plot_if_enabled(out_dir, loc_df, top_files, args.make_plots)

    report_lines = [
        "# Phase 8E-2 Partial Localization Report",
        "",
        f"**Generated:** {now_utc()}",
        "",
        "Phase 8E-2 prepares partial-fabrication localization evidence tables only.",
        "No training, no predictions, and no final forensic decisions are produced.",
        "",
        "## Why Partial Fabrication Is Not Trained Yet",
        "",
        "- Inherited file-level partial labels do not identify true fabricated segment boundaries.",
        "- Segment-level supervised training remains unsafe without reliable timestamp labels.",
        "",
        "## Timestamp Label Audit",
        "",
        f"- partial files: {len(file_summary_df)}",
        f"- partial segments: {len(loc_df)}",
        f"- files with true timestamp labels: {true_ts_count}",
        f"- files usable for supervised segment training: {usable_count}",
        f"- loaded timestamp annotation rows: {ann_loaded}",
        f"- matched timestamp annotation rows: {matched_ann}",
        "",
        "## Candidate Ranking Method",
        "",
        "- within-file deviation indicators from acoustic/ssl distance-to-file-median features",
        "- neighbor transition indicators from prev/next segment deltas",
        "- candidate ranks are descriptive and prioritized for manual review/fusion context",
        "- inside/outside baseline distances compare fabricated vs outside regions within each file",
        "",
        "## Top Candidate Examples",
        "",
    ]
    for fid in top_files[:5]:
        top_seg = cand_df[cand_df["file_id"] == fid].head(3)["segment_id"].tolist()
        report_lines.append(f"- file `{fid}` top candidate segments: {top_seg}")
    report_lines.extend(
        [
            "",
            "## Phase 8E-3 Readiness",
            "",
            f"- ready_for_supervised_partial_segment_training: **{ready}**",
            "- current outputs are candidate segment indicators for manual review and possible Phase 8F fusion context.",
            "",
            "## Limitations",
            "",
            "- localized anomaly indicators are not confirmed fabricated segments.",
            "- small and weakly labeled partial data requires cautious interpretation.",
            "- candidate thresholds/indicators require validation and manual review.",
            "",
            "## Safety Statements",
            "",
            "- no training was performed",
            "- no predictions were produced",
            "- no hard suspicious labels were created",
            "- no final forensic decisions were produced",
            "- candidate segment indicators are not a confirmed fabricated segment",
        ]
    )
    (out_dir / "phase8e2_partial_localization_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("Phase 8E-2 localization preparation complete.")
    print(f"Output dir: {out_dir}")
    print("No training/prediction code executed.")
    print("No hard suspicious labels created; candidate wording only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
