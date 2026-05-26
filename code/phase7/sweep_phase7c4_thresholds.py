"""
Phase 7C4: Sweep decision thresholds on existing Phase 7C1 result CSVs (no retraining).
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7c4_common import (  # noqa: E402
    ThresholdParams,
    build_ensemble_row,
    compute_metrics,
    load_partial,
    load_results,
    md_table,
    merge_partial,
    merge_three_checkpoints,
    reevaluate_dataframe,
    status_counts,
)
from phase7.phase7_paths import P7, add_phase7c4_calibration_args, resolve_phase7_report_path  # noqa: E402


def sweep_source(
    df: pd.DataFrame,
    source_name: str,
    vote_values: list[float],
    segment_values: list[float],
    ratio_values: list[float],
    borderline_margin: float,
) -> list[dict]:
    rows = []
    for vt, seg, ratio in itertools.product(vote_values, segment_values, ratio_values):
        params = ThresholdParams(
            vote_threshold=vt,
            segment_max_spoof_threshold=seg,
            suspicious_chunk_ratio_threshold=ratio,
            clean_human_borderline_margin=borderline_margin,
        )
        ev = reevaluate_dataframe(df, params)
        m = compute_metrics(ev, "baseline_status")
        rows.append({
            "source": source_name,
            "vote_threshold": vt,
            "segment_max_spoof_threshold": seg,
            "suspicious_chunk_ratio_threshold": ratio,
            "clean_human_borderline_margin": borderline_margin,
            **m,
        })
    return rows


def sweep_ensemble(
    merged: pd.DataFrame,
    vote_values: list[float],
    segment_values: list[float],
    ratio_values: list[float],
    borderline_margin: float,
) -> list[dict]:
    rows = []
    for vt, seg, ratio in itertools.product(vote_values, segment_values, ratio_values):
        params = ThresholdParams(
            vote_threshold=vt,
            segment_max_spoof_threshold=seg,
            suspicious_chunk_ratio_threshold=ratio,
            clean_human_borderline_margin=borderline_margin,
        )
        ens_rows = [build_ensemble_row(merged.loc[i], params) for i in merged.index]
        ev = pd.DataFrame(ens_rows)
        m = compute_metrics(ev, "baseline_status")
        rows.append({
            "source": "candidate_ensemble",
            "vote_threshold": vt,
            "segment_max_spoof_threshold": seg,
            "suspicious_chunk_ratio_threshold": ratio,
            "clean_human_borderline_margin": borderline_margin,
            **m,
        })
    return rows


def write_sweep_md(path: Path, sweep_df: pd.DataFrame, baseline_default: dict) -> None:
    lines = [
        "# Phase 7C4 Threshold Sweep Report",
        "",
        "Re-evaluates Phase 7C1 `baseline_status` from existing scores (no model re-run).",
        "",
        f"- Configurations tested: **{len(sweep_df)}**",
        "",
        "## Default baseline metrics (vote=0.70, segment_max=0.95, ratio=0.30)",
        "",
        f"- Clean human accept: {baseline_default.get('clean_human_accept_count', 'n/a')} / {baseline_default.get('clean_human_n', 23)}",
        f"- Clean human false alarms: {baseline_default.get('clean_human_false_alarm_count', 'n/a')}",
        f"- Direct AI detected + segment-suspicious: {baseline_default.get('direct_ai_detected_count', 0)} + {baseline_default.get('direct_ai_segment_suspicious_count', 0)}",
        f"- Product score: {baseline_default.get('product_score', 0):.4f}",
        "",
        "## Top 10 configurations by product_score (all sources)",
        "",
    ]
    top = sweep_df.sort_values("product_score", ascending=False).head(10)
    rows = []
    for _, r in top.iterrows():
        rows.append([
            r["source"],
            f"{r['vote_threshold']:.2f}",
            f"{r['segment_max_spoof_threshold']:.2f}",
            f"{r['suspicious_chunk_ratio_threshold']:.2f}",
            f"{r['product_score']:.4f}",
            int(r["clean_human_false_alarm_count"]),
            int(r["partial_fabrication_detected_count"]),
        ])
    lines.append(
        md_table(
            ["source", "vote", "seg_max", "chunk_ratio", "product_score", "ch_fp", "partial_det"],
            rows,
        )
    )

    for src in ["baseline", "r2_product", "r2_loss", "candidate_ensemble"]:
        sub = sweep_df[sweep_df["source"] == src].sort_values("product_score", ascending=False).head(5)
        if sub.empty:
            continue
        lines += [f"## Best for `{src}`", ""]
        rows = []
        for _, r in sub.iterrows():
            rows.append([
                f"{r['vote_threshold']:.2f}",
                f"{r['segment_max_spoof_threshold']:.2f}",
                f"{r['suspicious_chunk_ratio_threshold']:.2f}",
                f"{r['product_score']:.4f}",
                int(r["clean_human_accept_count"]),
                int(r["clean_human_false_alarm_count"]),
                int(r["direct_ai_detected_count"]) + int(r["direct_ai_segment_suspicious_count"]),
                int(r["partial_fabrication_detected_count"]),
            ])
        lines.append(
            md_table(
                ["vote", "seg_max", "ratio", "product", "ch_acc", "ch_fp", "direct_ai+", "partial"],
                rows,
            )
        )

    lines += [
        "",
        "## Notes",
        "",
        "- Sweep varies file-level vote and segment thresholds only; chunk spoof scores are fixed from saved CSVs.",
        "- `candidate_ensemble` uses max(decision_score) and max(chunk metrics) across baseline + R2 product + R2 loss.",
        "- Threshold sweep alone cannot recover all baseline partial/replay strength; see decision layer (7C4 script 3).",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Phase 7C4 threshold sweep")
    add_phase7c4_calibration_args(
        p,
        output_csv=f"{P7}/phase7c4_calibration/calibration_outputs/phase7c4_threshold_sweep.csv",
        output_md=f"{P7}/phase7c4_calibration/phase7c4_threshold_sweep_report.md",
    )
    args = p.parse_args()
    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)

    vote_values = [round(x, 2) for x in np.arange(0.40, 0.81, 0.05)]
    segment_values = [0.85, 0.90, 0.95]
    ratio_values = [0.10, 0.20, 0.30]
    borderline_margin = 0.05

    baseline = merge_partial(
        load_results(Path(args.baseline_csv)),
        load_partial(Path(args.baseline_partial_csv) if args.baseline_partial_csv else None),
    )
    r2_product = merge_partial(
        load_results(Path(args.r2_product_csv)),
        load_partial(Path(args.r2_product_partial_csv) if args.r2_product_partial_csv else None),
    )
    r2_loss = merge_partial(
        load_results(Path(args.r2_loss_csv)),
        load_partial(Path(args.r2_loss_partial_csv) if args.r2_loss_partial_csv else None),
    )
    merged = merge_three_checkpoints(baseline, r2_product, r2_loss)

    all_rows = []
    all_rows.extend(sweep_source(baseline, "baseline", vote_values, segment_values, ratio_values, borderline_margin))
    all_rows.extend(sweep_source(r2_product, "r2_product", vote_values, segment_values, ratio_values, borderline_margin))
    all_rows.extend(sweep_source(r2_loss, "r2_loss", vote_values, segment_values, ratio_values, borderline_margin))
    all_rows.extend(sweep_ensemble(merged, vote_values, segment_values, ratio_values, borderline_margin))

    sweep_df = pd.DataFrame(all_rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    sweep_df.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv} ({len(sweep_df)} rows)")

    default_params = ThresholdParams()
    baseline_default = compute_metrics(reevaluate_dataframe(baseline, default_params), "baseline_status")
    write_sweep_md(out_md, sweep_df, baseline_default)

    # terminal summary
    best = sweep_df.sort_values("product_score", ascending=False).iloc[0]
    print(
        f"[BEST] source={best['source']} product_score={best['product_score']:.4f} "
        f"vote={best['vote_threshold']} seg={best['segment_max_spoof_threshold']} ratio={best['suspicious_chunk_ratio_threshold']}"
    )


if __name__ == "__main__":
    main()
