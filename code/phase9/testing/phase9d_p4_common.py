"""Shared helpers for Phase 9D-P4 partial timestamp diagnostics (evaluation only)."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import pandas as pd

from phase9d_common import progress


SEGMENT_DIAG_COLUMNS = [
    "case_id",
    "audio_path",
    "fabrication_direction",
    "segment_id",
    "start_sec",
    "end_sec",
    "partial_probability",
    "partial_rank",
    "partial_above_threshold",
    "fabricated_start_sec",
    "fabricated_end_sec",
    "overlap_sec",
    "overlap_ratio_segment",
    "true_region_label",
    "distance_to_fabricated_region_sec",
    "is_top1",
    "is_top3",
    "is_top5",
]

FILE_DIAG_COLUMNS = [
    "case_id",
    "audio_path",
    "fabrication_direction",
    "fabricated_start_sec",
    "fabricated_end_sec",
    "segment_count",
    "inside_segment_count",
    "outside_segment_count",
    "max_prob_inside",
    "mean_prob_inside",
    "median_prob_inside",
    "max_prob_outside",
    "mean_prob_outside",
    "median_prob_outside",
    "inside_minus_outside_mean",
    "inside_minus_outside_max",
    "probability_std",
    "high_segment_fraction",
    "top1_inside_true_region",
    "top3_any_inside_true_region",
    "top5_any_inside_true_region",
    "top5_inside_count",
    "best_rank_inside_region",
    "partial_localization_gate",
    "partial_fusion_eligible",
    "broad_activation_warning",
    "localization_diagnostic_label",
    "interpretation",
]

BOUNDARY_DIAG_COLUMNS = [
    "case_id",
    "fabrication_direction",
    "boundary_type",
    "nearest_segment_id",
    "nearest_segment_start_sec",
    "nearest_segment_end_sec",
    "nearest_segment_probability",
    "local_probability_delta_before",
    "local_probability_delta_after",
    "boundary_signal_strength",
]

SUMMARY_COLUMNS = ["metric", "value"]


def _stem_from_output_file(value: str) -> str:
    s = str(value).strip().replace("\\", "/")
    if not s:
        return ""
    return Path(s).stem.lower()


def load_timestamp_records(
    csv_path: Path,
    audio_dir: Path,
    fabrication_direction: str,
    project_root: Path,
) -> list[dict[str, Any]]:
    """Load evaluation-only timestamp annotations (never used as model input)."""
    if not csv_path.is_file():
        return []
    df = pd.read_csv(csv_path, low_memory=False)
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        entry = {str(k).strip(): row[k] for k in df.columns}
        output_file = entry.get("output_file") or entry.get("filename") or entry.get("audio_path")
        if output_file is None or (isinstance(output_file, float) and math.isnan(output_file)):
            continue
        stem = _stem_from_output_file(str(output_file))
        start = entry.get("insert_start_sec", entry.get("fabricated_start_sec", entry.get("start_sec")))
        end = entry.get("insert_end_sec", entry.get("fabricated_end_sec", entry.get("end_sec")))
        if start is None or end is None:
            continue
        try:
            fab_start = float(start)
            fab_end = float(end)
        except (TypeError, ValueError):
            continue
        if fab_end <= fab_start:
            continue

        audio_path = audio_dir / Path(str(output_file)).name
        if not audio_path.is_file():
            matches = [p for p in audio_dir.iterdir() if p.suffix.lower() in {".wav", ".mp3", ".flac"} and p.stem.lower() == stem]
            audio_path = matches[0] if matches else audio_dir / str(output_file)

        try:
            rel_str = str(audio_path.resolve().relative_to(project_root.resolve())).replace("\\", "/")
        except ValueError:
            rel_str = str(audio_path.resolve()).replace("\\", "/")

        records.append(
            {
                "case_id": stem,
                "audio_path": rel_str,
                "audio_path_abs": str(audio_path.resolve()),
                "fabricated_start_sec": fab_start,
                "fabricated_end_sec": fab_end,
                "fabricated_duration_sec": round(fab_end - fab_start, 4),
                "fabrication_direction": fabrication_direction,
                "label": str(entry.get("label", "")),
            }
        )
    return records


def segment_overlap_metrics(
    seg_start: float,
    seg_end: float,
    fab_start: float,
    fab_end: float,
    overlap_threshold: float,
) -> dict[str, Any]:
    overlap_start = max(seg_start, fab_start)
    overlap_end = min(seg_end, fab_end)
    overlap_sec = max(0.0, overlap_end - overlap_start)
    seg_len = max(1e-9, seg_end - seg_start)
    overlap_ratio_segment = overlap_sec / seg_len

    if overlap_ratio_segment >= overlap_threshold:
        label = "inside_fabricated_region"
    elif overlap_sec > 0:
        label = "boundary_overlap"
    else:
        label = "outside_fabricated_region"

    seg_mid = (seg_start + seg_end) / 2.0
    if fab_start <= seg_mid <= fab_end:
        distance = 0.0
    elif seg_mid < fab_start:
        distance = fab_start - seg_mid
    else:
        distance = seg_mid - fab_end

    return {
        "overlap_sec": round(overlap_sec, 4),
        "overlap_ratio_segment": round(overlap_ratio_segment, 4),
        "true_region_label": label,
        "distance_to_fabricated_region_sec": round(distance, 4),
    }


def _safe_probs(values: list[Any]) -> list[float]:
    out: list[float] = []
    for v in values:
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if math.isnan(fv):
            continue
        out.append(fv)
    return out


def _stats(values: list[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    arr = sorted(values)
    n = len(arr)
    median = arr[n // 2] if n % 2 else (arr[n // 2 - 1] + arr[n // 2]) / 2
    return max(arr), sum(arr) / n, median


def assign_localization_diagnostic_label(
    *,
    inference_error: bool,
    partial_gate: str,
    broad_activation: bool,
    top1_inside: bool,
    top5_any_inside: bool,
    top5_inside_count: int,
    top5_boundary_only: bool,
) -> str:
    if inference_error:
        return "inference_error"
    if partial_gate == "global_activation_not_localized" or broad_activation:
        if top5_any_inside:
            return "topk_hits_but_broad_activation"
        return "broad_activation_not_localized"
    if top1_inside:
        return "localized_success"
    if top5_any_inside:
        return "topk_hits_but_broad_activation"
    if top5_boundary_only and top5_inside_count == 0:
        return "boundary_only_signal"
    return "no_timestamp_hit"


def interpretation_for_label(label: str) -> str:
    mapping = {
        "localized_success": "Top segment overlaps true fabricated region; localized contrast may support manual review.",
        "topk_hits_but_broad_activation": "Some top segments hit true region but broad activation limits fusion eligibility.",
        "broad_activation_not_localized": "Broad segment activation; timestamp region not distinguished from remainder.",
        "boundary_only_signal": "Strongest signal near splice boundaries rather than full fabricated region interior.",
        "no_timestamp_hit": "Top-ranked segments did not overlap true fabricated region at overlap threshold.",
        "inference_error": "Live inference failed for this file; no segment comparison available.",
    }
    return mapping.get(label, "Review segment diagnostics for manual review support only.")


def build_boundary_rows(
    case_id: str,
    fabrication_direction: str,
    segment_rows: list[dict[str, Any]],
    fab_start: float,
    fab_end: float,
) -> list[dict[str, Any]]:
    scored = [r for r in segment_rows if r.get("partial_probability") is not None]
    if not scored:
        return []

    def nearest_to(time_sec: float) -> dict[str, Any] | None:
        best = None
        best_dist = float("inf")
        for row in scored:
            mid = (float(row["start_sec"]) + float(row["end_sec"])) / 2.0
            dist = abs(mid - time_sec)
            if dist < best_dist:
                best_dist = dist
                best = row
        return best

    def neighbor_delta(row: dict[str, Any], before: bool) -> float | None:
        rank = int(row.get("partial_rank", 0))
        if rank <= 0:
            return None
        target_rank = rank + 1 if before else rank - 1
        if target_rank < 1:
            return None
        neighbor = next((r for r in scored if int(r.get("partial_rank", -1)) == target_rank), None)
        if neighbor is None:
            return None
        return float(row["partial_probability"]) - float(neighbor["partial_probability"])

    rows: list[dict[str, Any]] = []
    for boundary_type, time_sec in (("start_boundary", fab_start), ("end_boundary", fab_end)):
        nearest = nearest_to(time_sec)
        if nearest is None:
            continue
        delta_before = neighbor_delta(nearest, before=True)
        delta_after = neighbor_delta(nearest, before=False)
        prob = float(nearest["partial_probability"])
        deltas = [d for d in (delta_before, delta_after) if d is not None]
        strength = max(deltas) if deltas else prob
        rows.append(
            {
                "case_id": case_id,
                "fabrication_direction": fabrication_direction,
                "boundary_type": boundary_type,
                "nearest_segment_id": nearest.get("segment_id"),
                "nearest_segment_start_sec": nearest.get("start_sec"),
                "nearest_segment_end_sec": nearest.get("end_sec"),
                "nearest_segment_probability": prob,
                "local_probability_delta_before": delta_before,
                "local_probability_delta_after": delta_after,
                "boundary_signal_strength": round(strength, 4),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, summary: dict[str, Any]) -> None:
    rows = [{"metric": k, "value": v} for k, v in summary.items()]
    write_csv(path, rows, SUMMARY_COLUMNS)
