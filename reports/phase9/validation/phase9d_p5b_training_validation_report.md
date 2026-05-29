# Phase 9D-P5B Training Validation Report

Generated: 2026-05-29 18:48 UTC

**Overall result:** PASS

## Shared cascade acceptance thresholds

| Rule | Threshold |
|------|----------:|
| direct_false_partial_rate <= | 0.2000 |
| replay_false_partial_rate <= | 0.0500 |
| mixer_false_partial_rate <= | 0.0500 |
| broad_activation_rate_when_positive <= | 0.1000 |
| file_gate_threshold >= | 0.5000 |
| non_partial_false_alarm_rate <= | not enforced |
| partial_file_recall >= | not enforced |

## Cascade diagnostics (from CSV)

- Minimum observed direct_false_partial_rate: 0.1087
- Minimum observed non_partial_false_alarm_rate: 0.0362
- Valid recommended_threshold_pair rows in CSV: 1
- Release-ready assessment: PASS — recommended pair passes shared acceptance rules: file_gate=0.5,segment=0.9,contrast=0.25,broad_limit=0.45
- Report/CSV alignment: PASS — training report and cascade CSV both indicate a passing release-ready pair

## Checks

- [PASS] required_output_files_exist — all present
- [PASS] file_gate_metrics_acoustic — feature_set=acoustic
- [PASS] file_gate_metrics_ssl — feature_set=ssl
- [PASS] file_gate_metrics_combined — feature_set=combined
- [PASS] segment_metrics_acoustic — feature_set=acoustic
- [PASS] segment_metrics_ssl — feature_set=ssl
- [PASS] segment_metrics_localization — feature_set=localization
- [PASS] segment_metrics_combined — feature_set=combined
- [PASS] file_gate_oof_exists — rows=552
- [PASS] segment_oof_exists — rows=16572
- [PASS] file_gate_metrics_finite
- [PASS] segment_metrics_finite
- [PASS] feature_audit_leakage_passed
- [PASS] group_integrity_documented — ['StratifiedGroupKFold']
- [PASS] forbidden_features_not_used
- [PASS] group_aware_split_documented
- [PASS] same_file_not_split_across_folds
- [PASS] cascade_simulation_exists — rows=324
- [PASS] cascade_has_localized_evidence_columns — contrast_threshold and broad_limit present
- [PASS] cascade_release_ready_recommendation — recommended pair passes shared acceptance rules: file_gate=0.5,segment=0.9,contrast=0.25,broad_limit=0.45
- [PASS] training_report_cascade_alignment — training report and cascade CSV both indicate a passing release-ready pair
- [PASS] report_broad_activation_counts_plausible — broad=0/46
- [PASS] report_no_release_packaging
- [PASS] report_no_packaging_evaluation_claim — report must not recommend packaging when validation rules are not met
- [PASS] no_release_models_writes — []
- [PASS] no_models_saved_active_writes — []
- [PASS] no_fake_real_score_fields

## Notes

- Validates experimental P5B outputs only.
- Phase 9E apps: NOT STARTED.
- Release partial model NOT replaced by this phase.
- P5B-P2: training, report, and validator share CASCADE_ACCEPTANCE_CONFIG.
