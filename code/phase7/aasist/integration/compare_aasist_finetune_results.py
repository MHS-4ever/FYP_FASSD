"""
Phase 7E3C: Compare fine-tuned AASIST-L checkpoints vs pretrained AASIST-L and baselines.

Compares (Phase 7C1):
1) Pretrained AASIST-L (7E3A output)
2) Fine-tuned best_product
3) Fine-tuned best_loss
4) HybridResNet baseline
5) 7C4-v2 decision layer (context-only; not re-scored here)

Outputs:
- aasist_finetune_comparison.csv
- aasist_finetune_comparison.md
- aasist_finetune_recommendation.md

This script does not run inference; it only compares existing CSV outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from _common import ensure_dir, resolve_path, utc_now_iso, write_markdown
from analyze_aasist_pretrained_eval import (
    GATES_7C1,
    GATES_BRANCH,
    check_gates,
    compute_7c1_metrics,
    ensure_status_column,
    recommend_role_7c1,
)


def _load_predictions(path: Path, label: str) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    df = pd.read_csv(path)
    return ensure_status_column(df)


def _model_row(name: str, metrics: dict[str, int], gate: dict, branch: dict, role: str) -> dict[str, Any]:
    row: dict[str, Any] = {"model": name, "role_recommendation": role}
    row.update(metrics)
    for k, v in gate.items():
        row[f"gate_{k}_passed"] = bool(v["passed"])
        row[f"gate_{k}_value"] = int(v["value"])
    for k, v in branch.items():
        row[f"branch_{k}_passed"] = bool(v["passed"])
        row[f"branch_{k}_value"] = int(v["value"])
    return row


def _recommendation_type(role: str, clean_human_fa: int) -> str:
    if role == "standalone":
        return "accept_standalone_candidate"
    if role == "branch-only":
        return "accept_branch_only"
    if role == "needs_calibration":
        return "needs_threshold_calibration"
    if clean_human_fa > 10:
        return "reject_checkpoint"
    return "needs_more_data"


def write_comparison_md(rows: list[dict[str, Any]], out_md: Path) -> None:
    key_metrics = [
        "clean_human_false_alarm",
        "clean_human_accepted",
        "direct_ai_detected_or_segment_suspicious",
        "ai_replay_detected_or_segment_suspicious",
        "human_replay_detected",
        "human_mixer_detected",
        "ai_mixer_detected",
        "partial_fabrication_detected",
        "errors",
    ]
    lines = [
        "# Phase 7E3C — AASIST Fine-tune Comparison (Phase 7C1)",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Models compared",
        "",
        "| model | role_recommendation | " + " | ".join(key_metrics) + " |",
        "| --- | --- | " + " | ".join(["---"] * len(key_metrics)) + " |",
    ]
    for r in rows:
        lines.append(
            "| "
            + " | ".join([str(r.get("model", "")), str(r.get("role_recommendation", ""))] + [str(r.get(m, "")) for m in key_metrics])
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- These counts are computed from `aasist_status` (or reconstructed from predictions when missing).",
            "- Numeric gates are Phase 7E0 locked gates for Phase 7C1 only.",
            "",
        ]
    )
    write_markdown(out_md, lines)


def write_recommendation_md(summary: list[dict[str, Any]], out_md: Path) -> None:
    # Prefer best_product unless it violates clean-human hard gate (>10/23).
    best = next((r for r in summary if r["model"] == "finetuned_best_product"), None)
    alt = next((r for r in summary if r["model"] == "finetuned_best_loss"), None)
    pre = next((r for r in summary if r["model"] == "pretrained"), None)

    chosen = best or alt or pre
    if best and int(best.get("clean_human_false_alarm", 99)) > 10 and alt:
        chosen = alt

    rec_type = _recommendation_type(str(chosen.get("role_recommendation", "")), int(chosen.get("clean_human_false_alarm", 99)))

    lines = [
        "# Phase 7E3C — Fine-tuned AASIST-L Recommendation",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        f"## Recommendation: **{rec_type}**",
        "",
        "## Chosen checkpoint (Phase 7C1)",
        "",
        f"- model: **{chosen.get('model')}**",
        f"- role_recommendation: **{chosen.get('role_recommendation')}**",
        f"- clean_human_false_alarm: **{chosen.get('clean_human_false_alarm')}** / 23",
        f"- direct_ai_detected_or_segment_suspicious: **{chosen.get('direct_ai_detected_or_segment_suspicious')}** / 23",
        "",
        "## Next steps",
        "",
        "- If recommendation is not reject: run Phase 7A holdout eval in a new output folder and compare to Hybrid + 7C4-v2.",
        "- If clean-human false alarms remain high: do not accept checkpoint; adjust training design (sampler/weights/lr/data) rather than threshold tuning on holdout.",
        "",
    ]
    write_markdown(out_md, lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E3C: Compare fine-tuned AASIST results (no inference).")
    parser.add_argument(
        "--pretrained_phase7c1_csv",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv",
    )
    parser.add_argument("--finetuned_best_product_phase7c1_csv", type=str, required=True)
    parser.add_argument("--finetuned_best_loss_phase7c1_csv", type=str, required=True)
    parser.add_argument("--hybrid_phase7c1_csv", type=str, default="reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv")
    parser.add_argument(
        "--decision_phase7c4_v2_csv",
        type=str,
        default="reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv",
    )
    parser.add_argument("--output_dir", type=str, required=True)
    args = parser.parse_args()

    out_dir = ensure_dir(resolve_path(args.output_dir))

    pretrained_df = _load_predictions(resolve_path(args.pretrained_phase7c1_csv), "pretrained_phase7c1_csv")
    best_prod_df = _load_predictions(resolve_path(args.finetuned_best_product_phase7c1_csv), "finetuned_best_product_phase7c1_csv")
    best_loss_df = _load_predictions(resolve_path(args.finetuned_best_loss_phase7c1_csv), "finetuned_best_loss_phase7c1_csv")

    models = [
        ("pretrained", pretrained_df),
        ("finetuned_best_product", best_prod_df),
        ("finetuned_best_loss", best_loss_df),
    ]

    summary_rows: list[dict[str, Any]] = []
    for name, df in models:
        metrics = compute_7c1_metrics(df)
        gate = check_gates(metrics, GATES_7C1)
        branch = check_gates(metrics, GATES_BRANCH)
        role = recommend_role_7c1(gate, branch)
        summary_rows.append(_model_row(name, metrics, gate, branch, role))

    out_csv = out_dir / "aasist_finetune_comparison.csv"
    pd.DataFrame(summary_rows).to_csv(out_csv, index=False)

    write_comparison_md(summary_rows, out_dir / "aasist_finetune_comparison.md")
    write_recommendation_md(summary_rows, out_dir / "aasist_finetune_recommendation.md")

    # Context-only pointers for downstream review (not parsed here).
    write_markdown(
        out_dir / "context_inputs.md",
        [
            "# Phase 7E3C — Context inputs",
            "",
            "These are not re-scored by this script, but are required for the final decision review:",
            "",
            f"- Hybrid baseline (Phase 7C1): `{args.hybrid_phase7c1_csv}`",
            f"- 7C4-v2 decision layer: `{args.decision_phase7c4_v2_csv}`",
            "",
        ],
    )

    print(f"Wrote: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

