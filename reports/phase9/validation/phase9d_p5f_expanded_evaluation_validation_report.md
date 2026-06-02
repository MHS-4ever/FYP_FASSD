# Phase 9D-P5F Expanded Evaluation Validation Report

Generated: 2026-06-02T19:08:16.386789+00:00

**Overall:** PASS

## Checks

- [PASS] `run_status_present` — phase9d_p5f_run_status.json
- [PASS] `run_status_completed` — status=completed
- [PASS] `output_generation_complete` — True
- [PASS] `outputs_not_stale` — outputs refreshed after run_started_at
- [PASS] `required_output_files_exist`
- [PASS] `manifest_required_columns`
- [PASS] `fabricated_20pct_files_in_manifest` — fabricated_20pct_rows=10
- [PASS] `timestamp_loading_audit_exists` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5f\phase9d_p5f_timestamp_loading_audit.csv
- [PASS] `timestamp_spreadsheet_documented` — source='fabricated_20pct_timestamps.csv' warning=''
- [PASS] `fabricated_20pct_timestamp_labels_loaded` — fab_ts_labels=10 spreadsheet_rows=10 warn=''
- [PASS] `overlap_audit_exists` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5f\phase9d_p5f_overlap_audit.csv
- [PASS] `file_predictions_required_columns`
- [PASS] `fabricated_20pct_in_file_predictions` — rows=10
- [PASS] `timestamp_match_method_valid` — invalid=[]
- [PASS] `fabricated_20pct_timestamp_match_method_present` — missing_method=0 unique=['exact_file_name']
- [PASS] `fabricated_20pct_localization_metrics_available` — fabricated_20pct_top1_hit_rate=0.8571428571428571, fabricated_20pct_top3_hit_rate=1.0, fabricated_20pct_top5_hit_rate=1.0
- [PASS] `segment_predictions_required_columns`
- [PASS] `metrics_required_keys`
- [PASS] `fabricated_20pct_file_count_metric` — 10
- [PASS] `candidate_segment_rank_valid` — ok
- [PASS] `candidate_matches_rank1_segment` — ok
- [PASS] `segment_index_chronological_valid` — ok
- [PASS] `segment_rank_valid` — ok
- [PASS] `ssl_oom_fallback_reported` — oom=471 cpu_attempts=467 cpu_success=467 cpu_failure=0 chunked_attempts=4 chunked_success=4 chunked_failure=0 chunked_cpu_attempts=4 chunked_cpu_success=4 chunked_cpu_failure=0
- [PASS] `mp4_robustness_reported` — mp4_total=2
- [PASS] `failed_files_consistent_with_error_cases` — failed_files=0 non_ok=0 err_rows=0
- [PASS] `false_positives_visible_in_predictions` — false_partial_count=2 (report should list examples)
- [PASS] `false_negatives_visible_if_any` — fabricated_20pct_false_negative_count=3
- [PASS] `release_packaging_gate_metrics` — fabricated_20pct_recall 0.7000 < 0.8000; new_partial_recall 0.7000 < 0.8000; new_partial_false_negative_count=3 > 0
- [PASS] `release_remains_blocked` — packaging_ready=False partial=12 ts_pos=8
- [PASS] `release_readiness_assessment_consistent` — ready=False yes=False no=True
- [PASS] `release_readiness_uses_updated_timestamp_count` — ts_pos=8 expanded_ts_pos=8
- [PASS] `packaging_not_performed` — report must state packaging not performed
- [PASS] `report_forbidden_wording`
- [PASS] `accepted_thresholds_documented`
- [PASS] `robustness_behavior_section_present`
- [PASS] `no_release_models_writes` — []
- [PASS] `no_models_saved_active_writes` — []
- [PASS] `p5b_only_candidate_artifacts` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models
- [PASS] `reference_models_not_activated`

## Notes

- Validates P5F outputs only; does not run inference.
- P5F expands P5D with fabricated_20pct; P5D outputs under phase9d_p5d are preserved separately.
- Accepted thresholds: {'file_gate_threshold': 0.5, 'segment_threshold': 0.9, 'contrast_threshold': 0.25, 'broad_limit': 0.45}
