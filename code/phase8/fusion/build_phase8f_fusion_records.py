#!/usr/bin/env python3
"""
Phase 8F: build experimental multi-axis fusion records from Phase 8E outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from progress_utils import iter_with_progress  # noqa: E402
from phase8f_fusion_rules import (  # noqa: E402
    apply_multi_axis_fusion,
    classify_evidence_strength,
    fuse_mixer_evidence,
    fuse_origin_evidence,
    fuse_partial_evidence,
    fuse_replay_evidence,
)
from phase8f_report_generator import generate_safe_report  # noqa: E402

SCHEMA_VERSION = "phase8f_v1_experimental"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Phase 8F experimental fusion records.")
    p.add_argument(
        "--phase8e1_predictions",
        default="reports/phase8/models/phase8e1/phase8e1_out_of_fold_predictions.csv",
    )
    p.add_argument(
        "--phase8e1a_thresholds",
        default="reports/phase8/models/phase8e1a/phase8e1a_threshold_recommendations.csv",
    )
    p.add_argument(
        "--phase8e3_segment_predictions",
        default="reports/phase8/models/phase8e3/phase8e3_out_of_fold_segment_predictions.csv",
    )
    p.add_argument(
        "--phase8e3_file_localization",
        default="reports/phase8/models/phase8e3/phase8e3_file_level_localization_summary.csv",
    )
    p.add_argument(
        "--phase8e2_top_candidates",
        default="reports/phase8/models/phase8e2/phase8e2_top_suspicious_segment_candidates.csv",
    )
    p.add_argument(
        "--file_master",
        default="reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv",
    )
    p.add_argument(
        "--segment_master",
        default="reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/fusion/phase8f")
    p.add_argument("--origin_feature_set", default="ssl")
    p.add_argument("--replay_feature_set", default="acoustic")
    p.add_argument("--mixer_feature_set", default="acoustic")
    p.add_argument("--partial_feature_set", default="combined")
    p.add_argument("--make_reports", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_ROOT / p).resolve()


def _load_csv(path: str) -> pd.DataFrame:
    rp = _resolve(path)
    if not rp.is_file():
        raise FileNotFoundError(f"Required CSV missing: {rp}")
    return pd.read_csv(rp, dtype=str, keep_default_na=False)


def _num(s: Any) -> float | None:
    try:
        txt = str(s).strip()
        if not txt:
            return None
        return float(txt)
    except Exception:
        return None


def _is_blank(value: Any) -> bool:
    return str(value).strip() == ""


def _choose_threshold(
    thresh_df: pd.DataFrame, task_name: str, feature_set: str, fallback: float = 0.5
) -> float:
    rows = thresh_df[
        (thresh_df["task_name"] == task_name) & (thresh_df["feature_set"] == feature_set)
    ].copy()
    if len(rows) == 0:
        return fallback
    val_col = "recommended_threshold_candidate"
    if val_col in rows.columns:
        vals = pd.to_numeric(rows[val_col], errors="coerce").dropna()
        if len(vals):
            return float(vals.iloc[0])
    return fallback


def _aggregate_file_probability(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.assign(y_proba_num=pd.to_numeric(df["y_proba_experimental"], errors="coerce"))
        .groupby("file_id", as_index=False)["y_proba_num"]
        .mean()
        .rename(columns={"y_proba_num": "probability"})
    )
    return out


def _prepare_axis_file_table(
    e1_pred: pd.DataFrame,
    task_name: str,
    feature_set: str,
    threshold: float,
    axis_prefix: str,
    positive_label: str,
) -> pd.DataFrame:
    part = e1_pred[(e1_pred["task_name"] == task_name) & (e1_pred["feature_set"] == feature_set)].copy()
    if len(part) == 0:
        return pd.DataFrame(columns=["file_id", f"{axis_prefix}_model_available", f"{axis_prefix}_feature_set", f"{axis_prefix}_threshold_candidate", f"{axis_prefix}_probability"])
    agg = _aggregate_file_probability(part)
    agg[f"{axis_prefix}_model_available"] = "true"
    agg[f"{axis_prefix}_feature_set"] = feature_set
    agg[f"{axis_prefix}_threshold_candidate"] = threshold
    agg[f"{axis_prefix}_probability"] = agg["probability"]
    agg.drop(columns=["probability"], inplace=True)
    if axis_prefix == "origin":
        agg["origin_ai_probability"] = agg[f"{axis_prefix}_probability"]
        agg.drop(columns=[f"{axis_prefix}_probability"], inplace=True)
    return agg


def _prepare_partial_tables(
    e3_seg: pd.DataFrame,
    e3_file_loc: pd.DataFrame,
    e2_top: pd.DataFrame,
    feature_set: str,
    threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    seg = e3_seg[
        (e3_seg["task_name"] == "partial_fabrication_segment_model") & (e3_seg["feature_set"] == feature_set)
    ].copy()
    seg["y_proba_experimental"] = pd.to_numeric(seg["y_proba_experimental"], errors="coerce")
    seg["threshold"] = threshold
    seg["partial_segment_evidence_strength"] = seg["y_proba_experimental"].map(
        lambda x: classify_evidence_strength(x, threshold)
    )
    seg["partial_segment_evidence_label"] = np.where(
        seg["y_proba_experimental"] >= threshold,
        "elevated_partial_segment_indicator",
        "low_partial_segment_indicator",
    )
    seg["partial_segment_threshold_candidate"] = threshold
    seg["manual_review_candidate"] = np.where(
        seg["partial_segment_evidence_strength"].isin(["borderline", "moderate", "high"]),
        "true",
        "false",
    )
    seg["segment_report_note"] = (
        "experimental candidate segment indicator; does not by itself prove fabrication"
    )
    top_cols = ["file_id", "segment_id", "candidate_rank_within_file", "candidate_type", "timestamp_segment_label"]
    top_use = e2_top[[c for c in top_cols if c in e2_top.columns]].copy()
    seg = seg.merge(top_use, on=["file_id", "segment_id"], how="left")
    seg_out = seg[
        [
            "file_id",
            "segment_id",
            "start_sec",
            "end_sec",
            "y_proba_experimental",
            "partial_segment_threshold_candidate",
            "partial_segment_evidence_label",
            "partial_segment_evidence_strength",
            "candidate_rank_within_file",
            "candidate_type",
            "timestamp_segment_label",
            "manual_review_candidate",
            "segment_report_note",
        ]
    ].rename(columns={"y_proba_experimental": "partial_segment_probability"})

    seg_group = seg.groupby("file_id", dropna=False)
    file_part = seg_group["y_proba_experimental"].agg(["max", "mean", "count"]).reset_index()
    file_part.rename(
        columns={
            "max": "partial_max_segment_probability",
            "mean": "partial_mean_topk_probability",
            "count": "partial_predicted_candidate_count",
        },
        inplace=True,
    )
    pred_candidates = (
        seg.assign(pred=seg["y_proba_experimental"] >= threshold)
        .groupby("file_id", as_index=False)["pred"]
        .sum()
        .rename(columns={"pred": "partial_predicted_candidate_count"})
    )
    file_part = file_part.drop(columns=["partial_predicted_candidate_count"]).merge(pred_candidates, on="file_id", how="left")
    top_counts = (
        e2_top.groupby("file_id", as_index=False)["segment_id"]
        .count()
        .rename(columns={"segment_id": "partial_candidate_segment_count"})
    )
    file_part = file_part.merge(top_counts, on="file_id", how="left")

    ranges = (
        seg.sort_values(["file_id", "y_proba_experimental"], ascending=[True, False])
        .groupby("file_id")
        .head(3)
        .assign(r=lambda d: d["start_sec"].astype(str) + "-" + d["end_sec"].astype(str))
        .groupby("file_id")["r"]
        .apply(lambda x: ";".join(x.astype(str).tolist()))
        .reset_index(name="partial_top_segment_ranges")
    )
    file_part = file_part.merge(ranges, on="file_id", how="left")
    if "feature_set" in e3_file_loc.columns:
        part_loc = e3_file_loc[e3_file_loc["feature_set"] == feature_set][["file_id", "top_k_hit_rate"]].copy()
        file_part = file_part.merge(part_loc, on="file_id", how="left")
    file_part["partial_feature_set"] = feature_set
    file_part["partial_model_available"] = "true"
    file_part["partial_segment_threshold_candidate"] = threshold
    file_part["partial_trace"] = "from phase8e3 segment OOF and e2 candidate table"
    return file_part, seg_out


def _build_summary_records(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    rows.append({"metric_name": "total_files", "metric_value": str(len(df))})
    rows.append(
        {
            "metric_name": "status_distribution",
            "metric_value": json.dumps(df["experimental_fusion_status"].value_counts(dropna=False).to_dict()),
        }
    )
    rows.append(
        {
            "metric_name": "risk_distribution",
            "metric_value": json.dumps(df["forensic_risk_level"].value_counts(dropna=False).to_dict()),
        }
    )
    rows.append(
        {
            "metric_name": "manual_review_required_count",
            "metric_value": str(int((df["manual_review_required"] == "true").sum())),
        }
    )
    for axis in ["origin", "replay", "mixer", "partial"]:
        rows.append(
            {
                "metric_name": f"{axis}_evidence_available_count",
                "metric_value": str(int((df[f"{axis}_model_available"] == "true").sum())),
            }
        )
    rows.append(
        {
            "metric_name": "high_partial_candidate_count",
            "metric_value": str(int((df["partial_evidence_strength"] == "high").sum())),
        }
    )
    rows.append(
        {
            "metric_name": "inconclusive_count",
            "metric_value": str(int((df["experimental_fusion_status"] == "inconclusive_manual_review_experimental").sum())),
        }
    )
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    show_progress = not args.no_progress

    e1_pred = _load_csv(args.phase8e1_predictions)
    e1a_thr = _load_csv(args.phase8e1a_thresholds)
    e3_seg = _load_csv(args.phase8e3_segment_predictions)
    e3_file_loc = _load_csv(args.phase8e3_file_localization)
    e2_top = _load_csv(args.phase8e2_top_candidates)
    file_master = _load_csv(args.file_master)
    _segment_master = _load_csv(args.segment_master)

    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    origin_th = _choose_threshold(e1a_thr, "origin_file_model", args.origin_feature_set, 0.2)
    replay_th = _choose_threshold(e1a_thr, "replay_file_model", args.replay_feature_set, 0.65)
    mixer_th = _choose_threshold(e1a_thr, "mixer_file_model", args.mixer_feature_set, 0.75)
    partial_th = 0.5
    try:
        e3_grid = _load_csv("reports/phase8/models/phase8e3/phase8e3_threshold_grid.csv")
        pick = e3_grid[
            (e3_grid["task_name"] == "partial_fabrication_segment_model")
            & (e3_grid["feature_set"] == args.partial_feature_set)
        ].copy()
        pick["balanced_accuracy"] = pd.to_numeric(pick["balanced_accuracy"], errors="coerce")
        pick["threshold"] = pd.to_numeric(pick["threshold"], errors="coerce")
        if len(pick):
            pick = pick.sort_values("balanced_accuracy", ascending=False).head(1)
            if pd.notna(pick.iloc[0]["threshold"]):
                partial_th = float(pick.iloc[0]["threshold"])
    except Exception:
        partial_th = 0.5

    origin_df = _prepare_axis_file_table(
        e1_pred, "origin_file_model", args.origin_feature_set, origin_th, "origin", "ai_origin_indicator"
    )
    replay_df = _prepare_axis_file_table(
        e1_pred, "replay_file_model", args.replay_feature_set, replay_th, "replay", "replay_indicator"
    )
    mixer_df = _prepare_axis_file_table(
        e1_pred, "mixer_file_model", args.mixer_feature_set, mixer_th, "mixer", "mixer_indicator"
    )
    partial_file_df, segment_out_df = _prepare_partial_tables(
        e3_seg=e3_seg,
        e3_file_loc=e3_file_loc,
        e2_top=e2_top,
        feature_set=args.partial_feature_set,
        threshold=partial_th,
    )

    base_cols = [
        "file_id",
        "audio_path",
        "known_origin_label",
        "known_manipulation_labels",
        "source_dataset",
        "split",
    ]
    fusion = file_master[[c for c in base_cols if c in file_master.columns]].copy()
    fusion["schema_version"] = SCHEMA_VERSION
    fusion = fusion.merge(origin_df, on="file_id", how="left")
    fusion = fusion.merge(replay_df, on="file_id", how="left")
    fusion = fusion.merge(mixer_df, on="file_id", how="left")
    fusion = fusion.merge(partial_file_df, on="file_id", how="left")

    for axis in ["origin", "replay", "mixer", "partial"]:
        avail = f"{axis}_model_available"
        fset = f"{axis}_feature_set"
        if avail not in fusion.columns:
            fusion[avail] = "false"
        fusion[avail] = fusion[avail].astype(str).str.strip().str.lower().replace("", "false")
        fusion[avail] = np.where(fusion[avail] == "true", "true", "false")
        if fset not in fusion.columns:
            fusion[fset] = "not_evaluated"
        fusion[fset] = fusion[fset].replace("", "not_evaluated")
    for col in [
        "origin_ai_probability",
        "origin_threshold_candidate",
        "replay_probability",
        "replay_threshold_candidate",
        "mixer_probability",
        "mixer_threshold_candidate",
        "partial_max_segment_probability",
        "partial_mean_topk_probability",
        "partial_candidate_segment_count",
        "partial_predicted_candidate_count",
        "partial_segment_threshold_candidate",
    ]:
        if col not in fusion.columns:
            fusion[col] = ""

    fusion["origin_trace"] = "phase8e1 oof mean file probability"
    fusion["replay_trace"] = "phase8e1 oof mean file probability"
    fusion["mixer_trace"] = "phase8e1 oof mean file probability"
    if "partial_trace" not in fusion.columns:
        fusion["partial_trace"] = "not_evaluated"
    # Retrospective OOF fusion can have missing axes by design.
    for axis, prob_col in [
        ("origin", "origin_ai_probability"),
        ("replay", "replay_probability"),
        ("mixer", "mixer_probability"),
        ("partial", "partial_max_segment_probability"),
    ]:
        missing = fusion[prob_col].astype(str).str.strip().eq("") | fusion[prob_col].isna()
        fusion.loc[missing, f"{axis}_model_available"] = "false"
        trace_col = f"{axis}_trace"
        if trace_col in fusion.columns:
            fusion.loc[missing, trace_col] = (
                "axis not available for this retrospective OOF fusion record"
            )

    for i in iter_with_progress(
        range(len(fusion)),
        total=len(fusion),
        desc="phase8f fusion rows",
        enabled=show_progress,
        progress_every=25,
        unit="file",
    ):
        row = fusion.iloc[i].to_dict()
        row.update(fuse_origin_evidence(row))
        row.update(fuse_replay_evidence(row))
        row.update(fuse_mixer_evidence(row))
        row.update(fuse_partial_evidence(row))
        row.update(apply_multi_axis_fusion(row))
        fusion.loc[i, "origin_evidence_label"] = row["origin_evidence_label"]
        fusion.loc[i, "origin_evidence_strength"] = row["origin_evidence_strength"]
        fusion.loc[i, "replay_evidence_label"] = row["replay_evidence_label"]
        fusion.loc[i, "replay_evidence_strength"] = row["replay_evidence_strength"]
        fusion.loc[i, "mixer_evidence_label"] = row["mixer_evidence_label"]
        fusion.loc[i, "mixer_evidence_strength"] = row["mixer_evidence_strength"]
        fusion.loc[i, "partial_evidence_label"] = row["partial_evidence_label"]
        fusion.loc[i, "partial_evidence_strength"] = row["partial_evidence_strength"]
        fusion.loc[i, "experimental_fusion_status"] = row["experimental_fusion_status"]
        fusion.loc[i, "forensic_risk_level"] = row["forensic_risk_level"]
        fusion.loc[i, "manual_review_required"] = row["manual_review_required"]
        fusion.loc[i, "manual_review_reason"] = row["manual_review_reason"]
        fusion.loc[i, "fusion_trace"] = row["fusion_trace"]

    fusion["forensic_summary"] = fusion["experimental_fusion_status"].map(
        lambda s: f"Experimental status `{s}` from multi-axis evidence indicators."
    )
    fusion["safe_report_text"] = fusion.apply(
        lambda r: generate_safe_report(r.to_dict(), None),
        axis=1,
    )
    fusion["limitations"] = fusion.apply(
        lambda r: (
            "Experimental multi-axis evidence indicator only; does not by itself prove fabrication. "
            + "Missing retrospective OOF axes: "
            + ",".join(
                [
                    axis
                    for axis, avail in [
                        ("origin", r.get("origin_model_available", "false")),
                        ("replay", r.get("replay_model_available", "false")),
                        ("mixer", r.get("mixer_model_available", "false")),
                        ("partial", r.get("partial_model_available", "false")),
                    ]
                    if str(avail).strip().lower() != "true"
                ]
            )
        ),
        axis=1,
    )

    seg_by_file: dict[str, list[dict[str, Any]]] = {}
    for _, srow in segment_out_df.iterrows():
        seg_by_file.setdefault(str(srow["file_id"]), []).append(srow.to_dict())

    jsonl_path = out_dir / "phase8f_experimental_forensic_reports.jsonl"
    md_path = out_dir / "phase8f_experimental_forensic_reports.md"
    report_rows = []
    md_lines = ["# Phase 8F Experimental Forensic Reports", ""]
    with jsonl_path.open("w", encoding="utf-8") as f:
        for _, row in fusion.iterrows():
            file_id = str(row["file_id"])
            text = generate_safe_report(row.to_dict(), seg_by_file.get(file_id, []))
            payload = {
                "schema_version": SCHEMA_VERSION,
                "file_id": file_id,
                "experimental_fusion_status": row["experimental_fusion_status"],
                "forensic_risk_level": row["forensic_risk_level"],
                "manual_review_required": row["manual_review_required"],
                "safe_report_text": text,
            }
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
            md_lines.extend([f"## {file_id}", "", text, ""])
            report_rows.append(payload)

    fusion_report_path = out_dir / "phase8f_fusion_report.md"
    summary_df = _build_summary_records(fusion)
    summary_lines = [
        "# Phase 8F Fusion Report",
        "",
        "Experimental multi-axis fusion outputs only.",
        "No final proof claim, no fake/real collapse.",
        "",
        "## Key Counts",
        "",
    ]
    for _, rec in summary_df.iterrows():
        summary_lines.append(f"- {rec['metric_name']}: {rec['metric_value']}")
    summary_lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- origin, replay, mixer/channel, and partial evidence remain separate axes",
            "- replay evidence does not imply AI-generated origin",
            "- mixer/channel evidence does not imply AI-generated origin",
            "- partial evidence is timestamp/segment candidate evidence",
            "- manual review recommended for inconclusive/conflicting/borderline cases",
        ]
    )

    manual_review_queue = fusion[
        (fusion["manual_review_required"] == "true")
        | (fusion["origin_evidence_strength"] == "borderline")
        | (fusion["replay_evidence_strength"] == "borderline")
        | (fusion["mixer_evidence_strength"] == "borderline")
        | (fusion["partial_evidence_strength"].isin(["moderate", "high"]))
    ].copy()
    manual_review_queue["top_segment_ranges"] = manual_review_queue["partial_top_segment_ranges"].fillna("")
    manual_review_queue["priority"] = np.where(
        manual_review_queue["forensic_risk_level"] == "high",
        "high",
        np.where(manual_review_queue["forensic_risk_level"] == "medium", "medium", "low"),
    )
    manual_review_queue["reviewer_action"] = "review_multi_axis_evidence_and_context"
    manual_review_queue = manual_review_queue[
        [
            "file_id",
            "experimental_fusion_status",
            "forensic_risk_level",
            "manual_review_reason",
            "top_segment_ranges",
            "priority",
            "reviewer_action",
        ]
    ]

    file_cols = [
        "schema_version",
        "file_id",
        "audio_path",
        "known_origin_label",
        "known_manipulation_labels",
        "source_dataset",
        "split",
        "origin_model_available",
        "origin_feature_set",
        "origin_ai_probability",
        "origin_threshold_candidate",
        "origin_evidence_label",
        "origin_evidence_strength",
        "origin_trace",
        "replay_model_available",
        "replay_feature_set",
        "replay_probability",
        "replay_threshold_candidate",
        "replay_evidence_label",
        "replay_evidence_strength",
        "replay_trace",
        "mixer_model_available",
        "mixer_feature_set",
        "mixer_probability",
        "mixer_threshold_candidate",
        "mixer_evidence_label",
        "mixer_evidence_strength",
        "mixer_trace",
        "partial_model_available",
        "partial_feature_set",
        "partial_max_segment_probability",
        "partial_mean_topk_probability",
        "partial_candidate_segment_count",
        "partial_predicted_candidate_count",
        "partial_evidence_label",
        "partial_evidence_strength",
        "partial_top_segment_ranges",
        "partial_trace",
        "experimental_fusion_status",
        "forensic_risk_level",
        "manual_review_required",
        "manual_review_reason",
        "fusion_trace",
        "forensic_summary",
        "safe_report_text",
        "limitations",
    ]
    for c in file_cols:
        if c not in fusion.columns:
            fusion[c] = ""
    fusion = fusion[file_cols]

    fusion.to_csv(out_dir / "phase8f_file_fusion_records.csv", index=False)
    segment_out_df.to_csv(out_dir / "phase8f_segment_fusion_records.csv", index=False)
    manual_review_queue.to_csv(out_dir / "phase8f_manual_review_queue.csv", index=False)
    summary_df.to_csv(out_dir / "phase8f_fusion_summary.csv", index=False)
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    fusion_report_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    if args.make_reports:
        # Reports are always written; this flag is retained for interface compatibility.
        pass

    print("Phase 8F experimental fusion records created.")
    print(f"Output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
