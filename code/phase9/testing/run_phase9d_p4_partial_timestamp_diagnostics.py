#!/usr/bin/env python3
"""
Phase 9D-P4: compare live partial segment scores with evaluation-only fabricated timestamps.

Diagnostic only — timestamps are never model inputs.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path as _Path
from typing import Any

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9d_common import progress, repo_root, resolve_path
from phase9d_p4_common import (
    BOUNDARY_DIAG_COLUMNS,
    FILE_DIAG_COLUMNS,
    SEGMENT_DIAG_COLUMNS,
    assign_localization_diagnostic_label,
    build_boundary_rows,
    interpretation_for_label,
    load_timestamp_records,
    segment_overlap_metrics,
    write_csv,
    _safe_probs,
    _stats,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 9D-P4 partial timestamp diagnostics.")
    p.add_argument("--ai_timestamp_csv", default="data/phase7c1/raw/ai_fabricated/insertion_stamps.csv")
    p.add_argument("--human_timestamp_csv", default="data/phase7c1/raw/human_fabricated/insertion_stamps.csv")
    p.add_argument("--ai_audio_dir", default="data/phase7c1/raw/ai_fabricated")
    p.add_argument("--human_audio_dir", default="data/phase7c1/raw/human_fabricated")
    p.add_argument("--output_dir", default="reports/phase9/testing/phase9d_p4_partial_diagnostics")
    p.add_argument("--device", default="auto")
    p.add_argument("--max_files", type=int, default=0, help="0 = all timestamped files")
    p.add_argument("--top_k", type=int, default=5)
    p.add_argument("--overlap_threshold", type=float, default=0.25)
    p.add_argument("--continue_on_error", action="store_true", default=True)
    p.add_argument("--no_continue_on_error", action="store_false", dest="continue_on_error")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _build_file_diagnostic(
    record: dict[str, Any],
    segment_rows: list[dict[str, Any]],
    partial_evidence: dict[str, Any],
    inference_error: bool,
    top_k: int,
) -> dict[str, Any]:
    inside = [r for r in segment_rows if r.get("true_region_label") == "inside_fabricated_region"]
    outside = [r for r in segment_rows if r.get("true_region_label") == "outside_fabricated_region"]
    inside_probs = _safe_probs([r.get("partial_probability") for r in inside])
    outside_probs = _safe_probs([r.get("partial_probability") for r in outside])
    all_probs = _safe_probs([r.get("partial_probability") for r in segment_rows])

    max_in, mean_in, med_in = _stats(inside_probs)
    max_out, mean_out, med_out = _stats(outside_probs)
    inside_minus_mean = (mean_in - mean_out) if mean_in is not None and mean_out is not None else None
    inside_minus_max = (max_in - max_out) if max_in is not None and max_out is not None else None

    th = partial_evidence.get("threshold_candidate")
    high_frac = partial_evidence.get("high_segment_fraction")
    if high_frac is None and th is not None and all_probs:
        high_frac = sum(1 for p in all_probs if p >= float(th)) / len(all_probs)

    top_rows = [r for r in segment_rows if int(r.get("partial_rank", 999)) <= top_k]
    top5_inside = [r for r in top_rows if r.get("true_region_label") == "inside_fabricated_region"]
    top5_boundary = [r for r in top_rows if r.get("true_region_label") == "boundary_overlap"]
    inside_ranks = [int(r["partial_rank"]) for r in segment_rows if r.get("true_region_label") == "inside_fabricated_region" and r.get("partial_rank")]

    top1_inside = any(int(r.get("partial_rank", 0)) == 1 and r.get("true_region_label") == "inside_fabricated_region" for r in segment_rows)
    top3_inside = any(int(r.get("partial_rank", 0)) <= 3 and r.get("true_region_label") == "inside_fabricated_region" for r in segment_rows)
    top5_any_inside = len(top5_inside) > 0

    gate = str(partial_evidence.get("partial_localization_gate", ""))
    broad = bool(partial_evidence.get("broad_activation_warning"))

    label = assign_localization_diagnostic_label(
        inference_error=inference_error,
        partial_gate=gate,
        broad_activation=broad,
        top1_inside=top1_inside,
        top5_any_inside=top5_any_inside,
        top5_inside_count=len(top5_inside),
        top5_boundary_only=len(top5_boundary) > 0 and len(top5_inside) == 0,
    )

    std_prob = partial_evidence.get("probability_std")
    if std_prob is None and len(all_probs) > 1:
        mean_all = sum(all_probs) / len(all_probs)
        std_prob = (sum((p - mean_all) ** 2 for p in all_probs) / len(all_probs)) ** 0.5

    return {
        "case_id": record["case_id"],
        "audio_path": record["audio_path"],
        "fabrication_direction": record["fabrication_direction"],
        "fabricated_start_sec": record["fabricated_start_sec"],
        "fabricated_end_sec": record["fabricated_end_sec"],
        "segment_count": len(segment_rows),
        "inside_segment_count": len(inside),
        "outside_segment_count": len(outside),
        "max_prob_inside": max_in,
        "mean_prob_inside": mean_in,
        "median_prob_inside": med_in,
        "max_prob_outside": max_out,
        "mean_prob_outside": mean_out,
        "median_prob_outside": med_out,
        "inside_minus_outside_mean": inside_minus_mean,
        "inside_minus_outside_max": inside_minus_max,
        "probability_std": std_prob,
        "high_segment_fraction": high_frac,
        "top1_inside_true_region": top1_inside,
        "top3_any_inside_true_region": top3_inside,
        "top5_any_inside_true_region": top5_any_inside,
        "top5_inside_count": len(top5_inside),
        "best_rank_inside_region": min(inside_ranks) if inside_ranks else None,
        "partial_localization_gate": gate,
        "partial_fusion_eligible": partial_evidence.get("partial_fusion_eligible"),
        "broad_activation_warning": broad,
        "localization_diagnostic_label": label,
        "interpretation": interpretation_for_label(label),
    }


def run_diagnostics(args: argparse.Namespace) -> Path:
    root = repo_root()
    if str(root / "release") not in sys.path:
        sys.path.insert(0, str(root / "release"))
    from src.inference_pipeline import analyze_audio_file  # noqa: WPS433

    output_dir = resolve_path(args.output_dir, root)
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    records.extend(
        load_timestamp_records(
            resolve_path(args.ai_timestamp_csv, root),
            resolve_path(args.ai_audio_dir, root),
            "ai_fabricated",
            root,
        )
    )
    records.extend(
        load_timestamp_records(
            resolve_path(args.human_timestamp_csv, root),
            resolve_path(args.human_audio_dir, root),
            "human_fabricated",
            root,
        )
    )
    if args.max_files > 0:
        records = records[: args.max_files]

    segment_out: list[dict[str, Any]] = []
    file_out: list[dict[str, Any]] = []
    boundary_out: list[dict[str, Any]] = []

    for i, record in enumerate(records, start=1):
        case_id = f"p4_{record['fabrication_direction']}_{record['case_id']}"
        audio_abs = record["audio_path_abs"]
        progress(f"[{i}/{len(records)}] {case_id}", args.no_progress)

        partial_evidence: dict[str, Any] = {}
        scores: list[dict[str, Any]] = []
        inference_error = False

        try:
            if not _Path(audio_abs).is_file():
                raise FileNotFoundError(f"Audio not found: {audio_abs}")
            result = analyze_audio_file(
                audio_path=audio_abs,
                case_id=case_id,
                output_dir=None,
                device=args.device,
                return_debug=True,
            )
            if result.get("status") == "error":
                inference_error = True
            partial_evidence = result.get("partial_fabrication_evidence", {})
            debug = result.get("debug_info") or {}
            scores = list(debug.get("partial_segment_scores") or [])
        except Exception as exc:
            inference_error = True
            partial_evidence = {}
            scores = []
            progress(f"ERROR {case_id}: {exc}", args.no_progress)
            traceback.print_exc()
            if not args.continue_on_error:
                break

        fab_start = float(record["fabricated_start_sec"])
        fab_end = float(record["fabricated_end_sec"])
        file_segments: list[dict[str, Any]] = []

        for row in scores:
            seg_start = float(row.get("start_sec", 0))
            seg_end = float(row.get("end_sec", 0))
            overlap = segment_overlap_metrics(
                seg_start, seg_end, fab_start, fab_end, args.overlap_threshold
            )
            rank = int(row.get("partial_rank", 0))
            seg_row = {
                "case_id": case_id,
                "audio_path": record["audio_path"],
                "fabrication_direction": record["fabrication_direction"],
                "segment_id": row.get("segment_id"),
                "start_sec": seg_start,
                "end_sec": seg_end,
                "partial_probability": row.get("partial_probability"),
                "partial_rank": rank,
                "partial_above_threshold": row.get("partial_above_threshold"),
                "fabricated_start_sec": fab_start,
                "fabricated_end_sec": fab_end,
                "is_top1": rank == 1,
                "is_top3": rank <= 3,
                "is_top5": rank <= args.top_k,
                **overlap,
            }
            file_segments.append(seg_row)
            segment_out.append(seg_row)

        file_row = _build_file_diagnostic(
            record, file_segments, partial_evidence, inference_error, args.top_k
        )
        file_out.append(file_row)

        if file_segments and not inference_error:
            boundary_out.extend(
                build_boundary_rows(
                    case_id,
                    record["fabrication_direction"],
                    file_segments,
                    fab_start,
                    fab_end,
                )
            )

    write_csv(output_dir / "phase9d_p4_partial_segment_diagnostics.csv", segment_out, SEGMENT_DIAG_COLUMNS)
    write_csv(output_dir / "phase9d_p4_partial_file_diagnostics.csv", file_out, FILE_DIAG_COLUMNS)
    write_csv(output_dir / "phase9d_p4_boundary_diagnostics.csv", boundary_out, BOUNDARY_DIAG_COLUMNS)

    progress(f"Wrote {len(file_out)} file diagnostics to {output_dir}", args.no_progress)
    return output_dir


def main() -> int:
    args = parse_args()
    run_diagnostics(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
