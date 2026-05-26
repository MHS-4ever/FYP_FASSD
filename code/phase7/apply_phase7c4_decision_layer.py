"""
Phase 7C4: Calibrated forensic decision layer across baseline + R2 checkpoints.

Analysis only — does not train or overwrite checkpoint outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.analyze_forensic_test_results import has_valid_suspicious_timestamps, parse_bool
from phase7.phase7c4_common import (  # noqa: E402
    compute_metrics,
    load_partial,
    load_results,
    md_table,
    merge_partial,
    merge_three_checkpoints,
    status_counts,
)
from phase7.phase7_paths import add_phase7c4_calibration_args, resolve_phase7_report_path  # noqa: E402
from phase7.analyze_forensic_test_results import _to_float

# Calibrated thresholds (Phase 7C4 spec)
CLEAN_HUMAN_R2_SCORE_ACCEPT = 0.65
CLEAN_HUMAN_BASELINE_MAX_SPOOF = 0.98
DIRECT_AI_MAX_SPOOF = 0.95
DIRECT_AI_CHUNK_RATIO = 0.20
DIRECT_AI_R2_LOSS_SCORE = 0.55
REPLAY_BASELINE_SCORE = 0.65
REPLAY_R2_LOSS_SCORE = 0.55
PARTIAL_INSIDE_MAX_SPOOF = 0.65
PARTIAL_REGION_DELTA = 0.10


def _f(row: pd.Series, field: str, src: str):
    return _to_float(row.get(f"{field}_{src}"), np.nan)


def _s(row: pd.Series, field: str, src: str) -> str:
    v = row.get(f"{field}_{src}", "")
    return str(v).strip() if v is not None and not (isinstance(v, float) and np.isnan(v)) else ""


def _partial_detected(row: pd.Series, src: str) -> bool:
    return parse_bool(row.get(f"partial_region_detected_{src}", False))


def _partial_metrics(row: pd.Series, src: str) -> tuple[float, float]:
    inside = _f(row, "inside_region_max_spoof", src)
    delta = _to_float(row.get(f"region_delta_{src}", row.get("region_delta", "")), np.nan)
    return inside if not np.isnan(inside) else np.nan, delta if not np.isnan(delta) else np.nan


def apply_decision_layer(row: pd.Series) -> dict:
    manip = _s(row, "manipulation_type", "baseline").lower()
    origin = _s(row, "ground_truth_origin", "baseline").lower()
    pred_b = _s(row, "prediction", "baseline").upper()
    score_b = _f(row, "decision_score", "baseline")
    score_p = _f(row, "decision_score", "r2_product")
    score_l = _f(row, "decision_score", "r2_loss")
    max_spoof_b = _f(row, "max_chunk_spoof", "baseline")
    ratio_b = _f(row, "suspicious_chunk_ratio", "baseline")
    max_spoof_p = _f(row, "max_chunk_spoof", "r2_product")
    max_spoof_l = _f(row, "max_chunk_spoof", "r2_loss")

    evidence = []
    needs_review = False
    calibrated_status = "unknown_review_required"
    risk_level = "medium"
    origin_hint = ""
    manipulation_hint = ""
    selected = []

    if manip == "clean_direct" and origin == "human":
        origin_hint = "human_bonafide"
        pred_p = _s(row, "prediction", "r2_product").upper()
        accept_ok = (not np.isnan(score_p) and score_p < CLEAN_HUMAN_R2_SCORE_ACCEPT) and (
            np.isnan(max_spoof_b) or max_spoof_b < CLEAN_HUMAN_BASELINE_MAX_SPOOF
        )
        if accept_ok:
            calibrated_status = "clean_human_accepted"
            risk_level = "low"
            sp = f"{score_p:.3f}" if not np.isnan(score_p) else "n/a"
            ms = f"{max_spoof_b:.3f}" if not np.isnan(max_spoof_b) else "n/a"
            evidence.append(f"accepted: r2_score={sp}<0.65; baseline_max_chunk={ms}<0.98")
            selected.append("r2_product+segment")
        elif pred_b == "FAKE" or pred_p == "FAKE":
            calibrated_status = "clean_human_false_alarm"
            risk_level = "high"
            needs_review = True
            evidence.append(f"file-level FAKE: baseline={pred_b}, r2_product={pred_p}")
            selected.append("file_level_fake")
        else:
            calibrated_status = "clean_human_borderline"
            risk_level = "medium"
            needs_review = True
            sp = f"{score_p:.3f}" if not np.isnan(score_p) else "n/a"
            ms = f"{max_spoof_b:.3f}" if not np.isnan(max_spoof_b) else "n/a"
            evidence.append(f"borderline (manual review): r2_score={sp}, baseline_max_spoof={ms}")
            selected.append("ensemble_review")

    # --- Direct AI ---
    elif manip == "clean_direct" and origin == "ai":
        origin_hint = "ai_synthetic"
        manipulation_hint = "clean_direct_ai"
        ai_suspicious = False
        if not np.isnan(max_spoof_b) and max_spoof_b >= DIRECT_AI_MAX_SPOOF:
            ai_suspicious = True
            evidence.append(f"baseline max_chunk_spoof={max_spoof_b:.3f}>=0.95")
            selected.append("baseline_segment")
        if not np.isnan(ratio_b) and ratio_b >= DIRECT_AI_CHUNK_RATIO:
            ai_suspicious = True
            evidence.append(f"baseline suspicious_chunk_ratio={ratio_b:.3f}>=0.20")
            selected.append("baseline_chunk_ratio")
        if not np.isnan(score_l) and score_l >= DIRECT_AI_R2_LOSS_SCORE:
            ai_suspicious = True
            evidence.append(f"R2_loss decision_score={score_l:.3f}>=0.55")
            selected.append("r2_loss")
        if pred_b == "FAKE":
            calibrated_status = "direct_ai_detected"
            risk_level = "high"
        elif ai_suspicious:
            calibrated_status = "direct_ai_file_level_missed_but_segment_suspicious"
            risk_level = "high"
        else:
            calibrated_status = "direct_ai_missed"
            risk_level = "medium"

    # --- Human replay / human mixer ---
    elif manip in {"human_replay", "mixer_processed"} and origin == "human":
        manipulation_hint = manip
        origin_hint = "human_processed"
        detected = (
            pred_b == "FAKE"
            or (not np.isnan(score_b) and score_b >= REPLAY_BASELINE_SCORE)
            or (not np.isnan(score_l) and score_l >= REPLAY_R2_LOSS_SCORE)
        )
        if detected:
            calibrated_status = (
                "human_replay_manipulation_detected"
                if manip == "human_replay"
                else "human_mixer_manipulation_detected"
            )
            risk_level = "high"
            evidence.append(f"baseline pred={pred_b} score={score_b:.3f}; r2_loss={score_l:.3f}")
            selected.append("baseline+r2_loss")
        else:
            calibrated_status = "human_replay_missed" if manip == "human_replay" else "human_mixer_missed"
            risk_level = "medium"

    # --- AI replay / AI mixer ---
    elif manip in {"ai_replay", "mixer_processed"} and origin == "ai":
        manipulation_hint = manip
        origin_hint = "ai_processed"
        high_score = any(
            not np.isnan(s) and s >= REPLAY_BASELINE_SCORE for s in (score_b, score_p, score_l)
        )
        high_spoof = any(
            not np.isnan(m) and m >= DIRECT_AI_MAX_SPOOF
            for m in (max_spoof_b, max_spoof_p, max_spoof_l)
        )
        if manip == "ai_replay":
            if pred_b == "FAKE" or high_score:
                calibrated_status = "ai_replay_detected"
                risk_level = "high"
                evidence.append("file FAKE or elevated decision score")
                selected.append("ensemble")
            elif high_spoof:
                calibrated_status = "ai_replay_file_level_missed_but_segment_suspicious"
                risk_level = "high"
                evidence.append("segment-suspicious chunks (file-level REAL)")
                selected.append("segment")
            else:
                calibrated_status = "ai_replay_missed"
                risk_level = "medium"
        else:
            if pred_b == "FAKE" or high_score:
                calibrated_status = "ai_mixer_detected"
                risk_level = "high"
                evidence.append("file FAKE or elevated decision score")
                selected.append("ensemble")
            elif high_spoof:
                calibrated_status = "ai_mixer_file_level_missed_but_segment_suspicious"
                risk_level = "high"
                evidence.append("segment-suspicious chunks (file-level REAL)")
                selected.append("segment")
            else:
                calibrated_status = "ai_mixer_missed"
                risk_level = "medium"

    # --- Partial fabrication ---
    elif manip == "partial_ai_insert":
        manipulation_hint = "partial_ai_insert"
        origin_hint = "mixed"
        if not has_valid_suspicious_timestamps(
            row.get("suspicious_start_time_baseline"), row.get("suspicious_end_time_baseline")
        ):
            calibrated_status = "partial_fabrication_not_evaluable"
        else:
            partial_hit = False
            for src in ("baseline", "r2_product", "r2_loss"):
                if _partial_detected(row, src):
                    partial_hit = True
                    evidence.append(f"{src} partial_region_detected")
                    selected.append(src)
                inside, delta = _partial_metrics(row, src)
                if not np.isnan(inside) and inside >= PARTIAL_INSIDE_MAX_SPOOF:
                    partial_hit = True
                    evidence.append(f"{src} inside_max={inside:.3f}>=0.65")
                if not np.isnan(delta) and delta >= PARTIAL_REGION_DELTA:
                    partial_hit = True
                    evidence.append(f"{src} region_delta={delta:.3f}>=0.10")
            calibrated_status = (
                "partial_fabrication_detected" if partial_hit else "partial_fabrication_missed"
            )
            risk_level = "high" if partial_hit else "medium"

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
        "evidence_summary": "; ".join(evidence) if evidence else "",
        "needs_manual_review": needs_review,
        "selected_model_evidence": ",".join(selected),
        "decision_score_baseline": score_b,
        "decision_score_r2_product": score_p,
        "decision_score_r2_loss": score_l,
        "max_chunk_spoof_baseline": max_spoof_b,
        "baseline_status_baseline": _s(row, "baseline_status", "baseline"),
        "baseline_status_r2_product": _s(row, "baseline_status", "r2_product"),
        "baseline_status_r2_loss": _s(row, "baseline_status", "r2_loss"),
    }


def is_error_case(row: dict, baseline_metrics: dict) -> bool:
    """Flag cases where calibrated layer regresses vs baseline expectations."""
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
        baseline_had = baseline_metrics.get("ai_replay_detected_count", 0) > 0
        return st == "ai_replay_missed" and baseline_had
    if manip == "mixer_processed" and origin == "ai":
        baseline_had = baseline_metrics.get("ai_mixer_detected_count", 0) > 0
        return st == "ai_mixer_missed" and baseline_had
    if manip == "partial_ai_insert":
        return st == "partial_fabrication_missed"
    return False


def assess_acceptance(baseline_m: dict, r2_product_m: dict, calibrated_m: dict) -> list[dict]:
    """Acceptance matrix rows vs original baseline and R2 product."""
    ch_n = max(calibrated_m.get("clean_human_n", 1), 1)
    cal_accept_or_border = (
        calibrated_m["clean_human_accept_count"] + calibrated_m["clean_human_borderline_count"]
    )
    rows = []
    checks = [
        (
            "clean_human_false_alarms_lower_than_baseline",
            calibrated_m["clean_human_false_alarm_count"] < baseline_m["clean_human_false_alarm_count"],
            f"{baseline_m['clean_human_false_alarm_count']} -> {calibrated_m['clean_human_false_alarm_count']}",
        ),
        (
            "clean_human_accepted_or_borderline_gte_baseline_accepted",
            cal_accept_or_border >= baseline_m["clean_human_accept_count"],
            f"baseline_accept={baseline_m['clean_human_accept_count']} "
            f"cal_accept+borderline={cal_accept_or_border} "
            f"(accept={calibrated_m['clean_human_accept_count']}, "
            f"borderline={calibrated_m['clean_human_borderline_count']})",
        ),
        (
            "clean_human_accept_reported_separately",
            True,
            f"accepted={calibrated_m['clean_human_accept_count']}/{ch_n} "
            f"(borderline={calibrated_m['clean_human_borderline_count']}, "
            f"false_alarm={calibrated_m['clean_human_false_alarm_count']}, "
            f"review_rate={calibrated_m['clean_human_review_rate']:.2%})",
        ),
        (
            "direct_ai_suspicious_higher_than_r2_product_alone",
            (
                calibrated_m["direct_ai_detected_count"]
                + calibrated_m["direct_ai_segment_suspicious_count"]
            )
            > (
                r2_product_m["direct_ai_detected_count"]
                + r2_product_m["direct_ai_segment_suspicious_count"]
            ),
            "segment+detect vs R2-only",
        ),
        (
            "human_replay_detection_close_to_baseline",
            calibrated_m["human_replay_detected_count"] >= baseline_m["human_replay_detected_count"] - 3,
            f"{baseline_m['human_replay_detected_count']} -> {calibrated_m['human_replay_detected_count']}",
        ),
        (
            "mixer_detection_close_to_baseline",
            (
                calibrated_m["human_mixer_detected_count"] + calibrated_m["ai_mixer_detected_count"]
            )
            >= (
                baseline_m["human_mixer_detected_count"] + baseline_m["ai_mixer_detected_count"]
            )
            - 3,
            "human+ai mixer",
        ),
        (
            "partial_fabrication_close_to_baseline",
            calibrated_m["partial_fabrication_detected_count"]
            >= baseline_m["partial_fabrication_detected_count"] - 5,
            f"{baseline_m['partial_fabrication_detected_count']} -> {calibrated_m['partial_fabrication_detected_count']}",
        ),
        (
            "product_score_improves_over_r2_product",
            calibrated_m["product_score"] > r2_product_m["product_score"],
            f"{r2_product_m['product_score']:.4f} -> {calibrated_m['product_score']:.4f}",
        ),
    ]
    for name, ok, detail in checks:
        rows.append({"criterion": name, "passed": bool(ok), "detail": detail})
    return rows


def write_decision_md(
    path: Path,
    calibrated_m: dict,
    baseline_m: dict,
    r2_product_m: dict,
    acceptance: list[dict],
    n_errors: int,
) -> None:
    passed = sum(
        1
        for a in acceptance
        if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately"
    )
    n_criteria = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    lines = [
        "# Phase 7C4 Decision Layer Report",
        "",
        "## Calibrated layer metrics (Phase 7C1)",
        "",
        f"| Metric | Baseline | R2 product | Calibrated |",
        f"|--------|----------|------------|------------|",
        f"| Clean human accepted | {baseline_m['clean_human_accept_count']} | {r2_product_m['clean_human_accept_count']} | {calibrated_m['clean_human_accept_count']} |",
        f"| Clean human borderline (review) | {baseline_m.get('clean_human_borderline_count', 0)} | {r2_product_m.get('clean_human_borderline_count', 0)} | {calibrated_m['clean_human_borderline_count']} |",
        f"| Clean human false alarm | {baseline_m['clean_human_false_alarm_count']} | {r2_product_m['clean_human_false_alarm_count']} | {calibrated_m['clean_human_false_alarm_count']} |",
        f"| Clean human review rate | — | — | {calibrated_m['clean_human_review_rate']:.1%} |",
        f"| Direct AI detected | {baseline_m['direct_ai_detected_count']} | {r2_product_m['direct_ai_detected_count']} | {calibrated_m['direct_ai_detected_count']} |",
        f"| Direct AI segment-suspicious | {baseline_m['direct_ai_segment_suspicious_count']} | {r2_product_m['direct_ai_segment_suspicious_count']} | {calibrated_m['direct_ai_segment_suspicious_count']} |",
        f"| Human replay detected | {baseline_m['human_replay_detected_count']} | {r2_product_m['human_replay_detected_count']} | {calibrated_m['human_replay_detected_count']} |",
        f"| AI replay detected | {baseline_m['ai_replay_detected_count']} | {r2_product_m['ai_replay_detected_count']} | {calibrated_m['ai_replay_detected_count']} |",
        f"| Partial fabrication detected | {baseline_m['partial_fabrication_detected_count']} | {r2_product_m['partial_fabrication_detected_count']} | {calibrated_m['partial_fabrication_detected_count']} |",
        f"| Product score | {baseline_m['product_score']:.4f} | {r2_product_m['product_score']:.4f} | {calibrated_m['product_score']:.4f} |",
        "",
        "## Acceptance criteria",
        "",
    ]
    for a in acceptance:
        mark = "PASS" if a["passed"] else "FAIL"
        lines.append(f"- [{mark}] **{a['criterion']}**: {a['detail']}")
    lines += [
        "",
        f"- Criteria passed: **{passed}** / {n_criteria} (informational row excluded)",
        f"- Error cases flagged: **{n_errors}** (see `phase7c4_error_cases.csv`)",
        "",
        "## Decision",
        "",
    ]
    lines += [
        "",
        "> **Borderline is not accepted as clean** — it means manual review. "
        "Only `clean_human_accepted` counts as bonafide acceptance.",
        "",
    ]
    proto_ok = passed >= 6
    if proto_ok:
        lines.append(
            "Phase 7C1 criteria suggest the calibrated layer is a **decision-layer prototype** "
            "(not a final product model). Run `check_phase7c4_holdout_impact.py` on Phase 7A before any sign-off."
        )
    else:
        lines.append(
            "Calibrated layer **does not meet Phase 7C1 acceptance** — tune rules or proceed to Phase 7C3-R3."
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_recommendation(
    path: Path,
    acceptance: list[dict],
    calibrated_m: dict,
    baseline_m: dict,
    r2_product_m: dict,
) -> None:
    passed = sum(
        1
        for a in acceptance
        if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately"
    )
    n_criteria = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    proto_ok = passed >= max(n_criteria - 1, 5)
    ch_n = max(calibrated_m.get("clean_human_n", 23), 1)
    cal_accept = calibrated_m["clean_human_accept_count"]
    cal_border = calibrated_m["clean_human_borderline_count"]
    cal_fp = calibrated_m["clean_human_false_alarm_count"]
    r2_accept = r2_product_m["clean_human_accept_count"]

    lines = [
        "# Phase 7C4 Final Recommendation",
        "",
        "## Summary",
        "",
        "- Phase 7C3-v1 rejected (binary head as origin proxy; replay/mixer/partial collapsed).",
        "- **Standalone R2 checkpoints (`best_product`, `best_loss`) are not accepted.**",
        "- Phase 7C4 is **calibration only** (no training): threshold sweep + multi-checkpoint decision rules.",
        "",
        "## Recommendation",
        "",
    ]
    if proto_ok:
        lines += [
            "**Accepted for decision-layer prototype only** — not as a final product model.",
            "",
            "Use calibrated rules in `apply_phase7c4_decision_layer.py` instead of any single checkpoint file-level REAL/FAKE.",
            "",
            "**Required before product sign-off:**",
            "- Run `check_phase7c4_holdout_impact.py` on Phase 7A holdout CSVs.",
            "- Phase 7A impact must be reviewed; prototype is **not** fully accepted until holdout passes.",
            "- Collect more external audio beyond T1–T5 / 7C1 before any market-level performance claim.",
        ]
    else:
        lines += [
            "**Do not accept** the current calibrated layer or standalone R2 checkpoints.",
            "",
            "Tune decision rules and/or proceed to **Phase 7C3-R3** (separate heads / training targets).",
        ]
    lines += [
        "",
        "## Clean human accounting (Phase 7C1)",
        "",
        f"- Calibrated **accepted**: {cal_accept}/{ch_n}",
        f"- Calibrated **borderline** (manual review, not clean): {cal_border}/{ch_n}",
        f"- Calibrated **false alarm**: {cal_fp}/{ch_n}",
        f"- Calibrated review rate (borderline/n): {calibrated_m['clean_human_review_rate']:.1%}",
        f"- R2 product accepted (reference): {r2_accept}/{ch_n}",
        f"- Baseline accepted (reference): {baseline_m['clean_human_accept_count']}/{ch_n}",
        "",
        "> Borderline is not accepted as clean; it means manual review.",
        "",
        "## Other key metrics (calibrated vs baseline)",
        "",
        f"- Direct AI segment+detect: "
        f"{baseline_m['direct_ai_detected_count'] + baseline_m['direct_ai_segment_suspicious_count']} → "
        f"{calibrated_m['direct_ai_detected_count'] + calibrated_m['direct_ai_segment_suspicious_count']}",
        f"- AI replay detected / segment-suspicious: "
        f"{baseline_m['ai_replay_detected_count']}/{baseline_m.get('ai_replay_segment_suspicious_count', 0)} → "
        f"{calibrated_m['ai_replay_detected_count']}/{calibrated_m.get('ai_replay_segment_suspicious_count', 0)}",
        f"- Partial detected: {baseline_m['partial_fabrication_detected_count']} → {calibrated_m['partial_fabrication_detected_count']}",
        f"- Product score: {baseline_m['product_score']:.4f} → {calibrated_m['product_score']:.4f}",
        "",
        f"- Phase 7C1 acceptance criteria passed: **{passed}/{n_criteria}**",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Phase 7C4 calibrated decision layer")
    add_phase7c4_calibration_args(p, include_v1_outputs=True)
    args = p.parse_args()

    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)
    err_csv = resolve_phase7_report_path(args.error_csv, for_write=True)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)
    final_md = (
        resolve_phase7_report_path(args.final_recommendation_md, for_write=True)
        if args.final_recommendation_md
        else out_md.parent / "phase7c4_final_recommendation.md"
    )

    baseline = merge_partial(load_results(Path(args.baseline_csv)), load_partial(Path(args.baseline_partial_csv)))
    r2_product = merge_partial(load_results(Path(args.r2_product_csv)), load_partial(Path(args.r2_product_partial_csv)))
    r2_loss = merge_partial(load_results(Path(args.r2_loss_csv)), load_partial(Path(args.r2_loss_partial_csv)))
    merged = merge_three_checkpoints(baseline, r2_product, r2_loss)

    decisions = [apply_decision_layer(merged.loc[i]) for i in merged.index]
    dec_df = pd.DataFrame(decisions)

    # metrics use manipulation_type / ground_truth_origin columns
    eval_df = dec_df.copy()
    eval_df["manipulation_type"] = eval_df["manipulation_type"]
    eval_df["ground_truth_origin"] = eval_df["source_origin"]
    eval_df["suspicious_start_time"] = merged["suspicious_start_time_baseline"].values
    eval_df["suspicious_end_time"] = merged["suspicious_end_time_baseline"].values
    eval_df["partial_fabrication_binary"] = merged.get(
        "partial_fabrication_binary_baseline", False
    ).values

    baseline_eval = baseline.copy()
    baseline_eval["baseline_status"] = baseline_eval["baseline_status"]
    r2_eval = r2_product.copy()

    baseline_m = compute_metrics(baseline_eval, "baseline_status")
    r2_product_m = compute_metrics(r2_eval, "baseline_status")
    calibrated_m = compute_metrics(
        eval_df.rename(columns={"calibrated_status": "baseline_status"}),
        "baseline_status",
    )

    acceptance = assess_acceptance(baseline_m, r2_product_m, calibrated_m)
    acc_path = (
        resolve_phase7_report_path(args.acceptance_csv, for_write=True)
        if args.acceptance_csv
        else out_csv.parent / "phase7c4_acceptance_matrix.csv"
    )
    pd.DataFrame(acceptance).to_csv(acc_path, index=False)

    errors = []
    for d in decisions:
        if is_error_case(d, baseline_m):
            errors.append({**d, "error_reason": "regression_vs_baseline_expectation"})
    err_df = pd.DataFrame(errors)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    err_df.to_csv(err_csv, index=False)

    dec_df.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")
    print(f"[SAVE] {err_csv} ({len(err_df)} rows)")
    print(f"[SAVE] {acc_path}")

    write_decision_md(out_md, calibrated_m, baseline_m, r2_product_m, acceptance, len(err_df))
    print(f"[SAVE] {out_md}")

    write_final_recommendation(final_md, acceptance, calibrated_m, baseline_m, r2_product_m)
    print(f"[SAVE] {final_md}")

    passed = sum(
        1
        for a in acceptance
        if a["passed"] and a["criterion"] != "clean_human_accept_reported_separately"
    )
    n_criteria = sum(1 for a in acceptance if a["criterion"] != "clean_human_accept_reported_separately")
    print(
        f"[ACCEPTANCE] {passed}/{n_criteria} criteria passed "
        f"(prototype={'yes' if passed >= max(n_criteria - 1, 5) else 'no'}); "
        f"product_score={calibrated_m['product_score']:.4f}"
    )


if __name__ == "__main__":
    main()
