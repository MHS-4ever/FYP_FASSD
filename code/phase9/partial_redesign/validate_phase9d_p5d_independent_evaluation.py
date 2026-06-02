#!/usr/bin/env python3
"""Validate Phase 9D-P5D independent evaluation outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_evaluation_shared import (
    outputs_newer_than_run_start,
    p5d_run_status_path,
)
from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5C_CANDIDATE_MODEL_NAMES,
    P5D_RUN_STATUS_FILENAME,
    assess_p5d_release_readiness,
    evaluate_p5d_release_gates,
    p5c_candidate_models_dir,
    repo_root_from_here,
)

REQUIRED_OUTPUTS = [
    "phase9d_p5d_independent_manifest.csv",
    "phase9d_p5d_overlap_audit.csv",
    "phase9d_p5d_overlap_audit.md",
    "phase9d_p5d_file_predictions.csv",
    "phase9d_p5d_segment_predictions.csv",
    "phase9d_p5d_independent_metrics.csv",
    "phase9d_p5d_independent_metrics.json",
    "phase9d_p5d_error_cases.csv",
    "phase9d_p5d_independent_evaluation_report.md",
]

MANIFEST_COLUMNS = [
    "file_path",
    "file_name",
    "file_stem",
    "parent_folder",
    "test_group",
    "expected_condition",
    "expected_partial_label",
    "has_timestamp_label",
    "manifest_status",
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

METRIC_KEYS = [
    "total_files",
    "evaluated_files",
    "failed_files",
    "independent_holdout_count",
    "seen_in_p5_training_count",
    "seen_in_p5c_controlled_count",
    "unknown_overlap_count",
    "partial_file_count",
    "non_partial_file_count",
    "direct_condition_count",
    "replay_condition_count",
    "mixer_condition_count",
    "unknown_condition_count",
    "partial_evidence_recall",
    "non_partial_false_alarm_rate",
    "direct_false_partial_rate",
    "replay_false_partial_rate",
    "mixer_false_partial_rate",
    "unknown_condition_positive_rate",
    "broad_activation_rate_when_positive",
    "top1_hit_rate_when_positive",
    "top3_hit_rate_when_positive",
    "top5_hit_rate_when_positive",
    "timestamp_positive_count",
    "timestamp_error_count",
    "median_candidate_timestamp_error_seconds",
    "median_candidate_timestamp_error_available",
    "candidate_rank1_consistency_count",
    "candidate_rank1_consistency_rate",
    "candidate_segment_probability_available_rate",
    "mp4_file_count",
    "mp4_evaluated_count",
    "mp4_failed_count",
    "mp4_load_success_rate",
    "ssl_cuda_oom_count",
    "ssl_cpu_fallback_attempt_count",
    "ssl_cpu_fallback_success_count",
    "ssl_cpu_fallback_failure_count",
    "ssl_cpu_fallback_skipped_long_audio_count",
    "ssl_chunked_fallback_attempt_count",
    "ssl_chunked_fallback_success_count",
    "ssl_chunked_fallback_failure_count",
    "ssl_chunked_cpu_fallback_attempt_count",
    "ssl_chunked_cpu_fallback_success_count",
    "ssl_chunked_cpu_fallback_failure_count",
    "ssl_long_audio_file_count",
    "ssl_long_audio_recovered_count",
    "ssl_long_audio_failed_count",
    "ssl_chunked_embedding_used_count",
    "ssl_chunked_embedding_max_chunks_observed",
    "robustness_failed_file_count",
    "robustness_recovered_file_count",
    "evaluation_runtime_seconds",
    "invalid_file_handling_pass_rate",
]

CORE_FINITE_METRICS = frozenset(
    {
        "total_files",
        "evaluated_files",
        "failed_files",
        "independent_holdout_count",
        "seen_in_p5_training_count",
        "seen_in_p5c_controlled_count",
        "unknown_overlap_count",
        "partial_file_count",
        "non_partial_file_count",
        "direct_condition_count",
        "replay_condition_count",
        "mixer_condition_count",
        "unknown_condition_count",
        "timestamp_positive_count",
        "timestamp_error_count",
        "invalid_file_handling_pass_rate",
    }
)

OPTIONAL_METRIC_NA_RULES: dict[str, str] = {
    "unknown_condition_positive_rate": "unknown_condition_count",
    "direct_false_partial_rate": "direct_condition_count",
    "replay_false_partial_rate": "replay_condition_count",
    "mixer_false_partial_rate": "mixer_condition_count",
    "partial_evidence_recall": "partial_file_count",
    "non_partial_false_alarm_rate": "non_partial_file_count",
    "broad_activation_rate_when_positive": "partial_evidence_positive_file_count",
    "top1_hit_rate_when_positive": "timestamp_positive_count",
    "top3_hit_rate_when_positive": "timestamp_positive_count",
    "top5_hit_rate_when_positive": "timestamp_positive_count",
    "median_candidate_timestamp_error_seconds": "timestamp_error_count",
}


def _median_timestamp_error_metric_ok(metrics: dict[str, Any]) -> tuple[bool, str]:
    """Return (ok, detail) for median_candidate_timestamp_error_seconds finiteness rule."""
    ts_pos = int(metrics.get("timestamp_positive_count", 0))
    err_count = int(metrics.get("timestamp_error_count", 0))
    val = metrics.get("median_candidate_timestamp_error_seconds")
    if ts_pos == 0:
        return True, "no timestamp-positive files"
    if err_count > 0:
        if _metric_value_is_missing(val):
            return False, f"timestamp_error_count={err_count} but median missing"
        try:
            if not np.isfinite(float(val)):
                return False, f"median not finite: {val}"
        except (TypeError, ValueError):
            return False, f"median not numeric: {val}"
        return True, f"median computed from {err_count} error(s)"
    reason = str(metrics.get("median_candidate_timestamp_error_missing_reason", "")).strip()
    available = metrics.get("median_candidate_timestamp_error_available")
    if ts_pos > 0 and not available and reason:
        return True, reason
    return False, "timestamp-positive files without median or documented missing reason"

FORBIDDEN_REPORT_PHRASES = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court-ready",
    "court ready",
    "production-ready proof",
    "production ready proof",
    "final verdict",
]

REQUIRED_THRESHOLD_LINES = [
    f"file_gate_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['file_gate_threshold']}",
    f"segment_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['segment_threshold']}",
    f"contrast_threshold = {P5C_ACCEPTED_CASCADE_THRESHOLDS['contrast_threshold']}",
    f"broad_limit = {P5C_ACCEPTED_CASCADE_THRESHOLDS['broad_limit']}",
]

TIMESTAMP_METRICS = {
    "top1_hit_rate_when_positive",
    "top3_hit_rate_when_positive",
    "top5_hit_rate_when_positive",
    "median_candidate_timestamp_error_seconds",
}

def _metric_missing_allowed(metric_key: str, metrics: dict[str, Any]) -> bool:
    """True when null/NaN is expected because the stratum has zero evaluated files."""
    count_key = OPTIONAL_METRIC_NA_RULES.get(metric_key)
    if count_key is None:
        return False
    return int(metrics.get(count_key, 0)) == 0


def _metric_value_is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return False


FORBIDDEN_ARTIFACT_PATH_FRAGMENTS = (
    "release/models/reference",
    "reference/aasist",
    "reference/hybrid_resnet",
    "release/models/partial_segment",
    "release/models/partial_file_gate",
    "models_saved/active/",
)

REFERENCE_ACTIVE_PHRASES = (
    "reference models were used",
    "reference models were active",
    "reference models were enabled",
    "reference models were loaded",
    "reference models were fused",
    "aasist was used",
    "aasist was active",
    "aasist was enabled",
    "aasist was loaded",
    "aasist was fused",
    "hybridresnet was used",
    "hybrid resnet was used",
    "hybridresnet was active",
    "hybrid resnet was active",
    "hybridresnet was enabled",
    "hybrid resnet was enabled",
    "hybridresnet was loaded",
    "hybrid resnet was loaded",
    "hybridresnet was fused",
    "hybrid resnet was fused",
)

FORBIDDEN_PRED_COL_FRAGMENTS = (
    "aasist_prob",
    "aasist_score",
    "hybrid_resnet",
    "hybridresnet",
    "reference_fusion",
    "fusion_score",
)

ROBUST_FAILURE_TYPES = {
    "load_failure",
    "unsupported_container_or_decoder_missing",
    "no_audio_stream",
    "too_short",
    "silent_or_invalid",
    "acoustic_feature_failure",
    "ssl_cuda_oom",
    "ssl_cuda_oom_cpu_fallback_failed",
    "ssl_chunked_fallback_failed",
    "ssl_embedding_failure",
    "model_feature_mismatch",
    "prediction_failure",
}


def _ssl_oom_recovery_reported_ok(metrics: dict[str, Any]) -> tuple[bool, str]:
    """CUDA OOM is handled if full CPU or chunked (incl. chunked CPU) fallback was attempted and documented."""
    oom = int(metrics.get("ssl_cuda_oom_count", 0))
    cpu_attempts = int(metrics.get("ssl_cpu_fallback_attempt_count", 0))
    cpu_success = int(metrics.get("ssl_cpu_fallback_success_count", 0))
    cpu_failure = int(metrics.get("ssl_cpu_fallback_failure_count", 0))
    chunked_attempts = int(metrics.get("ssl_chunked_fallback_attempt_count", 0))
    chunked_success = int(metrics.get("ssl_chunked_fallback_success_count", 0))
    chunked_failure = int(metrics.get("ssl_chunked_fallback_failure_count", 0))
    chunked_cpu_attempts = int(metrics.get("ssl_chunked_cpu_fallback_attempt_count", 0))
    chunked_cpu_success = int(metrics.get("ssl_chunked_cpu_fallback_success_count", 0))
    chunked_cpu_failure = int(metrics.get("ssl_chunked_cpu_fallback_failure_count", 0))
    detail = (
        f"oom={oom} cpu_attempts={cpu_attempts} cpu_success={cpu_success} cpu_failure={cpu_failure} "
        f"chunked_attempts={chunked_attempts} chunked_success={chunked_success} chunked_failure={chunked_failure} "
        f"chunked_cpu_attempts={chunked_cpu_attempts} chunked_cpu_success={chunked_cpu_success} "
        f"chunked_cpu_failure={chunked_cpu_failure}"
    )
    if oom <= 0:
        return True, detail
    recovery_attempted = (
        cpu_attempts >= 1 or chunked_attempts >= 1 or chunked_cpu_attempts >= 1
    )
    recovery_documented = any(
        count >= 1
        for count in (
            cpu_success,
            cpu_failure,
            chunked_success,
            chunked_failure,
            chunked_cpu_success,
            chunked_cpu_failure,
        )
    )
    return recovery_attempted and recovery_documented, detail


def _norm_path_text(text: str) -> str:
    return str(text).replace("\\", "/").lower()


def _forbidden_phrase_hits(report_text: str) -> list[str]:
    hits: list[str] = []
    for line in report_text.splitlines():
        low = line.lower()
        for phrase in FORBIDDEN_REPORT_PHRASES:
            if phrase not in low:
                continue
            if any(neg in low for neg in ("not ", "no ", "does not ", "do not ", "without ", "excluded")):
                continue
            hits.append(phrase)
    return sorted(set(hits))


def _collect_path_strings(*text_blobs: str) -> str:
    return "\n".join(t for t in text_blobs if t)


def _path_has_forbidden_fragment(path_text: str) -> list[str]:
    norm = _norm_path_text(path_text)
    hits: list[str] = []
    for frag in FORBIDDEN_ARTIFACT_PATH_FRAGMENTS:
        if frag in norm:
            hits.append(frag)
    # Block models_saved/active only when used as a model directory, not safety prose.
    if "models_saved/active" in norm and "nothing written to" not in path_text.lower():
        if any(tok in norm for tok in ("/models_saved/active/", "\\models_saved\\active\\")):
            if "models_saved/active/" not in hits and "models_saved/active" not in hits:
                hits.append("models_saved/active (artifact path)")
    return hits


def _load_run_status(in_dir: Path) -> tuple[dict[str, Any] | None, str]:
    path = p5d_run_status_path(in_dir)
    if not path.is_file():
        return None, "run status file missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except json.JSONDecodeError as exc:
        return None, f"run status JSON invalid: {exc}"


def _report_claims_reference_models_active(report_text: str) -> list[str]:
    low = report_text.lower()
    return [p for p in REFERENCE_ACTIVE_PHRASES if p in low]


def _forbidden_prediction_columns(columns: list[str]) -> list[str]:
    hits: list[str] = []
    for col in columns:
        cl = col.lower()
        if any(frag in cl for frag in FORBIDDEN_PRED_COL_FRAGMENTS):
            hits.append(col)
    return hits


def _artifact_under_p5b_candidate(path: Path, p5b_dir: Path) -> bool:
    try:
        path.resolve().relative_to(p5c_candidate_models_dir(p5b_dir).resolve())
        return True
    except ValueError:
        return False


def audit_model_artifacts(
    *,
    cand_dir: Path,
    p5b_dir: Path,
    report_text: str,
    metrics: dict[str, Any],
    file_pred: pd.DataFrame,
    seg_pred: pd.DataFrame,
) -> tuple[dict[str, Any], list[str]]:
    """
    Build model artifact audit and return (audit_dict, failure_reasons).

    Does not fail on mere mention of reference architecture names; checks paths,
    active-use claims, and forbidden prediction columns.
    """
    fg_path = (cand_dir / P5C_CANDIDATE_MODEL_NAMES["file_gate"]).resolve()
    sg_path = (cand_dir / P5C_CANDIDATE_MODEL_NAMES["segment_localizer"]).resolve()
    cfg_path = (cand_dir / P5C_CANDIDATE_MODEL_NAMES["cascade_config"]).resolve()

    artifact_paths_blob = _collect_path_strings(str(fg_path), str(sg_path), str(cfg_path))
    forbidden_frags = _path_has_forbidden_fragment(artifact_paths_blob)

    reference_used = bool(forbidden_frags) or bool(_report_claims_reference_models_active(report_text))
    old_release_partial = any(
        frag in forbidden_frags
        for frag in (
            "release/models/partial_segment",
            "release/models/partial_file_gate",
        )
    )
    release_partial_used = old_release_partial

    audit: dict[str, Any] = {
        "file_gate_model_path": str(fg_path),
        "segment_localizer_model_path": str(sg_path),
        "cascade_config_path": str(cfg_path),
        "release_partial_model_used": release_partial_used,
        "reference_model_used": reference_used,
        "old_release_partial_model_used": old_release_partial,
    }

    failures: list[str] = []

    for label, path, expected_name in (
        ("file_gate", fg_path, P5C_CANDIDATE_MODEL_NAMES["file_gate"]),
        ("segment_localizer", sg_path, P5C_CANDIDATE_MODEL_NAMES["segment_localizer"]),
        ("cascade_config", cfg_path, P5C_CANDIDATE_MODEL_NAMES["cascade_config"]),
    ):
        if not path.is_file():
            failures.append(f"missing P5B candidate artifact: {expected_name}")
        elif path.name != expected_name:
            failures.append(f"unexpected artifact filename for {label}: {path.name}")
        elif not _artifact_under_p5b_candidate(path, p5b_dir):
            failures.append(f"{label} path not under phase9d_p5b/candidate_models: {path}")

    if forbidden_frags:
        failures.append(f"forbidden model path fragment(s): {', '.join(sorted(set(forbidden_frags)))}")

    active_claims = _report_claims_reference_models_active(report_text)
    if active_claims:
        failures.append(f"report claims reference models active: {active_claims[0]}")

    bad_cols = _forbidden_prediction_columns(list(file_pred.columns) + list(seg_pred.columns))
    if bad_cols:
        failures.append(f"forbidden prediction columns: {', '.join(bad_cols)}")

    p5b_stmt = (
        "only p5b experimental candidate artifacts were used" in report_text.lower()
        or "only p5b experimental candidate models were used" in report_text.lower()
    )
    if not p5b_stmt:
        failures.append("report missing P5B-only experimental candidate usage statement")

    return audit, failures


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5D independent evaluation outputs.")
    p.add_argument(
        "--input_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5d"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5d_independent_evaluation_validation_report.md"),
    )
    p.add_argument("--project_root", default=str(root))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    return p.parse_args()


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "pass": ok, "detail": detail}


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _candidate_segment_integrity_checks(file_pred: pd.DataFrame, seg_pred: pd.DataFrame) -> tuple[bool, str, bool, str]:
    """Return candidate_rank_valid, detail, candidate_match_valid, detail."""
    ok = file_pred[file_pred["error_status"].astype(str) == "ok"].copy()
    bad_rank: list[str] = []
    bad_match: list[str] = []
    for _, r in ok.iterrows():
        fp = str(r["file_path"])
        rank = pd.to_numeric(r.get("candidate_segment_rank"), errors="coerce")
        prob = pd.to_numeric(r.get("candidate_segment_probability"), errors="coerce")
        cs = pd.to_numeric(r.get("candidate_segment_start"), errors="coerce")
        ce = pd.to_numeric(r.get("candidate_segment_end"), errors="coerce")
        if not (np.isfinite(rank) and int(rank) == 1 and np.isfinite(prob) and np.isfinite(cs) and np.isfinite(ce)):
            bad_rank.append(fp)
            continue
        g = seg_pred[seg_pred["file_path"].astype(str) == fp]
        g1 = g[pd.to_numeric(g["segment_rank"], errors="coerce").eq(1)]
        if g1.empty:
            bad_match.append(f"{fp}:no_rank1")
            continue
        s = g1.iloc[0]
        s_start = float(pd.to_numeric(s["segment_start"], errors="coerce"))
        s_end = float(pd.to_numeric(s["segment_end"], errors="coerce"))
        s_prob = float(pd.to_numeric(s["segment_probability"], errors="coerce"))
        if not (
            abs(float(cs) - s_start) <= 1e-6
            and abs(float(ce) - s_end) <= 1e-6
            and abs(float(prob) - s_prob) <= 1e-6
        ):
            bad_match.append(fp)
    return (
        len(bad_rank) == 0,
        "ok" if not bad_rank else f"invalid rank/prob/start/end for {len(bad_rank)} file(s): {bad_rank[:3]}",
        len(bad_match) == 0,
        "ok" if not bad_match else f"candidate != rank1 segment for {len(bad_match)} file(s): {bad_match[:3]}",
    )


def _segment_index_rank_checks(seg_pred: pd.DataFrame) -> tuple[bool, str, bool, str]:
    """Return segment_index_chronological_valid + segment_rank_valid checks."""
    bad_idx: list[str] = []
    bad_rank: list[str] = []
    for fp, g in seg_pred.groupby("file_path"):
        gx = g.copy()
        gx["segment_index"] = pd.to_numeric(gx["segment_index"], errors="coerce")
        gx["segment_index_chronological"] = pd.to_numeric(gx["segment_index_chronological"], errors="coerce")
        gx["segment_rank"] = pd.to_numeric(gx["segment_rank"], errors="coerce")
        gx["segment_start"] = pd.to_numeric(gx["segment_start"], errors="coerce")
        gx["segment_probability"] = pd.to_numeric(gx["segment_probability"], errors="coerce")

        chrono = gx.sort_values("segment_start")["segment_index_chronological"].astype(int).tolist()
        same_index = (
            gx["segment_index"].astype(float).fillna(-1).to_numpy()
            == gx["segment_index_chronological"].astype(float).fillna(-2).to_numpy()
        ).all()
        if chrono != list(range(len(chrono))) or not same_index:
            bad_idx.append(str(fp))

        ranks = gx["segment_rank"].dropna().astype(int).tolist()
        expected = list(range(1, len(gx) + 1))
        rank1 = gx[gx["segment_rank"] == 1]
        max_prob = gx["segment_probability"].max()
        if sorted(ranks) != expected or len(set(ranks)) != len(ranks):
            bad_rank.append(str(fp))
        elif rank1.empty or abs(float(rank1.iloc[0]["segment_probability"]) - float(max_prob)) > 1e-9:
            bad_rank.append(str(fp))
    return (
        len(bad_idx) == 0,
        "ok" if not bad_idx else f"invalid segment index chronology in {len(bad_idx)} file(s): {bad_idx[:3]}",
        len(bad_rank) == 0,
        "ok" if not bad_rank else f"invalid segment ranks in {len(bad_rank)} file(s): {bad_rank[:3]}",
    )
    try:
        return pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root)
    in_dir = Path(args.input_dir)
    if not in_dir.is_absolute():
        in_dir = (root / in_dir).resolve()
    report_out = Path(args.report_out)
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    p5b_dir = Path(args.p5b_dir)
    if not p5b_dir.is_absolute():
        p5b_dir = (root / p5b_dir).resolve()
    cand_dir = p5c_candidate_models_dir(p5b_dir)

    report_path = in_dir / "phase9d_p5d_independent_evaluation_report.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""

    checks: list[dict] = []
    fresh_ok, fresh_detail = False, "run status not loaded"
    run_status, run_status_err = _load_run_status(in_dir)
    if run_status is None:
        checks.append(_check("run_status_present", False, run_status_err))
    else:
        checks.append(_check("run_status_present", True, P5D_RUN_STATUS_FILENAME))
        checks.append(
            _check(
                "run_status_completed",
                str(run_status.get("status", "")).lower() == "completed",
                f"status={run_status.get('status')}",
            )
        )
        checks.append(
            _check(
                "output_generation_complete",
                bool(run_status.get("output_generation_complete")) is True,
                str(run_status.get("output_generation_complete")),
            )
        )
        fresh_ok, fresh_detail = outputs_newer_than_run_start(
            in_dir, str(run_status.get("run_started_at", ""))
        )
        checks.append(_check("outputs_not_stale", fresh_ok, fresh_detail))

    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_output_files_exist", not missing, ", ".join(missing) if missing else "all present"))

    err_path = in_dir / "phase9d_p5d_error_cases.csv"
    if err_path.is_file() and err_path.stat().st_size > 0:
        err_df = _safe_read_csv(err_path)
        checks.append(_check("error_cases_has_header", len(err_df.columns) > 0, str(list(err_df.columns))))
        if not err_df.empty and "failure_type" in err_df.columns:
            bad_ft = sorted(set(err_df["failure_type"].dropna().astype(str)) - ROBUST_FAILURE_TYPES)
            checks.append(_check("error_case_failure_type_valid", len(bad_ft) == 0, ", ".join(bad_ft)))
    else:
        checks.append(_check("error_cases_has_header", err_path.is_file(), "file missing or empty"))

    manifest = _safe_read_csv(in_dir / "phase9d_p5d_independent_manifest.csv")
    missing_manifest_cols = [c for c in MANIFEST_COLUMNS if c not in manifest.columns]
    checks.append(
        _check("manifest_required_columns", not missing_manifest_cols, ", ".join(missing_manifest_cols))
    )

    file_pred = _safe_read_csv(in_dir / "phase9d_p5d_file_predictions.csv")
    missing_fp = [c for c in FILE_PRED_COLUMNS if c not in file_pred.columns]
    checks.append(_check("file_predictions_required_columns", not missing_fp, ", ".join(missing_fp)))

    seg_path = in_dir / "phase9d_p5d_segment_predictions.csv"
    seg_file_ok = seg_path.is_file()
    checks.append(
        _check("segment_predictions_file_exists", seg_file_ok, "phase9d_p5d_segment_predictions.csv")
    )
    seg_pred = _safe_read_csv(seg_path)
    if seg_file_ok and seg_path.stat().st_size > 0:
        try:
            seg_cols = pd.read_csv(seg_path, nrows=0).columns.tolist()
        except pd.errors.EmptyDataError:
            seg_cols = []
    else:
        seg_cols = list(seg_pred.columns)
    missing_sp = [c for c in SEG_PRED_COLUMNS if c not in seg_cols]
    checks.append(_check("segment_predictions_required_columns", not missing_sp, ", ".join(missing_sp)))
    if not seg_pred.empty and not file_pred.empty and not missing_sp and not missing_fp:
        rank_ok, rank_detail, match_ok, match_detail = _candidate_segment_integrity_checks(file_pred, seg_pred)
        checks.append(_check("candidate_segment_rank_valid", rank_ok, rank_detail))
        checks.append(_check("candidate_matches_rank1_segment", match_ok, match_detail))
        idx_ok, idx_detail, sr_ok, sr_detail = _segment_index_rank_checks(seg_pred)
        checks.append(_check("segment_index_chronological_valid", idx_ok, idx_detail))
        checks.append(_check("segment_rank_valid", sr_ok, sr_detail))

    metrics: dict[str, Any] = {}
    metrics_path = in_dir / "phase9d_p5d_independent_metrics.json"
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    missing_metrics = [k for k in METRIC_KEYS if k not in metrics]
    checks.append(_check("metrics_required_keys", not missing_metrics, ", ".join(missing_metrics)))

    if "partial_evidence_positive_file_count" not in metrics:
        metrics["partial_evidence_positive_file_count"] = int(metrics.get("timestamp_positive_count", 0))

    median_ok, median_detail = _median_timestamp_error_metric_ok(metrics)
    checks.append(_check("median_candidate_timestamp_error_rule", median_ok, median_detail))

    non_finite: list[str] = []
    for k, v in metrics.items():
        if k in (
            "folder_wise",
            "accepted_cascade_thresholds",
            "unknown_condition_positive_rate_status",
            "median_candidate_timestamp_error_missing_reason",
            "median_candidate_timestamp_error_available",
        ):
            continue
        if k == "median_candidate_timestamp_error_seconds":
            continue
        if _metric_value_is_missing(v):
            if _metric_missing_allowed(k, metrics):
                continue
            if k in CORE_FINITE_METRICS:
                non_finite.append(f"{k} (required, missing)")
            else:
                non_finite.append(f"{k} (missing, stratum non-empty)")
            continue
        try:
            fv = float(v)
            if not np.isfinite(fv):
                if _metric_missing_allowed(k, metrics):
                    continue
                non_finite.append(k)
        except (TypeError, ValueError):
            if k in CORE_FINITE_METRICS:
                non_finite.append(f"{k} (non-numeric)")
    checks.append(_check("metrics_finite_where_applicable", not non_finite, ", ".join(non_finite)))
    checks.append(
        _check(
            "robustness_metrics_present",
            all(k in metrics for k in (
                "mp4_file_count",
                "mp4_evaluated_count",
                "mp4_failed_count",
                "mp4_load_success_rate",
                "ssl_cuda_oom_count",
                "ssl_cpu_fallback_attempt_count",
                "ssl_cpu_fallback_success_count",
                "ssl_cpu_fallback_failure_count",
                "ssl_cpu_fallback_skipped_long_audio_count",
                "ssl_chunked_fallback_attempt_count",
                "ssl_chunked_fallback_success_count",
                "ssl_chunked_fallback_failure_count",
                "ssl_chunked_cpu_fallback_attempt_count",
                "ssl_chunked_cpu_fallback_success_count",
                "ssl_chunked_cpu_fallback_failure_count",
                "ssl_long_audio_file_count",
                "ssl_long_audio_recovered_count",
                "ssl_long_audio_failed_count",
                "ssl_chunked_embedding_used_count",
                "ssl_chunked_embedding_max_chunks_observed",
                "robustness_failed_file_count",
                "robustness_recovered_file_count",
            )),
            "",
        )
    )
    if int(metrics.get("mp4_file_count", 0)) > 0:
        checks.append(
            _check(
                "mp4_robustness_reported",
                int(metrics.get("mp4_evaluated_count", -1)) + int(metrics.get("mp4_failed_count", -1))
                == int(metrics.get("mp4_file_count", 0)),
                f"mp4_total={metrics.get('mp4_file_count')} ok={metrics.get('mp4_evaluated_count')} fail={metrics.get('mp4_failed_count')}",
            )
        )
    if int(metrics.get("ssl_cuda_oom_count", 0)) > 0:
        oom_recovery_ok, oom_recovery_detail = _ssl_oom_recovery_reported_ok(metrics)
        checks.append(
            _check(
                "ssl_oom_fallback_reported",
                oom_recovery_ok,
                oom_recovery_detail,
            )
        )
    if err_path.is_file() and err_path.stat().st_size > 0:
        err_df = _safe_read_csv(err_path)
        ssl_related = err_df["failure_type"].astype(str).isin(
            {"ssl_cuda_oom", "ssl_cuda_oom_cpu_fallback_failed", "ssl_chunked_fallback_failed"}
        ).sum() if not err_df.empty and "failure_type" in err_df.columns else 0
        ssl_fallback_failed = err_df["failure_type"].astype(str).eq(
            "ssl_cuda_oom_cpu_fallback_failed"
        ).sum() if not err_df.empty and "failure_type" in err_df.columns else 0
        ssl_chunked_failed = err_df["failure_type"].astype(str).eq(
            "ssl_chunked_fallback_failed"
        ).sum() if not err_df.empty and "failure_type" in err_df.columns else 0
        long_skip = err_df["error_message"].astype(str).str.contains(
            "CPU fallback skipped for long audio", na=False
        ).sum() if not err_df.empty and "error_message" in err_df.columns else 0
        checks.append(
            _check(
                "robustness_ssl_counters_match_error_cases",
                (
                    (ssl_related == 0 or int(metrics.get("ssl_cuda_oom_count", 0)) >= 1)
                    and (ssl_fallback_failed == 0 or int(metrics.get("ssl_cpu_fallback_attempt_count", 0)) >= 1)
                    and (ssl_fallback_failed == 0 or int(metrics.get("ssl_cpu_fallback_failure_count", 0)) >= 1)
                    and (long_skip == 0 or int(metrics.get("ssl_cpu_fallback_skipped_long_audio_count", 0)) >= 1)
                    and (
                        ssl_chunked_failed == 0
                        or int(metrics.get("ssl_chunked_fallback_failure_count", 0)) >= 1
                    )
                ),
                (
                    f"ssl_related={ssl_related}, ssl_fallback_failed={ssl_fallback_failed}, "
                    f"ssl_chunked_failed={ssl_chunked_failed}, long_skip={long_skip}, "
                    f"oom_count={metrics.get('ssl_cuda_oom_count', 0)}, "
                    f"fallback_attempt={metrics.get('ssl_cpu_fallback_attempt_count', 0)}, "
                    f"fallback_failure={metrics.get('ssl_cpu_fallback_failure_count', 0)}, "
                    f"skip_long={metrics.get('ssl_cpu_fallback_skipped_long_audio_count', 0)}, "
                    f"chunked_fail={metrics.get('ssl_chunked_fallback_failure_count', 0)}"
                ),
            )
        )

    long_audio_sec = 60.0
    if "audio_duration_sec" in file_pred.columns:
        dur_series = pd.to_numeric(file_pred["audio_duration_sec"], errors="coerce")
        long_files = dur_series[np.isfinite(dur_series) & (dur_series >= long_audio_sec)]
        if len(long_files) > 0:
            long_audio_reported = (
                int(metrics.get("ssl_long_audio_file_count", 0)) > 0
                and (
                    "long-audio" in report_text.lower()
                    or "long audio" in report_text.lower()
                    or "ssl_long_audio" in report_text.lower()
                )
            )
            checks.append(
                _check(
                    "long_audio_ssl_recovery_reported",
                    long_audio_reported,
                    f"long_files={len(long_files)} ssl_long_audio_file_count={metrics.get('ssl_long_audio_file_count', 0)}",
                )
            )

    chunked_attempts = int(metrics.get("ssl_chunked_fallback_attempt_count", 0))
    chunked_success = int(metrics.get("ssl_chunked_fallback_success_count", 0))
    chunked_failure = int(metrics.get("ssl_chunked_fallback_failure_count", 0))
    if chunked_attempts > 0:
        checks.append(
            _check(
                "chunked_fallback_counters_consistent",
                chunked_success + chunked_failure <= chunked_attempts
                and (chunked_success > 0 or chunked_failure > 0),
                f"attempts={chunked_attempts} success={chunked_success} failure={chunked_failure}",
            )
        )
    if "ssl_chunked_fallback_used" in file_pred.columns:
        chunked_used = int(file_pred["ssl_chunked_fallback_used"].astype(bool).sum())
        if chunked_used > 0:
            checks.append(
                _check(
                    "chunked_fallback_file_flags_consistent",
                    int(metrics.get("ssl_chunked_fallback_success_count", 0)) >= 1
                    and int(metrics.get("ssl_chunked_embedding_used_count", 0)) >= 1,
                    f"chunked_used={chunked_used} success={metrics.get('ssl_chunked_fallback_success_count', 0)}",
                )
            )

    t41_path = "testing_audios/t4/t4.1.mp3"
    t41_norm = file_pred["file_path"].astype(str).str.lower().str.replace("\\", "/") if not file_pred.empty else pd.Series(dtype=str)
    t41_mask = t41_norm == t41_path if len(t41_norm) else pd.Series(dtype=bool)
    t41_in_pred = bool(t41_mask.any()) if len(t41_mask) else False
    t41_in_err = False
    if err_path.is_file() and err_path.stat().st_size > 0:
        err_df_t41 = _safe_read_csv(err_path)
        if not err_df_t41.empty and "file_path" in err_df_t41.columns:
            t41_in_err = bool(
                (err_df_t41["file_path"].astype(str).str.lower().str.replace("\\", "/") == t41_path).any()
            )
    t41_ok = False
    t41_documented_fail = False
    if t41_in_pred:
        t41_row = file_pred.loc[t41_mask].iloc[0]
        t41_status = str(t41_row.get("error_status", ""))
        t41_ok = t41_status == "ok"
        t41_documented_fail = t41_status in (
            "ssl_chunked_fallback_failed",
            "ssl_cuda_oom_cpu_fallback_failed",
            "ssl_embedding_failure",
        )
    checks.append(
        _check(
            "previous_ssl_failure_recovered_or_documented",
            t41_in_pred and (t41_ok or t41_documented_fail),
            f"in_pred={t41_in_pred} ok={t41_ok} documented_fail={t41_documented_fail} in_err={t41_in_err}",
        )
    )

    non_ok_pred = int((file_pred["error_status"].astype(str) != "ok").sum()) if not file_pred.empty else 0
    err_rows = 0
    if err_path.is_file() and err_path.stat().st_size > 0:
        err_df_fc = _safe_read_csv(err_path)
        err_rows = len(err_df_fc) if not err_df_fc.empty else 0
    checks.append(
        _check(
            "failed_files_consistent_with_error_cases",
            int(metrics.get("failed_files", 0)) == non_ok_pred
            and (non_ok_pred == 0 or err_rows >= 1)
            and (non_ok_pred == err_rows or non_ok_pred <= err_rows),
            f"failed_files={metrics.get('failed_files', 0)} non_ok_pred={non_ok_pred} err_rows={err_rows}",
        )
    )

    forbidden_hits = _forbidden_phrase_hits(report_text)
    checks.append(_check("report_forbidden_wording", not forbidden_hits, ", ".join(forbidden_hits)))

    missing_th = [ln for ln in REQUIRED_THRESHOLD_LINES if ln not in report_text]
    checks.append(_check("accepted_thresholds_documented", not missing_th, ", ".join(missing_th)))
    checks.append(
        _check(
            "robustness_behavior_section_present",
            "robustness behavior" in report_text.lower(),
            "report must include robustness behavior section",
        )
    )

    release_hits = list((root / "release" / "models").rglob("phase9d_p5d*")) if (root / "release" / "models").is_dir() else []
    active_hits = list((root / "models_saved" / "active").rglob("phase9d_p5d*")) if (root / "models_saved" / "active").is_dir() else []
    checks.append(_check("no_release_models_writes", not release_hits, str(release_hits[:3])))
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:3])))

    artifact_audit, artifact_failures = audit_model_artifacts(
        cand_dir=cand_dir,
        p5b_dir=p5b_dir,
        report_text=report_text,
        metrics=metrics,
        file_pred=file_pred,
        seg_pred=seg_pred,
    )

    checks.append(
        _check(
            "p5b_only_candidate_artifacts",
            all(
                (cand_dir / name).is_file()
                for name in P5C_CANDIDATE_MODEL_NAMES.values()
            ),
            str(cand_dir),
        )
    )
    ref_usage_failures = [
        f
        for f in artifact_failures
        if any(
            k in f
            for k in (
                "forbidden model path",
                "reference models active",
                "forbidden prediction columns",
            )
        )
    ]
    checks.append(
        _check(
            "reference_models_not_activated",
            not artifact_audit["reference_model_used"] and not ref_usage_failures,
            "; ".join(ref_usage_failures[:5]) if ref_usage_failures else "ok",
        )
    )
    checks.append(
        _check(
            "p5b_only_model_usage_statement_in_report",
            (
                "only p5b experimental candidate artifacts were used" in report_text.lower()
                or "only p5b experimental candidate models were used" in report_text.lower()
            ),
            "report must state P5B-only experimental candidate usage",
        )
    )
    artifact_path_failures = [
        f for f in artifact_failures if f.startswith("missing") or f.startswith("unexpected") or "not under" in f
    ]
    if artifact_path_failures:
        checks.append(
            _check("p5b_candidate_artifact_paths", False, "; ".join(artifact_path_failures[:5]))
        )
    checks.append(
        _check(
            "release_partial_model_not_used",
            not artifact_audit["release_partial_model_used"],
            "release partial path detected" if artifact_audit["release_partial_model_used"] else "ok",
        )
    )
    checks.append(
        _check(
            "old_release_partial_model_not_used",
            not artifact_audit["old_release_partial_model_used"],
            "old release partial path detected" if artifact_audit["old_release_partial_model_used"] else "ok",
        )
    )

    holdout = int(metrics.get("independent_holdout_count", 0))
    if holdout == 0:
        blocked_ok = (
            "release packaging evaluation is blocked" in report_text.lower()
            or "no independent holdout" in report_text.lower()
        )
        checks.append(
            _check(
                "zero_holdout_blocks_packaging_in_report",
                blocked_ok,
                "report must block packaging when independent_holdout_count==0",
            )
        )

    lbl_complete = True
    if not manifest.empty and "expected_condition" in manifest.columns:
        conds = manifest["expected_condition"].astype(str)
        lbl_complete = float((conds == "unknown_testing_condition").mean()) < 0.5
        lbl_complete = lbl_complete and {"direct", "replay", "mixer_or_channel"}.issubset(set(conds.unique()))
    has_partial = int(metrics.get("partial_file_count", 0)) > 0
    has_ts = int(metrics.get("timestamp_positive_count", 0)) > 0
    release_gates = evaluate_p5d_release_gates(
        metrics,
        labels_complete=lbl_complete,
        has_partial_positives=has_partial,
        has_timestamp_positives=has_ts,
    )
    packaging_ready = bool(release_gates["release_packaging_ready"])
    _, assess_ready, assess_failures = assess_p5d_release_readiness(
        metrics,
        labels_complete=lbl_complete,
        has_partial_positives=has_partial,
        has_timestamp_positives=has_ts,
    )
    checks.append(
        _check(
            "release_packaging_gate_metrics",
            not packaging_ready,
            "; ".join(release_gates["failure_reasons"][:6]) if release_gates["failure_reasons"] else "unexpected ready",
        )
    )
    checks.append(
        _check(
            "release_assessment_aligned_with_gates",
            packaging_ready == assess_ready,
            f"gates={packaging_ready} assess={assess_ready}",
        )
    )
    report_says_yes = (
        "acceptable for release packaging evaluation" in report_text.lower()
        and re.search(r"\*\*yes\*\*", report_text, re.IGNORECASE) is not None
    )
    checks.append(_check("release_packaging_not_claimed_ready", not report_says_yes, f"report_yes={report_says_yes}"))
    if holdout == 0:
        checks.append(_check("packaging_matches_metrics_holdout", not report_says_yes, "must not claim ready with 0 holdout"))
    else:
        checks.append(
            _check(
                "packaging_recommendation_matches_metrics",
                report_says_yes == packaging_ready,
                f"report_yes={report_says_yes} metrics_ready={packaging_ready}",
            )
        )

    failed_n = int(metrics.get("failed_files", 0))
    checks.append(
        _check(
            "failed_files_reported_in_outputs",
            failed_n == 0 or err_path.is_file(),
            f"failed_files={failed_n}",
        )
    )
    limitations_present = (
        not lbl_complete
        or int(metrics.get("partial_file_count", 0)) < 5
        or failed_n > 0
        or int(metrics.get("timestamp_positive_count", 0)) == 0
    )
    checks.append(
        _check(
            "scientific_limitations_gate",
            (limitations_present and not packaging_ready) or (not limitations_present and packaging_ready),
            f"limitations_present={limitations_present} packaging_ready={packaging_ready}",
        )
    )
    blocked_in_report = (
        "release packaging blockers" in report_text.lower()
        or re.search(
            r"candidate acceptable for release packaging evaluation:\s*\*\*no\*\*",
            report_text,
            re.IGNORECASE,
        )
        is not None
    )
    checks.append(
        _check(
            "release_blockers_documented_in_report",
            (not packaging_ready and blocked_in_report) or packaging_ready,
            "report must document packaging blockers when not ready",
        )
    )
    checks.append(
        _check(
            "release_remains_blocked",
            not packaging_ready
            and int(metrics.get("partial_file_count", 0)) < 5,
            f"packaging_ready={packaging_ready} partial={metrics.get('partial_file_count', 0)} ts_pos={metrics.get('timestamp_positive_count', 0)}",
        )
    )

    all_pass = all(c["pass"] for c in checks)
    status = "PASS" if all_pass else "FAIL"

    run_status_lines = ["- run status: unavailable"]
    if run_status:
        run_status_lines = [
            f"- phase: {run_status.get('phase', '')}",
            f"- status: {run_status.get('status', '')}",
            f"- run_started_at: {run_status.get('run_started_at', '')}",
            f"- run_completed_at: {run_status.get('run_completed_at', '')}",
            f"- output_generation_complete: {run_status.get('output_generation_complete', False)}",
            f"- input_root: {run_status.get('input_root', '')}",
        ]
        if run_status.get("error_message"):
            run_status_lines.append(f"- error_message: {run_status.get('error_message')}")

    lines = [
        "# Phase 9D-P5D Independent Evaluation Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall:** {status}",
        "",
        "## Run status check",
        "",
        *run_status_lines,
        "",
        "## Stale output check",
        "",
        f"- outputs_not_stale: {fresh_ok if run_status else False} ({fresh_detail if run_status else run_status_err})",
        "",
        "## Model artifact audit",
        "",
        f"- file_gate_model_path: `{artifact_audit['file_gate_model_path']}`",
        f"- segment_localizer_model_path: `{artifact_audit['segment_localizer_model_path']}`",
        f"- cascade_config_path: `{artifact_audit['cascade_config_path']}`",
        f"- release_partial_model_used: {str(artifact_audit['release_partial_model_used']).lower()}",
        f"- reference_model_used: {str(artifact_audit['reference_model_used']).lower()}",
        f"- old_release_partial_model_used: {str(artifact_audit['old_release_partial_model_used']).lower()}",
        "",
        "## Release-readiness gate",
        "",
        f"- release_packaging_ready (metrics): {str(packaging_ready).lower()}",
    ]
    if release_gates["failure_reasons"]:
        lines.append("- blocking reasons:")
        for r in release_gates["failure_reasons"]:
            lines.append(f"  - {r}")
    lines.extend(
        [
            "",
            "## Scientific limitations gate",
            "",
            f"- labels_complete: {str(lbl_complete).lower()}",
            f"- partial_file_count: {metrics.get('partial_file_count', 0)}",
            f"- failed_files: {metrics.get('failed_files', 0)}",
            f"- timestamp_positive_count: {metrics.get('timestamp_positive_count', 0)}",
            "",
            "## Checks",
            "",
        ]
    )
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"- [{mark}] `{c['check']}`{detail}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validates P5D outputs only; does not run inference.",
            "- `reference_models_not_activated` checks artifact paths, active-use claims, and prediction columns — not bare architecture name mentions.",
            "- P5B experimental candidate models must exist under phase9d_p5b/candidate_models/.",
            "- No writes to release/models or models_saved/active.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"P5D validation {status}: {report_out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
