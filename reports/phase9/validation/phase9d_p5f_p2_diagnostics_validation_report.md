# Phase 9D-P5F-P2 Diagnostics Validation Report

Generated: 2026-06-02T19:25:13.836966+00:00

**Overall:** PASS

## Checks

- [PASS] `required_diagnostic_output_files_exist` — 
- [PASS] `case_summary_required_columns` — 
- [PASS] `top_segments_required_columns` — 
- [PASS] `timestamp_localization_required_columns` — 
- [PASS] `threshold_counterfactual_required_columns` — 
- [PASS] `threshold_sensitivity_required_columns` — 
- [PASS] `threshold_sensitivity_marked_diagnostic_only` — unique=[True]
- [PASS] `probability_distribution_required_columns` — 
- [PASS] `false_negative_count_matches_p5f_predictions` — diagnostic=3 p5f=3
- [PASS] `false_positive_count_matches_p5f_predictions` — diagnostic=2 p5f=2
- [PASS] `all_false_negatives_have_primary_failure_reason` — missing=0
- [PASS] `all_false_positives_have_explanation_label` — labels=['strong_file_gate_plus_strong_segment', 'high_contrast_artifact_like_pattern']
- [PASS] `report_states_thresholds_not_changed` — missing explicit no-threshold-change statement
- [PASS] `report_states_no_retraining` — missing no-retrain statement
- [PASS] `report_states_no_release_packaging` — missing no-packaging statement
- [PASS] `report_does_not_claim_release_ready` — forbidden release-ready phrasing found
- [PASS] `report_does_not_recommend_threshold_changes` — 
- [PASS] `report_forensic_safe_wording` — 
- [PASS] `no_release_models_writes` — []
- [PASS] `no_models_saved_active_writes` — []
- [PASS] `no_phase9e_files_changed_by_validator` — phase9e_paths_scanned=0 (diagnostic scripts only)

## Notes

- Validates P5F-P2 diagnostic outputs only; does not run inference.
- Compares case counts against latest P5F file predictions.
- P5F input: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5f`
- Diagnostics input: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5f_p2_diagnostics`
