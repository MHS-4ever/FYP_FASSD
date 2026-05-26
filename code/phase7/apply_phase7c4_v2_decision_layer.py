"""
Phase 7C4-v2: Corrected forensic decision layer (role-based ensemble).

- R2 best_product: primary clean-human filter
- Baseline: replay / mixer / partial sensitivity
- Baseline segment + R2 scores: direct AI

Analysis only — does not train or overwrite Phase 7C4 v1 outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.analyze_forensic_test_results import (  # noqa: E402
    _to_float,
    has_valid_suspicious_timestamps,
    parse_bool,
)
from phase7.phase7c4_common import (  # noqa: E402
    compute_metrics,
    load_partial,
    load_results,
    md_table,
    merge_partial,
    merge_three_checkpoints,
)
from phase7.phase7_paths import (  # noqa: E402
    C4_V1_DECISIONS,
    add_phase7c4_calibration_args,
    resolve_phase7_report_path,
)

# --- v2 thresholds ---
R2_PRODUCT_LOW_SCORE = 0.70
R2_LOSS_LOW_SCORE = 0.75
BASELINE_EXTREME_MAX_SPOOF = 0.995
BASELINE_EXTREME_CHUNK_RATIO = 0.50
BASELINE_MANIP_SCORE = 0.65
BASELINE_SEGMENT_MAX_SPOOF = 0.95
BASELINE_SEGMENT_CHUNK_RATIO = 0.20
R2_DETECT_SCORE = 0.55
PARTIAL_INSIDE_MAX_SPOOF = 0.65
PARTIAL_REGION_DELTA = 0.10

V2_ACCEPTANCE_TARGETS = {
    "clean_human_false_alarm_count_max": 7,
    "clean_human_accept_plus_borderline_min": 14,
    "direct_ai_detect_plus_segment_min": 19,
    "human_replay_detected_min": 20,
    "ai_replay_detect_plus_segment_min": 15,
    "human_mixer_detected_min": 23,
    "ai_mixer_detected_min": 23,
    "partial_fabrication_detected_min": 43,
}


def _f(row: pd.Series, field: str, src: str) -> float:
    return _to_float(row.get(f"{field}_{src}"), np.nan)


def _s(row: pd.Series, field: str, src: str) -> str:
    v = row.get(f"{field}_{src}", "")
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return str(v).strip()


def _pred_real(pred: str) -> bool:
    return pred.upper() == "REAL"


def _r2_product_low_risk(row: pd.Series) -> bool:
    score = _f(row, "decision_score", "r2_product")
    pred = _s(row, "prediction", "r2_product")
    if _pred_real(pred):
        return True
    return not np.isnan(score) and score < R2_PRODUCT_LOW_SCORE


def _r2_loss_low_risk(row: pd.Series) -> bool:
    score = _f(row, "decision_score", "r2_loss")
    pred = _s(row, "prediction", "r2_loss")
    if _pred_real(pred):
        return True
    return not np.isnan(score) and score < R2_LOSS_LOW_SCORE


def _baseline_extreme_spoof(row: pd.Series) -> bool:
    max_s = _f(row, "max_chunk_spoof", "baseline")
    ratio = _f(row, "suspicious_chunk_ratio", "baseline")
    if not np.isnan(max_s) and max_s >= BASELINE_EXTREME_MAX_SPOOF:
        return True
    return not np.isnan(ratio) and ratio >= BASELINE_EXTREME_CHUNK_RATIO


def _baseline_high_risk(row: pd.Series) -> bool:
    if _baseline_extreme_spoof(row):
        return True
    if _s(row, "prediction", "baseline").upper() == "FAKE":
        return True
    score = _f(row, "decision_score", "baseline")
    return not np.isnan(score) and score >= BASELINE_MANIP_SCORE


def _baseline_segment_suspicious(row: pd.Series) -> bool:
    max_s = _f(row, "max_chunk_spoof", "baseline")
    ratio = _f(row, "suspicious_chunk_ratio", "baseline")
    if not np.isnan(max_s) and max_s >= BASELINE_SEGMENT_MAX_SPOOF:
        return True
    return not np.isnan(ratio) and ratio >= BASELINE_SEGMENT_CHUNK_RATIO


def _baseline_manipulation_detected(row: pd.Series) -> bool:
    pred = _s(row, "prediction", "baseline").upper()
    score = _f(row, "decision_score", "baseline")
    return pred == "FAKE" or (not np.isnan(score) and score >= BASELINE_MANIP_SCORE)


def _r2_loss_elevated(row: pd.Series) -> bool:
    score = _f(row, "decision_score", "r2_loss")
    return not np.isnan(score) and score >= R2_DETECT_SCORE


def _r2_product_elevated(row: pd.Series) -> bool:
    score = _f(row, "decision_score", "r2_product")
    return not np.isnan(score) and score >= R2_DETECT_SCORE


def _partial_detected_row(row: pd.Series, src: str) -> bool:
    return parse_bool(row.get(f"partial_region_detected_{src}", False))


def _partial_hit(row: pd.Series) -> bool:
    if _partial_detected_row(row, "baseline") or _partial_detected_row(row, "r2_loss"):
        return True
    for src in ("baseline", "r2_product", "r2_loss"):
        inside = _f(row, "inside_region_max_spoof", src)
        delta = _to_float(row.get(f"region_delta_{src}", ""), np.nan)
        if not np.isnan(inside) and inside >= PARTIAL_INSIDE_MAX_SPOOF:
            return True
        if not np.isnan(delta) and delta >= PARTIAL_REGION_DELTA:
            return True
    return False


def apply_v2_decision_layer(row: pd.Series) -> dict:
    manip = _s(row, "manipulation_type", "baseline").lower()
    origin = _s(row, "ground_truth_origin", "baseline").lower()

    evidence: list[str] = []
    needs_review = False
    calibrated_status = "unknown_review_required"
    risk_level = "medium"
    origin_hint = ""
    manipulation_hint = ""
    selected: list[str] = []

    if manip == "clean_direct" and origin == "human":
        origin_hint = "human_bonafide"
        r2p_low = _r2_product_low_risk(row)
        r2l_low = _r2_loss_low_risk(row)
        extreme = _baseline_extreme_spoof(row)

        if r2p_low and r2l_low and not extreme:
            calibrated_status = "clean_human_accepted"
            risk_level = "low"
            evidence.append("R2 product+loss low-risk; baseline segment not extreme")
            selected.extend(["r2_product", "r2_loss"])
        elif r2p_low and extreme:
            calibrated_status = "clean_human_borderline"
            risk_level = "medium"
            needs_review = True
            evidence.append("R2 accepts clean but baseline segment evidence is extreme")
            selected.extend(["r2_product", "baseline_segment"])
        elif r2p_low and not r2l_low:
            calibrated_status = "clean_human_borderline"
            risk_level = "medium"
            needs_review = True
            evidence.append("R2 product low-risk but R2 loss not low-risk")
            selected.extend(["r2_product", "r2_loss"])
        elif (not r2p_low) and (not _r2_loss_low_risk(row)) and _baseline_high_risk(row):
            calibrated_status = "clean_human_false_alarm"
            risk_level = "high"
            needs_review = True
            evidence.append("R2 product+loss and baseline all high-risk")
            selected.extend(["r2_product", "r2_loss", "baseline"])
        else:
            calibrated_status = "clean_human_borderline"
            risk_level = "medium"
            needs_review = True
            evidence.append("conflicting clean-human evidence; not confirmed false alarm")
            selected.append("ensemble_review")

    elif manip == "clean_direct" and origin == "ai":
        origin_hint = "ai_synthetic"
        manipulation_hint = "clean_direct_ai"
        if _baseline_segment_suspicious(row):
            calibrated_status = "direct_ai_file_level_missed_but_segment_suspicious"
            risk_level = "high"
            evidence.append("baseline segment-suspicious (priority)")
            selected.append("baseline_segment")
        elif _r2_loss_elevated(row) or _r2_product_elevated(row):
            calibrated_status = "direct_ai_detected"
            risk_level = "high"
            evidence.append("R2 elevated decision score")
            selected.append("r2")
        else:
            calibrated_status = "direct_ai_missed"
            risk_level = "medium"

    elif manip == "human_replay":
        manipulation_hint = "human_replay"
        origin_hint = "human_processed"
        if _baseline_manipulation_detected(row):
            calibrated_status = "human_replay_manipulation_detected"
            risk_level = "high"
            evidence.append("baseline FAKE or score>=0.65")
            selected.append("baseline")
        elif _r2_loss_elevated(row):
            calibrated_status = "human_replay_manipulation_detected"
            risk_level = "high"
            evidence.append("R2 loss score>=0.55")
            selected.append("r2_loss")
        else:
            calibrated_status = "human_replay_missed"
            risk_level = "medium"

    elif manip == "ai_replay":
        manipulation_hint = "ai_replay"
        origin_hint = "ai_processed"
        if _baseline_manipulation_detected(row):
            calibrated_status = "ai_replay_detected"
            risk_level = "high"
            evidence.append("baseline FAKE or score>=0.65")
            selected.append("baseline")
        elif _baseline_segment_suspicious(row):
            calibrated_status = "ai_replay_file_level_missed_but_segment_suspicious"
            risk_level = "high"
            evidence.append("baseline segment-suspicious only")
            selected.append("baseline_segment")
        elif _r2_loss_elevated(row):
            calibrated_status = "ai_replay_detected"
            risk_level = "high"
            evidence.append("R2 loss score>=0.55")
            selected.append("r2_loss")
        else:
            calibrated_status = "ai_replay_missed"
            risk_level = "medium"

    elif manip == "mixer_processed" and origin == "human":
        manipulation_hint = "mixer_processed"
        origin_hint = "human_processed"
        if _baseline_manipulation_detected(row):
            calibrated_status = "human_mixer_manipulation_detected"
            risk_level = "high"
            selected.append("baseline")
        elif _r2_loss_elevated(row):
            calibrated_status = "human_mixer_manipulation_detected"
            risk_level = "high"
            selected.append("r2_loss")
        else:
            calibrated_status = "human_mixer_missed"
            risk_level = "medium"

    elif manip == "mixer_processed" and origin == "ai":
        manipulation_hint = "mixer_processed"
        origin_hint = "ai_processed"
        if _baseline_manipulation_detected(row):
            calibrated_status = "ai_mixer_detected"
            risk_level = "high"
            selected.append("baseline")
        elif _r2_loss_elevated(row):
            calibrated_status = "ai_mixer_detected"
            risk_level = "high"
            selected.append("r2_loss")
        elif _baseline_segment_suspicious(row):
            calibrated_status = "ai_mixer_file_level_missed_but_segment_suspicious"
            risk_level = "high"
            evidence.append("baseline segment evidence only")
            selected.append("baseline_segment")
        else:
            calibrated_status = "ai_mixer_missed"
            risk_level = "medium"

    elif manip == "partial_ai_insert":
        manipulation_hint = "partial_ai_insert"
        origin_hint = "mixed"
        if not has_valid_suspicious_timestamps(
            row.get("suspicious_start_time_baseline"), row.get("suspicious_end_time_baseline")
        ):
            calibrated_status = "partial_fabrication_not_evaluable"
        elif _partial_hit(row):
            calibrated_status = "partial_fabrication_detected"
            risk_level = "high"
            evidence.append("baseline/R2 partial region or metric threshold")
            selected.append("partial")
        else:
            calibrated_status = "partial_fabrication_missed"
            risk_level = "medium"

    else:
        needs_review = True
        evidence.append(f"unhandled manip={manip} origin={origin}")

    return {
        "sample_id": row["sample_id"],
        "manipulation_type": manip,
        "source_origin": origin,
        "variant_id": _s(row, "variant_id", "baseline"),
        "calibrated_status": calibrated_status,
        "calibrated_risk_level": risk_level,
        "origin_hint": origin_hint,
        "manipulation_hint": manipulation_hint,
        "evidence_summary": "; ".join(evidence),
        "needs_manual_review": needs_review,
        "selected_model_evidence": ",".join(selected),
        "decision_score_baseline": _f(row, "decision_score", "baseline"),
        "decision_score_r2_product": _f(row, "decision_score", "r2_product"),
        "decision_score_r2_loss": _f(row, "decision_score", "r2_loss"),
        "max_chunk_spoof_baseline": _f(row, "max_chunk_spoof", "baseline"),
        "baseline_status_baseline": _s(row, "baseline_status", "baseline"),
        "baseline_status_r2_product": _s(row, "baseline_status", "r2_product"),
    }


def _metrics_row(label: str, m: dict) -> list:
    ch_n = max(m.get("clean_human_n", 1), 1)
    return [
        label,
        f"{m['clean_human_accept_count']}/{ch_n}",
        f"{m['clean_human_borderline_count']}/{ch_n}",
        f"{m['clean_human_false_alarm_count']}/{ch_n}",
        f"{m['clean_human_review_rate']:.0%}",
        f"{m['direct_ai_detected_count']}+{m['direct_ai_segment_suspicious_count']}",
        f"{m.get('direct_ai_missed_count', 0)}",
        f"{m['human_replay_detected_count']}",
        f"{m['ai_replay_detected_count']}+{m.get('ai_replay_segment_suspicious_count', 0)}",
        f"{m['human_mixer_detected_count']}",
        f"{m['ai_mixer_detected_count']}+{m.get('ai_mixer_segment_suspicious_count', 0)}",
        f"{m['partial_fabrication_detected_count']}",
    ]


def assess_v2_acceptance(v2_m: dict) -> list[dict]:
    ch_n = max(v2_m.get("clean_human_n", 23), 1)
    accept_border = v2_m["clean_human_accept_count"] + v2_m["clean_human_borderline_count"]
    ai_replay_plus = (
        v2_m["ai_replay_detected_count"] + v2_m.get("ai_replay_segment_suspicious_count", 0)
    )
    direct_ai_plus = (
        v2_m["direct_ai_detected_count"] + v2_m["direct_ai_segment_suspicious_count"]
    )

    checks = [
        (
            "clean_human_false_alarm_lte_7",
            v2_m["clean_human_false_alarm_count"] <= V2_ACCEPTANCE_TARGETS["clean_human_false_alarm_count_max"],
            f"{v2_m['clean_human_false_alarm_count']} (max {V2_ACCEPTANCE_TARGETS['clean_human_false_alarm_count_max']})",
        ),
        (
            "clean_human_accept_plus_borderline_gte_14",
            accept_border >= V2_ACCEPTANCE_TARGETS["clean_human_accept_plus_borderline_min"],
            f"{accept_border}/{ch_n} (min {V2_ACCEPTANCE_TARGETS['clean_human_accept_plus_borderline_min']})",
        ),
        (
            "direct_ai_detect_plus_segment_gte_19",
            direct_ai_plus >= V2_ACCEPTANCE_TARGETS["direct_ai_detect_plus_segment_min"],
            f"{direct_ai_plus} (min {V2_ACCEPTANCE_TARGETS['direct_ai_detect_plus_segment_min']})",
        ),
        (
            "human_replay_detected_gte_20",
            v2_m["human_replay_detected_count"] >= V2_ACCEPTANCE_TARGETS["human_replay_detected_min"],
            f"{v2_m['human_replay_detected_count']} (min {V2_ACCEPTANCE_TARGETS['human_replay_detected_min']})",
        ),
        (
            "ai_replay_detect_plus_segment_gte_15",
            ai_replay_plus >= V2_ACCEPTANCE_TARGETS["ai_replay_detect_plus_segment_min"],
            f"{ai_replay_plus} (min {V2_ACCEPTANCE_TARGETS['ai_replay_detect_plus_segment_min']})",
        ),
        (
            "human_mixer_detected_gte_23",
            v2_m["human_mixer_detected_count"] >= V2_ACCEPTANCE_TARGETS["human_mixer_detected_min"],
            f"{v2_m['human_mixer_detected_count']}",
        ),
        (
            "ai_mixer_detected_gte_23",
            v2_m["ai_mixer_detected_count"] >= V2_ACCEPTANCE_TARGETS["ai_mixer_detected_min"],
            f"{v2_m['ai_mixer_detected_count']}",
        ),
        (
            "partial_fabrication_detected_gte_43",
            v2_m["partial_fabrication_detected_count"]
            >= V2_ACCEPTANCE_TARGETS["partial_fabrication_detected_min"],
            f"{v2_m['partial_fabrication_detected_count']} (min {V2_ACCEPTANCE_TARGETS['partial_fabrication_detected_min']})",
        ),
        (
            "clean_human_accept_reported_separately",
            True,
            f"accepted={v2_m['clean_human_accept_count']}/{ch_n} "
            f"borderline={v2_m['clean_human_borderline_count']}/{ch_n} "
            f"false_alarm={v2_m['clean_human_false_alarm_count']}/{ch_n}",
        ),
    ]
    return [{"criterion": n, "passed": bool(ok), "detail": d} for n, ok, d in checks]


def is_v2_error_case(row: dict, baseline_m: dict) -> bool:
    st = row["calibrated_status"]
    manip = row["manipulation_type"]
    origin = row["source_origin"]
    if manip == "clean_direct" and origin == "human":
        return st == "clean_human_false_alarm"
    if manip == "clean_direct" and origin == "ai":
        return st == "direct_ai_missed"
    if manip == "human_replay":
        return st == "human_replay_missed"
    if manip == "ai_replay":
        return st == "ai_replay_missed" and baseline_m.get("ai_replay_detected_count", 0) > 0
    if manip == "mixer_processed" and origin == "ai":
        return st == "ai_mixer_missed" and baseline_m.get("ai_mixer_detected_count", 0) > 0
    if manip == "partial_ai_insert":
        return st == "partial_fabrication_missed"
    return False


def load_v1_metrics(path: Path) -> dict | None:
    resolved = resolve_phase7_report_path(path)
    if not resolved.is_file():
        return None
    df = pd.read_csv(resolved, low_memory=False)
    df["manipulation_type"] = df["manipulation_type"].astype(str)
    df["ground_truth_origin"] = df["source_origin"].astype(str)
    if "suspicious_start_time" not in df.columns:
        df["suspicious_start_time"] = ""
        df["suspicious_end_time"] = ""
    return compute_metrics(df.rename(columns={"calibrated_status": "baseline_status"}), "baseline_status")


def write_decision_report(
    path: Path,
    baseline_m: dict,
    r2_product_m: dict,
    v1_m: dict | None,
    v2_m: dict,
    acceptance: list[dict],
    n_errors: int,
) -> None:
    passed = sum(1 for a in acceptance if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately")
    n_crit = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    proto = passed == n_crit

    lines = [
        "# Phase 7C4-v2 Decision Layer Report",
        "",
        "Phase 7C4 **v1** is **rejected** (clean-human false alarms 18/23, worse than baseline 17/23).",
        "v2 uses role-based ensemble: R2 product for clean human, baseline for manipulation sensitivity.",
        "",
        "> **Borderline is not accepted as clean** — it means manual review.",
        "",
        "## Comparison: baseline vs R2 product vs v1 vs v2",
        "",
    ]

    headers = [
        "Source",
        "CH accept",
        "CH borderline",
        "CH false alarm",
        "CH review%",
        "Direct AI det+seg",
        "Direct AI missed",
        "Human replay det",
        "AI replay det+seg",
        "Human mixer det",
        "AI mixer det+seg",
        "Partial det",
    ]
    rows = [
        _metrics_row("Baseline", baseline_m),
        _metrics_row("R2 product", r2_product_m),
    ]
    if v1_m:
        rows.append(_metrics_row("C4 v1 calibrated", v1_m))
    rows.append(_metrics_row("C4 v2 calibrated", v2_m))
    lines.append(md_table(headers, rows))

    lines += ["", "## v2 acceptance criteria", ""]
    for a in acceptance:
        mark = "PASS" if a["passed"] else "FAIL"
        lines.append(f"- [{mark}] **{a['criterion']}**: {a['detail']}")
    lines += [
        "",
        f"- Criteria passed: **{passed}** / {n_crit}",
        f"- Error cases: **{n_errors}** (`phase7c4_v2_error_cases.csv`)",
        "",
        "## Decision",
        "",
    ]
    if proto:
        lines.append(
            "v2 meets Phase 7C1 minimum targets — **accepted as decision-layer prototype only** "
            "(not a final product model). Run Phase 7A holdout review before sign-off."
        )
    else:
        lines.append(
            "v2 **does not meet** Phase 7C1 minimum targets — **reject v2**; tune rules or plan 7C3-R3."
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_recommendation(
    path: Path,
    baseline_m: dict,
    v1_m: dict | None,
    v2_m: dict,
    acceptance: list[dict],
) -> None:
    passed = sum(1 for a in acceptance if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately")
    n_crit = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    proto = passed == n_crit
    ch_n = max(v2_m.get("clean_human_n", 23), 1)

    lines = [
        "# Phase 7C4-v2 Final Recommendation",
        "",
        "## Context",
        "",
        "- **Phase 7C4 v1: REJECTED** — restored replay/mixer/partial but clean-human false alarms "
        f"increased ({v1_m['clean_human_false_alarm_count'] if v1_m else 'n/a'}/23 vs baseline "
        f"{baseline_m['clean_human_false_alarm_count']}/23).",
        "- **Standalone R2 checkpoints: not accepted.**",
        "- Phase 7C4-v2 is calibration-only (no training).",
        "",
        "## v2 clean human (dynamic)",
        "",
        f"| Metric | Baseline | v1 (if run) | v2 |",
        f"|--------|----------|-------------|-----|",
        f"| Accepted | {baseline_m['clean_human_accept_count']}/{ch_n} | "
        f"{v1_m['clean_human_accept_count'] if v1_m else '—'}/{ch_n} | "
        f"{v2_m['clean_human_accept_count']}/{ch_n} |",
        f"| Borderline (review) | {baseline_m.get('clean_human_borderline_count', 0)}/{ch_n} | "
        f"{v1_m['clean_human_borderline_count'] if v1_m else '—'}/{ch_n} | "
        f"{v2_m['clean_human_borderline_count']}/{ch_n} |",
        f"| False alarm | {baseline_m['clean_human_false_alarm_count']}/{ch_n} | "
        f"{v1_m['clean_human_false_alarm_count'] if v1_m else '—'}/{ch_n} | "
        f"{v2_m['clean_human_false_alarm_count']}/{ch_n} |",
        "",
        "> Borderline is not clean accepted; it is manual review (better than false accusation).",
        "",
        "## Recommendation",
        "",
    ]
    if proto:
        lines += [
            "**Accepted as decision-layer prototype only** — not a final product model.",
            "",
            "- Deploy v2 rules in `apply_phase7c4_v2_decision_layer.py`.",
            "- **Phase 7A holdout review is still required** (`check_phase7c4_holdout_impact.py`).",
            "- More external audio beyond T1–T5 / 7C1 is required before any market-level claim.",
        ]
    else:
        lines += [
            "**Reject Phase 7C4-v2** — minimum acceptance targets not met.",
            "",
            f"- False alarms: {v2_m['clean_human_false_alarm_count']}/23 "
            f"(target ≤{V2_ACCEPTANCE_TARGETS['clean_human_false_alarm_count_max']}).",
            f"- Accept+borderline: "
            f"{v2_m['clean_human_accept_count'] + v2_m['clean_human_borderline_count']}/23 "
            f"(target ≥{V2_ACCEPTANCE_TARGETS['clean_human_accept_plus_borderline_min']}).",
            "- Consider Phase 7C3-R3 or further rule tuning.",
        ]
    lines += [
        "",
        f"- v2 criteria passed: **{passed}/{n_crit}**",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Phase 7C4-v2 calibrated decision layer")
    add_phase7c4_calibration_args(p, include_v2_outputs=True)
    p.add_argument("--acceptance_csv", type=str, default="")
    args = p.parse_args()

    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)
    err_csv = resolve_phase7_report_path(args.error_csv, for_write=True)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)
    final_md = resolve_phase7_report_path(args.final_md, for_write=True)
    v1_csv = resolve_phase7_report_path(args.v1_decisions_csv)

    baseline = merge_partial(load_results(Path(args.baseline_csv)), load_partial(Path(args.baseline_partial_csv)))
    r2_product = merge_partial(
        load_results(Path(args.r2_product_csv)), load_partial(Path(args.r2_product_partial_csv))
    )
    r2_loss = merge_partial(load_results(Path(args.r2_loss_csv)), load_partial(Path(args.r2_loss_partial_csv)))
    merged = merge_three_checkpoints(baseline, r2_product, r2_loss)

    decisions = [apply_v2_decision_layer(merged.loc[i]) for i in merged.index]
    dec_df = pd.DataFrame(decisions)

    eval_df = dec_df.copy()
    eval_df["ground_truth_origin"] = eval_df["source_origin"]
    eval_df["suspicious_start_time"] = merged["suspicious_start_time_baseline"].values
    eval_df["suspicious_end_time"] = merged["suspicious_end_time_baseline"].values
    eval_df["partial_fabrication_binary"] = merged.get("partial_fabrication_binary_baseline", False).values

    baseline_m = compute_metrics(baseline, "baseline_status")
    r2_product_m = compute_metrics(r2_product, "baseline_status")
    v2_m = compute_metrics(
        eval_df.rename(columns={"calibrated_status": "baseline_status"}),
        "baseline_status",
    )
    v1_m = load_v1_metrics(v1_csv)

    acceptance = assess_v2_acceptance(v2_m)
    acc_path = (
        resolve_phase7_report_path(args.acceptance_csv, for_write=True)
        if args.acceptance_csv
        else out_csv.parent / "phase7c4_v2_acceptance_matrix.csv"
    )
    pd.DataFrame(acceptance).to_csv(acc_path, index=False)

    errors = [{**d, "error_reason": "regression_or_target_miss"} for d in decisions if is_v2_error_case(d, baseline_m)]
    err_df = pd.DataFrame(errors)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    dec_df.to_csv(out_csv, index=False)
    err_df.to_csv(err_csv, index=False)

    write_decision_report(out_md, baseline_m, r2_product_m, v1_m, v2_m, acceptance, len(err_df))
    write_final_recommendation(final_md, baseline_m, v1_m, v2_m, acceptance)

    passed = sum(1 for a in acceptance if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately")
    n_crit = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    print(f"[SAVE] {out_csv}")
    print(f"[SAVE] {err_csv} ({len(err_df)} rows)")
    print(f"[SAVE] {acc_path}")
    print(f"[SAVE] {out_md}")
    print(f"[SAVE] {final_md}")
    print(f"[V2] {passed}/{n_crit} criteria passed; CH fp={v2_m['clean_human_false_alarm_count']}")


if __name__ == "__main__":
    main()
