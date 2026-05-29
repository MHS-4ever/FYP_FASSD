# Phase 9D-P5C Controlled Evaluation Validation Report

Generated: 2026-05-29 19:05 UTC

**Overall result:** PASS

## Accepted cascade thresholds (shared config)

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

## Checks

- [PASS] required_output_files_exist — all present
- [PASS] no_release_models_writes — []
- [PASS] no_models_saved_active_writes — []
- [PASS] no_fastapi_gradio_files_modified_by_p5c — P5C scripts do not modify app code (manual verification of scope)
- [PASS] file_predictions_required_columns — ok
- [PASS] metrics_finite_where_present
- [PASS] release_packaging_blocked_without_holdout — independent_holdout_count == 0
- [PASS] accepted_cascade_thresholds_documented
- [PASS] report_no_forbidden_verdict_wording
- [PASS] report_separates_evidence_axes — partial fabrication evidence described separately from other axes
- [PASS] report_no_release_packaging
- [PASS] report_no_impossible_broad_counts

## Notes

- Phase 9E apps: NOT STARTED.
- P5B experimental candidates only; release partial model not replaced.
