#!/usr/bin/env python3
"""
Phase 9D-P5D: Independent held-out evaluation of accepted P5B partial-fabrication cascade.

Uses testing_audios (t1–t5, fabricated) only. Experimental — no release packaging.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_evaluation_shared import (
    AUDIO_EXTENSIONS,
    cheap_file_hash,
    evaluate_manifest_cascade,
    init_p5d_run_status,
    rel_path,
    write_p5d_run_status,
)
from phase9d_p5_partial_utils import (
    normalize_path_str,
    path_basename,
    path_stem_lower,
    progress,
    repo_root_from_here,
)
from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5C_FILE_GATE_FEATURE_SET,
    P5C_SEGMENT_FEATURE_SET,
    P5D_ALLOWED_TEST_GROUPS,
    assess_p5d_release_readiness,
    load_dataset_csv,
    load_p5b_candidate_artifacts,
    now_utc_str,
)

SEG_PRED_COLUMNS = [
    "file_path",
    "file_name",
    "segment_index",
    "segment_index_chronological",
    "segment_start",
    "segment_end",
    "segment_probability",
    "segment_rank",
    "is_high_segment",
    "overlaps_known_fabricated_timestamp",
    "expected_segment_label",
]

FILE_PRED_COLUMNS = [
    "file_path",
    "file_name",
    "file_stem",
    "parent_folder",
    "test_group",
    "expected_condition",
    "expected_partial_label",
    "source_split_status",
    "file_gate_probability",
    "file_gate_positive",
    "max_segment_probability",
    "segment_threshold_positive",
    "high_segment_fraction",
    "broad_activation_flag",
    "topk_minus_rest_probability",
    "contrast_positive",
    "partial_evidence_positive",
    "candidate_segment_start",
    "candidate_segment_end",
    "candidate_segment_probability",
    "candidate_segment_rank",
    "has_timestamp_label",
    "candidate_timestamp_error_seconds",
    "top1_timestamp_hit",
    "top3_timestamp_hit",
    "top5_timestamp_hit",
    "error_status",
    "error_message",
    "ssl_extraction_mode",
    "ssl_chunked_fallback_used",
    "ssl_cpu_fallback_used",
    "ssl_cuda_oom_recovered",
    "audio_duration_sec",
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P5D independent testing-audio cascade evaluation.")
    p.add_argument("--input_root", default="testing_audios", help="testing_audios or data/testing_audios")
    p.add_argument("--output_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5d"))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    p.add_argument(
        "--file_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv"),
    )
    p.add_argument(
        "--segment_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv"),
    )
    p.add_argument(
        "--file_gate_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_file_partial_gate_dataset.csv"),
    )
    p.add_argument(
        "--segment_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_segment_partial_localizer_dataset.csv"),
    )
    p.add_argument(
        "--p5c_manifest",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5c/phase9d_p5c_controlled_manifest.csv"),
    )
    p.add_argument("--ssl_device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--disable_ssl_cpu_fallback", action="store_true")
    p.add_argument("--ssl_chunk_sec", type=float, default=30.0)
    p.add_argument("--ssl_chunk_hop_sec", type=float, default=None)
    p.add_argument("--ssl_chunk_max_chunks", type=int, default=200)
    p.add_argument("--disable_ssl_chunked_fallback", action="store_true")
    p.add_argument("--prefer_cpu_for_long_audio", action="store_true")
    p.add_argument("--long_audio_sec", type=float, default=60.0)
    p.add_argument("--max_audio_duration_sec", type=float, default=None)
    p.add_argument("--max_segments_per_file", type=int, default=500)
    p.add_argument("--keep_failed_outputs", action="store_true", default=True)
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def resolve_testing_input_root(project_root: Path, user_arg: str) -> Path:
    if user_arg:
        p = Path(user_arg)
        for cand in (p, project_root / p):
            if cand.is_dir():
                return cand.resolve()
    for cand in (project_root / "testing_audios", project_root / "data" / "testing_audios"):
        if cand.is_dir():
            return cand.resolve()
    raise FileNotFoundError(
        f"No testing audio root found for --input_root={user_arg!r}. "
        "Expected testing_audios or data/testing_audios under project root."
    )


P5D_GROUP_DEFAULT_CONDITION = {
    "t1": "direct",
    "t2": "replay",
    "t3": "direct",
    "t4": "direct",
    "t5": "direct",
    "fabricated": "fabricated",
}


def condition_from_phase7_fields(recording_condition: str, manipulation_type: str, partial_bin: int) -> str:
    rec = str(recording_condition or "").lower()
    manip = str(manipulation_type or "").lower()
    if partial_bin == 1 or "partial" in rec or "partial" in manip:
        return "fabricated"
    if "replay" in rec or "replay" in manip:
        return "replay"
    if any(k in rec or k in manip for k in ("mixer", "channel", "compressed", "whatsapp")):
        return "mixer_or_channel"
    if "clean_direct" in rec or rec.endswith("direct"):
        return "direct"
    if "edited" in rec or "spliced" in rec:
        return "direct"
    return "unknown_testing_condition"


def load_phase7_testing_label_lookup(project_root: Path) -> dict[str, dict[str, Any]]:
    """Optional Phase 7A forensic labels for testing_audios stems (test_id)."""
    path = project_root / "reports/phase7/phase7_dataset/forensic_labeled_master.csv"
    if not path.is_file():
        return {}
    df = pd.read_csv(path, low_memory=False)
    lookup: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        key = str(row.get("test_id", "") or path_stem_lower(str(row.get("filename", "")))).strip().lower()
        if not key:
            continue
        partial_bin = int(pd.to_numeric(row.get("partial_fabrication_binary", 0), errors="coerce") or 0)
        start = row.get("suspicious_start_time", "")
        end = row.get("suspicious_end_time", "")
        has_ts = bool(
            partial_bin
            and pd.notna(start)
            and pd.notna(end)
            and str(start).strip() not in ("", "nan")
            and str(end).strip() not in ("", "nan")
        )
        lookup[key] = {
            "expected_condition": condition_from_phase7_fields(
                str(row.get("recording_condition", "")),
                str(row.get("manipulation_type", "")),
                partial_bin,
            ),
            "expected_partial_label": partial_bin,
            "expected_origin_label": str(row.get("origin_label", "") or row.get("ground_truth_origin", "")),
            "has_timestamp_label": has_ts,
            "timestamp_start": str(start) if has_ts else "",
            "timestamp_end": str(end) if has_ts else "",
        }
    return lookup


def infer_expected_condition(name_lower: str, test_group: str) -> str:
    if test_group == "fabricated" or any(k in name_lower for k in ("fabricated", "partial", "insertion")):
        return "fabricated"
    if any(k in name_lower for k in ("replay", "rerecord", "speaker", "mobile", "bluetooth", "phone_to")):
        return "replay"
    if any(k in name_lower for k in ("mixer", "channel", "compress", "noisy", "whatsapp")):
        return "mixer_or_channel"
    if any(k in name_lower for k in ("clean", "direct", "human", "studio", "podcast", "bonafide")):
        return "direct"
    if any(k in name_lower for k in ("tts", "clone", "synthesis", "ai", "spoof")):
        return "direct"
    return P5D_GROUP_DEFAULT_CONDITION.get(test_group, "unknown_testing_condition")


def infer_expected_partial_label(name_lower: str, test_group: str) -> int:
    if test_group == "fabricated":
        return 1
    if any(k in name_lower for k in ("fabricated", "partial", "fab_", "_fab", "insertion")):
        return 1
    return 0


def infer_expected_origin_label(name_lower: str) -> str:
    if any(k in name_lower for k in ("human", "bonafide", "speaker", "urdu", "podcast")):
        return "human_likely"
    if any(k in name_lower for k in ("tts", "clone", "ai", "synthesis", "spoof")):
        return "ai_likely"
    return ""


def _try_sidecar_timestamps(path: Path) -> tuple[bool, str, str]:
    """Load timestamps only from explicit sidecar JSON (do not invent)."""
    side = path.with_suffix(".json")
    if not side.is_file():
        return False, "", ""
    try:
        data = json.loads(side.read_text(encoding="utf-8"))
        start = data.get("fabricated_start_sec", data.get("timestamp_start", data.get("start_sec")))
        end = data.get("fabricated_end_sec", data.get("timestamp_end", data.get("end_sec")))
        if start is None or end is None:
            return False, "", ""
        return True, str(start), str(end)
    except (json.JSONDecodeError, OSError):
        return False, "", ""


def scan_testing_audio(
    input_root: Path,
    project_root: Path,
    *,
    phase7_lookup: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    phase7_lookup = phase7_lookup or {}
    for sub in sorted(input_root.iterdir()):
        if not sub.is_dir():
            continue
        group = sub.name.lower()
        if group not in P5D_ALLOWED_TEST_GROUPS:
            continue
        for f in sorted(sub.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            rel = rel_path(f, project_root)
            name_lower = f.name.lower()
            has_ts, ts_start, ts_end = _try_sidecar_timestamps(f)
            row = {
                "file_path": rel,
                "file_name": f.name,
                "file_stem": f.stem,
                "parent_folder": sub.name,
                "test_group": group,
                "expected_condition": infer_expected_condition(name_lower, group),
                "expected_partial_label": infer_expected_partial_label(name_lower, group),
                "expected_origin_label": infer_expected_origin_label(name_lower),
                "has_timestamp_label": has_ts,
                "timestamp_start": ts_start,
                "timestamp_end": ts_end,
                "manifest_status": "included",
            }
            p7 = phase7_lookup.get(f.stem.lower()) or phase7_lookup.get(path_stem_lower(f.name))
            if p7:
                row.update(p7)
            if has_ts:
                row["has_timestamp_label"] = True
                row["timestamp_start"] = ts_start
                row["timestamp_end"] = ts_end
            rows.append(row)
    return rows


def build_p5d_overlap_audit(
    manifest: pd.DataFrame,
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    p5c_manifest: pd.DataFrame,
    root: Path,
) -> pd.DataFrame:
    train_paths: set[str] = set()
    train_names: set[str] = set()
    train_stems: set[str] = set()
    for df in (file_gate_df, segment_df):
        if df.empty or "audio_path" not in df.columns:
            continue
        for p in df["audio_path"].astype(str):
            train_paths.add(normalize_path_str(p))
            train_names.add(path_basename(p).lower())
            train_stems.add(path_stem_lower(p))

    p5c_paths: set[str] = set()
    p5c_names: set[str] = set()
    p5c_stems: set[str] = set()
    if not p5c_manifest.empty and "file_path" in p5c_manifest.columns:
        for p in p5c_manifest["file_path"].astype(str):
            p5c_paths.add(normalize_path_str(p))
            p5c_names.add(path_basename(p).lower())
            p5c_stems.add(path_stem_lower(p))

    rows: list[dict[str, Any]] = []
    for _, m in manifest.iterrows():
        fp = normalize_path_str(str(m["file_path"]))
        name = path_basename(fp).lower()
        stem = path_stem_lower(fp)
        abs_path = root / fp
        file_hash = cheap_file_hash(abs_path) if abs_path.is_file() else ""
        if fp in train_paths or name in train_names or stem in train_stems:
            status = "seen_in_p5_training"
        elif fp in p5c_paths or name in p5c_names or stem in p5c_stems:
            status = "seen_in_p5c_controlled"
        elif abs_path.is_file():
            status = "independent_holdout"
        else:
            status = "unknown_overlap_status"
        rows.append(
            {
                "file_path": fp,
                "file_name": m["file_name"],
                "normalized_file_name": name,
                "file_stem": stem,
                "file_hash_prefix": file_hash,
                "overlap_status": status,
            }
        )
    return pd.DataFrame(rows)


def _empty_file_pred_row(base: dict[str, Any]) -> dict[str, Any]:
    row = {c: np.nan for c in FILE_PRED_COLUMNS}
    row.update(base)
    for k in (
        "file_gate_positive",
        "segment_threshold_positive",
        "broad_activation_flag",
        "contrast_positive",
        "partial_evidence_positive",
        "top1_timestamp_hit",
        "top3_timestamp_hit",
        "top5_timestamp_hit",
        "ssl_chunked_fallback_used",
        "ssl_cpu_fallback_used",
        "ssl_cuda_oom_recovered",
    ):
        row[k] = False
    row["error_status"] = base.get("error_status", "skipped")
    row["error_message"] = base.get("error_message", "")
    return row


def normalize_file_predictions(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        base = {c: r.get(c, np.nan) for c in FILE_PRED_COLUMNS}
        for c in FILE_PRED_COLUMNS:
            if c not in base:
                base[c] = np.nan
        rows.append(base)
    return pd.DataFrame(rows, columns=FILE_PRED_COLUMNS)


P5D_KNOWN_CONDITIONS = frozenset({"direct", "replay", "mixer", "mixer_or_channel", "fabricated"})


def _is_unknown_testing_condition(value: object) -> bool:
    text = str(value or "").strip().lower()
    if not text or text in {"unknown", "unknown_testing_condition", "nan", "none"}:
        return True
    return text not in P5D_KNOWN_CONDITIONS


def _format_metric_for_report(value: Any, *, not_applicable: bool = False) -> str:
    if not_applicable:
        return "not_applicable (no files in this condition stratum)"
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return "not_available"
    return str(value)


def compute_p5d_metrics(
    file_df: pd.DataFrame, overlap_df: pd.DataFrame, robustness_stats: dict[str, Any] | None = None
) -> dict[str, Any]:
    robustness_stats = robustness_stats or {}
    ok = file_df[file_df["error_status"].astype(str) == "ok"].copy()
    metrics: dict[str, Any] = {
        "total_files": int(len(file_df)),
        "evaluated_files": int(len(ok)),
        "failed_files": int(len(file_df) - len(ok)),
        "independent_holdout_count": int((overlap_df["overlap_status"] == "independent_holdout").sum()),
        "seen_in_p5_training_count": int((overlap_df["overlap_status"] == "seen_in_p5_training").sum()),
        "seen_in_p5c_controlled_count": int((overlap_df["overlap_status"] == "seen_in_p5c_controlled").sum()),
        "unknown_overlap_count": int((overlap_df["overlap_status"] == "unknown_overlap_status").sum()),
    }
    partial = ok[ok["expected_partial_label"].astype(int) == 1]
    non_partial = ok[ok["expected_partial_label"].astype(int) == 0]
    metrics["partial_file_count"] = int(len(partial))
    metrics["non_partial_file_count"] = int(len(non_partial))

    metrics["partial_evidence_recall"] = (
        float(partial["partial_evidence_positive"].astype(bool).mean()) if len(partial) else None
    )
    metrics["non_partial_false_alarm_rate"] = (
        float(non_partial["partial_evidence_positive"].astype(bool).mean()) if len(non_partial) else None
    )

    direct = ok[ok["expected_condition"].astype(str) == "direct"]
    replay = ok[ok["expected_condition"].astype(str) == "replay"]
    mixer = ok[ok["expected_condition"].astype(str).isin(("mixer_or_channel", "mixer"))]
    unknown = ok[ok["expected_condition"].astype(str).apply(_is_unknown_testing_condition)]

    metrics["direct_condition_count"] = int(len(direct))
    metrics["replay_condition_count"] = int(len(replay))
    metrics["mixer_condition_count"] = int(len(mixer))
    metrics["unknown_condition_count"] = int(len(unknown))

    def _cond_rate(group: pd.DataFrame) -> float | None:
        if group.empty:
            return None
        return float(group["partial_evidence_positive"].astype(bool).mean())

    metrics["direct_false_partial_rate"] = _cond_rate(direct)
    metrics["replay_false_partial_rate"] = _cond_rate(replay)
    metrics["mixer_false_partial_rate"] = _cond_rate(mixer)
    if metrics["unknown_condition_count"] > 0:
        metrics["unknown_condition_positive_rate"] = _cond_rate(unknown)
        metrics["unknown_condition_positive_rate_status"] = "computed"
    else:
        metrics["unknown_condition_positive_rate"] = None
        metrics["unknown_condition_positive_rate_status"] = "not_applicable"

    pos = ok[ok["partial_evidence_positive"].astype(bool)]
    metrics["partial_evidence_positive_file_count"] = int(len(pos))
    if len(pos):
        metrics["broad_activation_rate_when_positive"] = float(pos["broad_activation_flag"].astype(bool).mean())
        ts_pos = pos[pos["has_timestamp_label"].astype(bool)]
        if len(ts_pos):
            metrics["top1_hit_rate_when_positive"] = float(ts_pos["top1_timestamp_hit"].astype(bool).mean())
            metrics["top3_hit_rate_when_positive"] = float(ts_pos["top3_timestamp_hit"].astype(bool).mean())
            metrics["top5_hit_rate_when_positive"] = float(ts_pos["top5_timestamp_hit"].astype(bool).mean())
        else:
            metrics["top1_hit_rate_when_positive"] = None
            metrics["top3_hit_rate_when_positive"] = None
            metrics["top5_hit_rate_when_positive"] = None
    else:
        metrics["broad_activation_rate_when_positive"] = None
        metrics["top1_hit_rate_when_positive"] = None
        metrics["top3_hit_rate_when_positive"] = None
        metrics["top5_hit_rate_when_positive"] = None

    ts_pos_all = ok[ok["has_timestamp_label"].astype(bool) & ok["partial_evidence_positive"].astype(bool)]
    metrics["timestamp_positive_count"] = int(len(ts_pos_all))
    if "candidate_timestamp_error_seconds" in ts_pos_all.columns:
        err_series = pd.to_numeric(ts_pos_all["candidate_timestamp_error_seconds"], errors="coerce")
        valid_errors = err_series[np.isfinite(err_series)]
    else:
        valid_errors = pd.Series(dtype=float)
    metrics["timestamp_error_count"] = int(len(valid_errors))
    if len(valid_errors) > 0:
        metrics["median_candidate_timestamp_error_seconds"] = float(np.median(valid_errors))
        metrics["median_candidate_timestamp_error_available"] = True
        metrics["median_candidate_timestamp_error_missing_reason"] = ""
    else:
        metrics["median_candidate_timestamp_error_seconds"] = None
        metrics["median_candidate_timestamp_error_available"] = False
        if len(ts_pos_all) > 0:
            metrics["median_candidate_timestamp_error_missing_reason"] = (
                "timestamp labels exist but candidate/label boundaries unavailable"
            )
        else:
            metrics["median_candidate_timestamp_error_missing_reason"] = ""

    bad_statuses = {"too_short", "silent", "silent_or_invalid", "load_failure", "invalid", "unsupported_extension"}
    invalid_cases = file_df[file_df["error_status"].astype(str).isin(bad_statuses)]
    metrics["invalid_file_handling_pass_rate"] = (
        1.0 if invalid_cases.empty else float((invalid_cases["error_status"].astype(str) != "ok").mean())
    )

    folder_stats: dict[str, Any] = {}
    for grp in sorted(P5D_ALLOWED_TEST_GROUPS):
        g = ok[ok["test_group"].astype(str) == grp]
        if g.empty:
            continue
        folder_stats[grp] = {
            "files": int(len(g)),
            "partial_evidence_positive_rate": float(g["partial_evidence_positive"].astype(bool).mean()),
            "partial_evidence_recall": float(
                g.loc[g["expected_partial_label"].astype(int) == 1, "partial_evidence_positive"].astype(bool).mean()
            )
            if (g["expected_partial_label"].astype(int) == 1).any()
            else np.nan,
        }
    metrics["folder_wise"] = folder_stats
    metrics["candidate_rank1_consistency_count"] = int(
        ok["candidate_segment_rank"].fillna(-1).astype(float).eq(1.0).sum()
    )
    metrics["candidate_rank1_consistency_rate"] = (
        float(metrics["candidate_rank1_consistency_count"] / len(ok)) if len(ok) else None
    )
    metrics["candidate_segment_probability_available_rate"] = (
        float(pd.to_numeric(ok["candidate_segment_probability"], errors="coerce").notna().mean())
        if len(ok)
        else None
    )
    mp4_mask = file_df["file_name"].astype(str).str.lower().str.endswith(".mp4")
    mp4_all = file_df[mp4_mask]
    mp4_ok = mp4_all[mp4_all["error_status"].astype(str) == "ok"]
    metrics["mp4_file_count"] = int(len(mp4_all))
    metrics["mp4_evaluated_count"] = int(len(mp4_ok))
    metrics["mp4_failed_count"] = int(len(mp4_all) - len(mp4_ok))
    metrics["mp4_load_success_rate"] = float(len(mp4_ok) / len(mp4_all)) if len(mp4_all) else None
    metrics["ssl_cuda_oom_count"] = int(robustness_stats.get("ssl_cuda_oom_count", 0))
    metrics["ssl_cpu_fallback_attempt_count"] = int(robustness_stats.get("ssl_cpu_fallback_attempt_count", 0))
    metrics["ssl_cpu_fallback_success_count"] = int(robustness_stats.get("ssl_cpu_fallback_success_count", 0))
    metrics["ssl_cpu_fallback_failure_count"] = int(robustness_stats.get("ssl_cpu_fallback_failure_count", 0))
    metrics["ssl_cpu_fallback_skipped_long_audio_count"] = int(
        robustness_stats.get("ssl_cpu_fallback_skipped_long_audio_count", 0)
    )
    metrics["ssl_chunked_fallback_attempt_count"] = int(
        robustness_stats.get("ssl_chunked_fallback_attempt_count", 0)
    )
    metrics["ssl_chunked_fallback_success_count"] = int(
        robustness_stats.get("ssl_chunked_fallback_success_count", 0)
    )
    metrics["ssl_chunked_fallback_failure_count"] = int(
        robustness_stats.get("ssl_chunked_fallback_failure_count", 0)
    )
    metrics["ssl_chunked_cpu_fallback_attempt_count"] = int(
        robustness_stats.get("ssl_chunked_cpu_fallback_attempt_count", 0)
    )
    metrics["ssl_chunked_cpu_fallback_success_count"] = int(
        robustness_stats.get("ssl_chunked_cpu_fallback_success_count", 0)
    )
    metrics["ssl_chunked_cpu_fallback_failure_count"] = int(
        robustness_stats.get("ssl_chunked_cpu_fallback_failure_count", 0)
    )
    metrics["ssl_long_audio_file_count"] = int(robustness_stats.get("ssl_long_audio_file_count", 0))
    metrics["ssl_long_audio_recovered_count"] = int(robustness_stats.get("ssl_long_audio_recovered_count", 0))
    metrics["ssl_long_audio_failed_count"] = int(robustness_stats.get("ssl_long_audio_failed_count", 0))
    metrics["ssl_chunked_embedding_used_count"] = int(
        robustness_stats.get("ssl_chunked_embedding_used_count", 0)
    )
    metrics["ssl_chunked_embedding_max_chunks_observed"] = int(
        robustness_stats.get("ssl_chunked_embedding_max_chunks_observed", 0)
    )
    metrics["robustness_failed_file_count"] = int(
        file_df["error_status"].astype(str).isin(
            {
                "unsupported_container_or_decoder_missing",
                "no_audio_stream",
                "ssl_cuda_oom",
                "ssl_cuda_oom_cpu_fallback_failed",
                "ssl_chunked_fallback_failed",
                "ssl_embedding_failure",
            }
        ).sum()
    )
    recovered_files = 0
    if "ssl_cuda_oom_recovered" in file_df.columns:
        recovered_files += int(file_df["ssl_cuda_oom_recovered"].astype(bool).sum())
    metrics["robustness_recovered_file_count"] = int(
        max(
            recovered_files,
            metrics["ssl_cpu_fallback_success_count"] + metrics["ssl_chunked_fallback_success_count"],
        )
    )
    metrics["evaluation_runtime_seconds"] = float(robustness_stats.get("evaluation_runtime_seconds", np.nan))
    return metrics


def labels_complete(manifest: pd.DataFrame) -> bool:
    if manifest.empty or "expected_condition" not in manifest.columns:
        return False
    conds = manifest["expected_condition"].astype(str)
    unknown_frac = float((conds == "unknown_testing_condition").mean())
    if unknown_frac >= 0.5:
        return False
    required = {"direct", "replay", "mixer_or_channel"}
    present = set(conds.unique())
    return required.issubset(present)


def write_p5d_report(
    path: Path,
    *,
    input_root: Path,
    scanned_groups: list[str],
    manifest: pd.DataFrame,
    overlap_df: pd.DataFrame,
    metrics: dict[str, Any],
    artifacts: dict[str, Any],
    assessment: str,
    packaging_ready: bool,
    failure_reasons: list[str],
    examples_success: pd.DataFrame,
    examples_false: pd.DataFrame,
    file_pred: pd.DataFrame | None = None,
) -> None:
    holdout = int(metrics.get("independent_holdout_count", 0))
    seen_train = int(metrics.get("seen_in_p5_training_count", 0))
    seen_p5c = int(metrics.get("seen_in_p5c_controlled_count", 0))
    if holdout > 0 and seen_train == 0 and seen_p5c == 0:
        eval_mode = "independent held-out testing audio"
    elif holdout > 0:
        eval_mode = "mixed independent holdout with some training/P5C overlap (see overlap audit)"
    else:
        eval_mode = "NOT independent — no holdout files"

    th = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    paths = artifacts.get("paths", {})

    lines = [
        "# Phase 9D-P5D Independent Evaluation Report (Experimental)",
        "",
        f"Generated: {now_utc_str()}",
        "",
        "**Production claim:** NO — experimental partial-fabrication evidence indicator only.",
        "",
        "**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.",
        "",
        "## Purpose",
        "",
        "Evaluate whether the accepted P5B partial-fabrication candidate cascade generalizes on "
        "independent `testing_audios` holdout (t1–t5 and fabricated) outside P5A/P5B/P5C training reuse.",
        "",
        "## Input",
        "",
        f"- Input root: `{input_root}`",
        f"- Scanned test folders: {', '.join(scanned_groups) if scanned_groups else '(none found)'}",
        f"- Files in manifest: {len(manifest)}",
        "",
        "## Overlap audit summary",
        "",
        f"- Evaluation mode: **{eval_mode}**",
        f"- Independent holdout files: {holdout}",
        f"- Seen in P5 training: {seen_train}",
        f"- Seen in P5C controlled: {seen_p5c}",
        f"- Unknown overlap: {int(metrics.get('unknown_overlap_count', 0))}",
        "",
        "Overlap with P5 training or P5C is reported explicitly and not hidden.",
        "",
        "## Accepted P5B cascade thresholds",
        "",
        f"- file_gate_threshold = {th['file_gate_threshold']}",
        f"- segment_threshold = {th['segment_threshold']}",
        f"- contrast_threshold = {th['contrast_threshold']}",
        f"- broad_limit = {th['broad_limit']}",
        "",
        f"- File gate feature set: `{P5C_FILE_GATE_FEATURE_SET}`",
        f"- Segment localizer feature set: `{P5C_SEGMENT_FEATURE_SET}`",
        "",
        "## Candidate model artifacts (P5B experimental only)",
        "",
        f"- File gate: `{paths.get('file_gate', 'missing')}`",
        f"- Segment localizer v2: `{paths.get('segment_localizer', 'missing')}`",
        f"- Cascade config: `{paths.get('cascade_config', 'missing')}`",
        "",
        "Only P5B experimental candidate artifacts were used for the partial cascade. "
        "No release or reference-model artifacts were activated.",
        "",
        "## File-level results",
        "",
        f"- Total files: {metrics.get('total_files')}",
        f"- Evaluated (ok): {metrics.get('evaluated_files')}",
        f"- Failed/skipped: {metrics.get('failed_files')}",
        f"- Partial evidence recall: {metrics.get('partial_evidence_recall', np.nan)}",
        f"- Non-partial false alarm rate: {metrics.get('non_partial_false_alarm_rate', np.nan)}",
        "",
        "## Folder-wise results (t1–t5, fabricated)",
        "",
    ]
    fw = metrics.get("folder_wise", {})
    if not fw:
        lines.append("- No folder-wise stats (no evaluated files).")
    else:
        for grp, st in fw.items():
            lines.append(
                f"- **{grp}**: files={st.get('files')}, "
                f"positive_rate={st.get('partial_evidence_positive_rate', np.nan)}, "
                f"partial_recall={st.get('partial_evidence_recall', np.nan)}"
            )

    lines.extend(
        [
            "",
            "## Condition-wise false partial rates",
            "",
            f"- direct_condition_count: {metrics.get('direct_condition_count', 0)}",
            f"- direct_false_partial_rate: {_format_metric_for_report(metrics.get('direct_false_partial_rate'), not_applicable=metrics.get('direct_condition_count', 0) == 0)}",
            f"- replay_condition_count: {metrics.get('replay_condition_count', 0)}",
            f"- replay_false_partial_rate: {_format_metric_for_report(metrics.get('replay_false_partial_rate'), not_applicable=metrics.get('replay_condition_count', 0) == 0)}",
            f"- mixer_condition_count: {metrics.get('mixer_condition_count', 0)}",
            f"- mixer_false_partial_rate: {_format_metric_for_report(metrics.get('mixer_false_partial_rate'), not_applicable=metrics.get('mixer_condition_count', 0) == 0)}",
            f"- unknown_condition_count: {metrics.get('unknown_condition_count', 0)}",
            f"- unknown_condition_positive_rate: {_format_metric_for_report(metrics.get('unknown_condition_positive_rate'), not_applicable=metrics.get('unknown_condition_count', 0) == 0)}",
            "",
            "## Localization behavior",
            "",
            f"- timestamp_positive_count: {metrics.get('timestamp_positive_count', 0)}",
            f"- timestamp_error_count: {metrics.get('timestamp_error_count', 0)}",
            "- Candidate segment means rank-1 segment by segment-localizer probability.",
            "- median_candidate_timestamp_error_seconds is computed from the corrected rank-1 candidate segment.",
            f"- top1_hit_rate_when_positive: {_format_metric_for_report(metrics.get('top1_hit_rate_when_positive'), not_applicable=int(metrics.get('timestamp_positive_count', 0)) == 0)}",
            f"- top3_hit_rate_when_positive: {_format_metric_for_report(metrics.get('top3_hit_rate_when_positive'), not_applicable=int(metrics.get('timestamp_positive_count', 0)) == 0)}",
            f"- top5_hit_rate_when_positive: {_format_metric_for_report(metrics.get('top5_hit_rate_when_positive'), not_applicable=int(metrics.get('timestamp_positive_count', 0)) == 0)}",
        ]
    )
    if metrics.get("median_candidate_timestamp_error_available"):
        lines.append(
            f"- median_candidate_timestamp_error_seconds: {metrics.get('median_candidate_timestamp_error_seconds')}"
        )
    elif int(metrics.get("timestamp_positive_count", 0)) > 0:
        lines.append(
            f"- median_candidate_timestamp_error_seconds: not_available "
            f"({metrics.get('median_candidate_timestamp_error_missing_reason', 'missing')})"
        )
    else:
        lines.append("- median_candidate_timestamp_error_seconds: not_applicable (no timestamp-positive files)")
    lines.extend(
        [
            "",
            "## Broad activation behavior",
            "",
            f"- broad_activation_rate_when_positive: {metrics.get('broad_activation_rate_when_positive', np.nan)}",
            f"- candidate_rank1_consistency_count: {metrics.get('candidate_rank1_consistency_count', 0)}",
            f"- candidate_rank1_consistency_rate: {metrics.get('candidate_rank1_consistency_rate', np.nan)}",
            f"- candidate_segment_probability_available_rate: {metrics.get('candidate_segment_probability_available_rate', np.nan)}",
            "",
            "## Error handling",
            "",
            f"- invalid_file_handling_pass_rate: {metrics.get('invalid_file_handling_pass_rate', np.nan)}",
            "",
            "## Robustness behavior",
            "",
            f"- mp4_file_count: {metrics.get('mp4_file_count', 0)}",
            f"- mp4_evaluated_count: {metrics.get('mp4_evaluated_count', 0)}",
            f"- mp4_failed_count: {metrics.get('mp4_failed_count', 0)}",
            f"- mp4_load_success_rate: {_format_metric_for_report(metrics.get('mp4_load_success_rate'), not_applicable=metrics.get('mp4_file_count', 0) == 0)}",
            f"- ssl_cuda_oom_count: {metrics.get('ssl_cuda_oom_count', 0)}",
            f"- ssl_cpu_fallback_attempt_count: {metrics.get('ssl_cpu_fallback_attempt_count', 0)}",
            f"- ssl_cpu_fallback_success_count: {metrics.get('ssl_cpu_fallback_success_count', 0)}",
            f"- ssl_cpu_fallback_failure_count: {metrics.get('ssl_cpu_fallback_failure_count', 0)}",
            f"- ssl_cpu_fallback_skipped_long_audio_count: {metrics.get('ssl_cpu_fallback_skipped_long_audio_count', 0)}",
            f"- ssl_chunked_fallback_attempt_count: {metrics.get('ssl_chunked_fallback_attempt_count', 0)}",
            f"- ssl_chunked_fallback_success_count: {metrics.get('ssl_chunked_fallback_success_count', 0)}",
            f"- ssl_chunked_fallback_failure_count: {metrics.get('ssl_chunked_fallback_failure_count', 0)}",
            f"- ssl_chunked_cpu_fallback_attempt_count: {metrics.get('ssl_chunked_cpu_fallback_attempt_count', 0)}",
            f"- ssl_chunked_cpu_fallback_success_count: {metrics.get('ssl_chunked_cpu_fallback_success_count', 0)}",
            f"- ssl_chunked_cpu_fallback_failure_count: {metrics.get('ssl_chunked_cpu_fallback_failure_count', 0)}",
            f"- ssl_long_audio_file_count: {metrics.get('ssl_long_audio_file_count', 0)}",
            f"- ssl_long_audio_recovered_count: {metrics.get('ssl_long_audio_recovered_count', 0)}",
            f"- ssl_long_audio_failed_count: {metrics.get('ssl_long_audio_failed_count', 0)}",
            f"- ssl_chunked_embedding_used_count: {metrics.get('ssl_chunked_embedding_used_count', 0)}",
            f"- ssl_chunked_embedding_max_chunks_observed: {metrics.get('ssl_chunked_embedding_max_chunks_observed', 0)}",
            f"- robustness_failed_file_count: {metrics.get('robustness_failed_file_count', 0)}",
            f"- robustness_recovered_file_count: {metrics.get('robustness_recovered_file_count', 0)}",
            "",
            "Robustness counters are derived from SSL extraction/fallback events and cross-checked against error cases.",
            "P5D-R2 improves memory-safe SSL extraction only; it does not change the partial cascade model, thresholds, or release readiness decision.",
            "",
        ]
    )
    t41_path = "testing_audios/t4/t4.1.mp3"
    fp_df = file_pred if file_pred is not None else pd.DataFrame()
    t41_rows = fp_df[fp_df["file_path"].astype(str).str.lower().str.replace("\\", "/") == t41_path]
    if not t41_rows.empty and str(t41_rows.iloc[0].get("error_status", "")) == "ok":
        lines.append(
            "The previous long-audio SSL failure was recovered through chunked fallback."
        )
        lines.append("")
    elif not t41_rows.empty:
        t41_err = str(t41_rows.iloc[0].get("error_status", ""))
        if t41_err == "ssl_chunked_fallback_failed":
            lines.append(
                "The previous long-audio SSL failure remains; chunked fallback attempted but did not recover the file."
            )
        elif t41_err == "ssl_cuda_oom_cpu_fallback_failed":
            lines.append(
                "The previous long-audio SSL failure remains; chunked fallback was not attempted or did not recover the file."
            )
        lines.append("")
    if int(metrics.get("ssl_long_audio_failed_count", 0)) > 0:
        lines.append(
            "Some long-audio files remain failed after chunked SSL fallback; review error cases for details."
        )
        lines.append("")
    failed_n = int(metrics.get("failed_files", 0))
    if failed_n:
        lines.extend(
            [
                f"- Skipped/failed files in this run: {failed_n}",
                "",
                "**Skipped/failed file note:** "
                f"{failed_n} file(s) failed or were skipped in this independent run. "
                "These should be reviewed before any release packaging decision. "
                "MP4 loading and SSL memory behavior may need a later robustness fix.",
                "",
            ]
        )
    lines.extend(
        [
            "## Examples — partial evidence positives (candidate segments)",
            "",
        ]
    )
    if examples_success.empty:
        lines.append("- None selected.")
    else:
        rank_warn = (
            int(metrics.get("candidate_rank1_consistency_count", 0)) != int(metrics.get("evaluated_files", 0))
            if metrics.get("evaluated_files", 0)
            else False
        )
        if rank_warn:
            lines.append(
                "- **Integrity warning:** some candidate segments are not rank-1; review localization outputs."
            )
        for _, r in examples_success.head(5).iterrows():
            rank_val = pd.to_numeric(r.get("candidate_segment_rank"), errors="coerce")
            rank_str = str(int(rank_val)) if np.isfinite(rank_val) else "n/a"
            lines.append(
                f"- `{r['file_path']}` — experimental partial-fabrication candidate segment "
                f"{r.get('candidate_segment_start', 'n/a')}–{r.get('candidate_segment_end', 'n/a')}s "
                f"(gate={r.get('file_gate_probability', np.nan):.3f}, "
                f"candidate_seg_prob={r.get('candidate_segment_probability', np.nan):.3f}, "
                f"candidate_rank={rank_str}; manual review recommended)"
            )

    lines.extend(["", "## Examples — false partial evidence (if any)", ""])
    if examples_false.empty:
        lines.append("- None selected.")
    else:
        for _, r in examples_false.head(5).iterrows():
            lines.append(
                f"- `{r['file_path']}` ({r.get('expected_condition', 'n/a')}) — "
                f"partial_evidence_positive=True; gate={r.get('file_gate_probability', np.nan):.3f}"
            )

    lines.extend(
        [
            "",
            "## Release packaging evaluation assessment",
            "",
            f"**Assessment:** {assessment}",
            "",
            f"**Candidate acceptable for release packaging evaluation:** "
            f"{'yes' if packaging_ready else 'no'}",
            "",
        ]
    )
    if failure_reasons:
        lines.append("Blocking or limiting reasons:")
        for r in failure_reasons:
            lines.append(f"- {r}")

    if not packaging_ready:
        partial_n = int(metrics.get("partial_file_count", 0))
        min_partial_packaging = 5
        ts_pos_n = int(metrics.get("timestamp_positive_count", 0))
        lines.extend(
            [
                "",
                "## Release packaging blockers (explicit)",
                "",
                "- Labels/conditions are incomplete or only partially inferred for this holdout.",
                (
                    f"- Only {partial_n} labelled partial-positive file(s) are available in this testing set, "
                    f"which is below the minimum {min_partial_packaging} required for release-packaging evaluation."
                ),
            ]
        )
        if ts_pos_n == 0:
            lines.append(
                "- Timestamp localization cannot be scored when no timestamp-positive cascade outputs exist."
            )
        else:
            lines.append(
                f"- Timestamp localization evidence is limited (timestamp_positive_count={ts_pos_n}; "
                "insufficient for packaging-quality localization assessment)."
            )
        if failed_n:
            lines.append(
                f"- {failed_n} file(s) failed/skipped; see error cases CSV and overlap audit before any packaging step."
            )
        lines.append(
            "- Independent testing set is small; false partial evidence cases (e.g. on direct-condition files) "
            "must be reviewed before any packaging step."
        )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Independent holdout depends on overlap audit; filenames/paths may collide with training.",
            "- Live acoustic/SSL extraction is used when phase8e0 masters lack the file.",
            "- Does not establish legally admissible authentication proof; separate evidence axes remain required.",
            "- Outputs are candidate indicators for manual review, not final authenticity verdicts.",
            "",
            "## Recommended next action",
            "",
            assessment if packaging_ready else (
                "Review overlap audit and metrics; address false partial rates or recall before "
                "any release packaging evaluation. Manual review of candidate segments remains required."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import traceback

    args = parse_args()
    show = not args.no_progress
    root = repo_root_from_here(Path(__file__))
    out_dir = Path(args.output_dir)
    p5b_dir = Path(args.p5b_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    if not p5b_dir.is_absolute():
        p5b_dir = (root / p5b_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    input_root = resolve_testing_input_root(root, args.input_root)
    run_status = init_p5d_run_status(out_dir, input_root)

    try:
        return _run_p5d_evaluation(
            args=args,
            show=show,
            root=root,
            out_dir=out_dir,
            p5b_dir=p5b_dir,
            input_root=input_root,
            run_status=run_status,
        )
    except BaseException as exc:
        run_status["status"] = "failed"
        run_status["error_message"] = str(exc)
        run_status["traceback_summary"] = traceback.format_exc()[-4000:]
        run_status["output_generation_complete"] = False
        run_status["run_completed_at"] = now_utc_str()
        write_p5d_run_status(out_dir, run_status)
        raise


def _run_p5d_evaluation(
    *,
    args: argparse.Namespace,
    show: bool,
    root: Path,
    out_dir: Path,
    p5b_dir: Path,
    input_root: Path,
    run_status: dict[str, Any],
) -> int:
    scanned_dirs = [
        d.name
        for d in sorted(input_root.iterdir())
        if d.is_dir() and d.name.lower() in P5D_ALLOWED_TEST_GROUPS
    ]

    progress("Loading P5B experimental candidate models...", enabled=show)
    artifacts = load_p5b_candidate_artifacts(p5b_dir)

    progress("Building independent evaluation manifest...", enabled=show)
    phase7_lookup = load_phase7_testing_label_lookup(root)
    manifest_rows = scan_testing_audio(input_root, root, phase7_lookup=phase7_lookup)
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(out_dir / "phase9d_p5d_independent_manifest.csv", index=False)

    fg_path = Path(args.file_gate_dataset) if Path(args.file_gate_dataset).is_absolute() else root / args.file_gate_dataset
    sg_path = Path(args.segment_dataset) if Path(args.segment_dataset).is_absolute() else root / args.segment_dataset
    file_gate_df = load_dataset_csv(fg_path)
    segment_df = load_dataset_csv(sg_path)

    p5c_path = Path(args.p5c_manifest) if Path(args.p5c_manifest).is_absolute() else root / args.p5c_manifest
    p5c_manifest = pd.read_csv(p5c_path, low_memory=False) if p5c_path.is_file() else pd.DataFrame()

    overlap_df = build_p5d_overlap_audit(manifest, file_gate_df, segment_df, p5c_manifest, root)
    overlap_df.to_csv(out_dir / "phase9d_p5d_overlap_audit.csv", index=False)
    manifest["source_split_status"] = manifest["file_path"].map(
        dict(zip(overlap_df["file_path"], overlap_df["overlap_status"]))
    )

    overlap_md = [
        "# Phase 9D-P5D Overlap Audit",
        "",
        f"Generated: {now_utc_str()}",
        "",
        f"- Input root: `{input_root}`",
        f"- Independent holdout: {(overlap_df['overlap_status'] == 'independent_holdout').sum()}",
        f"- Seen in P5 training: {(overlap_df['overlap_status'] == 'seen_in_p5_training').sum()}",
        f"- Seen in P5C controlled: {(overlap_df['overlap_status'] == 'seen_in_p5c_controlled').sum()}",
        f"- Unknown: {(overlap_df['overlap_status'] == 'unknown_overlap_status').sum()}",
        "",
    ]
    if (overlap_df["overlap_status"] == "independent_holdout").sum() == 0:
        overlap_md.append(
            "**Blocked:** No independent holdout files — release packaging evaluation must not proceed on this run alone."
        )
    (out_dir / "phase9d_p5d_overlap_audit.md").write_text("\n".join(overlap_md) + "\n", encoding="utf-8")

    fm_path = Path(args.file_master) if Path(args.file_master).is_absolute() else root / args.file_master
    sm_path = Path(args.segment_master) if Path(args.segment_master).is_absolute() else root / args.segment_master
    file_master = pd.read_csv(fm_path, low_memory=False) if fm_path.is_file() else pd.DataFrame()
    segment_master = pd.read_csv(sm_path, low_memory=False) if sm_path.is_file() else pd.DataFrame()

    progress("Running independent cascade inference (live extraction when needed)...", enabled=show)
    import time
    t_eval0 = time.perf_counter()
    ssl_chunk_hop = args.ssl_chunk_hop_sec
    if ssl_chunk_hop is None:
        ssl_chunk_hop = float(args.ssl_chunk_sec)

    file_pred, seg_pred, error_list, robustness_stats = evaluate_manifest_cascade(
        manifest=manifest,
        overlap_df=overlap_df,
        file_master=file_master,
        segment_master=segment_master,
        artifacts=artifacts,
        root=root,
        show=show,
        progress_fn=lambda msg: progress(msg, enabled=show),
        use_live_extraction=True,
        ssl_device=args.ssl_device,
        disable_ssl_cpu_fallback=args.disable_ssl_cpu_fallback,
        disable_ssl_chunked_fallback=args.disable_ssl_chunked_fallback,
        ssl_chunk_sec=float(args.ssl_chunk_sec),
        ssl_chunk_hop_sec=ssl_chunk_hop,
        ssl_chunk_max_chunks=int(args.ssl_chunk_max_chunks),
        prefer_cpu_for_long_audio=bool(args.prefer_cpu_for_long_audio),
        long_audio_sec=float(args.long_audio_sec),
        max_audio_duration_sec=args.max_audio_duration_sec,
        max_segments_per_file=args.max_segments_per_file,
    )
    robustness_stats["evaluation_runtime_seconds"] = float(time.perf_counter() - t_eval0)
    file_pred = normalize_file_predictions(file_pred)
    file_pred.to_csv(out_dir / "phase9d_p5d_file_predictions.csv", index=False)
    if seg_pred.empty:
        seg_pred = pd.DataFrame(columns=SEG_PRED_COLUMNS)
    else:
        for c in SEG_PRED_COLUMNS:
            if c not in seg_pred.columns:
                seg_pred[c] = np.nan
        seg_pred = seg_pred.reindex(columns=SEG_PRED_COLUMNS)
    seg_pred.to_csv(out_dir / "phase9d_p5d_segment_predictions.csv", index=False)

    err_df = pd.DataFrame(error_list)
    if not err_df.empty and "failure_type" in err_df.columns:
        err_df["failure_type"] = (
            err_df["failure_type"]
            .replace(
                {
                    "feature_extraction_failure": "acoustic_feature_failure",
                    "file_gate_predict_failure": "prediction_failure",
                    "segment_predict_failure": "prediction_failure",
                }
            )
            .fillna("prediction_failure")
        )
    if err_df.empty:
        err_df = pd.DataFrame(columns=["file_path", "failure_type", "error_message"])
    err_df.to_csv(out_dir / "phase9d_p5d_error_cases.csv", index=False)

    metrics = compute_p5d_metrics(file_pred, overlap_df, robustness_stats=robustness_stats)
    metrics["accepted_cascade_thresholds"] = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    csv_row = {
        k: ("" if v is None else v)
        for k, v in metrics.items()
        if k
        not in (
            "folder_wise",
            "unknown_condition_positive_rate_status",
            "median_candidate_timestamp_error_missing_reason",
        )
    }
    pd.DataFrame([csv_row]).to_csv(out_dir / "phase9d_p5d_independent_metrics.csv", index=False)

    def _json_default(val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, float) and np.isnan(val):
            return None
        return str(val) if isinstance(val, (np.floating, np.integer)) else val

    (out_dir / "phase9d_p5d_independent_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=_json_default), encoding="utf-8"
    )

    lbl_ok = labels_complete(manifest)
    has_partial = int(metrics.get("partial_file_count", 0)) > 0
    has_ts = int(metrics.get("timestamp_positive_count", 0)) > 0
    assessment, packaging_ready, failure_reasons = assess_p5d_release_readiness(
        metrics,
        labels_complete=lbl_ok,
        has_partial_positives=has_partial,
        has_timestamp_positives=has_ts,
    )

    ok = file_pred[file_pred["error_status"].astype(str) == "ok"]
    examples_success = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(1)
    ].sort_values("max_segment_probability", ascending=False)
    examples_false = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(0)
    ].sort_values("file_gate_probability", ascending=False)

    write_p5d_report(
        out_dir / "phase9d_p5d_independent_evaluation_report.md",
        input_root=input_root,
        scanned_groups=scanned_dirs,
        manifest=manifest,
        overlap_df=overlap_df,
        metrics=metrics,
        artifacts=artifacts,
        assessment=assessment,
        packaging_ready=packaging_ready,
        failure_reasons=failure_reasons,
        examples_success=examples_success,
        examples_false=examples_false,
        file_pred=file_pred,
    )

    if args.make_plots:
        progress("P5D: --make_plots requested; no plots implemented in P5D v1.", enabled=show)

    run_status["status"] = "completed"
    run_status["run_completed_at"] = now_utc_str()
    run_status["output_generation_complete"] = True
    run_status["error_message"] = ""
    run_status["traceback_summary"] = ""
    write_p5d_run_status(out_dir, run_status)

    progress(f"P5D complete. Outputs: {out_dir}", enabled=show)
    progress("No release packaging performed.", enabled=show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
