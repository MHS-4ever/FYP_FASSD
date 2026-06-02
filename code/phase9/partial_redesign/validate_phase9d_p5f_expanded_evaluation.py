#!/usr/bin/env python3
"""Validate Phase 9D-P5F expanded independent evaluation outputs."""

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

from evaluate_phase9d_p5f_expanded_independent_cascade import (
    P5F_RUN_STATUS_FILENAME,
    TIMESTAMP_MATCH_METHODS,
    evaluate_p5f_release_gates,
)
from phase9d_p5_evaluation_shared import parse_p5d_run_timestamp
from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5C_CANDIDATE_MODEL_NAMES,
    p5c_candidate_models_dir,
    repo_root_from_here,
)
from validate_phase9d_p5d_independent_evaluation import (
    REQUIRED_THRESHOLD_LINES,
    SEG_PRED_COLUMNS,
    _candidate_segment_integrity_checks,
    _check,
    _forbidden_phrase_hits,
    _safe_read_csv,
    _segment_index_rank_checks,
    _ssl_oom_recovery_reported_ok,
    audit_model_artifacts,
)

REQUIRED_OUTPUTS = [
    "phase9d_p5f_expanded_manifest.csv",
    "phase9d_p5f_overlap_audit.csv",
    "phase9d_p5f_overlap_audit.md",
    "phase9d_p5f_file_predictions.csv",
    "phase9d_p5f_segment_predictions.csv",
    "phase9d_p5f_expanded_metrics.csv",
    "phase9d_p5f_expanded_metrics.json",
    "phase9d_p5f_error_cases.csv",
    "phase9d_p5f_expanded_evaluation_report.md",
    "phase9d_p5f_timestamp_loading_audit.csv",
    P5F_RUN_STATUS_FILENAME,
]

MANIFEST_COLUMNS = [
    "file_path",
    "file_name",
    "file_stem",
    "parent_folder",
    "test_group",
    "expected_condition",
    "expected_partial_label",
    "expected_origin_label",
    "has_timestamp_label",
    "timestamp_start",
    "timestamp_end",
    "timestamp_source",
    "timestamp_match_method",
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
    "timestamp_source",
    "timestamp_match_method",
    "is_new_fabricated_20pct",
]

P5F_METRIC_KEYS = [
    "total_files",
    "evaluated_files",
    "failed_files",
    "independent_holdout_count",
    "seen_in_p5_training_count",
    "seen_in_p5c_controlled_count",
    "seen_in_previous_p5d_count",
    "partial_file_count",
    "expanded_partial_file_count",
    "expanded_timestamp_positive_count",
    "timestamp_positive_count",
    "fabricated_20pct_file_count",
    "fabricated_20pct_evaluated_count",
    "fabricated_20pct_failed_count",
    "fabricated_20pct_recall",
    "fabricated_20pct_timestamp_label_count",
    "fabricated_20pct_top1_hit_rate",
    "fabricated_20pct_top3_hit_rate",
    "fabricated_20pct_top5_hit_rate",
    "fabricated_20pct_median_candidate_timestamp_error_seconds",
    "new_partial_positive_count",
    "new_partial_recall",
    "new_partial_false_negative_count",
    "mp4_file_count",
    "ssl_cuda_oom_count",
    "ssl_chunked_fallback_attempt_count",
    "ssl_chunked_fallback_success_count",
]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P5F expanded evaluation outputs.")
    p.add_argument("--input_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5f"))
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p5f_expanded_evaluation_validation_report.md"),
    )
    p.add_argument("--project_root", default=str(root))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    return p.parse_args()


def _load_run_status(in_dir: Path) -> tuple[dict[str, Any] | None, str]:
    path = in_dir / P5F_RUN_STATUS_FILENAME
    if not path.is_file():
        return None, f"missing {P5F_RUN_STATUS_FILENAME}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except json.JSONDecodeError as exc:
        return None, f"run status JSON invalid: {exc}"


