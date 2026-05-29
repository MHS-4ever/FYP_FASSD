# Phase 9D-P5D Independent Evaluation Validation Report

Generated: 2026-05-29T19:55:04.687956+00:00

**Overall:** FAIL

## Run status check

- phase: Phase 9D-P5D
- status: completed
- run_started_at: 2026-05-29 19:52:17 UTC
- run_completed_at: 2026-05-29 19:54:56 UTC
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
  - failed_files=3 > 0 (robustness limitation; packaging blocked)
  - partial_file_count=2 < 5

## Scientific limitations gate

- labels_complete: true
- partial_file_count: 2
- failed_files: 3
- timestamp_positive_count: 1

## Checks

- [PASS] `run_status_present` — phase9d_p5d_run_status.json
- [PASS] `run_status_completed` — status=completed
- [PASS] `output_generation_complete` — True
- [PASS] `outputs_not_stale` — outputs refreshed after run_started_at
- [PASS] `required_output_files_exist` — all present
- [PASS] `error_cases_has_header` — ['file_path', 'file_name', 'file_stem', 'parent_folder', 'test_group', 'expected_condition', 'expected_partial_label', 'expected_origin_label', 'has_timestamp_label', 'timestamp_start', 'timestamp_end', 'manifest_status', 'source_split_status', 'error_status', 'error_message', 'failure_type']
- [PASS] `manifest_required_columns`
- [PASS] `file_predictions_required_columns`
- [PASS] `segment_predictions_file_exists` — phase9d_p5d_segment_predictions.csv
- [PASS] `segment_predictions_required_columns`
- [PASS] `metrics_required_keys`
- [FAIL] `metrics_finite_where_applicable` — median_candidate_timestamp_error_seconds (missing, stratum non-empty)
- [PASS] `report_forbidden_wording`
- [PASS] `accepted_thresholds_documented`
- [PASS] `no_release_models_writes` — []
- [PASS] `no_models_saved_active_writes` — []
- [PASS] `p5b_only_candidate_artifacts` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models
- [PASS] `reference_models_not_activated` — ok
- [PASS] `p5b_only_model_usage_statement_in_report` — report must state P5B-only experimental candidate usage
- [PASS] `release_partial_model_not_used` — ok
- [PASS] `old_release_partial_model_not_used` — ok
- [PASS] `release_packaging_gate_metrics` — failed_files=3 > 0 (robustness limitation; packaging blocked); partial_file_count=2 < 5
- [PASS] `release_assessment_aligned_with_gates` — gates=False assess=False
- [PASS] `release_packaging_not_claimed_ready` — report_yes=False
- [PASS] `packaging_recommendation_matches_metrics` — report_yes=False metrics_ready=False
- [PASS] `failed_files_reported_in_outputs` — failed_files=3
- [PASS] `scientific_limitations_gate` — limitations_present=True packaging_ready=False
- [PASS] `release_blockers_documented_in_report` — report must document packaging blockers when not ready

## Notes

- Validates P5D outputs only; does not run inference.
- `reference_models_not_activated` checks artifact paths, active-use claims, and prediction columns — not bare architecture name mentions.
- P5B experimental candidate models must exist under phase9d_p5b/candidate_models/.
- No writes to release/models or models_saved/active.
