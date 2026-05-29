# Phase 9D-P5 Partial Dataset Validation Report

Generated: 2026-05-29 18:07 UTC

**Overall result:** PASS

## Checks

- [PASS] required_output_files_exist — all present
- [PASS] file_gate_has_positive_and_negative
- [PASS] file_gate_metadata_columns
- [PASS] file_gate_no_fake_real_score
- [PASS] segment_has_positive_and_negative
- [PASS] segment_negatives_include_all_categories — {"fabricated_outside_same_file": true, "clean_direct_negative": true, "replay_negative": true, "mixer_negative": true}
- [PASS] segment_metadata_columns
- [PASS] segment_no_fake_real_score
- [PASS] timestamp_audit_has_matched_rows — matched=46
- [PASS] no_timestamp_values_in_model_features — clean
- [PASS] leakage_audit_no_forbidden_usable_features
- [PASS] leakage_audit_rows_clean — bad_rows=0
- [PASS] class_balance_not_empty
- [PASS] report_states_no_training

## Warnings

- leakage_audit_rows_clean: bad_rows=0
- nan

## Notes

- Validation only; no model training performed by this script.
- Phase 9E apps: NOT STARTED.
- Phase 9D-P5B training: NOT STARTED (run after validation PASS).
