"""
Phase 7C4: Compare baseline vs R2 best_product vs R2 best_loss on Phase 7C1 results.

Analysis only — does not train or modify checkpoints.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7c4_common import (  # noqa: E402
    CATEGORY_STATUS_KEYS,
    disagreement_type,
    format_category_counts,
    load_partial,
    load_results,
    md_table,
    merge_partial,
    merge_three_checkpoints,
    score_better_clean_human,
    status_counts,
)
from phase7.phase7_paths import P7, add_phase7c4_calibration_args, resolve_phase7_report_path  # noqa: E402


def _category_summary(df: pd.DataFrame, manip: str, origin: str | None = None) -> dict:
    sub = df[df["manipulation_type"].astype(str).str.lower() == manip]
    if origin:
        sub = sub[sub["ground_truth_origin"].astype(str).str.lower() == origin]
    return dict(Counter(sub["baseline_status"].fillna("").astype(str)))


def _format_category_row(counter: dict, category_key: str) -> str:
    return format_category_counts(counter, CATEGORY_STATUS_KEYS[category_key])


def write_comparison_md(
    path: Path,
    baseline: pd.DataFrame,
    r2_product: pd.DataFrame,
    r2_loss: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    lines = [
        "# Phase 7C4 Checkpoint Comparison",
        "",
        f"- Samples compared: **{len(comparison)}**",
        "",
        "## Status counts (Phase 7C1 `baseline_status`)",
        "",
        "### Original baseline",
        "",
    ]
    for k, v in sorted(status_counts(baseline).items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")
    lines += ["", "### R2 best_product", ""]
    for k, v in sorted(status_counts(r2_product).items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")
    lines += ["", "### R2 best_loss", ""]
    for k, v in sorted(status_counts(r2_loss).items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")

    lines += [
        "",
        "## Per-category summary",
        "",
        "_Status counts per manipulation category (not generic acc/fp)._",
        "",
    ]
    rows = []
    cat_specs = [
        ("clean_direct", "human", "Clean human", "clean_human"),
        ("clean_direct", "ai", "Direct AI", "direct_ai"),
        ("human_replay", None, "Human replay", "human_replay"),
        ("ai_replay", None, "AI replay", "ai_replay"),
        ("mixer_processed", "human", "Human mixer", "human_mixer"),
        ("mixer_processed", "ai", "AI mixer", "ai_mixer"),
        ("partial_ai_insert", None, "Partial fabrication", "partial"),
    ]
    for manip, origin, label, cat_key in cat_specs:
        b = _category_summary(baseline, manip, origin)
        pr = _category_summary(r2_product, manip, origin)
        lo = _category_summary(r2_loss, manip, origin)
        rows.append([
            label,
            _format_category_row(b, cat_key),
            _format_category_row(pr, cat_key),
            _format_category_row(lo, cat_key),
        ])
    lines.append(md_table(["Category", "Baseline", "R2 product", "R2 loss"], rows))

    ch = comparison[
        (comparison["manipulation_type"].astype(str).str.lower() == "clean_direct")
        & (comparison["source_origin"].astype(str).str.lower() == "human")
    ]
    if len(ch):
        r2p_better = (ch["clean_human_r2_product_better"] == "r2_better").sum()
        r2l_better = (ch["clean_human_r2_loss_better"] == "r2_better").sum()
        base_better = (ch["clean_human_r2_product_better"] == "baseline_better").sum()
        lines += [
            "",
            "## Clean human (23 samples)",
            "",
            f"- R2 product better than baseline: **{int(r2p_better)}**",
            f"- R2 loss better than baseline: **{int(r2l_better)}**",
            f"- Baseline better than R2 product: **{int(base_better)}**",
            "",
        ]

    disc = Counter(comparison["disagreement_type"])
    lines += ["## Disagreement types", ""]
    for k, v in disc.most_common():
        lines.append(f"- {k}: {v}")

    lines += [
        "",
        "## Where R2 helps",
        "",
        "- Clean human false alarms: R2 product/loss reduce false alarms vs original baseline (14/23 vs 4/23 accepted; 7 vs 17 false alarms).",
        "- Forensic-risk binary head (R2) is better calibrated for bonafide acceptance than v1 origin proxy.",
        "",
        "## Where original baseline remains stronger",
        "",
        "- **Direct AI:** baseline segment-suspicious signal (19/23) vs R2 file-level 0/23 detected.",
        "- **AI replay:** baseline 15/23 detected vs R2 0/23.",
        "- **Partial fabrication:** baseline 43/46 vs R2 product 33/46, R2 loss 36/46.",
        "",
        "## Conclusion",
        "",
        "No fine-tuned checkpoint is accepted standalone. Phase 7C4 threshold sweep and calibrated decision layer are required.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Phase 7C4 checkpoint comparison")
    add_phase7c4_calibration_args(
        p,
        output_csv=f"{P7}/phase7c4_calibration/calibration_outputs/phase7c4_checkpoint_comparison.csv",
        output_md=f"{P7}/phase7c4_calibration/phase7c4_checkpoint_comparison.md",
    )
    args = p.parse_args()
    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)

    baseline = merge_partial(load_results(Path(args.baseline_csv)), load_partial(Path(args.baseline_partial_csv) if args.baseline_partial_csv else None))
    r2_product = merge_partial(load_results(Path(args.r2_product_csv)), load_partial(Path(args.r2_product_partial_csv) if args.r2_product_partial_csv else None))
    r2_loss = merge_partial(load_results(Path(args.r2_loss_csv)), load_partial(Path(args.r2_loss_partial_csv) if args.r2_loss_partial_csv else None))

    merged = merge_three_checkpoints(baseline, r2_product, r2_loss)

    rows = []
    for _, row in merged.iterrows():
        sid = row["sample_id"]
        manip = row.get("manipulation_type_baseline", "")
        origin = row.get("source_origin_baseline", "")
        st_b = row.get("baseline_status_baseline", "")
        st_p = row.get("baseline_status_r2_product", "")
        st_l = row.get("baseline_status_r2_loss", "")
        rows.append({
            "sample_id": sid,
            "manipulation_type": manip,
            "source_origin": origin,
            "variant_id": row.get("variant_id_baseline", ""),
            "baseline_status_baseline": st_b,
            "baseline_status_r2_product": st_p,
            "baseline_status_r2_loss": st_l,
            "prediction_baseline": row.get("prediction_baseline", ""),
            "prediction_r2_product": row.get("prediction_r2_product", ""),
            "prediction_r2_loss": row.get("prediction_r2_loss", ""),
            "decision_score_baseline": row.get("decision_score_baseline", ""),
            "decision_score_r2_product": row.get("decision_score_r2_product", ""),
            "decision_score_r2_loss": row.get("decision_score_r2_loss", ""),
            "max_chunk_spoof_baseline": row.get("max_chunk_spoof_baseline", ""),
            "max_chunk_spoof_r2_product": row.get("max_chunk_spoof_r2_product", ""),
            "max_chunk_spoof_r2_loss": row.get("max_chunk_spoof_r2_loss", ""),
            "suspicious_chunk_ratio_baseline": row.get("suspicious_chunk_ratio_baseline", ""),
            "suspicious_chunk_ratio_r2_product": row.get("suspicious_chunk_ratio_r2_product", ""),
            "suspicious_chunk_ratio_r2_loss": row.get("suspicious_chunk_ratio_r2_loss", ""),
            "partial_region_detected_baseline": row.get("partial_region_detected_baseline", ""),
            "partial_region_detected_r2_product": row.get("partial_region_detected_r2_product", ""),
            "partial_region_detected_r2_loss": row.get("partial_region_detected_r2_loss", ""),
            "baseline_better": score_better_clean_human(st_b, st_p) == "baseline_better" if str(manip).lower() == "clean_direct" and str(origin).lower() == "human" else "",
            "r2_product_better": score_better_clean_human(st_b, st_p) == "r2_better" if str(manip).lower() == "clean_direct" and str(origin).lower() == "human" else "",
            "r2_loss_better": score_better_clean_human(st_b, st_l) == "r2_better" if str(manip).lower() == "clean_direct" and str(origin).lower() == "human" else "",
            "clean_human_r2_product_better": score_better_clean_human(st_b, st_p),
            "clean_human_r2_loss_better": score_better_clean_human(st_b, st_l),
            "disagreement_type": disagreement_type(row),
        })

    out = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")

    write_comparison_md(out_md, baseline, r2_product, r2_loss, out)
    print(f"[SAVE] {out_md}")


if __name__ == "__main__":
    main()
