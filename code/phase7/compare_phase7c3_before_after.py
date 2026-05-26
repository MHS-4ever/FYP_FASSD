"""
Phase 7C3: Compare before/after fine-tuning on Phase 7C1 baseline and Phase 7A holdout.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7_paths import BASELINE_RESULTS, HOLDOUT_PRODUCT, resolve_phase7_report_path  # noqa: E402

# Phase 7C1 baseline_status values
P7C1_STATUSES = [
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

# Phase 7A product_status values (additional / overlapping)
P7A_PRODUCT_STATUSES = [
    "clean_human_accepted",
    "clean_human_borderline",
    "clean_human_false_alarm",
    "direct_ai_detected",
    "direct_ai_missed",
    "direct_ai_file_level_missed_but_segment_suspicious",
    "direct_ai_borderline",
    "processed_human_manipulation_detected",
    "processed_human_missed",
    "ai_replay_or_processed_detected",
    "ai_replay_or_processed_missed",
    "ai_replay_file_level_missed_but_segment_suspicious",
    "processed_ai_file_level_missed_but_segment_suspicious",
    "partial_fabrication_detected",
    "partial_fabrication_missed",
    "partial_not_evaluated_missing_timestamp",
    "unknown_review_required",
]

KEY_STATUSES = sorted(set(P7C1_STATUSES + P7A_PRODUCT_STATUSES))


def _status_counts(path: Path, col: str = "baseline_status") -> Counter:
    resolved = resolve_phase7_report_path(path)
    if not resolved.is_file():
        return Counter()
    df = pd.read_csv(resolved, low_memory=False)
    if col not in df.columns:
        if "product_status" in df.columns:
            col = "product_status"
        else:
            return Counter()
    return Counter(df[col].fillna("").astype(str))


def _md_table(headers, rows):
    if not rows:
        return "_No data._\n"
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"


def compare_counts(before: Counter, after: Counter, label: str) -> list[str]:
    lines = [f"## {label}", ""]
    rows = []
    for st in KEY_STATUSES:
        b, a = before.get(st, 0), after.get(st, 0)
        if b or a:
            rows.append([st, b, a, a - b])
    lines.append(_md_table(["status", "before", "after", "delta"], rows))
    return lines


def assess_acceptance(before_p7c1: Counter, after_p7c1: Counter) -> list[str]:
    lines = ["## Acceptance assessment (heuristic)", ""]
    fp_before = before_p7c1.get("clean_human_false_alarm", 0)
    fp_after = after_p7c1.get("clean_human_false_alarm", 0)
    ai_before = before_p7c1.get("direct_ai_detected", 0)
    ai_after = after_p7c1.get("direct_ai_detected", 0)
    partial_before = before_p7c1.get("partial_fabrication_detected", 0)
    partial_after = after_p7c1.get("partial_fabrication_detected", 0)

    checks = [
        ("Clean human false alarms decrease", fp_after < fp_before, f"{fp_before} -> {fp_after}"),
        ("Direct AI detected increases", ai_after > ai_before, f"{ai_before} -> {ai_after}"),
        (
            "Partial fabrication detection stable",
            partial_after >= partial_before - 3,
            f"{partial_before} -> {partial_after}",
        ),
    ]
    for name, ok, detail in checks:
        lines.append(f"- [{'x' if ok else ' '}] {name}: {detail}")
    lines.append("")
    lines.append("Review Phase 7A `product_status` table above before accepting checkpoint.")
    lines.append("")
    return lines


def main():
    p = argparse.ArgumentParser(description="Phase 7C3 — before/after comparison")
    p.add_argument("--before_phase7c1", type=str, default=BASELINE_RESULTS)
    p.add_argument("--after_phase7c1", type=str, required=True)
    p.add_argument("--before_phase7a", type=str, default=HOLDOUT_PRODUCT)
    p.add_argument("--after_phase7a", type=str, default="")
    p.add_argument("--output_md", type=str, required=True)
    args = p.parse_args()

    before_p7c1 = _status_counts(Path(args.before_phase7c1), "baseline_status")
    after_p7c1 = _status_counts(Path(args.after_phase7c1), "baseline_status")
    before_p7a = _status_counts(Path(args.before_phase7a), "product_status") if args.before_phase7a else Counter()
    after_p7a = _status_counts(Path(args.after_phase7a), "product_status") if args.after_phase7a else Counter()

    lines = [
        "# Phase 7C3 — Before / After Fine-Tuning Comparison",
        "",
        "Phase 7C1 uses `baseline_status`; Phase 7A holdout uses `product_status`.",
        "",
    ]
    lines.extend(compare_counts(before_p7c1, after_p7c1, "Phase 7C1 (baseline_status)"))
    if before_p7a or after_p7a:
        lines.extend(compare_counts(before_p7a, after_p7a, "Phase 7A holdout (product_status)"))
    lines.extend(assess_acceptance(before_p7c1, after_p7c1))

    out = resolve_phase7_report_path(args.output_md, for_write=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVE] {out}")


if __name__ == "__main__":
    main()
