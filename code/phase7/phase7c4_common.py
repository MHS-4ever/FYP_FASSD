"""
Phase 7C4 shared utilities: threshold re-evaluation, metrics, merges.
Analysis only — no training.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from phase7.analyze_forensic_test_results import (
    _has_error,
    _to_float,
    has_valid_suspicious_timestamps,
    parse_bool,
)

MANIPULATION_DETECT_SCORE = 0.65

KEY_STATUSES = [
    "clean_human_accepted",
    "clean_human_false_alarm",
    "clean_human_borderline",
    "direct_ai_detected",
    "direct_ai_missed",
    "direct_ai_file_level_missed_but_segment_suspicious",
    "human_replay_manipulation_detected",
    "human_replay_missed",
    "ai_replay_detected",
    "ai_replay_missed",
    "ai_replay_file_level_missed_but_segment_suspicious",
    "human_mixer_manipulation_detected",
    "human_mixer_missed",
    "ai_mixer_detected",
    "ai_mixer_missed",
    "ai_mixer_file_level_missed_but_segment_suspicious",
    "partial_fabrication_detected",
    "partial_fabrication_missed",
    "partial_fabrication_not_evaluable",
    "borderline_needs_review",
    "unknown_review_required",
]


@dataclass(frozen=True)
class ThresholdParams:
    vote_threshold: float = 0.70
    segment_max_spoof_threshold: float = 0.95
    suspicious_chunk_ratio_threshold: float = 0.30
    clean_human_borderline_margin: float = 0.05
    manipulation_detect_score: float = MANIPULATION_DETECT_SCORE


from phase7.phase7_paths import resolve_phase7_report_path  # noqa: E402


def load_results(path: Path) -> pd.DataFrame:
    p = resolve_phase7_report_path(path)
    if not p.is_file():
        relocated = Path("reports", "phase7", *Path(path).parts[1:]) if len(Path(path).parts) > 1 else path
        raise FileNotFoundError(
            f"{path} not found (also tried {relocated}). Use reports/phase7/... paths."
        )
    df = pd.read_csv(p, low_memory=False)
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_partial(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()
    resolved = resolve_phase7_report_path(path)
    if not resolved.is_file():
        return pd.DataFrame()
    df = pd.read_csv(resolved, low_memory=False)
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def merge_partial(results: pd.DataFrame, partial: pd.DataFrame) -> pd.DataFrame:
    if partial.empty:
        return results.copy()
    cols = [
        "inside_region_max_spoof",
        "outside_region_max_spoof",
        "inside_region_avg_spoof",
        "outside_region_avg_spoof",
        "region_delta",
        "partial_region_detected",
    ]
    p = partial[["sample_id"] + [c for c in cols if c in partial.columns]].copy()
    out = results.merge(p, on="sample_id", how="left", suffixes=("", "_partial_dup"))
    dup = [c for c in out.columns if c.endswith("_partial_dup")]
    if dup:
        out.drop(columns=dup, inplace=True)
    if "partial_region_detected" in out.columns:
        out["partial_region_detected"] = out["partial_region_detected"].map(
            lambda x: parse_bool(x) if x is not None and str(x) != "" else False
        )
    return out


def prefix_dataframe(df: pd.DataFrame, prefix: str, id_col: str = "sample_id") -> pd.DataFrame:
    df = df.copy()
    df[id_col] = df[id_col].astype(str)
    rename = {c: f"{c}_{prefix}" for c in df.columns if c != id_col}
    return df.rename(columns=rename)


def merge_three_checkpoints(
    baseline: pd.DataFrame,
    r2_product: pd.DataFrame,
    r2_loss: pd.DataFrame,
) -> pd.DataFrame:
    b = prefix_dataframe(baseline, "baseline")
    p = prefix_dataframe(r2_product, "r2_product")
    l = prefix_dataframe(r2_loss, "r2_loss")
    meta_cols = [
        "manipulation_type_baseline",
        "source_origin_baseline",
        "variant_id_baseline",
        "ground_truth_origin_baseline",
        "partial_fabrication_binary_baseline",
        "suspicious_start_time_baseline",
        "suspicious_end_time_baseline",
    ]
    merged = b.merge(p, on="sample_id", how="inner").merge(l, on="sample_id", how="inner")
    return merged


def _is_borderline(row: dict, params: ThresholdParams) -> bool:
    score = _to_float(row.get("decision_score"))
    threshold = params.vote_threshold
    if score is None:
        return False
    return abs(score - threshold) <= params.clean_human_borderline_margin


def _segment_suspicious(row: dict, params: ThresholdParams) -> bool:
    max_spoof = _to_float(row.get("max_chunk_spoof"))
    ratio = _to_float(row.get("suspicious_chunk_ratio"), 0.0) or 0.0
    if max_spoof is not None and max_spoof >= params.segment_max_spoof_threshold:
        return True
    return ratio >= params.suspicious_chunk_ratio_threshold


def _manipulation_detected(row: dict, params: ThresholdParams) -> bool:
    pred = str(row.get("prediction", "")).strip().upper()
    score = _to_float(row.get("decision_score"), 0.0) or 0.0
    return pred == "FAKE" or score >= params.manipulation_detect_score


def row_with_thresholds(row: dict, params: ThresholdParams) -> dict:
    """Re-derive prediction and effective_threshold from decision_score."""
    out = dict(row)
    score = _to_float(row.get("decision_score"))
    if score is not None:
        out["effective_threshold"] = params.vote_threshold
        out["prediction"] = "FAKE" if score >= params.vote_threshold else "REAL"
    return out


def evaluate_baseline_status(row: dict, params: ThresholdParams) -> str:
    """Phase 7C1 baseline_status with configurable thresholds."""
    if _has_error(row.get("error")):
        return "unknown_review_required"

    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    pred = str(row.get("prediction", "")).strip().upper()
    borderline = _is_borderline(row, params)
    partial_bin = parse_bool(row.get("partial_fabrication_binary"))

    if partial_bin is True or manip == "partial_ai_insert":
        if not has_valid_suspicious_timestamps(
            row.get("suspicious_start_time"), row.get("suspicious_end_time")
        ):
            return "partial_fabrication_not_evaluable"
        if parse_bool(row.get("partial_region_detected")) is True:
            return "partial_fabrication_detected"
        return "partial_fabrication_missed"

    if manip == "clean_direct" and gt_origin == "human":
        if borderline:
            return "clean_human_borderline"
        if pred == "REAL":
            return "clean_human_accepted"
        if pred == "FAKE":
            return "clean_human_false_alarm"
        return "borderline_needs_review"

    if manip == "clean_direct" and gt_origin == "ai":
        if pred == "FAKE":
            return "direct_ai_detected"
        if pred == "REAL" and _segment_suspicious(row, params):
            return "direct_ai_file_level_missed_but_segment_suspicious"
        if pred == "REAL":
            return "direct_ai_missed"
        return "borderline_needs_review"

    if manip == "human_replay":
        if _manipulation_detected(row, params):
            return "human_replay_manipulation_detected"
        return "human_replay_missed"

    if manip == "ai_replay":
        if _manipulation_detected(row, params):
            return "ai_replay_detected"
        if pred == "REAL" and _segment_suspicious(row, params):
            return "ai_replay_file_level_missed_but_segment_suspicious"
        return "ai_replay_missed"

    if manip == "mixer_processed" and gt_origin == "human":
        if _manipulation_detected(row, params):
            return "human_mixer_manipulation_detected"
        return "human_mixer_missed"

    if manip == "mixer_processed" and gt_origin == "ai":
        if _manipulation_detected(row, params):
            return "ai_mixer_detected"
        if pred == "REAL" and _segment_suspicious(row, params):
            return "ai_mixer_file_level_missed_but_segment_suspicious"
        return "ai_mixer_missed"

    if borderline:
        return "borderline_needs_review"
    return "unknown_review_required"


def status_counts(df: pd.DataFrame, col: str = "baseline_status") -> Counter:
    if col not in df.columns:
        return Counter()
    return Counter(df[col].fillna("").astype(str))


def count_status(df: pd.DataFrame, status: str, col: str = "baseline_status") -> int:
    return int((df[col].astype(str) == status).sum())


def compute_metrics(df: pd.DataFrame, status_col: str = "baseline_status") -> dict[str, Any]:
    ch = df[
        (df["manipulation_type"].astype(str).str.lower() == "clean_direct")
        & (df["ground_truth_origin"].astype(str).str.lower() == "human")
    ]
    ai_direct = df[
        (df["manipulation_type"].astype(str).str.lower() == "clean_direct")
        & (df["ground_truth_origin"].astype(str).str.lower() == "ai")
    ]
    human_replay = df[df["manipulation_type"].astype(str).str.lower() == "human_replay"]
    ai_replay = df[df["manipulation_type"].astype(str).str.lower() == "ai_replay"]
    human_mixer = df[
        (df["manipulation_type"].astype(str).str.lower() == "mixer_processed")
        & (df["ground_truth_origin"].astype(str).str.lower() == "human")
    ]
    ai_mixer = df[
        (df["manipulation_type"].astype(str).str.lower() == "mixer_processed")
        & (df["ground_truth_origin"].astype(str).str.lower() == "ai")
    ]
    partial = df[df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert"]
    partial_eval = partial[
        partial.apply(
            lambda r: has_valid_suspicious_timestamps(
                r.get("suspicious_start_time"), r.get("suspicious_end_time")
            ),
            axis=1,
        )
    ]

    ch_n = len(ch)
    ch_accept = count_status(ch, "clean_human_accepted", status_col)
    ch_fp = count_status(ch, "clean_human_false_alarm", status_col)
    ch_border = count_status(ch, "clean_human_borderline", status_col)

    m = {
        "n_samples": len(df),
        "clean_human_false_alarm_count": ch_fp,
        "clean_human_accept_count": ch_accept,
        "clean_human_borderline_count": ch_border,
        "clean_human_review_rate": float(ch_border / ch_n) if ch_n else 0.0,
        "clean_human_n": ch_n,
        "human_replay_n": len(human_replay),
        "ai_replay_n": len(ai_replay),
        "direct_ai_detected_count": count_status(ai_direct, "direct_ai_detected", status_col),
        "direct_ai_segment_suspicious_count": count_status(
            ai_direct, "direct_ai_file_level_missed_but_segment_suspicious", status_col
        ),
        "human_replay_detected_count": count_status(
            human_replay, "human_replay_manipulation_detected", status_col
        ),
        "ai_replay_detected_count": count_status(ai_replay, "ai_replay_detected", status_col),
        "ai_replay_missed_count": count_status(ai_replay, "ai_replay_missed", status_col),
        "ai_replay_segment_suspicious_count": count_status(
            ai_replay, "ai_replay_file_level_missed_but_segment_suspicious", status_col
        ),
        "human_mixer_detected_count": count_status(
            human_mixer, "human_mixer_manipulation_detected", status_col
        ),
        "human_mixer_missed_count": count_status(human_mixer, "human_mixer_missed", status_col),
        "ai_mixer_detected_count": count_status(ai_mixer, "ai_mixer_detected", status_col),
        "ai_mixer_missed_count": count_status(ai_mixer, "ai_mixer_missed", status_col),
        "ai_mixer_segment_suspicious_count": count_status(
            ai_mixer, "ai_mixer_file_level_missed_but_segment_suspicious", status_col
        ),
        "direct_ai_missed_count": count_status(ai_direct, "direct_ai_missed", status_col),
        "human_replay_missed_count": count_status(human_replay, "human_replay_missed", status_col),
        "partial_fabrication_missed_count": count_status(
            partial, "partial_fabrication_missed", status_col
        ),
        "partial_fabrication_not_evaluable_count": count_status(
            partial, "partial_fabrication_not_evaluable", status_col
        ),
        "partial_fabrication_detected_count": count_status(
            partial_eval, "partial_fabrication_detected", status_col
        ),
        "partial_fabrication_evaluable_n": len(partial_eval),
        "direct_ai_n": len(ai_direct),
        "human_mixer_n": len(human_mixer),
        "ai_mixer_n": len(ai_mixer),
    }
    m["product_score"] = compute_product_score(m)
    return m


def compute_product_score(m: dict[str, Any]) -> float:
    ch_n = max(m.get("clean_human_n", 0), 1)
    ai_n = max(m.get("direct_ai_n", 23), 1)
    hr_n = max(m.get("human_replay_n", 0), 1)
    ar_n = max(m.get("ai_replay_n", 0), 1)
    hm_n = max(m.get("human_mixer_n", 1), 1)
    am_n = max(m.get("ai_mixer_n", 1), 1)
    partial_n = max(m.get("partial_fabrication_evaluable_n", 1), 1)

    clean_rate = m.get("clean_human_accept_count", 0) / ch_n
    direct_ai_rate = (
        m.get("direct_ai_detected_count", 0) + m.get("direct_ai_segment_suspicious_count", 0)
    ) / ai_n
    replay_rate = (
        m.get("human_replay_detected_count", 0) / hr_n + m.get("ai_replay_detected_count", 0) / ar_n
    ) / 2.0
    mixer_rate = (
        m.get("human_mixer_detected_count", 0) / hm_n + m.get("ai_mixer_detected_count", 0) / am_n
    ) / 2.0
    partial_rate = m.get("partial_fabrication_detected_count", 0) / partial_n

    return float(
        0.20 * clean_rate
        + 0.20 * direct_ai_rate
        + 0.20 * replay_rate
        + 0.20 * mixer_rate
        + 0.20 * partial_rate
    )


def reevaluate_dataframe(df: pd.DataFrame, params: ThresholdParams) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        row = r.to_dict()
        row = row_with_thresholds(row, params)
        row["baseline_status"] = evaluate_baseline_status(row, params)
        rows.append(row)
    return pd.DataFrame(rows)


def build_ensemble_row(merged: pd.Series, params: ThresholdParams) -> dict:
    """Ensemble: max scores across checkpoints for sweep."""
    def g(field: str, src: str):
        return _to_float(merged.get(f"{field}_{src}"), np.nan)

    scores = [g("decision_score", s) for s in ("baseline", "r2_product", "r2_loss")]
    scores = [s for s in scores if not np.isnan(s)]
    max_spoof = max(
        [g("max_chunk_spoof", s) for s in ("baseline", "r2_product", "r2_loss") if not np.isnan(g("max_chunk_spoof", s))],
        default=np.nan,
    )
    ratios = [
        g("suspicious_chunk_ratio", s)
        for s in ("baseline", "r2_product", "r2_loss")
        if not np.isnan(g("suspicious_chunk_ratio", s))
    ]
    row = {
        "sample_id": merged["sample_id"],
        "manipulation_type": merged.get("manipulation_type_baseline", merged.get("manipulation_type", "")),
        "ground_truth_origin": merged.get("ground_truth_origin_baseline", ""),
        "partial_fabrication_binary": merged.get("partial_fabrication_binary_baseline", ""),
        "suspicious_start_time": merged.get("suspicious_start_time_baseline", ""),
        "suspicious_end_time": merged.get("suspicious_end_time_baseline", ""),
        "decision_score": max(scores) if scores else np.nan,
        "max_chunk_spoof": max_spoof,
        "suspicious_chunk_ratio": max(ratios) if ratios else 0.0,
        "partial_region_detected": any(
            parse_bool(merged.get(f"partial_region_detected_{s}", False))
            for s in ("baseline", "r2_product", "r2_loss")
        ),
        "error": "",
    }
    row = row_with_thresholds(row, params)
    row["baseline_status"] = evaluate_baseline_status(row, params)
    return row


def score_better_clean_human(baseline_st: str, r2_st: str) -> str:
    rank = {"clean_human_accepted": 0, "clean_human_borderline": 1, "clean_human_false_alarm": 2}
    br = rank.get(str(baseline_st), 9)
    r2 = rank.get(str(r2_st), 9)
    if r2 < br:
        return "r2_better"
    if r2 > br:
        return "baseline_better"
    return "tie"


def disagreement_type(row: pd.Series) -> str:
    preds = {
        "baseline": str(row.get("baseline_status_baseline", "")),
        "r2_product": str(row.get("baseline_status_r2_product", "")),
        "r2_loss": str(row.get("baseline_status_r2_loss", "")),
    }
    unique = set(preds.values()) - {""}
    if len(unique) <= 1:
        return "agreement"
    if preds["baseline"] == "clean_human_accepted" and preds["r2_product"] != "clean_human_accepted":
        return "clean_human_disagreement"
    if preds["baseline"] in {"human_replay_manipulation_detected", "human_mixer_manipulation_detected"}:
        if preds["r2_product"] not in {
            "human_replay_manipulation_detected",
            "human_mixer_manipulation_detected",
        }:
            return "replay_mixer_disagreement"
    if preds["baseline"] == "partial_fabrication_detected" and preds["r2_product"] != "partial_fabrication_detected":
        return "partial_disagreement"
    if "direct_ai" in preds["baseline"] or "direct_ai" in preds["r2_product"]:
        return "direct_ai_disagreement"
    return "mixed_disagreement"


def format_category_counts(counter: dict[str, int], keys: list[str]) -> str:
    """Format status counts for markdown tables (missing keys shown as 0)."""
    labels = {
        "clean_human_accepted": "accepted",
        "clean_human_false_alarm": "false_alarm",
        "clean_human_borderline": "borderline",
        "direct_ai_detected": "detected",
        "direct_ai_missed": "missed",
        "direct_ai_file_level_missed_but_segment_suspicious": "segment_suspicious",
        "human_replay_manipulation_detected": "detected",
        "human_replay_missed": "missed",
        "ai_replay_detected": "detected",
        "ai_replay_missed": "missed",
        "ai_replay_file_level_missed_but_segment_suspicious": "segment_suspicious",
        "human_mixer_manipulation_detected": "detected",
        "human_mixer_missed": "missed",
        "ai_mixer_detected": "detected",
        "ai_mixer_missed": "missed",
        "ai_mixer_file_level_missed_but_segment_suspicious": "segment_suspicious",
        "partial_fabrication_detected": "detected",
        "partial_fabrication_missed": "missed",
        "partial_fabrication_not_evaluable": "not_evaluable",
    }
    parts = [f"{labels.get(k, k)}={counter.get(k, 0)}" for k in keys]
    return ", ".join(parts)


# Per-category status keys for checkpoint comparison markdown
CATEGORY_STATUS_KEYS: dict[str, list[str]] = {
    "clean_human": [
        "clean_human_accepted",
        "clean_human_false_alarm",
        "clean_human_borderline",
    ],
    "direct_ai": [
        "direct_ai_detected",
        "direct_ai_missed",
        "direct_ai_file_level_missed_but_segment_suspicious",
    ],
    "human_replay": ["human_replay_manipulation_detected", "human_replay_missed"],
    "ai_replay": [
        "ai_replay_detected",
        "ai_replay_missed",
        "ai_replay_file_level_missed_but_segment_suspicious",
    ],
    "human_mixer": ["human_mixer_manipulation_detected", "human_mixer_missed"],
    "ai_mixer": [
        "ai_mixer_detected",
        "ai_mixer_missed",
        "ai_mixer_file_level_missed_but_segment_suspicious",
    ],
    "partial": [
        "partial_fabrication_detected",
        "partial_fabrication_missed",
        "partial_fabrication_not_evaluable",
    ],
}


def md_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_No data._\n"
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"
