"""
Phase 7C1: Analyze baseline results CSV and generate reports.

Does not train models. Reads runner output; optional partial fabrication CSV.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.run_phase7c1_baseline import (
    evaluate_baseline_status,
    build_final_baseline_interpretation,
)

ERROR_BASELINE_STATUSES = frozenset(
    {
        "clean_human_false_alarm",
        "direct_ai_missed",
        "direct_ai_file_level_missed_but_segment_suspicious",
        "human_replay_missed",
        "ai_replay_missed",
        "ai_replay_file_level_missed_but_segment_suspicious",
        "human_mixer_missed",
        "ai_mixer_missed",
        "ai_mixer_file_level_missed_but_segment_suspicious",
        "partial_fabrication_missed",
        "partial_fabrication_not_evaluable",
        "clean_human_borderline",
        "borderline_needs_review",
        "unknown_review_required",
    }
)

FAILURE_BASELINE_STATUSES = frozenset(
    s
    for s in ERROR_BASELINE_STATUSES
    if s
    not in {
        "clean_human_borderline",
        "borderline_needs_review",
        "direct_ai_file_level_missed_but_segment_suspicious",
        "ai_replay_file_level_missed_but_segment_suspicious",
        "ai_mixer_file_level_missed_but_segment_suspicious",
    }
)


def _to_float(value, default=None):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    s = str(value).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _has_error(value) -> bool:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    return str(value).strip() != ""


def _status_counts(df: pd.DataFrame, col: str = "baseline_status") -> Counter:
    if df.empty or col not in df.columns:
        return Counter()
    return Counter(df[col].fillna("").astype(str))


def _pct(n: int, d: int) -> str:
    if d <= 0:
        return "n/a"
    return f"{100.0 * n / d:.1f}%"


def _mean_col(df: pd.DataFrame, col: str) -> float | None:
    if col not in df.columns or df.empty:
        return None
    vals = [_to_float(v) for v in df[col]]
    vals = [v for v in vals if v is not None]
    return float(np.mean(vals)) if vals else None


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["manipulation_type", "source_origin", "split", "variant_id"]
    for c in group_cols:
        if c not in df.columns:
            df[c] = ""

    rows = []
    grouped = df.groupby(group_cols, dropna=False)
    for keys, gdf in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["total"] = len(gdf)
        statuses = _status_counts(gdf)
        for status, cnt in statuses.items():
            if status:
                row[f"status_{status}"] = cnt
        row["avg_decision_score"] = _mean_col(gdf, "decision_score")
        row["avg_suspicious_chunk_ratio"] = _mean_col(gdf, "suspicious_chunk_ratio")
        row["avg_max_chunk_spoof"] = _mean_col(gdf, "max_chunk_spoof")

        partial_mask = gdf["baseline_status"].isin(
            ["partial_fabrication_detected", "partial_fabrication_missed", "partial_fabrication_not_evaluable"]
        )
        partial_sub = gdf[partial_mask]
        if len(partial_sub) > 0:
            detected = int((partial_sub["baseline_status"] == "partial_fabrication_detected").sum())
            evaluable = int(
                (partial_sub["baseline_status"] != "partial_fabrication_not_evaluable").sum()
            )
            row["partial_detection_rate"] = detected / evaluable if evaluable else ""
        else:
            row["partial_detection_rate"] = ""

        rows.append(row)

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(group_cols).reset_index(drop=True)
    return out


def build_error_cases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    mask_err_col = df["error"].apply(_has_error) if "error" in df.columns else False
    mask_status = df["baseline_status"].isin(ERROR_BASELINE_STATUSES) if "baseline_status" in df.columns else False
    err_df = df[mask_err_col | mask_status].copy()
    if err_df.empty:
        return err_df

    # Priority sort: hard failures first
    priority = {
        "clean_human_false_alarm": 1,
        "direct_ai_missed": 2,
        "partial_fabrication_missed": 3,
        "ai_replay_missed": 4,
        "ai_mixer_missed": 5,
        "human_replay_missed": 6,
        "human_mixer_missed": 7,
    }

    def sort_key(row):
        st = str(row.get("baseline_status", ""))
        return (priority.get(st, 50), st, str(row.get("sample_id", "")))

    err_df["_sort"] = err_df.apply(sort_key, axis=1)
    err_df = err_df.sort_values("_sort").drop(columns=["_sort"])
    return err_df


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"


def write_analysis_markdown(
    df: pd.DataFrame,
    category_df: pd.DataFrame,
    error_df: pd.DataFrame,
    partial_df: pd.DataFrame,
    output_md: Path,
) -> None:
    n = len(df)
    base_ids = df["base_id"].nunique() if "base_id" in df.columns else 0
    split_counts = df["split"].value_counts().to_dict() if "split" in df.columns else {}
    variant_counts = df["variant_id"].value_counts().to_dict() if "variant_id" in df.columns else {}
    statuses = _status_counts(df)
    errors_n = int(df["error"].apply(_has_error).sum()) if "error" in df.columns else 0

    def sc(*keys: str) -> int:
        return sum(statuses.get(k, 0) for k in keys)

    lines = [
        "# Phase 7C1 — Baseline Analysis (Pre Fine-Tuning)",
        "",
        "Generated by `analyze_phase7c1_baseline.py`. Model: current Phase 4/6 hybrid checkpoint.",
        "**No training** was performed for this report.",
        "",
        "## 1. Executive summary",
        "",
        f"- **Files evaluated:** {n} ({base_ids} base IDs)",
        f"- **Inference errors:** {errors_n}",
        f"- **Clean human accepted:** {sc('clean_human_accepted')} "
        f"(false alarms: {sc('clean_human_false_alarm')}, borderline: {sc('clean_human_borderline')})",
        f"- **Direct AI:** detected {sc('direct_ai_detected')}, missed {sc('direct_ai_missed')}, "
        f"segment-suspicious miss {sc('direct_ai_file_level_missed_but_segment_suspicious')}",
        f"- **Partial fabrication:** detected {sc('partial_fabrication_detected')}, "
        f"missed {sc('partial_fabrication_missed')}, not evaluable {sc('partial_fabrication_not_evaluable')}",
        "",
        "This benchmark captures **current-model** behavior on the Round-1 7C1 collection before Phase 7C fine-tuning.",
        "",
        "## 2. Dataset summary",
        "",
        f"- Total files: **{n}**",
        f"- Unique base IDs: **{base_ids}**",
        f"- Variants per base (design): **8**",
        "",
        "### Split counts",
        "",
        _md_table(["split", "count"], [[k, v] for k, v in sorted(split_counts.items())]),
        "",
        "### Variant counts",
        "",
        _md_table(
            ["variant_id", "count"],
            [[k, v] for k, v in sorted(variant_counts.items())],
        ),
        "",
        "## 3. Overall baseline behavior",
        "",
        _md_table(
            ["baseline_status", "count", "% of total"],
            [
                [st, cnt, _pct(cnt, n)]
                for st, cnt in statuses.most_common()
                if st
            ],
        ),
        "",
        f"- Mean decision score (all): `{_mean_col(df, 'decision_score')}`",
        f"- Mean max chunk spoof: `{_mean_col(df, 'max_chunk_spoof')}`",
        f"- Mean suspicious chunk ratio: `{_mean_col(df, 'suspicious_chunk_ratio')}`",
        "",
    ]

    sections = [
        (
            "4. Clean human performance",
            ["clean_human_accepted", "clean_human_false_alarm", "clean_human_borderline"],
            "clean_direct",
            "human",
        ),
        (
            "5. Direct AI performance",
            [
                "direct_ai_detected",
                "direct_ai_missed",
                "direct_ai_file_level_missed_but_segment_suspicious",
            ],
            "clean_direct",
            "ai",
        ),
        (
            "6. Human replay performance",
            ["human_replay_manipulation_detected", "human_replay_missed"],
            "human_replay",
            None,
        ),
        (
            "7. AI replay performance",
            [
                "ai_replay_detected",
                "ai_replay_missed",
                "ai_replay_file_level_missed_but_segment_suspicious",
            ],
            "ai_replay",
            None,
        ),
        (
            "8. Human mixer performance",
            ["human_mixer_manipulation_detected", "human_mixer_missed"],
            "mixer_processed",
            "human",
        ),
        (
            "9. AI mixer performance",
            [
                "ai_mixer_detected",
                "ai_mixer_missed",
                "ai_mixer_file_level_missed_but_segment_suspicious",
            ],
            "mixer_processed",
            "ai",
        ),
    ]

    for title, status_keys, manip, origin in sections:
        lines.append(f"## {title}")
        lines.append("")
        sub = df
        if manip and "manipulation_type" in df.columns:
            sub = sub[sub["manipulation_type"].astype(str).str.lower() == manip]
        if origin and "ground_truth_origin" in df.columns:
            sub = sub[sub["ground_truth_origin"].astype(str).str.lower() == origin]
        total = len(sub)
        rows = [[k, sc(k), _pct(sc(k), total)] for k in status_keys]
        lines.append(_md_table(["status", "count", "% within group"], rows))
        lines.append("")

    lines.extend(
        [
            "## 10. Partial fabrication performance",
            "",
            f"- Rows in partial analysis CSV: **{len(partial_df)}**",
            f"- Region detected (baseline status): **{sc('partial_fabrication_detected')}**",
            f"- Region missed: **{sc('partial_fabrication_missed')}**",
            "",
        ]
    )
    if not partial_df.empty and "region_delta" in partial_df.columns:
        deltas = [_to_float(v) for v in partial_df["region_delta"]]
        deltas = [d for d in deltas if d is not None]
        if deltas:
            lines.append(
                f"- Mean region_delta (inside_avg − outside_avg): **{np.mean(deltas):.3f}**"
            )
        lines.append("")

    lines.extend(
        [
            "## 11. Segment-suspicious file-level misses",
            "",
            "Cases where file-level prediction is REAL but chunk evidence is strong:",
            "",
            _md_table(
                ["status", "count"],
                [
                    [st, sc(st)]
                    for st in (
                        "direct_ai_file_level_missed_but_segment_suspicious",
                        "ai_replay_file_level_missed_but_segment_suspicious",
                        "ai_mixer_file_level_missed_but_segment_suspicious",
                    )
                ],
            ),
            "",
            "## 12. Borderline cases",
            "",
            f"- `clean_human_borderline`: {sc('clean_human_borderline')}",
            f"- `borderline_needs_review`: {sc('borderline_needs_review')}",
            "",
            "## 13. Worst failure cases",
            "",
        ]
    )

    worst = error_df.head(15)
    if worst.empty:
        lines.append("_No failure cases in error extract._\n")
    else:
        cols = [
            c
            for c in [
                "sample_id",
                "variant_id",
                "baseline_status",
                "prediction",
                "decision_score",
                "max_chunk_spoof",
            ]
            if c in worst.columns
        ]
        lines.append(_md_table(cols, worst[cols].astype(str).values.tolist()))

    lines.extend(
        [
            "",
            "## 14. Implications for Phase 7C2 training dataset builder",
            "",
            "- Use **variant-level** baseline_status to weight or stratify fine-tuning manifests.",
            "- Prioritize rows with `partial_fabrication_missed` and segment-suspicious file-level misses for chunk-aware training.",
            "- Keep clean human false alarms visible — calibration / threshold work may be needed alongside data.",
            "",
            "## 15. Implications for Phase 7C fine-tuning",
            "",
            "- This report is the **before** snapshot; repeat after 7C training for comparison.",
            "- Weak areas (direct AI misses, partial region misses, pct_vote vs chunk mismatch) guide loss weighting and evaluation splits.",
            "- Do **not** merge Phase 7A controlled holdout (T1–T5) into training.",
            "",
            "## 16. Recommended next action",
            "",
            "1. Review `phase7c1_baseline_error_cases.csv` and partial fabrication CSV.",
            "2. Sign off baseline in project docs when acceptable as pre-training reference.",
            "3. Proceed to Phase 7C2 dataset builder design (still no training until approved).",
            "4. Re-run this baseline pipeline after any inference-threshold changes for fair comparison.",
            "",
        ]
    )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVE] Analysis markdown -> {output_md}")


def enrich_results_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "baseline_status" not in out.columns or out["baseline_status"].fillna("").eq("").all():
        out["baseline_status"] = out.apply(lambda r: evaluate_baseline_status(r.to_dict()), axis=1)
    if "final_baseline_interpretation" not in out.columns or out["final_baseline_interpretation"].fillna("").eq("").all():
        out["final_baseline_interpretation"] = out.apply(
            lambda r: build_final_baseline_interpretation(r.to_dict()), axis=1
        )
    return out


def main():
    p = argparse.ArgumentParser(description="Phase 7C1 — analyze baseline results")
    p.add_argument("--results_csv", type=str, required=True)
    p.add_argument("--output_md", type=str, default="reports/phase7/phase7c1_baseline/results/PHASE7C1_BASELINE_ANALYSIS.md")
    p.add_argument("--category_csv", type=str, default="reports/phase7/phase7c1_baseline/results/phase7c1_baseline_category_summary.csv")
    p.add_argument("--error_csv", type=str, default="reports/phase7/phase7c1_baseline/results/phase7c1_baseline_error_cases.csv")
    p.add_argument("--partial_csv", type=str, default="reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv")
    args = p.parse_args()

    from phase7.phase7_paths import resolve_phase7_report_path

    results_path = resolve_phase7_report_path(args.results_csv)
    if not results_path.is_file():
        raise FileNotFoundError(results_path)

    df = pd.read_csv(results_path, low_memory=False)
    df = enrich_results_if_needed(df)

    partial_path = resolve_phase7_report_path(args.partial_csv) if args.partial_csv else None
    partial_df = pd.read_csv(partial_path, low_memory=False) if partial_path.is_file() else pd.DataFrame()

    category_df = build_category_summary(df)
    category_path = resolve_phase7_report_path(args.category_csv, for_write=True)
    category_path.parent.mkdir(parents=True, exist_ok=True)
    category_df.to_csv(category_path, index=False)
    print(f"[SAVE] Category summary -> {category_path} ({len(category_df)} groups)")

    error_df = build_error_cases(df)
    error_path = resolve_phase7_report_path(args.error_csv, for_write=True)
    error_df.to_csv(error_path, index=False)
    print(f"[SAVE] Error cases -> {error_path} ({len(error_df)} rows)")

    write_analysis_markdown(
        df,
        category_df,
        error_df,
        partial_df,
        resolve_phase7_report_path(args.output_md, for_write=True),
    )

    print(
        f"\n[OK] Analysis complete. Errors/warnings extract: {len(error_df)} rows; "
        f"status groups: {len(category_df)}."
    )


if __name__ == "__main__":
    main()
