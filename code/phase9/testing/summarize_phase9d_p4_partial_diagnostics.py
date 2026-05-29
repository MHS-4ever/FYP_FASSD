#!/usr/bin/env python3
"""Summarize Phase 9D-P4 partial timestamp diagnostic CSVs into summary + report."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path as _Path
from typing import Any

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9d_common import progress, repo_root, resolve_path
from phase9d_p4_common import write_summary_csv


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize Phase 9D-P4 partial diagnostics.")
    p.add_argument(
        "--diagnostics_dir",
        default="reports/phase9/testing/phase9d_p4_partial_diagnostics",
    )
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _read_csv(path: _Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _rate(num: int, denom: int) -> str:
    if denom <= 0:
        return "n/a"
    return f"{100.0 * num / denom:.1f}%"


def _as_bool(val: Any) -> bool:
    return str(val).strip().lower() in {"true", "1", "yes"}


def _recommendation(file_rows: list[dict[str, str]]) -> str:
    if not file_rows:
        return "insufficient_data_rerun_diagnostics"

    labels = [r.get("localization_diagnostic_label", "") for r in file_rows]
    broad = sum(1 for l in labels if l in {"broad_activation_not_localized", "topk_hits_but_broad_activation"})
    success = sum(1 for l in labels if l == "localized_success")
    boundary = sum(1 for l in labels if l == "boundary_only_signal")
    no_hit = sum(1 for l in labels if l == "no_timestamp_hit")
    total = len(file_rows)

    if success >= total * 0.4:
        return "gate_tuning_may_be_sufficient_review_thresholds"
    if boundary >= total * 0.3:
        return "investigate_splice_boundary_indicator_model"
    if broad >= total * 0.5:
        return "segment_retraining_with_non_partial_negatives_and_file_level_partial_candidate"
    if no_hit >= total * 0.5:
        return "segment_model_redesign_and_file_level_partial_candidate"
    return "combine_gate_tuning_with_file_level_partial_candidate_and_segment_retraining"


def _build_summary(file_rows: list[dict[str, str]]) -> dict[str, Any]:
    ai_rows = [r for r in file_rows if r.get("fabrication_direction") == "ai_fabricated"]
    human_rows = [r for r in file_rows if r.get("fabrication_direction") == "human_fabricated"]

    def count(rows: list[dict[str, str]], pred) -> int:
        return sum(1 for r in rows if pred(r))

    top5_hit = lambda r: _as_bool(r.get("top5_any_inside_true_region"))
    broad = lambda r: _as_bool(r.get("broad_activation_warning")) or r.get("localization_diagnostic_label") in {
        "broad_activation_not_localized",
        "topk_hits_but_broad_activation",
    }

    rec = _recommendation(file_rows)
    return {
        "total_partial_files": len(file_rows),
        "ai_fabricated_files": len(ai_rows),
        "human_fabricated_files": len(human_rows),
        "localized_success_count": count(file_rows, lambda r: r.get("localization_diagnostic_label") == "localized_success"),
        "top5_hit_count": count(file_rows, top5_hit),
        "broad_activation_count": count(file_rows, broad),
        "no_timestamp_hit_count": count(file_rows, lambda r: r.get("localization_diagnostic_label") == "no_timestamp_hit"),
        "ai_fabricated_top5_hit_rate": _rate(count(ai_rows, top5_hit), len(ai_rows)),
        "human_fabricated_top5_hit_rate": _rate(count(human_rows, top5_hit), len(human_rows)),
        "ai_fabricated_broad_activation_rate": _rate(count(ai_rows, broad), len(ai_rows)),
        "human_fabricated_broad_activation_rate": _rate(count(human_rows, broad), len(human_rows)),
        "recommendation": rec,
    }


def _write_report(
    path: _Path,
    summary: dict[str, Any],
    file_rows: list[dict[str, str]],
    boundary_rows: list[dict[str, str]],
) -> None:
    ai_rows = [r for r in file_rows if r.get("fabrication_direction") == "ai_fabricated"]
    human_rows = [r for r in file_rows if r.get("fabrication_direction") == "human_fabricated"]
    rec = summary.get("recommendation", "")

    rec_text = {
        "gate_tuning_may_be_sufficient_review_thresholds": "Gate tuning alone may help some cases, but verify broad-activation cases manually.",
        "investigate_splice_boundary_indicator_model": "Evidence suggests splice/boundary sensitivity; consider a dedicated boundary indicator.",
        "segment_retraining_with_non_partial_negatives_and_file_level_partial_candidate": "Broad activation dominates; segment retraining with non-partial negatives plus a file-level partial candidate model is likely needed.",
        "segment_model_redesign_and_file_level_partial_candidate": "Low timestamp hit rate; segment model redesign and file-level partial candidate recommended.",
        "combine_gate_tuning_with_file_level_partial_candidate_and_segment_retraining": "Mixed behavior; combine conservative gating, file-level partial candidate, and targeted segment retraining.",
        "insufficient_data_rerun_diagnostics": "Run Phase 9D-P4 diagnostics first.",
    }.get(str(rec), str(rec))

    lines = [
        "# Phase 9D-P4 Partial Timestamp Diagnostic Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "- Scope: **evaluation-only timestamp comparison** (timestamps never used as live inference input)",
        "",
        "## Purpose",
        "",
        "Compare live segment-level partial probabilities against true fabricated timestamp regions",
        "from Phase 7C1 annotations. This is diagnostic architecture verification, not final forensic proof.",
        "",
        "## Summary",
        "",
        f"- Total fabricated files: {summary.get('total_partial_files', 0)}",
        f"- AI fabricated: {summary.get('ai_fabricated_files', 0)}",
        f"- Human fabricated: {summary.get('human_fabricated_files', 0)}",
        f"- Localized success (top-1 inside region): {summary.get('localized_success_count', 0)}",
        f"- Top-5 timestamp hit count: {summary.get('top5_hit_count', 0)}",
        f"- Broad activation cases: {summary.get('broad_activation_count', 0)}",
        f"- No timestamp hit: {summary.get('no_timestamp_hit_count', 0)}",
        "",
        "## AI fabricated behavior",
        "",
        f"- Top-5 hit rate: {summary.get('ai_fabricated_top5_hit_rate', 'n/a')}",
        f"- Broad activation rate: {summary.get('ai_fabricated_broad_activation_rate', 'n/a')}",
        "",
    ]
    for row in ai_rows[:8]:
        lines.append(
            f"- `{row.get('case_id')}`: label={row.get('localization_diagnostic_label')}, "
            f"top5_inside={row.get('top5_any_inside_true_region')}, gate={row.get('partial_localization_gate')}"
        )

    lines.extend(
        [
            "",
            "## Human fabricated behavior",
            "",
            f"- Top-5 hit rate: {summary.get('human_fabricated_top5_hit_rate', 'n/a')}",
            f"- Broad activation rate: {summary.get('human_fabricated_broad_activation_rate', 'n/a')}",
            "",
        ]
    )
    for row in human_rows[:8]:
        lines.append(
            f"- `{row.get('case_id')}`: label={row.get('localization_diagnostic_label')}, "
            f"top5_inside={row.get('top5_any_inside_true_region')}, gate={row.get('partial_localization_gate')}"
        )

    lines.extend(
        [
            "",
            "## Top-k timestamp hit results",
            "",
            "Timestamp hit rate measures whether high-probability segments overlap the annotated fabricated region.",
            "This supports manual review planning only — not confirmed fake segment claims.",
            "",
            "## Broad activation results",
            "",
            "Broad activation indicates the partial segment model scores many segments similarly high,",
            "preventing localized partial-fabrication fusion eligibility under current gates.",
            "",
            "## Boundary / splice findings",
            "",
        ]
    )
    if boundary_rows:
        for brow in boundary_rows[:12]:
            lines.append(
                f"- `{brow.get('case_id')}` {brow.get('boundary_type')}: "
                f"nearest_p={brow.get('nearest_segment_probability')}, strength={brow.get('boundary_signal_strength')}"
            )
    else:
        lines.append("- (no boundary rows — run diagnostics first)")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- **Recommendation:** `{rec}`",
            f"- {rec_text}",
            "",
            "### Next steps (choose based on diagnostic rates)",
            "",
            "- **Gate tuning only:** if localized_success and top-5 hits are frequent but fusion gates are conservative.",
            "- **File-level partial candidate model:** if segment scores vary but file-level localization remains weak.",
            "- **Segment retraining with non-partial negatives:** if broad activation dominates across fabricated files.",
            "- **Splice/boundary indicator:** if boundary_only_signal is frequent near insert_start/end.",
            "",
            "Phase 9E apps may proceed after documenting this limitation; optional Phase 9D-P4 follow-up tuning is separate.",
            "",
            "## Safety",
            "",
            "- No single binary authenticity score was produced.",
            "- Timestamps used for evaluation only, never as model inputs.",
            "- Avoid terms like perfect detector or confirmed fake segment.",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _maybe_plot(
    diagnostics_dir: _Path,
    segment_rows: list[dict[str, str]],
    file_rows: list[dict[str, str]],
    no_progress: bool,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        progress("WARNING: matplotlib unavailable; skipping plots.", no_progress)
        return

    figures_dir = diagnostics_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in segment_rows:
        by_case[row.get("case_id", "")].append(row)

    file_lookup = {r.get("case_id"): r for r in file_rows}

    for case_id, rows in list(by_case.items())[:20]:
        if not case_id:
            continue
        meta = file_lookup.get(case_id, {})
        try:
            fab_start = float(meta.get("fabricated_start_sec", rows[0].get("fabricated_start_sec", 0)))
            fab_end = float(meta.get("fabricated_end_sec", rows[0].get("fabricated_end_sec", 0)))
        except (TypeError, ValueError):
            continue

        sorted_rows = sorted(rows, key=lambda r: float(r.get("start_sec", 0)))
        times = [(float(r["start_sec"]) + float(r["end_sec"])) / 2 for r in sorted_rows]
        probs = [float(r["partial_probability"]) if r.get("partial_probability") not in (None, "") else 0.0 for r in sorted_rows]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(times, probs, marker="o", markersize=3, linewidth=1)
        ax.axvspan(fab_start, fab_end, alpha=0.2, color="green", label="true fabricated region")
        for r in sorted(rows, key=lambda x: int(x.get("partial_rank", 999)))[:5]:
            mid = (float(r["start_sec"]) + float(r["end_sec"])) / 2
            ax.axvline(mid, color="orange", alpha=0.4, linewidth=0.8)
        ax.set_xlabel("time (sec)")
        ax.set_ylabel("partial_probability")
        ax.set_title(f"P4 diagnostic timeline: {case_id}")
        ax.legend(loc="upper right")
        fig.tight_layout()
        safe_name = case_id.replace("/", "_")[:80]
        fig.savefig(figures_dir / f"{safe_name}_timeline.png", dpi=120)
        plt.close(fig)

    progress(f"Wrote timeline plots under {figures_dir}", no_progress)


def summarize(args: argparse.Namespace) -> _Path:
    root = repo_root()
    diagnostics_dir = resolve_path(args.diagnostics_dir, root)
    file_rows = _read_csv(diagnostics_dir / "phase9d_p4_partial_file_diagnostics.csv")
    segment_rows = _read_csv(diagnostics_dir / "phase9d_p4_partial_segment_diagnostics.csv")
    boundary_rows = _read_csv(diagnostics_dir / "phase9d_p4_boundary_diagnostics.csv")

    summary = _build_summary(file_rows)
    write_summary_csv(diagnostics_dir / "phase9d_p4_partial_summary.csv", summary)
    report_path = diagnostics_dir / "phase9d_p4_partial_diagnostic_report.md"
    _write_report(report_path, summary, file_rows, boundary_rows)

    if args.make_plots and segment_rows:
        _maybe_plot(diagnostics_dir, segment_rows, file_rows, args.no_progress)

    progress(f"Summary: {diagnostics_dir / 'phase9d_p4_partial_summary.csv'}", args.no_progress)
    progress(f"Report: {report_path}", args.no_progress)
    return report_path


def main() -> int:
    args = parse_args()
    summarize(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
