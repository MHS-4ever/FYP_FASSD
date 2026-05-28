#!/usr/bin/env python3
"""Validate Phase 8E-2 localization-preparation outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_COLUMNS = {
    "fake_score",
    "real_score",
    "ai_score",
    "predicted_label",
    "prediction",
    "final_forensic_status",
    "suspicious_segment_flag",
    "evidence_origin_score",
    "origin_score",
}
ALLOWED_CANDIDATE_TYPES = {
    "within_file_deviation_candidate",
    "neighbor_transition_candidate",
    "inside_outside_candidate",
    "combined_localization_candidate",
    "both_deviation_and_transition",
    "not_top_candidate",
    "insufficient_data",
}
ALLOWED_USE_VALUES = {
    "manual_review_candidate",
    "phase8f_fusion_candidate",
    "not_supervised_training_label",
    "supervised_training_candidate",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8E-2 localization outputs.")
    p.add_argument("--input_dir", default="reports/phase8/models/phase8e2")
    p.add_argument("--timestamp_annotations_used", action="store_true")
    p.add_argument("--expected_timestamp_rows", type=int, default=0)
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8e2_localization_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def validate(args: argparse.Namespace) -> dict[str, object]:
    blocking: list[str] = []
    warnings: list[str] = []
    base = _resolve(args.input_dir)

    req = {
        "file_summary": base / "phase8e2_partial_file_summary.csv",
        "segment_table": base / "phase8e2_partial_segment_localization_table.csv",
        "inside_outside": base / "phase8e2_inside_outside_delta_features.csv",
        "neighbor": base / "phase8e2_neighbor_transition_features.csv",
        "candidates": base / "phase8e2_suspicious_segment_candidates.csv",
        "top_candidates": base / "phase8e2_top_suspicious_segment_candidates.csv",
        "timestamp_audit": base / "phase8e2_timestamp_label_audit.csv",
        "readiness": base / "phase8e2_phase8e3_readiness_review.csv",
        "report": base / "phase8e2_partial_localization_report.md",
        "normalized_annotations": base / "phase8e2_timestamp_annotation_normalized.csv",
    }
    required = {k: v for k, v in req.items() if k != "normalized_annotations"}
    missing = [k for k, v in required.items() if not v.is_file()]
    if missing:
        return {"status": "FAIL", "blocking": [f"Missing required files: {missing}"], "warnings": []}
    if args.timestamp_annotations_used and (not req["normalized_annotations"].is_file()):
        return {
            "status": "FAIL",
            "blocking": ["Missing phase8e2_timestamp_annotation_normalized.csv while timestamp annotations were used."],
            "warnings": [],
        }

    file_df = _read(req["file_summary"])
    seg_df = _read(req["segment_table"])
    cand_df = _read(req["candidates"])
    top_cand_df = _read(req["top_candidates"])
    ts_df = _read(req["timestamp_audit"])
    ready_df = _read(req["readiness"])
    ann_df = _read(req["normalized_annotations"]) if req["normalized_annotations"].is_file() else pd.DataFrame()

    required_cols = {
        "file_summary": {"file_id", "segment_count", "has_true_timestamp_labels", "usable_for_phase8e3_training", "localization_status"},
        "segment_table": {
            "file_id",
            "segment_id",
            "candidate_type",
            "candidate_reason",
            "localization_candidate_rank_within_file",
            "timestamp_segment_label",
            "training_label_available",
            "max_fabricated_overlap_sec",
            "max_fabricated_overlap_ratio",
            "total_fabricated_overlap_sec",
            "allowed_use",
        },
        "inside_outside": {"file_id", "segment_id", "mode", "combined_deviation_score"},
        "top_candidates": {
            "file_id",
            "segment_id",
            "candidate_rank_within_file",
            "candidate_type",
            "timestamp_segment_label",
            "training_label_available",
            "allowed_use",
        },
        "neighbor": {"file_id", "segment_id", "combined_neighbor_transition_score", "transition_rank_within_file"},
        "candidates": {
            "file_id",
            "segment_id",
            "candidate_rank_within_file",
            "candidate_type",
            "timestamp_segment_label",
            "training_label_available",
            "allowed_use",
        },
        "timestamp_audit": {
            "file_id",
            "has_true_timestamp_labels",
            "timestamp_columns_found",
            "timestamp_label_source",
            "valid_timestamp_region_count",
            "usable_for_supervised_segment_training",
            "fabricated_segment_count",
            "outside_segment_count",
            "reason",
        },
        "readiness": {"criterion", "status", "evidence", "recommendation"},
        "normalized_annotations": {
            "annotation_id",
            "source_annotation_file",
            "matched_file_id",
            "fabricated_start_sec",
            "fabricated_end_sec",
            "annotation_status",
        },
    }
    for name, cols in required_cols.items():
        if name == "normalized_annotations" and len(ann_df) == 0:
            continue
        df = _read(req[name]) if name in req and name not in {"report"} else None
        if df is None:
            continue
        miss = sorted(cols - set(df.columns))
        if miss:
            blocking.append(f"{name} missing required columns: {miss}")

    for name, p in req.items():
        if name == "report" or (name == "normalized_annotations" and not p.is_file()):
            continue
        d = _read(p)
        hit = sorted(FORBIDDEN_COLUMNS.intersection(set(d.columns)))
        if hit:
            blocking.append(f"{name} contains forbidden columns: {hit}")

    artifacts = list(base.glob("*.joblib")) + list(base.glob("*.pkl")) + list(base.glob("*.pt")) + list(base.glob("*.onnx"))
    if artifacts:
        blocking.append(f"Unexpected model artifacts in phase8e2 dir: {[a.name for a in artifacts]}")

    if "candidate_type" in seg_df.columns:
        bad = sorted(set(seg_df["candidate_type"]) - ALLOWED_CANDIDATE_TYPES)
        if bad:
            blocking.append(f"Invalid candidate_type values: {bad}")
    if "allowed_use" in cand_df.columns:
        bad = sorted(set(cand_df["allowed_use"]) - ALLOWED_USE_VALUES)
        if bad:
            blocking.append(f"Invalid allowed_use values: {bad}")
    if "timestamp_segment_label" in seg_df.columns:
        allowed_tsl = {"fabricated_region", "outside_fabricated_region", "unknown_no_timestamp", "ambiguous_timestamp"}
        bad = sorted(set(seg_df["timestamp_segment_label"]) - allowed_tsl)
        if bad:
            blocking.append(f"Invalid timestamp_segment_label values: {bad}")
    if "mode" in _read(req["inside_outside"]).columns:
        mode_vals = set(_read(req["inside_outside"])["mode"].astype(str).unique())
        if args.timestamp_annotations_used and "timestamp_inside_outside" not in mode_vals:
            blocking.append("inside_outside features missing mode=timestamp_inside_outside rows while timestamp annotations used.")

    merged = cand_df.merge(ts_df[["file_id", "has_true_timestamp_labels"]], on="file_id", how="left")
    if len(merged):
        unsafe = merged[
            (merged["training_label_available"].astype(str).str.lower() == "true")
            & (merged["has_true_timestamp_labels"].astype(str).str.lower() != "true")
        ]
        if len(unsafe):
            blocking.append("training_label_available=true found without true timestamp labels.")
    if len(cand_df):
        invalid_true = cand_df[
            (cand_df["training_label_available"].astype(str).str.lower() == "true")
            & (~cand_df["timestamp_segment_label"].isin(["fabricated_region", "outside_fabricated_region"]))
        ]
        if len(invalid_true):
            blocking.append("training_label_available=true appears for non timestamp-aligned labels.")
        invalid_use = cand_df[
            (cand_df["allowed_use"] == "supervised_training_candidate")
            & (cand_df["training_label_available"].astype(str).str.lower() != "true")
        ]
        if len(invalid_use):
            blocking.append("supervised_training_candidate appears without training_label_available=true.")
    if len(top_cand_df):
        frac_not_top = float((top_cand_df["candidate_type"] == "not_top_candidate").mean())
        if frac_not_top > 0.8:
            blocking.append("Top-candidates table contains too many not_top_candidate rows.")

    ready_row = ready_df[ready_df["criterion"] == "ready_for_supervised_partial_segment_training"]
    ts_true = int((ts_df["has_true_timestamp_labels"].astype(str).str.lower() == "true").sum())
    if len(ready_row):
        status = ready_row["status"].iloc[0].strip().lower()
        if ts_true == 0 and status != "no":
            blocking.append("Readiness is not 'no' despite no true timestamp labels.")
    else:
        blocking.append("Missing readiness criterion row for ready_for_supervised_partial_segment_training.")

    if len(ann_df):
        if args.expected_timestamp_rows > 0 and len(ann_df) != args.expected_timestamp_rows:
            blocking.append(
                f"Normalized annotation row count mismatch: expected {args.expected_timestamp_rows}, found {len(ann_df)}"
            )
        matched_count = int((ann_df["annotation_status"] == "matched").sum())
        if matched_count == 0 and args.timestamp_annotations_used:
            blocking.append("No matched timestamp annotations found despite timestamp_annotations_used.")

    if len(ready_df):
        crits = set(ready_df["criterion"].astype(str))
        for needed in {"inside_outside_feature_columns_created", "top_candidate_table_created"}:
            if needed not in crits:
                blocking.append(f"Readiness review missing criterion: {needed}")

    report_txt = req["report"].read_text(encoding="utf-8").lower()
    must_phrases = [
        "no training",
        "no predictions",
        "no final forensic decisions",
        "not a confirmed fabricated segment",
    ]
    for ph in must_phrases:
        if ph not in report_txt:
            warnings.append(f"Report missing phrase: '{ph}'")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "partial_file_count": len(file_df),
        "partial_segment_count": len(seg_df),
        "timestamp_label_availability_count": ts_true,
        "top_candidate_count": int((cand_df["candidate_rank_within_file"].astype(str).str.strip() == "1").sum()) if "candidate_rank_within_file" in cand_df.columns else 0,
        "top_candidates_rows": len(top_cand_df),
        "phase8e3_readiness": ready_row["status"].iloc[0] if len(ready_row) else "unknown",
        "normalized_annotation_rows": len(ann_df),
        "matched_annotations": int((ann_df["annotation_status"] == "matched").sum()) if len(ann_df) else 0,
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8E-2 Localization Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "## Summary",
        "",
        f"- partial file count: {result.get('partial_file_count', 0)}",
        f"- partial segment count: {result.get('partial_segment_count', 0)}",
        f"- timestamp label availability count: {result.get('timestamp_label_availability_count', 0)}",
        f"- top candidate count: {result.get('top_candidate_count', 0)}",
        f"- top candidates rows: {result.get('top_candidates_rows', 0)}",
        f"- phase8e3 readiness: {result.get('phase8e3_readiness', 'unknown')}",
        f"- normalized annotation rows: {result.get('normalized_annotation_rows', 0)}",
        f"- matched annotation rows: {result.get('matched_annotations', 0)}",
    ]
    if result.get("blocking"):
        lines.extend(["", "## Blocking Errors", ""])
        lines.extend(f"- {x}" for x in result["blocking"])  # type: ignore[index]
    if result.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {x}" for x in result["warnings"])  # type: ignore[index]
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Phase 8E-2 is localization preparation only.",
            "- No training, no predictions, and no final forensic decisions are allowed.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result)
    print(f"Validation: {result.get('status')}")
    print(f"Report -> {out}")
    return 1 if result.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
