#!/usr/bin/env python3
"""
Phase 9D: batch run Phase 9C live inference on manifest rows.

Does not train/refit/package models or launch apps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import csv
import traceback
from pathlib import Path
from typing import Any

from phase9d_common import ensure_repo_on_path, progress, repo_root, resolve_path

BATCH_COLUMNS = [
    "case_id",
    "audio_path",
    "expected_category",
    "run_status",
    "error_message",
    "experimental_fusion_status",
    "forensic_risk_level",
    "manual_review_required",
    "origin_probability",
    "replay_probability",
    "mixer_probability",
    "partial_raw_max_segment_probability",
    "partial_gated_probability",
    "partial_localization_gate",
    "partial_fusion_eligible",
    "partial_fusion_block_reason",
    "segment_candidate_count",
    "successful_axis_predictions",
    "output_json",
    "output_report",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Phase 9D batch inference on manifest.")
    p.add_argument("--manifest", default="reports/phase9/testing/phase9d_test_manifest.csv")
    p.add_argument("--output_dir", default="reports/phase9/testing/phase9d_outputs")
    p.add_argument("--release_sample_outputs", default="release/sample_outputs")
    p.add_argument("--device", default="auto")
    p.add_argument("--continue_on_error", action="store_true", default=True)
    p.add_argument("--no_continue_on_error", action="store_false", dest="continue_on_error")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _prob(axis: dict[str, Any]) -> Any:
    return axis.get("probability")


def _successful_axis_count(result: dict[str, Any]) -> int:
    count = 0
    for key in ("origin_evidence", "replay_evidence", "mixer_channel_evidence"):
        if result.get(key, {}).get("prediction_success"):
            count += 1
    if result.get("partial_fabrication_evidence", {}).get("prediction_success"):
        count += 1
    return count


def _row_from_result(
    manifest_row: dict[str, str],
    result: dict[str, Any],
    json_path: Path,
    md_path: Path,
    run_status: str,
    error_message: str,
) -> dict[str, Any]:
    partial = result.get("partial_fabrication_evidence", {})
    return {
        "case_id": manifest_row.get("case_id", result.get("case_id")),
        "audio_path": manifest_row.get("audio_path", ""),
        "expected_category": manifest_row.get("expected_category", ""),
        "run_status": run_status,
        "error_message": error_message,
        "experimental_fusion_status": result.get("fusion_status", ""),
        "forensic_risk_level": result.get("forensic_risk_level", ""),
        "manual_review_required": result.get("manual_review_required", ""),
        "origin_probability": _prob(result.get("origin_evidence", {})),
        "replay_probability": _prob(result.get("replay_evidence", {})),
        "mixer_probability": _prob(result.get("mixer_channel_evidence", {})),
        "partial_raw_max_segment_probability": partial.get("raw_max_segment_probability"),
        "partial_gated_probability": partial.get("gated_partial_probability"),
        "partial_localization_gate": partial.get("partial_localization_gate", ""),
        "partial_fusion_eligible": partial.get("partial_fusion_eligible", ""),
        "partial_fusion_block_reason": partial.get("partial_fusion_block_reason", ""),
        "segment_candidate_count": len(result.get("segment_candidates", [])),
        "successful_axis_predictions": _successful_axis_count(result),
        "output_json": str(json_path).replace("\\", "/"),
        "output_report": str(md_path).replace("\\", "/"),
    }


def run_batch(args: argparse.Namespace) -> Path:
    root = ensure_repo_on_path()
    release_dir = root / "release"
    if str(release_dir) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(release_dir))

    from src.inference_pipeline import analyze_audio_file  # noqa: WPS433
    from src.utils import write_json, write_markdown  # noqa: WPS433

    manifest_path = resolve_path(args.manifest, root)
    output_dir = resolve_path(args.output_dir, root)
    batch_csv = output_dir.parent / "phase9d_batch_results.csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        manifest_rows = list(csv.DictReader(fh))

    batch_rows: list[dict[str, Any]] = []
    for i, row in enumerate(manifest_rows, start=1):
        case_id = row.get("case_id") or f"phase9d_case_{i:03d}"
        audio_path = resolve_path(row.get("audio_path", ""), root)
        json_path = output_dir / f"{case_id}_analysis.json"
        md_path = output_dir / f"{case_id}_report.md"

        progress(f"[{i}/{len(manifest_rows)}] {case_id} -> {audio_path.name}", args.no_progress)

        result: dict[str, Any] = {"case_id": case_id, "status": "error"}
        error_message = ""
        run_status = "ok"

        try:
            if not audio_path.is_file():
                raise FileNotFoundError(f"Audio not found: {audio_path}")
            result = analyze_audio_file(
                audio_path=str(audio_path),
                case_id=case_id,
                output_dir=None,
                device=args.device,
                return_debug=False,
            )
            if result.get("status") == "error":
                run_status = "pipeline_error"
                error_message = str(result.get("forensic_summary", "pipeline returned error status"))
            write_json(json_path, result)
            write_markdown(md_path, result.get("report_markdown", ""))
        except Exception as exc:
            run_status = "exception"
            error_message = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
            result = {
                "case_id": case_id,
                "status": "error",
                "forensic_summary": error_message,
                "fusion_status": "inconclusive_manual_review_experimental",
                "partial_fabrication_evidence": {},
                "segment_candidates": [],
            }
            write_json(json_path, result)
            write_markdown(md_path, f"# Error\n\n{error_message}\n")
            if not args.continue_on_error:
                batch_rows.append(
                    _row_from_result(row, result, json_path, md_path, run_status, error_message)
                )
                break

        batch_rows.append(_row_from_result(row, result, json_path, md_path, run_status, error_message))

    with batch_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=BATCH_COLUMNS)
        writer.writeheader()
        writer.writerows(batch_rows)

    ok_count = sum(1 for r in batch_rows if r["run_status"] == "ok")
    progress(f"Batch complete: {ok_count}/{len(batch_rows)} ok", args.no_progress)
    progress(f"Results CSV: {batch_csv}", args.no_progress)
    return batch_csv


def main() -> int:
    args = parse_args()
    run_batch(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
