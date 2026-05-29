#!/usr/bin/env python3
"""
Phase 9D: summarize batch inference behavior vs expected categories.

Architecture verification only — not final accuracy claims.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase9d_common import progress, repo_root, resolve_path

ELEVATED_FUSIONS = {
    "suspicious_origin_experimental",
    "suspicious_replay_experimental",
    "suspicious_mixer_channel_experimental",
    "suspicious_partial_fabrication_experimental",
    "suspicious_mixed_evidence_experimental",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize Phase 9D batch test results.")
    p.add_argument("--manifest", default="reports/phase9/testing/phase9d_test_manifest.csv")
    p.add_argument("--batch_results", default="reports/phase9/testing/phase9d_batch_results.csv")
    p.add_argument("--outputs_dir", default="reports/phase9/testing/phase9d_outputs")
    p.add_argument("--output_dir", default="reports/phase9/testing")
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _as_bool(val: Any) -> bool | None:
    if isinstance(val, bool):
        return val
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in {"true", "1", "yes"}:
        return True
    if s in {"false", "0", "no"}:
        return False
    return None


def classify_axis_consistency(
    expected_category: str,
    fusion_status: str,
    run_status: str,
    partial_gate: str,
    partial_fusion_eligible: Any,
    partial_block: str,
) -> str:
    if run_status in {"exception", "pipeline_error"}:
        if expected_category.startswith("bad_audio"):
            return "expected"
        return "pipeline_error"

    fusion = fusion_status or ""
    eligible = _as_bool(partial_fusion_eligible)

    if expected_category == "ai_direct":
        if fusion == "suspicious_origin_experimental":
            return "expected"
        if fusion == "inconclusive_manual_review_experimental":
            return "acceptable_with_manual_review"
        return "unexpected_axis"

    if expected_category == "human_direct":
        if fusion in {"accept_human_clean_experimental", "inconclusive_manual_review_experimental"}:
            return "expected" if fusion == "accept_human_clean_experimental" else "acceptable_with_manual_review"
        if fusion.startswith("suspicious_"):
            return "needs_review"
        return "acceptable_with_manual_review"

    if expected_category in {"ai_replay", "human_replay", "replay"}:
        if fusion == "suspicious_replay_experimental":
            return "expected"
        if fusion == "suspicious_mixed_evidence_experimental" and eligible is False:
            return "needs_review"
        return "unexpected_axis"

    if expected_category in {"ai_mixer", "human_mixer", "mixer_channel"}:
        if fusion == "suspicious_mixer_channel_experimental":
            return "expected"
        if fusion == "suspicious_mixed_evidence_experimental" and eligible is False:
            return "needs_review"
        return "unexpected_axis"

    if expected_category in {"ai_fabricated", "human_fabricated"}:
        if fusion == "suspicious_partial_fabrication_experimental" and eligible is True:
            return "expected"
        if partial_gate == "global_activation_not_localized":
            return "needs_review"
        if fusion in ELEVATED_FUSIONS:
            return "acceptable_with_manual_review"
        return "needs_review"

    if expected_category.startswith("bad_audio"):
        if run_status == "ok" and fusion == "inconclusive_manual_review_experimental":
            return "acceptable_with_manual_review"
        if run_status in {"exception", "pipeline_error"}:
            return "expected"
        return "acceptable_with_manual_review"

    if expected_category == "unknown":
        return "needs_review"

    return "needs_review"


def _partial_interpretation(row: dict[str, Any]) -> str:
    gate = str(row.get("partial_localization_gate", ""))
    block = str(row.get("partial_fusion_block_reason", ""))
    broad = row.get("broad_activation_warning")
    eligible = row.get("partial_fusion_eligible")
    if gate == "global_activation_not_localized" or broad is True:
        return "Broad segment activation; localized partial region not supported (known limitation)."
    if block == "blocked_by_replay_or_mixer_context":
        return "Partial blocked under replay/mixer context (conservative arbitration)."
    if eligible is True and gate == "localized_pattern_supported":
        return "Localized partial pattern supported and fusion-eligible."
    if gate == "weak_localization_contrast":
        return "High scores without sufficient localization contrast."
    if gate == "low_partial_indicator":
        return "Low partial indicator across segments."
    return "Review partial metrics for experimental localization support."


def summarize(args: argparse.Namespace) -> Path:
    root = repo_root()
    manifest_rows = _load_csv(resolve_path(args.manifest, root))
    batch_rows = _load_csv(resolve_path(args.batch_results, root))
    outputs_dir = resolve_path(args.outputs_dir, root)
    output_dir = resolve_path(args.output_dir, root)
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_by_case = {r["case_id"]: r for r in manifest_rows if r.get("case_id")}
    summary_rows: list[dict[str, Any]] = []
    partial_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    category_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for batch in batch_rows:
        case_id = batch.get("case_id", "")
        manifest = manifest_by_case.get(case_id, {})
        expected_category = batch.get("expected_category") or manifest.get("expected_category", "unknown")
        fusion = batch.get("experimental_fusion_status", "")
        run_status = batch.get("run_status", "")
        partial_gate = batch.get("partial_localization_gate", "")
        partial_eligible = batch.get("partial_fusion_eligible", "")
        partial_block = batch.get("partial_fusion_block_reason", "")

        consistency = classify_axis_consistency(
            expected_category,
            fusion,
            run_status,
            partial_gate,
            partial_eligible,
            partial_block,
        )

        json_path = Path(batch.get("output_json", outputs_dir / f"{case_id}_analysis.json"))
        if not json_path.is_absolute():
            json_path = (root / json_path).resolve()
        payload = _load_json(json_path)
        partial = payload.get("partial_fabrication_evidence", {})

        summary_rows.append(
            {
                "case_id": case_id,
                "expected_category": expected_category,
                "expected_primary_axis": manifest.get("expected_primary_axis", ""),
                "run_status": run_status,
                "experimental_fusion_status": fusion,
                "axis_consistency": consistency,
                "partial_localization_gate": partial_gate,
                "partial_fusion_eligible": partial_eligible,
                "partial_fusion_block_reason": partial_block,
                "manual_review_required": batch.get("manual_review_required", ""),
                "successful_axis_predictions": batch.get("successful_axis_predictions", ""),
                "notes": manifest.get("notes", ""),
            }
        )

        partial_rows.append(
            {
                "case_id": case_id,
                "expected_category": expected_category,
                "partial_localization_gate": partial_gate,
                "partial_fusion_eligible": partial_eligible,
                "partial_fusion_block_reason": partial_block,
                "high_segment_fraction": partial.get("high_segment_fraction", batch.get("high_segment_fraction", "")),
                "topk_minus_rest_probability": partial.get("topk_minus_rest_probability", ""),
                "probability_std": partial.get("probability_std", ""),
                "broad_activation_warning": partial.get("broad_activation_warning", ""),
                "segment_candidate_count": batch.get("segment_candidate_count", ""),
                "interpretation": _partial_interpretation(
                    {
                        "partial_localization_gate": partial_gate,
                        "partial_fusion_block_reason": partial_block,
                        "broad_activation_warning": partial.get("broad_activation_warning"),
                        "partial_fusion_eligible": partial_eligible,
                    }
                ),
            }
        )

        category_stats[expected_category]["total"] += 1
        category_stats[expected_category][consistency] += 1
        if run_status != "ok":
            failures.append({**batch, "axis_consistency": consistency})
        elif consistency in {"unexpected_axis", "pipeline_error"}:
            failures.append({**batch, "axis_consistency": consistency})

    def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str] | None = None) -> Path:
        path = output_dir / name
        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        cols = columns or list(rows[0].keys())
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return path

    summary_csv = _write_csv("phase9d_test_summary.csv", summary_rows)
    partial_csv = _write_csv("phase9d_partial_behavior_review.csv", partial_rows)
    failure_csv = _write_csv("phase9d_failure_cases.csv", failures)

    category_rows: list[dict[str, Any]] = []
    for category, stats in sorted(category_stats.items()):
        total = stats.get("total", 0)
        category_rows.append(
            {
                "expected_category": category,
                "case_count": total,
                "expected_count": stats.get("expected", 0),
                "acceptable_with_manual_review": stats.get("acceptable_with_manual_review", 0),
                "unexpected_axis": stats.get("unexpected_axis", 0),
                "pipeline_error": stats.get("pipeline_error", 0),
                "needs_review": stats.get("needs_review", 0),
            }
        )
    category_csv = _write_csv("phase9d_category_behavior_summary.csv", category_rows)

    if args.make_plots and summary_rows:
        _maybe_make_plots(figures_dir, category_rows, args.no_progress)

    report_path = output_dir / "phase9d_end_to_end_test_report.md"
    _write_report(
        report_path,
        manifest_rows,
        batch_rows,
        summary_rows,
        category_rows,
        partial_rows,
        failures,
    )

    progress(f"Summary CSV: {summary_csv}", args.no_progress)
    progress(f"Category summary: {category_csv}", args.no_progress)
    progress(f"Partial review: {partial_csv}", args.no_progress)
    progress(f"Failures: {failure_csv}", args.no_progress)
    progress(f"Report: {report_path}", args.no_progress)
    return report_path


def _maybe_make_plots(figures_dir: Path, category_rows: list[dict[str, Any]], no_progress: bool) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        progress("WARNING: matplotlib not available; skipping plots.", no_progress)
        return

    figures_dir.mkdir(parents=True, exist_ok=True)
    categories = [r["expected_category"] for r in category_rows]
    expected_counts = [int(r.get("expected_count", 0)) for r in category_rows]
    review_counts = [int(r.get("needs_review", 0)) for r in category_rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(categories))
    ax.bar(x, expected_counts, label="expected")
    ax.bar(x, review_counts, bottom=expected_counts, label="needs_review")
    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, rotation=45, ha="right")
    ax.set_title("Phase 9D axis consistency by category (behavior check)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "phase9d_category_consistency.png", dpi=120)
    plt.close(fig)
    progress(f"Wrote plot: {figures_dir / 'phase9d_category_consistency.png'}", no_progress)


def _write_report(
    path: Path,
    manifest_rows: list[dict[str, str]],
    batch_rows: list[dict[str, str]],
    summary_rows: list[dict[str, Any]],
    category_rows: list[dict[str, Any]],
    partial_rows: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    total = len(batch_rows) if batch_rows else len(manifest_rows)
    ok = sum(1 for r in batch_rows if r.get("run_status") == "ok")
    failed = total - ok
    expected_n = sum(1 for r in summary_rows if r.get("axis_consistency") == "expected")
    review_n = sum(1 for r in summary_rows if r.get("axis_consistency") == "needs_review")

    examples_ok = [r for r in summary_rows if r.get("axis_consistency") == "expected"][:5]
    examples_review = [r for r in summary_rows if r.get("axis_consistency") in {"needs_review", "unexpected_axis"}][:5]

    lines = [
        "# Phase 9D End-to-End Test Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "- Status: **experimental architecture verification** (not production-ready, not court-ready proof)",
        "",
        "## Purpose",
        "",
        "Phase 9D verifies that the Phase 9C live inference pipeline runs end-to-end on controlled",
        "testing audios, that evidence axes remain separate, and that fusion behavior is logically",
        "consistent with expected categories before FastAPI/Gradio finalization (Phase 9E).",
        "",
        "## Run summary",
        "",
        f"- Manifest cases: {len(manifest_rows)}",
        f"- Batch rows: {total}",
        f"- Successful runs (`run_status=ok`): {ok}",
        f"- Failed/errored runs: {failed}",
        f"- Expected-axis consistency (`expected`): {expected_n}",
        f"- Cases needing review: {review_n}",
        "",
        "## Category-wise behavior",
        "",
        "| Category | Cases | Expected | Acceptable review | Unexpected | Pipeline error | Needs review |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in category_rows:
        lines.append(
            f"| {row['expected_category']} | {row['case_count']} | {row['expected_count']} | "
            f"{row['acceptable_with_manual_review']} | {row['unexpected_axis']} | "
            f"{row['pipeline_error']} | {row['needs_review']} |"
        )

    lines.extend(
        [
            "",
            "## Partial fabrication review (known limitation)",
            "",
            "Partial fabrication localization remains a known limitation in this release verification.",
            "On many fabricated test cases, the live partial segment model produces **broad activation**",
            "(`global_activation_not_localized`) rather than a localized region. Fabricated cases therefore",
            "mostly require manual review; treating broad activation as localized fabrication would",
            "overclaim evidence. This conservative behavior is safer than overclaiming localized fabrication.",
            "Replay/mixer context can also block `partial_fusion_eligible` under strict arbitration rules.",
            "",
            "Phase 9E apps may proceed only after this limitation is documented in review outputs.",
            "Optional Phase 9D-P4 can tune partial handling later; it is not required to unblock app wiring.",
            "",
            "| Case | Category | Gate | Fusion eligible | Block reason |",
            "|---|---|---|---|---|",
        ]
    )
    for row in partial_rows[:20]:
        lines.append(
            f"| {row['case_id']} | {row['expected_category']} | {row['partial_localization_gate']} | "
            f"{row['partial_fusion_eligible']} | {row['partial_fusion_block_reason']} |"
        )
    if len(partial_rows) > 20:
        lines.append(f"| ... | ({len(partial_rows) - 20} more rows in CSV) | | | |")

    lines.extend(["", "## Examples of expected behavior", ""])
    if examples_ok:
        for ex in examples_ok:
            lines.append(
                f"- `{ex['case_id']}` ({ex['expected_category']}): fusion `{ex['experimental_fusion_status']}`"
            )
    else:
        lines.append("- (none recorded yet — run batch inference first)")

    lines.extend(["", "## Examples needing review", ""])
    if examples_review:
        for ex in examples_review:
            lines.append(
                f"- `{ex['case_id']}` ({ex['expected_category']}): fusion `{ex['experimental_fusion_status']}`, "
                f"consistency `{ex['axis_consistency']}`"
            )
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- No single binary authenticity score was produced; evidence axes remain separate.",
            "- No single fake/real decision field is emitted.",
            "- AASIST/HybridResNet reference models remain inactive.",
            "- Partial localization is experimental; broad activation is documented, not proof of a localized region.",
            "- Category-to-fusion mappings are behavior checks, not validated forensic accuracy.",
            "",
            "## Recommendation before Phase 9E",
            "",
            "1. Review `phase9d_failure_cases.csv` and `phase9d_partial_behavior_review.csv`.",
            "2. Confirm mixer/replay cases do not become `suspicious_mixed` solely due to partial overfire.",
            "3. Confirm fabricated cases are flagged for review when partial gates show broad activation.",
            "4. Re-run batch inference after limitation wording fixes so JSON/Markdown outputs pass validation.",
            "5. Proceed to FastAPI/Gradio only after manual review of this report and validation PASS.",
            "",
        ]
    )

    if failures:
        lines.extend(["## Failure / unexpected cases", ""])
        for frow in failures[:15]:
            lines.append(
                f"- `{frow.get('case_id')}`: run_status={frow.get('run_status')}, "
                f"fusion={frow.get('experimental_fusion_status')}, consistency={frow.get('axis_consistency')}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    summarize(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
