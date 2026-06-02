# Phase 9D-P6 Partial Integration Validation Report

Generated: 2026-06-02T19:53:07.108752+00:00

**Overall:** PASS

## Checks

- [PASS] `package_directory_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b
- [PASS] `required_package_files_exist` — 
- [PASS] `sha256sums_match_files` — all listed files match
- [PASS] `sha256sums_file_exists` — 
- [PASS] `metadata_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_module_metadata.json
- [PASS] `metadata_status_experimental_manual_review_only` — experimental_manual_review_only
- [PASS] `metadata_production_ready_false` — False
- [PASS] `metadata_court_ready_false` — False
- [PASS] `metadata_final_verdict_model_false` — False
- [PASS] `metadata_manual_review_required_true` — True
- [PASS] `metadata_thresholds_match_accepted` — {'file_gate_threshold': 0.5, 'segment_threshold': 0.9, 'contrast_threshold': 0.25, 'broad_limit': 0.45}
- [PASS] `validation_summary_documents_p5f_limitations` — fn=3 fp=2
- [PASS] `report_contract_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_report_contract.json
- [PASS] `report_contract_has_partial_fabrication_section` — ['partial_fabrication']
- [PASS] `report_contract_module_status_safe` — experimental_manual_review_only
- [PASS] `wording_avoids_forbidden_phrases` — 
- [PASS] `forensic_safe_wording` — 
- [PASS] `packaging_is_experimental_not_production_release` — decision report must state experimental integration packaging
- [PASS] `no_models_saved_active_writes` — []
- [PASS] `no_phase9e_implementation_files` — found=0
- [PASS] `no_fastapi_gradio_changes_in_p6_validator_scope` — fastapi_paths=0 gradio_paths=0 (P6 does not modify app files)
- [PASS] `old_partial_segment_model_not_active_for_demo` — legacy active_for_phase9e_demo=False
- [PASS] `registry_integration_module_entry` — {'status': 'experimental_manual_review_only', 'active_for_phase9e_demo': True, 'final_verdict_model': False, 'manual_review_required': True, 'package_path': 'release/models/partial_fabrication_experim
- [PASS] `p5b_candidate_artifacts_are_packaged_source` — E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models
- [PASS] `packaging_manifest_exists` — E:\FYP\reports\phase9\partial_redesign\phase9d_p6_partial_integration\phase9d_p6_packaging_manifest.csv

## Phase 9E start condition

Phase 9E may start using this module as an **experimental/manual-review partial-fabrication evidence axis** (not as a final verdict model).

## Notes

- Validates experimental integration packaging under `release/models/partial_fabrication_experimental_p5b/`.
- Does not run inference or start Phase 9E.
- Package: `E:\FYP\release\models\partial_fabrication_experimental_p5b`