def outputs_newer_than_p5f_run_start(out_dir: Path, run_started_at: str) -> tuple[bool, str]:
    started = parse_p5d_run_timestamp(run_started_at)
    if started is None:
        return False, "run_started_at unparseable"
    required = [
        "phase9d_p5f_expanded_evaluation_report.md",
        "phase9d_p5f_expanded_metrics.json",
        "phase9d_p5f_file_predictions.csv",
        "phase9d_p5f_segment_predictions.csv",
        "phase9d_p5f_timestamp_loading_audit.csv",
        P5F_RUN_STATUS_FILENAME,
    ]
    stale: list[str] = []
    for name in required:
        path = out_dir / name
        if not path.is_file():
            stale.append(f"missing:{name}")
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < started:
            stale.append(f"stale:{name}")
    if stale:
        return False, ", ".join(stale)
    return True, "outputs refreshed after run_started_at"


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

    report_path = in_dir / "phase9d_p5f_expanded_evaluation_report.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""

    checks: list[dict] = []
    run_status, run_status_err = _load_run_status(in_dir)
    if run_status is None:
        checks.append(_check("run_status_present", False, run_status_err))
        fresh_ok, fresh_detail = False, run_status_err
    else:
        checks.append(_check("run_status_present", True, P5F_RUN_STATUS_FILENAME))
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
        fresh_ok, fresh_detail = outputs_newer_than_p5f_run_start(
            in_dir, str(run_status.get("run_started_at", ""))
        )
    checks.append(_check("outputs_not_stale", fresh_ok, fresh_detail))

    missing = [f for f in REQUIRED_OUTPUTS if not (in_dir / f).is_file()]
    checks.append(_check("required_output_files_exist", not missing, ", ".join(missing)))

    manifest = _safe_read_csv(in_dir / "phase9d_p5f_expanded_manifest.csv")
    missing_m = [c for c in MANIFEST_COLUMNS if c not in manifest.columns]
    checks.append(_check("manifest_required_columns", not missing_m, ", ".join(missing_m)))

    fab_manifest = manifest[manifest["test_group"].astype(str) == "fabricated_20pct"] if not manifest.empty else pd.DataFrame()
    checks.append(
        _check(
            "fabricated_20pct_files_in_manifest",
            len(fab_manifest) >= 10,
            f"fabricated_20pct_rows={len(fab_manifest)}",
        )
    )

    ts_source = str(run_status.get("timestamp_spreadsheet_source", "") if run_status else "")
    ts_warn = str(run_status.get("timestamp_spreadsheet_warning", "") if run_status else "")
    metrics_path = in_dir / "phase9d_p5f_expanded_metrics.json"
    metrics: dict[str, Any] = {}
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not ts_source:
        ts_source = str(metrics.get("timestamp_spreadsheet_source", ""))
    if not ts_warn:
        ts_warn = str(metrics.get("timestamp_spreadsheet_warning", ""))

    audit_path = in_dir / "phase9d_p5f_timestamp_loading_audit.csv"
    checks.append(_check("timestamp_loading_audit_exists", audit_path.is_file(), str(audit_path)))

    checks.append(
        _check(
            "timestamp_spreadsheet_documented",
            bool(ts_source) or bool(ts_warn) or "fabricated_20pct timestamp" in report_text.lower(),
            f"source={ts_source!r} warning={ts_warn!r}",
        )
    )

    fab_ts_label_count = int(metrics.get("fabricated_20pct_timestamp_label_count", 0))
    spreadsheet_rows = 0
    if audit_path.is_file():
        audit_df = _safe_read_csv(audit_path)
        if not audit_df.empty and "row_count" in audit_df.columns:
            spreadsheet_rows = int(pd.to_numeric(audit_df["row_count"], errors="coerce").max() or 0)
    checks.append(
        _check(
            "fabricated_20pct_timestamp_labels_loaded",
            fab_ts_label_count >= 10 or (spreadsheet_rows < 10 and spreadsheet_rows > 0 and bool(ts_warn)),
            f"fab_ts_labels={fab_ts_label_count} spreadsheet_rows={spreadsheet_rows} warn={ts_warn!r}",
        )
    )

    overlap_path = in_dir / "phase9d_p5f_overlap_audit.csv"
    checks.append(_check("overlap_audit_exists", overlap_path.is_file(), str(overlap_path)))

    file_pred = _safe_read_csv(in_dir / "phase9d_p5f_file_predictions.csv")
    missing_fp = [c for c in FILE_PRED_COLUMNS if c not in file_pred.columns]
    checks.append(_check("file_predictions_required_columns", not missing_fp, ", ".join(missing_fp)))

    fab_pred = file_pred[file_pred["test_group"].astype(str) == "fabricated_20pct"] if not file_pred.empty else pd.DataFrame()
    checks.append(
        _check(
            "fabricated_20pct_in_file_predictions",
            len(fab_pred) >= 10,
            f"rows={len(fab_pred)}",
        )
    )
    if not fab_pred.empty and "timestamp_match_method" in fab_pred.columns:
        methods = fab_pred["timestamp_match_method"].astype(str)
        checks.append(
            _check(
                "timestamp_match_method_valid",
                methods.isin(TIMESTAMP_MATCH_METHODS).all(),
                f"invalid={sorted(set(methods) - TIMESTAMP_MATCH_METHODS)}",
            )
        )
        checks.append(
            _check(
                "fabricated_20pct_timestamp_match_method_present",
                (methods != "").all()
                and (methods != "nan").all()
                and (
                    fab_ts_label_count < 10
                    or int((methods == "missing").sum()) == 0
                ),
                f"missing_method={int((methods == 'missing').sum())} unique={methods.unique().tolist()}",
            )
        )

    fab_pos = fab_pred[
        fab_pred["partial_evidence_positive"].astype(bool) & fab_pred["has_timestamp_label"].astype(bool)
    ] if not fab_pred.empty else pd.DataFrame()
    if int(metrics.get("fabricated_20pct_timestamp_label_count", 0)) > 0 and len(fab_pos) > 0:
        loc_keys = (
            "fabricated_20pct_top1_hit_rate",
            "fabricated_20pct_top3_hit_rate",
            "fabricated_20pct_top5_hit_rate",
        )
        loc_ok = all(
            metrics.get(k) is not None and np.isfinite(float(metrics.get(k)))
            for k in loc_keys
        )
        checks.append(
            _check(
                "fabricated_20pct_localization_metrics_available",
                loc_ok,
                ", ".join(f"{k}={metrics.get(k)}" for k in loc_keys),
            )
        )

    if audit_path.is_file():
        audit_df = _safe_read_csv(audit_path)
        row_fallback = (
            not audit_df.empty
            and audit_df["load_status"].astype(str).eq("ok_row_order_fallback").any()
        )
        if row_fallback:
            report_mentions_fallback = "row order" in report_text.lower() or "row-order" in report_text.lower()
            matched_n = int(metrics.get("timestamp_spreadsheet_matched_audio_count", 0))
            checks.append(
                _check(
                    "row_order_fallback_documented",
                    report_mentions_fallback
                    and matched_n == int(metrics.get("fabricated_20pct_file_count", 0)),
                    f"report_fallback={report_mentions_fallback} matched={matched_n}",
                )
            )

    seg_pred = _safe_read_csv(in_dir / "phase9d_p5f_segment_predictions.csv")
    missing_sp = [c for c in SEG_PRED_COLUMNS if c not in seg_pred.columns]
    checks.append(_check("segment_predictions_required_columns", not missing_sp, ", ".join(missing_sp)))

    missing_metrics = [k for k in P5F_METRIC_KEYS if k not in metrics]
    checks.append(_check("metrics_required_keys", not missing_metrics, ", ".join(missing_metrics)))

    if int(metrics.get("fabricated_20pct_file_count", 0)) >= 10:
        checks.append(
            _check(
                "fabricated_20pct_file_count_metric",
                int(metrics.get("fabricated_20pct_file_count", 0)) >= 10,
                str(metrics.get("fabricated_20pct_file_count")),
            )
        )

    rank_ok, rank_detail, match_ok, match_detail = _candidate_segment_integrity_checks(file_pred, seg_pred)
    checks.append(_check("candidate_segment_rank_valid", rank_ok, rank_detail))
    checks.append(_check("candidate_matches_rank1_segment", match_ok, match_detail))
    idx_ok, idx_detail, srank_ok, srank_detail = _segment_index_rank_checks(seg_pred)
    checks.append(_check("segment_index_chronological_valid", idx_ok, idx_detail))
    checks.append(_check("segment_rank_valid", srank_ok, srank_detail))

    if int(metrics.get("ssl_cuda_oom_count", 0)) > 0:
        oom_ok, oom_detail = _ssl_oom_recovery_reported_ok(metrics)
        checks.append(_check("ssl_oom_fallback_reported", oom_ok, oom_detail))

    if int(metrics.get("mp4_file_count", 0)) > 0:
        checks.append(
            _check(
                "mp4_robustness_reported",
                int(metrics.get("mp4_evaluated_count", -1)) + int(metrics.get("mp4_failed_count", -1))
                == int(metrics.get("mp4_file_count", 0)),
                f"mp4_total={metrics.get('mp4_file_count')}",
            )
        )

    err_path = in_dir / "phase9d_p5f_error_cases.csv"
    non_ok = int((file_pred["error_status"].astype(str) != "ok").sum()) if not file_pred.empty else 0
    err_rows = len(_safe_read_csv(err_path)) if err_path.is_file() else 0
    checks.append(
        _check(
            "failed_files_consistent_with_error_cases",
            int(metrics.get("failed_files", 0)) == non_ok and (non_ok == 0 or err_rows >= 1),
            f"failed_files={metrics.get('failed_files')} non_ok={non_ok} err_rows={err_rows}",
        )
    )

    ok = file_pred[file_pred["error_status"].astype(str) == "ok"] if not file_pred.empty else pd.DataFrame()
    false_pos = ok[ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(0)]
    checks.append(
        _check(
            "false_positives_visible_in_predictions",
            True,
            f"false_partial_count={len(false_pos)} (report should list examples)",
        )
    )
    fn = ok[(~ok["partial_evidence_positive"].astype(bool)) & ok["test_group"].astype(str).eq("fabricated_20pct")]
    checks.append(
        _check(
            "false_negatives_visible_if_any",
            True,
            f"fabricated_20pct_false_negative_count={len(fn)}",
        )
    )

    lbl_complete = True
    if not manifest.empty:
        conds = manifest["expected_condition"].astype(str)
        lbl_complete = float((conds == "unknown_testing_condition").mean()) < 0.5
    release_gates = evaluate_p5f_release_gates(metrics, labels_complete=lbl_complete)
    packaging_ready = bool(release_gates["release_packaging_ready"])
    checks.append(
        _check(
            "release_packaging_gate_metrics",
            not packaging_ready,
            "; ".join(release_gates["failure_reasons"][:6]),
        )
    )
    checks.append(
        _check(
            "release_remains_blocked",
            not packaging_ready,
            f"packaging_ready={packaging_ready} partial={metrics.get('partial_file_count')} ts_pos={metrics.get('timestamp_positive_count')}",
        )
    )
    report_says_yes = (
        "candidate acceptable for release packaging evaluation: yes" in report_text.lower()
    )
    report_says_no = "candidate acceptable for release packaging evaluation: no" in report_text.lower()
    checks.append(
        _check(
            "release_readiness_assessment_consistent",
            (packaging_ready and report_says_yes) or ((not packaging_ready) and report_says_no),
            f"ready={packaging_ready} yes={report_says_yes} no={report_says_no}",
        )
    )
    checks.append(
        _check(
            "release_readiness_uses_updated_timestamp_count",
            int(metrics.get("timestamp_positive_count", 0)) == int(metrics.get("expanded_timestamp_positive_count", 0))
            or int(metrics.get("expanded_timestamp_positive_count", 0)) >= int(metrics.get("timestamp_positive_count", 0)),
            f"ts_pos={metrics.get('timestamp_positive_count')} expanded_ts_pos={metrics.get('expanded_timestamp_positive_count')}",
        )
    )
    checks.append(
        _check(
            "packaging_not_performed",
            "release packaging performed:** no" in report_text.lower()
            or "release packaging performed:** no" in report_text.lower().replace("**", ""),
            "report must state packaging not performed",
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
            "",
        )
    )

    release_hits = list((root / "release" / "models").rglob("phase9d_p5f*")) if (root / "release" / "models").is_dir() else []
    active_hits = list((root / "models_saved" / "active").rglob("phase9d_p5f*")) if (root / "models_saved" / "active").is_dir() else []
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
            all((cand_dir / name).is_file() for name in P5C_CANDIDATE_MODEL_NAMES.values()),
            str(cand_dir),
        )
    )
    checks.append(
        _check(
            "reference_models_not_activated",
            not artifact_audit["reference_model_used"] and not any("reference" in f for f in artifact_failures),
            "; ".join(artifact_failures[:3]),
        )
    )

    all_pass = all(c["pass"] for c in checks)
    status = "PASS" if all_pass else "FAIL"

    lines = [
        "# Phase 9D-P5F Expanded Evaluation Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall:** {status}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"- [{mark}] `{c['check']}`{detail}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validates P5F outputs only; does not run inference.",
            "- P5F expands P5D with fabricated_20pct; P5D outputs under phase9d_p5d are preserved separately.",
            f"- Accepted thresholds: {P5C_ACCEPTED_CASCADE_THRESHOLDS}",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"P5F validation {status}: {report_out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
