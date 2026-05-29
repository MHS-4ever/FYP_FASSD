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
    "has_timestamp_label",
    "candidate_timestamp_error_seconds",
    "top1_timestamp_hit",
    "top3_timestamp_hit",
    "top5_timestamp_hit",
    "error_status",
    "error_message",
]

SEG_PRED_COLUMNS = [
    "file_path",
    "file_name",
    "segment_index",
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

    report_text = (
        (in_dir / "phase9d_p5d_independent_evaluation_report.md").read_text(encoding="utf-8")
        if (in_dir / "phase9d_p5d_independent_evaluation_report.md").is_file()
        else ""
    )
    forbidden_hits = _forbidden_phrase_hits(report_text)
    checks.append(_check("report_forbidden_wording", not forbidden_hits, ", ".join(forbidden_hits)))

    missing_th = [ln for ln in REQUIRED_THRESHOLD_LINES if ln not in report_text]
    checks.append(_check("accepted_thresholds_documented", not missing_th, ", ".join(missing_th)))

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
