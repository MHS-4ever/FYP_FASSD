#!/usr/bin/env python3
"""
Phase 8B — Build file/segment evidence tables from manifests (metadata only).

Does NOT train models, run inference, or fill evidence scores from labels.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_EVIDENCE_DIR = Path(__file__).resolve().parent
if str(_EVIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_EVIDENCE_DIR))

from phase8b_schema_utils import (  # noqa: E402
    FILE_TABLE_COLUMNS,
    REPO_ROOT,
    SEGMENT_TABLE_COLUMNS,
    SCHEMA_VERSION_DEFAULT,
    create_segments,
    empty_file_evidence_scores,
    empty_file_fusion_placeholders,
    empty_segment_placeholders,
    empty_segment_scores,
    get_audio_metadata,
    infer_audio_path,
    infer_origin_from_row,
    infer_segment_labels_available,
    infer_source_dataset,
    infer_split,
    make_file_id,
    normalize_column_names,
    normalize_manipulation_labels,
    parse_optional_float,
    resolve_audio_path,
    segment_overlaps_ground_truth,
    validate_allowed_labels,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Phase 8B evidence tables from manifests.")
    p.add_argument(
        "--input_manifests",
        nargs="+",
        required=True,
        help="One or more manifest CSV paths.",
    )
    p.add_argument(
        "--output_file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--output_segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument(
        "--build_report",
        default="reports/phase8/evidence_table/phase8b_build_report.md",
    )
    p.add_argument("--segment_length_sec", type=float, default=4.0)
    p.add_argument("--segment_hop_sec", type=float, default=2.0)
    p.add_argument(
        "--allow_missing_audio",
        action="store_true",
        help="Continue when audio file is missing; leave duration/sample_rate empty.",
    )
    p.add_argument("--schema_version", default=SCHEMA_VERSION_DEFAULT)
    return p.parse_args()


def _resolve_repo_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def build_tables(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_paths: list[Path] = []
    for raw in args.input_manifests:
        mp = _resolve_repo_path(raw)
        if not mp.is_file():
            errors.append(f"Manifest not found: {mp}")
            continue
        manifest_paths.append(mp)

    if not manifest_paths:
        raise SystemExit("No valid input manifests. Provide at least one existing CSV via --input_manifests.")

    file_rows: list[dict] = []
    segment_rows: list[dict] = []
    seen_file_ids: set[str] = set()

    for manifest_path in manifest_paths:
        df = normalize_column_names(pd.read_csv(manifest_path))
        try:
            rel_manifest = str(manifest_path.relative_to(REPO_ROOT))
        except ValueError:
            rel_manifest = str(manifest_path)

        for row_index, row in df.iterrows():
            file_id = make_file_id(row, manifest_path, int(row_index))
            if file_id in seen_file_ids:
                file_id = f"{file_id}_dup{len(seen_file_ids)}"
            seen_file_ids.add(file_id)

            audio_path = infer_audio_path(row) or ""
            known_origin = infer_origin_from_row(row)
            known_manip = normalize_manipulation_labels(row)
            label_warnings = validate_allowed_labels(known_origin, known_manip)
            for w in label_warnings:
                warnings.append(f"{file_id}: {w}")

            duration = parse_optional_float(row.get("duration_sec"))
            sample_rate = parse_optional_float(row.get("sample_rate"))
            if sample_rate is not None:
                sample_rate = int(sample_rate)

            if audio_path:
                if duration is None or sample_rate is None:
                    meta_dur, meta_sr = get_audio_metadata(audio_path)
                    if duration is None:
                        duration = meta_dur
                    if sample_rate is None and meta_sr is not None:
                        sample_rate = meta_sr

                if resolve_audio_path(audio_path) is None:
                    msg = f"{file_id}: audio not found at {audio_path}"
                    if args.allow_missing_audio:
                        warnings.append(msg)
                    else:
                        errors.append(msg)

            duration_str = "" if duration is None else f"{duration:.6f}".rstrip("0").rstrip(".")
            sr_str = "" if sample_rate is None else str(int(sample_rate))

            file_row: dict = {
                "schema_version": args.schema_version,
                "file_id": file_id,
                "audio_path": audio_path,
                "original_manifest_path": rel_manifest,
                "original_row_index": int(row_index),
                "duration_sec": duration_str,
                "sample_rate": sr_str,
                "source_dataset": infer_source_dataset(row, manifest_path),
                "split": infer_split(row, manifest_path),
                "known_origin_label": known_origin,
                "known_manipulation_labels": known_manip,
                "known_segment_labels_available": str(infer_segment_labels_available(row)).lower(),
                **empty_file_evidence_scores(),
                **empty_file_fusion_placeholders(),
                "evidence_source_paths": rel_manifest,
            }
            file_rows.append(file_row)

            if duration is None or duration <= 0:
                warnings.append(f"{file_id}: no duration_sec — segment rows skipped")
                continue

            gt_start = parse_optional_float(row.get("suspicious_start_time"))
            gt_end = parse_optional_float(row.get("suspicious_end_time"))
            has_gt_segment = infer_segment_labels_available(row)

            for seg in create_segments(duration, args.segment_length_sec, args.segment_hop_sec):
                seg_id = f"{file_id}_w{seg['segment_index']:04d}"
                seg_placeholders = empty_segment_placeholders()
                if has_gt_segment and segment_overlaps_ground_truth(
                    seg["start_sec"], seg["end_sec"], gt_start, gt_end
                ):
                    seg_placeholders["suspicious_segment_flag"] = "true"
                    seg_placeholders["segment_reason"] = "ground_truth_partial_region"
                seg_row = {
                    "schema_version": args.schema_version,
                    "file_id": file_id,
                    "segment_id": seg_id,
                    "audio_path": audio_path,
                    "start_sec": seg["start_sec"],
                    "end_sec": seg["end_sec"],
                    "segment_duration_sec": seg["segment_duration_sec"],
                    **empty_segment_scores(),
                    **seg_placeholders,
                }
                segment_rows.append(seg_row)

    if errors and not args.allow_missing_audio:
        raise SystemExit("Build aborted:\n" + "\n".join(errors))

    file_df = pd.DataFrame(file_rows, columns=FILE_TABLE_COLUMNS)
    segment_df = pd.DataFrame(segment_rows, columns=SEGMENT_TABLE_COLUMNS)
    return file_df, segment_df, warnings, errors


def write_build_report(
    path: Path,
    args: argparse.Namespace,
    file_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    warnings: list[str],
    errors: list[str],
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8B Build Report",
        "",
        f"**Generated:** {now}",
        f"**Schema version:** {args.schema_version}",
        "",
        "## Summary",
        "",
        f"- File rows: **{len(file_df)}**",
        f"- Segment rows: **{len(segment_df)}**",
        f"- Input manifests: {len(args.input_manifests)}",
        "",
        "## What this build did",
        "",
        "- Loaded manifest CSV(s) and normalized column names",
        "- Mapped known ground-truth labels to frozen Phase 8 vocabulary",
        "- Left all evidence score columns **empty** (not copied from labels)",
        "- Left fusion/calibration placeholders **empty** for Phase 8F",
        "- Created segment windows where `duration_sec` was available",
        "",
        "## What this build did NOT do",
        "",
        "- No model training or inference",
        "- No binary fake/real score",
        "- No filling of evidence scores from known labels",
        "",
        "## Outputs",
        "",
        f"- `{args.output_file_table}`",
        f"- `{args.output_segment_table}`",
        "",
        "## Parameters",
        "",
        f"- segment_length_sec: {args.segment_length_sec}",
        f"- segment_hop_sec: {args.segment_hop_sec}",
        f"- allow_missing_audio: {args.allow_missing_audio}",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {w}" for w in warnings[:200])
        if len(warnings) > 200:
            lines.append(f"- … and {len(warnings) - 200} more")
        lines.append("")
    if errors:
        lines.extend(["## Errors (non-fatal when allow_missing_audio)", ""])
        lines.extend(f"- {e}" for e in errors)
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    file_df, segment_df, warnings, errors = build_tables(args)

    out_file = _resolve_repo_path(args.output_file_table)
    out_seg = _resolve_repo_path(args.output_segment_table)
    out_report = _resolve_repo_path(args.build_report)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_seg.parent.mkdir(parents=True, exist_ok=True)

    file_df.to_csv(out_file, index=False)
    segment_df.to_csv(out_seg, index=False)
    write_build_report(out_report, args, file_df, segment_df, warnings, errors)

    print(f"Wrote {len(file_df)} file rows -> {out_file}")
    print(f"Wrote {len(segment_df)} segment rows -> {out_seg}")
    print(f"Build report -> {out_report}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
