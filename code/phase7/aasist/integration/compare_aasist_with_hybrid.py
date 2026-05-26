"""
Phase 7E3A: Compare AASIST-L Phase 7C1 predictions with HybridResNet baseline and 7C4-v2.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from _common import ensure_dir, resolve_path, utc_now_iso, write_markdown
from analyze_aasist_pretrained_eval import compute_7c1_metrics, ensure_status_column
from aasist_eval_common import evaluate_aasist_status

IMPROVEMENT_STATUSES = {
    "direct_ai": {
        "hybrid_ok": {"direct_ai_detected", "direct_ai_file_level_missed_but_segment_suspicious"},
        "aasist_ok": {"direct_ai_detected", "direct_ai_file_level_missed_but_segment_suspicious"},
    },
    "clean_human": {
        "hybrid_bad": {"clean_human_false_alarm"},
        "aasist_bad": {"clean_human_false_alarm"},
    },
}

ID_CANDIDATES = ("sample_id", "test_id", "file_id", "utt_id", "id")


def normalize_sample_id(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Ensure DataFrame has a non-empty sample_id column."""
    out = df.copy()
    if "sample_id" in out.columns and out["sample_id"].notna().any():
        out["sample_id"] = out["sample_id"].astype(str).str.strip()
        if (out["sample_id"] != "").any():
            return out

    for col in ID_CANDIDATES:
        if col in out.columns:
            out["sample_id"] = out[col].astype(str).str.strip()
            if (out["sample_id"] != "").any():
                return out

    raise ValueError(
        f"{label}: no sample_id column and none of {ID_CANDIDATES} found. "
        f"Columns: {list(df.columns)}"
    )


def merge_predictions(
    aasist_df: pd.DataFrame,
    hybrid_df: pd.DataFrame,
    decision_df: pd.DataFrame | None,
) -> pd.DataFrame:
    a = normalize_sample_id(aasist_df, "aasist_csv")
    h = normalize_sample_id(hybrid_df, "hybrid_csv")

    if "aasist_status" not in a.columns:
        a["aasist_status"] = a.apply(lambda r: evaluate_aasist_status(r.to_dict()), axis=1)

    merged = a.merge(h, on="sample_id", how="left", suffixes=("", "_hybrid"))

    if decision_df is not None:
        d = normalize_sample_id(decision_df, "decision_csv")
        keep_cols = ["sample_id"]
        for col in ("calibrated_status", "calibrated_risk_level", "selected_model_evidence"):
            if col in d.columns:
                keep_cols.append(col)
        merged = merged.merge(d[keep_cols], on="sample_id", how="left", suffixes=("", "_decision"))

    if "baseline_status" in merged.columns:
        missing_hybrid = int(merged["baseline_status"].isna().sum())
    elif "baseline_status_hybrid" in merged.columns:
        missing_hybrid = int(merged["baseline_status_hybrid"].isna().sum())
    else:
        missing_hybrid = 0

    if missing_hybrid > 0:
        print(f"Warning: {missing_hybrid} AASIST rows have no matching hybrid baseline row.")

    return merged


def compare_metrics(aasist_df: pd.DataFrame, hybrid_df: pd.DataFrame) -> dict:
    a_metrics = compute_7c1_metrics(ensure_status_column(aasist_df))
    h = normalize_sample_id(hybrid_df, "hybrid_csv")
    if "baseline_status" in h.columns:
        h = h.copy()
        h["aasist_status"] = h["baseline_status"]
    h_metrics = compute_7c1_metrics(h)
    delta = {k: a_metrics.get(k, 0) - h_metrics.get(k, 0) for k in a_metrics}
    return {"aasist": a_metrics, "hybrid": h_metrics, "delta_aasist_minus_hybrid": delta}


