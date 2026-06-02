# Phase 9D-P5D Independent Evaluation Validation Report

Generated: 2026-06-02T18:02:19.669157+00:00

**Overall:** PASS

## Run status check

- phase: Phase 9D-P5D
- status: completed
- run_started_at: 2026-06-02 17:59:03 UTC
- run_completed_at: 2026-06-02 18:01:50 UTC
- output_generation_complete: True
- input_root: E:\FYP\testing_audios

## Stale output check

- outputs_not_stale: True (outputs refreshed after run_started_at)

## Model artifact audit

- file_gate_model_path: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- segment_localizer_model_path: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- cascade_config_path: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_cascade_config__p5b_experimental_candidate.json`
- release_partial_model_used: false
- reference_model_used: false
- old_release_partial_model_used: false

## Release-readiness gate

- release_packaging_ready (metrics): false
- blocking reasons:
  - partial_file_count=2 < 5

## Scientific limitations gate

- labels_complete: true
- partial_file_count: 2
- failed_files: 0
- timestamp_positive_count: 1

## Checks

- [PASS] `run_status_present` — phase9d_p5d_run_status.json
- [PASS] `run_status_completed` — status=completed
- [PASS] `output_generation_complete` — True
- [PASS] `outputs_not_stale` — outputs refreshed after run_started_at
- [PASS] `required_output_files_exist` — all present
- [PASS] `error_cases_has_header` — ['file_path', 'failure_type', 'error_message']
- [PASS] `manifest_required_columns`
- [PASS] `file_predictions_required_columns`
- [PASS] `segment_predictions_file_exists` — phase9d_p5d_segment_predictions.csv
- [PASS] `segment_predictions_required_columns`
- [PASS] `candidate_segment_rank_valid` — ok
- [PASS] `candidate_matches_rank1_segment` — ok
- [PASS] `segment_index_chronological_valid` — ok
- [PASS] `segment_rank_valid` — ok
- [PASS] `metrics_required_keys`
- [PASS] `median_candidate_timestamp_error_rule` — median computed from 1 error(s)
- [PASS] `metrics_finite_where_applicable`
- [PASS] `robustness_metrics_present`
- [PASS] `mp4_robustness_reported` — mp4_total=2 ok=2 fail=0
- [PASS] `ssl_oom_fallback_reported` — oom=1 cpu_attempts=0 cpu_success=0 cpu_failure=0 chunked_attempts=1 chunked_success=1 chunked_failure=0 chunked_cpu_attempts=1 chunked_cpu_success=1 chunked_cpu_failure=0
- [PASS] `robustness_ssl_counters_match_error_cases` — ssl_related=0, ssl_fallback_failed=0, ssl_chunked_failed=0, long_skip=0, oom_count=1, fallback_attempt=0, fallback_failure=0, skip_long=1, chunked_fail=0
- [PASS] `long_audio_ssl_recovery_reported` — long_files=3 ssl_long_audio_file_count=1
- [PASS] `chunked_fallback_counters_consistent` — attempts=1 success=1 failure=0
- [PASS] `chunked_fallback_file_flags_consistent` — chunked_used=1 success=1
- [PASS] `previous_ssl_failure_recovered_or_documented` — in_pred=True ok=True documented_fail=False in_err=False
- [PASS] `failed_files_consistent_with_error_cases` — failed_files=0 non_ok_pred=0 err_rows=0
- [PASS] `report_forbidden_wording`
- [PASS] `accepted_thresholds_documented`
- [PASS] `robustness_behavior_section_present` — report must include robustness behavior section
- [PASS] `no_release_models_writes` — []
- [PASS] `no_models_saved_active_writes` — []
- [PASS] `p5b_only_candidate_artifacts` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models
- [PASS] `reference_models_not_activated` — ok
- [PASS] `p5b_only_model_usage_statement_in_report` — report must state P5B-only experimental candidate usage
- [PASS] `release_partial_model_not_used` — ok
- [PASS] `old_release_partial_model_not_used` — ok
- [PASS] `release_packaging_gate_metrics` — partial_file_count=2 < 5
- [PASS] `release_assessment_aligned_with_gates` — gates=False assess=False
- [PASS] `release_packaging_not_claimed_ready` — report_yes=False
- [PASS] `packaging_recommendation_matches_metrics` — report_yes=False metrics_ready=False
- [PASS] `failed_files_reported_in_outputs` — failed_files=0
- [PASS] `scientific_limitations_gate` — limitations_present=True packaging_ready=False
- [PASS] `release_blockers_documented_in_report` — report must document packaging blockers when not ready
- [PASS] `release_remains_blocked` — packaging_ready=False partial=2 ts_pos=1

## Notes

- Validates P5D outputs only; does not run inference.
- `reference_models_not_activated` checks artifact paths, active-use claims, and prediction columns — not bare architecture name mentions.
- P5B experimental candidate models must exist under phase9d_p5b/candidate_models/.
- No writes to release/models or models_saved/active.
