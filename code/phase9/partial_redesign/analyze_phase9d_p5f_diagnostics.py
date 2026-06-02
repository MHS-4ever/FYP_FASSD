#!/usr/bin/env python3
"""
Phase 9D-P5F-P2: Diagnostic analysis of false negatives and false positives.

Analysis only — no retrain, no threshold changes, no release packaging.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_evaluation_shared import P5D_TIMESTAMP_OVERLAP_THRESHOLD, segment_overlap_metrics
from phase9d_p5_training_utils import P5C_ACCEPTED_CASCADE_THRESHOLDS, apply_p5c_cascade_rule, repo_root_from_here

ACCEPTED = P5C_ACCEPTED_CASCADE_THRESHOLDS
FILE_GATE_TH = float(ACCEPTED["file_gate_threshold"])
SEGMENT_TH = float(ACCEPTED["segment_threshold"])
CONTRAST_TH = float(ACCEPTED["contrast_threshold"])
BROAD_LIMIT = float(ACCEPTED["broad_limit"])

CASE_SUMMARY_COLUMNS = [
    "case_type",
    "file_path",
    "file_name",
    "test_group",
    "expected_condition",
    "expected_partial_label",
    "partial_evidence_positive",
    "file_gate_probability",
    "file_gate_positive",
    "max_segment_probability",
    "segment_threshold_positive",
    "high_segment_fraction",
    "broad_activation_flag",
    "topk_minus_rest_probability",
    "contrast_positive",
    "candidate_segment_start",
    "candidate_segment_end",
    "candidate_segment_probability",
    "candidate_segment_rank",
    "has_timestamp_label",
    "timestamp_start",
    "timestamp_end",
    "top1_timestamp_hit",
    "top3_timestamp_hit",
    "top5_timestamp_hit",
    "candidate_timestamp_error_seconds",
    "timestamp_match_method",
    "primary_failure_reason",
    "secondary_failure_reason",
    "threshold_failure_flags",
    "near_miss_flags",
    "recommended_manual_review_note",
]

TOP_SEGMENT_COLUMNS = [
    "case_type",
    "file_path",
    "file_name",
    "segment_rank",
    "segment_index_chronological",
    "segment_start",
    "segment_end",
    "segment_probability",
    "is_high_segment",
    "has_timestamp_label",
    "timestamp_start",
    "timestamp_end",
    "overlaps_known_fabricated_timestamp",
    "expected_segment_label",
    "segment_relation_to_timestamp",
    "segment_manual_review_note",
]

TS_LOC_COLUMNS = [
    "file_path",
    "file_name",
    "partial_evidence_positive",
    "timestamp_start",
    "timestamp_end",
    "candidate_segment_start",
    "candidate_segment_end",
    "candidate_timestamp_error_seconds",
    "top1_timestamp_hit",
    "top3_timestamp_hit",
    "top5_timestamp_hit",
    "best_timestamp_overlap_rank",
    "best_timestamp_overlap_probability",
    "max_inside_timestamp_probability",
    "max_outside_timestamp_probability",
    "inside_minus_outside_probability",
    "localization_status",
]

COUNTERFACTUAL_COLUMNS = [
    "file_path",
    "file_name",
    "case_type",
    "current_file_gate_threshold",
    "current_segment_threshold",
    "current_contrast_threshold",
    "current_broad_limit",
    "required_file_gate_threshold_to_pass",
    "required_segment_threshold_to_pass",
    "required_contrast_threshold_to_pass",
    "required_broad_limit_to_pass",
    "which_single_gate_relaxation_would_recover",
    "whether_single_gate_relaxation_would_create_risk",
    "primary_failure_reason",
]

SENSITIVITY_COLUMNS = [
    "file_gate_threshold",
    "segment_threshold",
    "contrast_threshold",
    "broad_limit",
    "partial_recall",
    "fabricated_20pct_recall",
    "non_partial_false_alarm_rate",
    "direct_false_partial_rate",
    "false_positive_count",
    "false_negative_count",
    "recovered_fabricated_20pct_count",
    "new_false_positive_count",
    "diagnostic_only",
]

PROB_DIST_COLUMNS = [
    "group",
    "count",
    "median_file_gate_probability",
    "median_max_segment_probability",
    "median_high_segment_fraction",
    "median_topk_minus_rest_probability",
    "min_file_gate_probability",
    "max_file_gate_probability",
    "min_max_segment_probability",
    "max_max_segment_probability",
    "min_high_segment_fraction",
    "max_high_segment_fraction",
    "min_topk_minus_rest_probability",
    "max_topk_minus_rest_probability",
]

FP_EXPLANATIONS = (
    "strong_file_gate_plus_strong_segment",
    "localized_high_segment_false_alarm",
    "broad_activation_false_alarm",
    "high_contrast_artifact_like_pattern",
    "condition_label_needs_manual_review",
    "unknown_false_positive_pattern",
)


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P5F-P2 diagnostic analysis (read-only).")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5f"),
    )
    p.add_argument(
        "--output_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5f_p2_diagnostics"),
    )
    p.add_argument("--make_plots", action="store_true")
    return p.parse_args()


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(("true", "1", "yes"))


def _num(s: Any) -> float:
    v = pd.to_numeric(s, errors="coerce")
    return float(v) if np.isfinite(v) else np.nan


def load_p5f_outputs(input_dir: Path) -> dict[str, Any]:
    return {
        "file_pred": _safe_read_csv(input_dir / "phase9d_p5f_file_predictions.csv"),
        "seg_pred": _safe_read_csv(input_dir / "phase9d_p5f_segment_predictions.csv"),
        "manifest": _safe_read_csv(input_dir / "phase9d_p5f_expanded_manifest.csv"),
        "metrics": json.loads((input_dir / "phase9d_p5f_expanded_metrics.json").read_text(encoding="utf-8"))
        if (input_dir / "phase9d_p5f_expanded_metrics.json").is_file()
        else {},
        "ts_audit": _safe_read_csv(input_dir / "phase9d_p5f_timestamp_loading_audit.csv"),
    }


def ok_files(file_pred: pd.DataFrame) -> pd.DataFrame:
    return file_pred[file_pred["error_status"].astype(str) == "ok"].copy()


def enrich_with_manifest_timestamps(
    file_pred: pd.DataFrame,
    manifest: pd.DataFrame,
) -> pd.DataFrame:
    """Merge timestamp_start/end from manifest (not stored on file_predictions)."""
    if file_pred.empty:
        return file_pred.copy()
    out = file_pred.copy()
    if manifest.empty or "file_path" not in manifest.columns:
        for col in ("timestamp_start", "timestamp_end"):
            if col not in out.columns:
                out[col] = np.nan
        return out

    ts_cols = [c for c in ("timestamp_start", "timestamp_end") if c in manifest.columns]
    if not ts_cols:
        for col in ("timestamp_start", "timestamp_end"):
            if col not in out.columns:
                out[col] = np.nan
        return out

    m = manifest[["file_path", *ts_cols]].drop_duplicates(subset=["file_path"])
    out = out.merge(m, on="file_path", how="left", suffixes=("", "_manifest"))
    for col in ts_cols:
        manifest_col = f"{col}_manifest"
        if manifest_col in out.columns:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce").fillna(
                    pd.to_numeric(out[manifest_col], errors="coerce")
                )
            else:
                out[col] = pd.to_numeric(out[manifest_col], errors="coerce")
            out.drop(columns=[manifest_col], inplace=True, errors="ignore")
    return out


def identify_false_negatives(ok: pd.DataFrame) -> pd.DataFrame:
    m = (
        ok["expected_partial_label"].astype(int).eq(1)
        & ok["test_group"].astype(str).eq("fabricated_20pct")
        & (~_bool_series(ok["partial_evidence_positive"]))
    )
    return ok[m].copy()


def identify_false_positives(ok: pd.DataFrame) -> pd.DataFrame:
    m = ok["expected_partial_label"].astype(int).eq(0) & _bool_series(ok["partial_evidence_positive"])
    return ok[m].copy()


def _cascade_flags(row: pd.Series) -> dict[str, bool]:
    fg = _num(row.get("file_gate_probability"))
    mx = _num(row.get("max_segment_probability"))
    hf = _num(row.get("high_segment_fraction"))
    tk = _num(row.get("topk_minus_rest_probability"))
    return {
        "file_gate_miss": fg < FILE_GATE_TH,
        "segment_threshold_miss": mx < SEGMENT_TH,
        "broad_activation_block": hf > BROAD_LIMIT,
        "contrast_miss": tk < CONTRAST_TH,
    }


def _primary_failure(flags: dict[str, bool]) -> tuple[str, str, str]:
    order = [
        ("file_gate_miss", "file_gate_miss"),
        ("segment_threshold_miss", "segment_threshold_miss"),
        ("broad_activation_block", "broad_activation_block"),
        ("contrast_miss", "contrast_miss"),
    ]
    active = [name for key, name in order if flags.get(key, False)]
    if not active:
        return "unknown_cascade_failure", "", ""
    primary = active[0]
    secondary = active[1] if len(active) > 1 else ""
    return primary, secondary, ";".join(active)


def _near_miss_flags(row: pd.Series) -> str:
    fg_margin = _num(row.get("file_gate_probability")) - FILE_GATE_TH
    seg_margin = _num(row.get("max_segment_probability")) - SEGMENT_TH
    contrast_margin = _num(row.get("topk_minus_rest_probability")) - CONTRAST_TH
    broad_margin = BROAD_LIMIT - _num(row.get("high_segment_fraction"))
    flags: list[str] = []
    if -0.10 <= fg_margin < 0:
        flags.append("near_file_gate")
    if -0.10 <= seg_margin < 0:
        flags.append("near_segment_threshold")
    if -0.10 <= contrast_margin < 0:
        flags.append("near_contrast")
    if -0.10 <= broad_margin < 0:
        flags.append("near_broad_limit")
    return ";".join(flags)


def diagnose_false_negative_row(row: pd.Series) -> dict[str, str]:
    flags = _cascade_flags(row)
    primary, secondary, flag_str = _primary_failure(flags)
    note = (
        f"Experimental cascade did not flag partial evidence; primary gate failure: {primary}. "
        "Manual review of candidate segments and timestamp alignment recommended."
    )
    return {
        "primary_failure_reason": primary,
        "secondary_failure_reason": secondary,
        "threshold_failure_flags": flag_str,
        "near_miss_flags": _near_miss_flags(row),
        "recommended_manual_review_note": note,
    }


def diagnose_false_positive_row(row: pd.Series) -> dict[str, str]:
    cond = str(row.get("expected_condition", "unknown"))
    fg = _num(row.get("file_gate_probability"))
    mx = _num(row.get("max_segment_probability"))
    hf = _num(row.get("high_segment_fraction"))
    broad = _bool_series(pd.Series([row.get("broad_activation_flag")])).iloc[0]
    contrast = _bool_series(pd.Series([row.get("contrast_positive")])).iloc[0]

    if fg >= 0.95 and mx >= 0.95:
        expl = "strong_file_gate_plus_strong_segment"
    elif broad or hf > BROAD_LIMIT:
        expl = "broad_activation_false_alarm"
    elif contrast and mx >= SEGMENT_TH:
        expl = "high_contrast_artifact_like_pattern"
    elif mx >= SEGMENT_TH and hf <= BROAD_LIMIT:
        expl = "localized_high_segment_false_alarm"
    elif cond in ("unknown", "unknown_testing_condition", ""):
        expl = "condition_label_needs_manual_review"
    else:
        expl = "unknown_false_positive_pattern"

    note = (
        f"Non-partial label ({cond}) but experimental partial-fabrication candidate segment flagged "
        f"({expl}). Manual label/audio review recommended — do not treat as final authenticity verdict."
    )
    return {
        "primary_failure_reason": expl,
        "secondary_failure_reason": cond,
        "threshold_failure_flags": "",
        "near_miss_flags": "",
        "recommended_manual_review_note": note,
    }


def build_case_summary(fn: pd.DataFrame, fp: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for case_type, subset in (("fabricated_20pct_false_negative", fn), ("nonpartial_false_positive", fp)):
        for _, row in subset.iterrows():
            diag = (
                diagnose_false_negative_row(row)
                if case_type == "fabricated_20pct_false_negative"
                else diagnose_false_positive_row(row)
            )
            rec = {"case_type": case_type}
            for col in CASE_SUMMARY_COLUMNS:
                if col in ("case_type", "primary_failure_reason", "secondary_failure_reason", "threshold_failure_flags", "near_miss_flags", "recommended_manual_review_note"):
                    continue
                rec[col] = row.get(col, "")
            rec.update(diag)
            rows.append(rec)
    if not rows:
        return pd.DataFrame(columns=CASE_SUMMARY_COLUMNS)
    out = pd.DataFrame(rows)
    return out.reindex(columns=CASE_SUMMARY_COLUMNS)


def _segment_relation(overlaps: bool, prob: float, ts_start: float, ts_end: float) -> str:
    if not np.isfinite(ts_start) or not np.isfinite(ts_end):
        return "timestamp_unavailable"
    if overlaps:
        return "overlaps_fabricated_timestamp"
    return "outside_fabricated_timestamp"


def build_top_segments(
    cases: pd.DataFrame,
    seg_pred: pd.DataFrame,
    file_pred: pd.DataFrame,
    *,
    top_n: int = 10,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fp_lookup = file_pred.set_index("file_path") if not file_pred.empty else pd.DataFrame()

    for _, case in cases.iterrows():
        fp = str(case["file_path"])
        case_type = str(case["case_type"])
        segs = seg_pred[seg_pred["file_path"].astype(str) == fp].copy()
        if segs.empty:
            continue
        segs = segs.sort_values("segment_probability", ascending=False).head(top_n)
        frow = fp_lookup.loc[fp] if fp in fp_lookup.index else case
        has_ts = _bool_series(pd.Series([frow.get("has_timestamp_label")])).iloc[0]
        ts_start = _num(frow.get("timestamp_start"))
        ts_end = _num(frow.get("timestamp_end"))

        for _, s in segs.iterrows():
            ov = bool(s.get("overlaps_known_fabricated_timestamp"))
            if has_ts and np.isfinite(ts_start) and np.isfinite(ts_end):
                ov_metrics = segment_overlap_metrics(
                    float(s["segment_start"]),
                    float(s["segment_end"]),
                    ts_start,
                    ts_end,
                    P5D_TIMESTAMP_OVERLAP_THRESHOLD,
                )
                rel = ov_metrics.get("timestamp_region_label", "outside_fabricated_region")
                if rel == "inside_fabricated_region":
                    rel_str = "overlaps_fabricated_timestamp"
                elif rel == "partial_overlap":
                    rel_str = "partial_overlap_timestamp"
                else:
                    rel_str = "outside_fabricated_timestamp"
            else:
                rel_str = _segment_relation(ov, _num(s["segment_probability"]), ts_start, ts_end)

            note = (
                "Top-ranked candidate segment for diagnostic review; "
                "experimental evidence indicator only."
            )
            rows.append(
                {
                    "case_type": case_type,
                    "file_path": fp,
                    "file_name": case.get("file_name", s.get("file_name")),
                    "segment_rank": int(s["segment_rank"]),
                    "segment_index_chronological": int(s["segment_index_chronological"]),
                    "segment_start": float(s["segment_start"]),
                    "segment_end": float(s["segment_end"]),
                    "segment_probability": float(s["segment_probability"]),
                    "is_high_segment": bool(s.get("is_high_segment")),
                    "has_timestamp_label": has_ts,
                    "timestamp_start": ts_start if has_ts else "",
                    "timestamp_end": ts_end if has_ts else "",
                    "overlaps_known_fabricated_timestamp": ov,
                    "expected_segment_label": int(s.get("expected_segment_label", 0)),
                    "segment_relation_to_timestamp": rel_str,
                    "segment_manual_review_note": note,
                }
            )

    if not rows:
        return pd.DataFrame(columns=TOP_SEGMENT_COLUMNS)
    return pd.DataFrame(rows).reindex(columns=TOP_SEGMENT_COLUMNS)


def _localization_status(row: pd.Series, inside_max: float, outside_max: float) -> str:
    if not _bool_series(pd.Series([row.get("has_timestamp_label")])).iloc[0]:
        return "timestamp_unavailable"
    if _bool_series(pd.Series([row.get("partial_evidence_positive")])).iloc[0]:
        if _bool_series(pd.Series([row.get("top1_timestamp_hit")])).iloc[0]:
            return "detected_top1_localized"
        if _bool_series(pd.Series([row.get("top3_timestamp_hit")])).iloc[0]:
            return "detected_top3_localized"
        if _bool_series(pd.Series([row.get("top5_timestamp_hit")])).iloc[0]:
            return "detected_top5_localized"
        return "detected_but_not_top5"
    if inside_max >= SEGMENT_TH and inside_max > outside_max:
        return "missed_but_timestamp_region_has_signal"
    return "missed_no_timestamp_region_signal"


def build_timestamp_localization(
    ok: pd.DataFrame,
    seg_pred: pd.DataFrame,
) -> pd.DataFrame:
    fab = ok[ok["test_group"].astype(str).eq("fabricated_20pct")].copy()
    fab = fab[_bool_series(fab["has_timestamp_label"])]
    rows: list[dict[str, Any]] = []

    for _, row in fab.iterrows():
        fp = str(row["file_path"])
        segs = seg_pred[seg_pred["file_path"].astype(str) == fp]
        ts_start = _num(row.get("timestamp_start"))
        ts_end = _num(row.get("timestamp_end"))

        inside_max = outside_max = np.nan
        best_rank = np.nan
        best_prob = np.nan

        if not segs.empty and np.isfinite(ts_start) and np.isfinite(ts_end):
            inside_probs: list[float] = []
            outside_probs: list[float] = []
            ranked = segs.sort_values("segment_probability", ascending=False)
            for _, s in ranked.iterrows():
                ov = segment_overlap_metrics(
                    float(s["segment_start"]),
                    float(s["segment_end"]),
                    ts_start,
                    ts_end,
                    P5D_TIMESTAMP_OVERLAP_THRESHOLD,
                )
                p = float(s["segment_probability"])
                if ov.get("timestamp_region_label") == "inside_fabricated_region":
                    inside_probs.append(p)
                    if not np.isfinite(best_rank):
                        best_rank = int(s["segment_rank"])
                        best_prob = p
                else:
                    outside_probs.append(p)
            inside_max = max(inside_probs) if inside_probs else 0.0
            outside_max = max(outside_probs) if outside_probs else 0.0

        inside_minus = (
            float(inside_max - outside_max)
            if np.isfinite(inside_max) and np.isfinite(outside_max)
            else np.nan
        )
        loc_status = _localization_status(row, inside_max, outside_max)

        rows.append(
            {
                "file_path": fp,
                "file_name": row.get("file_name"),
                "partial_evidence_positive": _bool_series(pd.Series([row["partial_evidence_positive"]])).iloc[0],
                "timestamp_start": ts_start,
                "timestamp_end": ts_end,
                "candidate_segment_start": _num(row.get("candidate_segment_start")),
                "candidate_segment_end": _num(row.get("candidate_segment_end")),
                "candidate_timestamp_error_seconds": _num(row.get("candidate_timestamp_error_seconds")),
                "top1_timestamp_hit": _bool_series(pd.Series([row.get("top1_timestamp_hit")])).iloc[0],
                "top3_timestamp_hit": _bool_series(pd.Series([row.get("top3_timestamp_hit")])).iloc[0],
                "top5_timestamp_hit": _bool_series(pd.Series([row.get("top5_timestamp_hit")])).iloc[0],
                "best_timestamp_overlap_rank": best_rank,
                "best_timestamp_overlap_probability": best_prob,
                "max_inside_timestamp_probability": inside_max,
                "max_outside_timestamp_probability": outside_max,
                "inside_minus_outside_probability": inside_minus,
                "localization_status": loc_status,
            }
        )

    if not rows:
        return pd.DataFrame(columns=TS_LOC_COLUMNS)
    return pd.DataFrame(rows).reindex(columns=TS_LOC_COLUMNS)


def _segment_probs_for_file(seg_pred: pd.DataFrame, file_path: str) -> np.ndarray:
    segs = seg_pred[seg_pred["file_path"].astype(str) == file_path]
    if segs.empty:
        return np.array([], dtype=float)
    return segs["segment_probability"].astype(float).to_numpy()


def _would_pass_cascade(
    file_gate_probability: float,
    segment_probs: np.ndarray,
    thresholds: dict[str, float],
) -> bool:
    out = apply_p5c_cascade_rule(
        file_gate_probability=float(file_gate_probability),
        segment_probs=segment_probs,
        thresholds=thresholds,
    )
    return bool(out["partial_evidence_positive"])


def _single_gate_recover(
    row: pd.Series,
    segment_probs: np.ndarray,
) -> tuple[str, str]:
    fg = _num(row["file_gate_probability"])
    base = dict(ACCEPTED)
    recoveries: list[str] = []
    risks: list[str] = []

    variants: dict[str, dict[str, float]] = {}
    if fg < FILE_GATE_TH:
        variants["file_gate"] = {**base, "file_gate_threshold": max(0.0, fg - 1e-9)}
    if _num(row["max_segment_probability"]) < SEGMENT_TH:
        variants["segment"] = {**base, "segment_threshold": max(0.0, _num(row["max_segment_probability"]) - 1e-9)}
    if _num(row["topk_minus_rest_probability"]) < CONTRAST_TH:
        variants["contrast"] = {**base, "contrast_threshold": max(0.0, _num(row["topk_minus_rest_probability"]) - 1e-9)}
    if _num(row["high_segment_fraction"]) > BROAD_LIMIT:
        variants["broad_limit"] = {**base, "broad_limit": _num(row["high_segment_fraction"]) + 1e-9}

    for name, th in variants.items():
        if _would_pass_cascade(fg, segment_probs, th):
            recoveries.append(name)

    return (";".join(recoveries) if recoveries else "none"), "see_global_sensitivity"


def _global_risk_for_relaxation(
    ok: pd.DataFrame,
    seg_pred: pd.DataFrame,
    gate_key: str,
    gate_value: float,
) -> int:
    """Count non-partial files that would become false positive under one relaxed gate."""
    th = dict(ACCEPTED)
    th[gate_key] = gate_value
    new_fp = 0
    non_partial = ok[ok["expected_partial_label"].astype(int).eq(0)]
    for _, row in non_partial.iterrows():
        if _bool_series(pd.Series([row["partial_evidence_positive"]])).iloc[0]:
            continue
        probs = _segment_probs_for_file(seg_pred, str(row["file_path"]))
        if _would_pass_cascade(_num(row["file_gate_probability"]), probs, th):
            new_fp += 1
    return new_fp


def build_threshold_counterfactual(
    fn: pd.DataFrame,
    ok: pd.DataFrame,
    seg_pred: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in fn.iterrows():
        fp = str(row["file_path"])
        probs = _segment_probs_for_file(seg_pred, fp)
        fg = _num(row["file_gate_probability"])
        mx = _num(row["max_segment_probability"])
        tk = _num(row["topk_minus_rest_probability"])
        hf = _num(row["high_segment_fraction"])
        flags = _cascade_flags(row)
        primary, _, _ = _primary_failure(flags)
        recover, _ = _single_gate_recover(row, probs)

        risk_notes: list[str] = []
        if fg < FILE_GATE_TH:
            new_fp = _global_risk_for_relaxation(ok, seg_pred, "file_gate_threshold", fg)
            risk_notes.append(f"file_gate_relaxation_new_fp={new_fp}")
        if mx < SEGMENT_TH:
            new_fp = _global_risk_for_relaxation(ok, seg_pred, "segment_threshold", mx)
            risk_notes.append(f"segment_relaxation_new_fp={new_fp}")
        if tk < CONTRAST_TH:
            new_fp = _global_risk_for_relaxation(ok, seg_pred, "contrast_threshold", tk)
            risk_notes.append(f"contrast_relaxation_new_fp={new_fp}")
        if hf > BROAD_LIMIT:
            new_fp = _global_risk_for_relaxation(ok, seg_pred, "broad_limit", hf)
            risk_notes.append(f"broad_relaxation_new_fp={new_fp}")

        rows.append(
            {
                "file_path": fp,
                "file_name": row.get("file_name"),
                "case_type": "fabricated_20pct_false_negative",
                "current_file_gate_threshold": FILE_GATE_TH,
                "current_segment_threshold": SEGMENT_TH,
                "current_contrast_threshold": CONTRAST_TH,
                "current_broad_limit": BROAD_LIMIT,
                "required_file_gate_threshold_to_pass": fg if fg < FILE_GATE_TH else FILE_GATE_TH,
                "required_segment_threshold_to_pass": mx if mx < SEGMENT_TH else SEGMENT_TH,
                "required_contrast_threshold_to_pass": tk if tk < CONTRAST_TH else CONTRAST_TH,
                "required_broad_limit_to_pass": hf if hf > BROAD_LIMIT else BROAD_LIMIT,
                "which_single_gate_relaxation_would_recover": recover,
                "whether_single_gate_relaxation_would_create_risk": "; ".join(risk_notes) or "no_relaxation_tested",
                "primary_failure_reason": primary,
            }
        )

    if not rows:
        return pd.DataFrame(columns=COUNTERFACTUAL_COLUMNS)
    return pd.DataFrame(rows).reindex(columns=COUNTERFACTUAL_COLUMNS)


def _eval_metrics_at_thresholds(
    ok: pd.DataFrame,
    seg_pred: pd.DataFrame,
    thresholds: dict[str, float],
    baseline_pos: dict[str, bool],
) -> dict[str, Any]:
    pred_pos: dict[str, bool] = {}
    for _, row in ok.iterrows():
        fp = str(row["file_path"])
        probs = _segment_probs_for_file(seg_pred, fp)
        pred_pos[fp] = _would_pass_cascade(_num(row["file_gate_probability"]), probs, thresholds)

    partial = ok[ok["expected_partial_label"].astype(int).eq(1)]
    non_partial = ok[ok["expected_partial_label"].astype(int).eq(0)]
    fab = ok[ok["test_group"].astype(str).eq("fabricated_20pct") & ok["expected_partial_label"].astype(int).eq(1)]
    direct = ok[ok["expected_condition"].astype(str).eq("direct")]

    def recall(df: pd.DataFrame) -> float | None:
        if df.empty:
            return None
        hits = sum(pred_pos.get(str(r["file_path"]), False) for _, r in df.iterrows())
        return float(hits / len(df))

    fp_count = sum(
        1
        for _, r in non_partial.iterrows()
        if pred_pos.get(str(r["file_path"]), False)
    )
    fn_count = sum(
        1
        for _, r in partial.iterrows()
        if not pred_pos.get(str(r["file_path"]), False)
    )
    recovered_fab = sum(
        1
        for _, r in fab.iterrows()
        if pred_pos.get(str(r["file_path"]), False) and not baseline_pos.get(str(r["file_path"]), False)
    )
    new_fp = sum(
        1
        for _, r in non_partial.iterrows()
        if pred_pos.get(str(r["file_path"]), False) and not baseline_pos.get(str(r["file_path"]), False)
    )

    direct_fp = 0
    direct_n = 0
    for _, r in direct.iterrows():
        direct_n += 1
        if pred_pos.get(str(r["file_path"]), False):
            direct_fp += 1

    return {
        "partial_recall": recall(partial),
        "fabricated_20pct_recall": recall(fab),
        "non_partial_false_alarm_rate": float(fp_count / len(non_partial)) if len(non_partial) else None,
        "direct_false_partial_rate": float(direct_fp / direct_n) if direct_n else None,
        "false_positive_count": fp_count,
        "false_negative_count": fn_count,
        "recovered_fabricated_20pct_count": recovered_fab,
        "new_false_positive_count": new_fp,
    }


def build_threshold_sensitivity(ok: pd.DataFrame, seg_pred: pd.DataFrame) -> pd.DataFrame:
    baseline_pos = {
        str(r["file_path"]): _bool_series(pd.Series([r["partial_evidence_positive"]])).iloc[0]
        for _, r in ok.iterrows()
    }
    fg_candidates = [0.40, 0.45, 0.50]
    seg_candidates = [0.80, 0.85, 0.90]
    contrast_candidates = [0.15, 0.20, 0.25]
    broad_candidates = [0.45]

    rows: list[dict[str, Any]] = []
    for fg in fg_candidates:
        for st in seg_candidates:
            for ct in contrast_candidates:
                for bl in broad_candidates:
                    th = {
                        "file_gate_threshold": fg,
                        "segment_threshold": st,
                        "contrast_threshold": ct,
                        "broad_limit": bl,
                    }
                    m = _eval_metrics_at_thresholds(ok, seg_pred, th, baseline_pos)
                    rows.append(
                        {
                            "file_gate_threshold": fg,
                            "segment_threshold": st,
                            "contrast_threshold": ct,
                            "broad_limit": bl,
                            **m,
                            "diagnostic_only": True,
                        }
                    )

    if not rows:
        return pd.DataFrame(columns=SENSITIVITY_COLUMNS)
    return pd.DataFrame(rows).reindex(columns=SENSITIVITY_COLUMNS)


def build_probability_distribution(ok: pd.DataFrame, fn: pd.DataFrame, fp: pd.DataFrame) -> pd.DataFrame:
    fn_paths = set(fn["file_path"].astype(str))
    fp_paths = set(fp["file_path"].astype(str))

    def label_row(r: pd.Series) -> str:
        fp = str(r["file_path"])
        if fp in fn_paths:
            return "fabricated_20pct_false_negative"
        if fp in fp_paths:
            return "nonpartial_false_positive"
        if r["expected_partial_label"] == 1 and _bool_series(pd.Series([r["partial_evidence_positive"]])).iloc[0]:
            return "true_partial_detected"
        if r["expected_partial_label"] == 0 and not _bool_series(pd.Series([r["partial_evidence_positive"]])).iloc[0]:
            return "nonpartial_true_negative"
        return "other"

    work = ok.copy()
    work["_group"] = work.apply(label_row, axis=1)
    work = work[work["_group"] != "other"]

    rows: list[dict[str, Any]] = []
    for group, g in work.groupby("_group"):
        rows.append(
            {
                "group": group,
                "count": int(len(g)),
                "median_file_gate_probability": float(g["file_gate_probability"].median()),
                "median_max_segment_probability": float(g["max_segment_probability"].median()),
                "median_high_segment_fraction": float(g["high_segment_fraction"].median()),
                "median_topk_minus_rest_probability": float(g["topk_minus_rest_probability"].median()),
                "min_file_gate_probability": float(g["file_gate_probability"].min()),
                "max_file_gate_probability": float(g["file_gate_probability"].max()),
                "min_max_segment_probability": float(g["max_segment_probability"].min()),
                "max_max_segment_probability": float(g["max_segment_probability"].max()),
                "min_high_segment_fraction": float(g["high_segment_fraction"].min()),
                "max_high_segment_fraction": float(g["high_segment_fraction"].max()),
                "min_topk_minus_rest_probability": float(g["topk_minus_rest_probability"].min()),
                "max_topk_minus_rest_probability": float(g["topk_minus_rest_probability"].max()),
            }
        )

    if not rows:
        return pd.DataFrame(columns=PROB_DIST_COLUMNS)
    return pd.DataFrame(rows).reindex(columns=PROB_DIST_COLUMNS)


def make_plots(
    out_dir: Path,
    case_summary: pd.DataFrame,
    top_segments: pd.DataFrame,
    prob_dist: pd.DataFrame,
) -> None:
    import matplotlib.pyplot as plt

    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    metrics_cols = [
        ("file_gate_probability", "file_gate_probability_by_case_group.png"),
        ("max_segment_probability", "max_segment_probability_by_case_group.png"),
        ("topk_minus_rest_probability", "topk_minus_rest_probability_by_case_group.png"),
        ("high_segment_fraction", "high_segment_fraction_by_case_group.png"),
    ]
    for col, fname in metrics_cols:
        if col not in case_summary.columns or case_summary.empty:
            continue
        groups = case_summary["case_type"].unique()
        data = [case_summary.loc[case_summary["case_type"] == g, col].astype(float).values for g in groups]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.boxplot(data, tick_labels=list(groups))
        ax.set_title(f"{col} by diagnostic case group")
        ax.set_ylabel(col)
        fig.tight_layout()
        fig.savefig(plot_dir / fname, dpi=120)
        plt.close(fig)

    for case_type, fname in (
        ("fabricated_20pct_false_negative", "fn_top_segment_probabilities.png"),
        ("nonpartial_false_positive", "fp_top_segment_probabilities.png"),
    ):
        sub = top_segments[top_segments["case_type"].astype(str) == case_type]
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=(10, 5))
        for fp, g in sub.groupby("file_path"):
            g = g.sort_values("segment_rank")
            ax.plot(
                g["segment_rank"].astype(int),
                g["segment_probability"].astype(float),
                marker="o",
                label=Path(str(fp)).name,
            )
        ax.axhline(SEGMENT_TH, color="red", linestyle="--", label=f"segment_threshold={SEGMENT_TH}")
        ax.set_xlabel("segment_rank")
        ax.set_ylabel("segment_probability")
        ax.set_title(f"Top segment probabilities — {case_type}")
        ax.legend(fontsize=7, loc="best")
        fig.tight_layout()
        fig.savefig(plot_dir / fname, dpi=120)
        plt.close(fig)


def write_diagnostic_report(
    path: Path,
    *,
    input_dir: Path,
    metrics: dict[str, Any],
    case_summary: pd.DataFrame,
    ts_loc: pd.DataFrame,
    counterfactual: pd.DataFrame,
    sensitivity: pd.DataFrame,
    prob_dist: pd.DataFrame,
    fn_count: int,
    fp_count: int,
) -> None:
    fn_rows = case_summary[case_summary["case_type"] == "fabricated_20pct_false_negative"]
    fp_rows = case_summary[case_summary["case_type"] == "nonpartial_false_positive"]

    lines = [
        "# Phase 9D-P5F-P2 Diagnostic Report (Experimental)",
        "",
        "**Production claim:** NO — experimental partial-fabrication evidence indicator only.",
        "",
        "**Retraining performed:** NO",
        "",
        "**Thresholds changed:** NO — counterfactual tables are diagnostic-only.",
        "",
        "**Release packaging performed:** NO",
        "",
        "## Purpose",
        "",
        "Diagnose why the P5F-P1 expanded evaluation still has fabricated_20pct false negatives "
        "and non-partial false positives, without changing models, thresholds, or cascade logic.",
        "",
        "## Input P5F run",
        "",
        f"- Input directory: `{input_dir}`",
        f"- Total evaluated files (metrics): {metrics.get('evaluated_files', 'n/a')}",
        f"- fabricated_20pct_recall: {metrics.get('fabricated_20pct_recall', 'n/a')}",
        f"- timestamp_positive_count: {metrics.get('timestamp_positive_count', 'n/a')}",
        "",
        "## Accepted cascade thresholds (unchanged)",
        "",
        f"- file_gate_threshold = {FILE_GATE_TH}",
        f"- segment_threshold = {SEGMENT_TH}",
        f"- contrast_threshold = {CONTRAST_TH}",
        f"- broad_limit = {BROAD_LIMIT}",
        "",
        "## Case counts",
        "",
        f"- fabricated_20pct false negatives (computed): {fn_count}",
        f"- non-partial false positives (computed): {fp_count}",
        f"- metrics new_partial_false_negative_count: {metrics.get('new_partial_false_negative_count', 'n/a')}",
        f"- metrics false_partial_count (non-partial positives): {fp_count}",
        "",
        "## False negative summary",
        "",
    ]

    if fn_rows.empty:
        lines.append("- None identified.")
    else:
        for _, r in fn_rows.iterrows():
            lines.append(
                f"- `{r['file_path']}` — primary: **{r['primary_failure_reason']}**; "
                f"flags: {r['threshold_failure_flags']}; near-miss: {r['near_miss_flags'] or 'none'}; "
                f"file_gate={_num(r['file_gate_probability']):.4f}, max_seg={_num(r['max_segment_probability']):.4f}, "
                f"contrast={_num(r['topk_minus_rest_probability']):.4f}, high_frac={_num(r['high_segment_fraction']):.4f}"
            )
            if _bool_series(pd.Series([r.get("top1_timestamp_hit")])).iloc[0]:
                loc_note = "top-1 timestamp overlap among ranked segments despite cascade miss"
            elif _bool_series(pd.Series([r.get("top5_timestamp_hit")])).iloc[0]:
                loc_note = "top-5 timestamp overlap but cascade did not flag partial evidence"
            else:
                loc_note = "review timestamp vs candidate segment alignment"
            lines.append(f"  - Localization note: {loc_note}")

    lines.extend(["", "## False positive summary", ""])
    if fp_rows.empty:
        lines.append("- None identified.")
    else:
        for _, r in fp_rows.iterrows():
            lines.append(
                f"- `{r['file_path']}` ({r['expected_condition']}) — pattern: **{r['primary_failure_reason']}**; "
                f"file_gate={_num(r['file_gate_probability']):.4f}, max_seg={_num(r['max_segment_probability']):.4f}, "
                f"broad_flag={r['broad_activation_flag']}; manual label/audio review recommended."
            )

    lines.extend(["", "## Timestamp localization diagnostic", ""])
    if ts_loc.empty:
        lines.append("- No timestamp-labelled fabricated_20pct rows.")
    else:
        for status, g in ts_loc.groupby("localization_status"):
            lines.append(f"- {status}: {len(g)} file(s)")

    lines.extend(
        [
            "",
            "## Threshold counterfactual diagnostic",
            "",
            "Counterfactual thresholds show what would be required for each false negative file to pass "
            "**if only that file were considered**. Global sensitivity grid is in "
            "`phase9d_p5f_p2_threshold_sensitivity_summary.csv` (diagnostic_only=True). "
            "**These are not recommended threshold changes.**",
            "",
        ]
    )
    if not counterfactual.empty:
        for _, r in counterfactual.iterrows():
            lines.append(
                f"- `{r['file_name']}`: recover via single-gate relaxation: {r['which_single_gate_relaxation_would_recover']}; "
                f"risk note: {r['whether_single_gate_relaxation_would_create_risk']}"
            )

    lines.extend(["", "## Probability distribution comparison", ""])
    if not prob_dist.empty:
        lines.append("```text")
        lines.append(prob_dist.to_string(index=False))
        lines.append("```")
    else:
        lines.append("- No distribution summary computed.")

    lines.extend(
        [
            "",
            "## Robustness note",
            "",
            f"- P5F run failed_files: {metrics.get('failed_files', 0)}",
            f"- SSL OOM events (metrics): {metrics.get('ssl_cuda_oom_count', 0)}",
            "",
            "## Release readiness implication",
            "",
            "Release packaging evaluation remains **blocked** in P5F-P1 (fabricated_20pct recall below 0.80, "
            "false negatives remain). This diagnostic phase does not change that assessment and does not "
            "recommend release packaging.",
            "",
            "## Recommended next action",
            "",
            "- Review false negative gate failures (file gate vs segment threshold) with segment CSVs.",
            "- Review false positives on direct-labelled files; manual label/audio review recommended.",
            "- Do not tune thresholds based solely on counterfactual tables without independent holdout review.",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = load_p5f_outputs(input_dir)
    file_pred = enrich_with_manifest_timestamps(data["file_pred"], data["manifest"])
    seg_pred = data["seg_pred"]
    metrics = data["metrics"]

    if file_pred.empty:
        print("ERROR: missing file predictions", file=sys.stderr)
        return 1

    ok = ok_files(file_pred)
    fn = identify_false_negatives(ok)
    fp = identify_false_positives(ok)

    case_summary = build_case_summary(fn, fp)
    cases = case_summary if not case_summary.empty else pd.concat([fn.assign(case_type="fabricated_20pct_false_negative"), fp.assign(case_type="nonpartial_false_positive")], ignore_index=True)
    top_segments = build_top_segments(cases, seg_pred, file_pred)
    ts_loc = build_timestamp_localization(ok, seg_pred)
    counterfactual = build_threshold_counterfactual(fn, ok, seg_pred)
    sensitivity = build_threshold_sensitivity(ok, seg_pred)
    prob_dist = build_probability_distribution(ok, fn, fp)

    case_summary.to_csv(out_dir / "phase9d_p5f_p2_case_summary.csv", index=False)
    top_segments.to_csv(out_dir / "phase9d_p5f_p2_top_segments_for_cases.csv", index=False)
    ts_loc.to_csv(out_dir / "phase9d_p5f_p2_timestamp_localization_diagnostics.csv", index=False)
    counterfactual.to_csv(out_dir / "phase9d_p5f_p2_threshold_counterfactual.csv", index=False)
    sensitivity.to_csv(out_dir / "phase9d_p5f_p2_threshold_sensitivity_summary.csv", index=False)
    prob_dist.to_csv(out_dir / "phase9d_p5f_p2_probability_distribution_summary.csv", index=False)

    write_diagnostic_report(
        out_dir / "phase9d_p5f_p2_diagnostic_report.md",
        input_dir=input_dir,
        metrics=metrics,
        case_summary=case_summary,
        ts_loc=ts_loc,
        counterfactual=counterfactual,
        sensitivity=sensitivity,
        prob_dist=prob_dist,
        fn_count=len(fn),
        fp_count=len(fp),
    )

    if args.make_plots:
        try:
            make_plots(out_dir, case_summary, top_segments, prob_dist)
        except ImportError as exc:
            print(f"P5F-P2: --make_plots skipped ({exc})", file=sys.stderr)

    meta = {
        "phase": "Phase 9D-P5F-P2",
        "input_dir": str(input_dir),
        "output_dir": str(out_dir),
        "false_negative_count": int(len(fn)),
        "false_positive_count": int(len(fp)),
        "metrics_fn_count": int(metrics.get("new_partial_false_negative_count", -1)),
    }
    (out_dir / "phase9d_p5f_p2_run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"P5F-P2 diagnostics complete. Outputs: {out_dir}")
    print(f"  false_negatives={len(fn)} false_positives={len(fp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