def per_sample_improvements(merged: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in merged.iterrows():
        ast = str(r.get("aasist_status", ""))
        bst = str(r.get("baseline_status", r.get("baseline_status_hybrid", "")))
        rows.append(
            {
                "sample_id": r.get("sample_id"),
                "manipulation_type": r.get("manipulation_type", r.get("manipulation_type_hybrid", "")),
                "source_origin": r.get("source_origin", r.get("source_origin_hybrid", "")),
                "aasist_status": ast,
                "hybrid_baseline_status": bst,
                "mean_spoof_score": r.get("mean_spoof_score"),
                "decision_score": r.get("decision_score", r.get("decision_score_hybrid")),
                "calibrated_status": r.get("calibrated_status", ""),
                "aasist_better_direct_ai": ast in IMPROVEMENT_STATUSES["direct_ai"]["aasist_ok"]
                and bst not in IMPROVEMENT_STATUSES["direct_ai"]["hybrid_ok"],
                "aasist_worse_clean_human": ast in IMPROVEMENT_STATUSES["clean_human"]["aasist_bad"]
                and bst not in IMPROVEMENT_STATUSES["clean_human"]["hybrid_bad"],
                "hybrid_better_direct_ai": bst in IMPROVEMENT_STATUSES["direct_ai"]["hybrid_ok"]
                and ast not in IMPROVEMENT_STATUSES["direct_ai"]["aasist_ok"],
            }
        )
    return pd.DataFrame(rows)


def write_comparison_md(cmp: dict, improvements: pd.DataFrame, output_md: Path) -> None:
    a = cmp["aasist"]
    h = cmp["hybrid"]
    d = cmp["delta_aasist_minus_hybrid"]

    lines = [
        "# Phase 7E3A — AASIST-L vs HybridResNet (Phase 7C1)",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Aggregate metrics",
        "",
        "| metric | hybrid_baseline | aasist_l | delta (AASIST − Hybrid) |",
        "| --- | --- | --- | --- |",
    ]
    for metric in [
        "clean_human_false_alarm",
        "clean_human_accepted",
        "direct_ai_detected_or_segment_suspicious",
        "ai_replay_detected_or_segment_suspicious",
        "human_replay_detected",
        "human_mixer_detected",
        "ai_mixer_detected",
        "partial_fabrication_detected",
    ]:
        lines.append(
            f"| {metric} | {h.get(metric, '')} | {a.get(metric, '')} | {d.get(metric, '')} |"
        )

    n_better = int(improvements["aasist_better_direct_ai"].sum()) if not improvements.empty else 0
    n_worse_clean = int(improvements["aasist_worse_clean_human"].sum()) if not improvements.empty else 0
    n_hybrid_better = int(improvements["hybrid_better_direct_ai"].sum()) if not improvements.empty else 0

    lines.extend(
        [
            "",
            "## Per-sample highlights",
            "",
            f"- AASIST better on direct AI (hybrid missed): **{n_better}**",
            f"- AASIST worse on clean human (new false alarm): **{n_worse_clean}**",
            f"- Hybrid better on direct AI (AASIST missed): **{n_hybrid_better}**",
            "",
        ]
    )
    write_markdown(output_md, lines)


def write_decision_recommendation(cmp: dict, output_md: Path) -> None:
    a = cmp["aasist"]
    h = cmp["hybrid"]
    d = cmp["delta_aasist_minus_hybrid"]

    fa_ok_standalone = a.get("clean_human_false_alarm", 99) <= 7
    fa_ok_branch = a.get("clean_human_false_alarm", 99) <= 10
    direct_ok = a.get("direct_ai_detected_or_segment_suspicious", 0) >= 15

    if fa_ok_standalone and direct_ok:
        verdict = "standalone_candidate"
        fine_tune = "Optional — pretrained meets key gates; confirm 7A holdout."
    elif fa_ok_branch and direct_ok:
        verdict = "branch_only_direct_ai"
        fine_tune = "Recommended if 7A holdout confirms direct-AI lift without clean-human regression."
    elif d.get("direct_ai_detected_or_segment_suspicious", 0) > 0 and not fa_ok_branch:
        verdict = "needs_calibration_or_finetune"
        fine_tune = "Yes — threshold tuning or 7E3B fine-tune before any product branch."
    else:
        verdict = "reject_or_defer"
        fine_tune = "Defer 7E3B until adapter/threshold audit; HybridResNet remains primary evidence."

    lines = [
        "# Phase 7E3A — AASIST-L Decision Recommendation",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        f"## Verdict: **{verdict}**",
        "",
        f"**Fine-tune next (7E3B)?** {fine_tune}",
        "",
        "## Rationale",
        "",
        f"- AASIST clean-human false alarms: **{a.get('clean_human_false_alarm')}** "
        f"(Hybrid: **{h.get('clean_human_false_alarm')}**, Δ **{d.get('clean_human_false_alarm')}**)",
        f"- AASIST direct AI detected/segment: **{a.get('direct_ai_detected_or_segment_suspicious')}** "
        f"(Hybrid: **{h.get('direct_ai_detected_or_segment_suspicious')}**)",
        "",
    ]
    write_markdown(output_md, lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare AASIST with Hybrid baseline")
    parser.add_argument("--aasist_csv", type=str, required=True)
    parser.add_argument("--hybrid_csv", type=str, required=True)
    parser.add_argument("--decision_csv", type=str, default="")
    parser.add_argument("--output_dir", type=str, required=True)
    args = parser.parse_args()

    out_dir = ensure_dir(resolve_path(args.output_dir))
    aasist_df = pd.read_csv(resolve_path(args.aasist_csv))
    hybrid_df = pd.read_csv(resolve_path(args.hybrid_csv))
    decision_df = None
    if args.decision_csv:
        p = resolve_path(args.decision_csv)
        if p.is_file():
            decision_df = pd.read_csv(p)

    try:
        merged = merge_predictions(aasist_df, hybrid_df, decision_df)
    except ValueError as e:
        print(f"Merge failed: {e}")
        return 1

    improvements = per_sample_improvements(merged)
    cmp = compare_metrics(aasist_df, hybrid_df)

    merged.to_csv(out_dir / "aasist_l_vs_hybrid_comparison.csv", index=False)
    write_comparison_md(cmp, improvements, out_dir / "aasist_l_vs_hybrid_comparison.md")
    write_decision_recommendation(cmp, out_dir / "aasist_l_decision_recommendation.md")

    print(f"Wrote comparison to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
