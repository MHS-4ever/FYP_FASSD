# Phase 9E Release App Validation Report

Generated: 2026-06-02T20:18:42.990011+00:00

**Overall:** PASS

## Checks

- [PASS] `release_required_files_exist` — 
- [PASS] `partial_package_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b
- [PASS] `partial_metadata_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_module_metadata.json
- [PASS] `partial_report_contract_exists` — E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_report_contract.json
- [PASS] `partial_metadata_status_experimental` — experimental_manual_review_only
- [PASS] `manual_review_required_true` — True
- [PASS] `production_ready_false` — False
- [PASS] `court_ready_false` — False
- [PASS] `final_verdict_model_false` — False
- [PASS] `partial_thresholds_match_p5b` — {'file_gate_threshold': 0.5, 'segment_threshold': 0.9, 'contrast_threshold': 0.25, 'broad_limit': 0.45}
- [PASS] `partial_report_contract_has_section` — 
- [PASS] `forbidden_wording_absent_in_release_sources` — 
- [PASS] `fastapi_route_root` — /
- [PASS] `fastapi_route_health` — /health
- [PASS] `fastapi_route_model-info` — /model-info
- [PASS] `fastapi_route_analyze-audio` — /analyze-audio
- [PASS] `fastapi_uses_analyze_audio_file` — 
- [PASS] `fastapi_uses_app_report_formatting` — 
- [PASS] `gradio_audio_upload` — 
- [PASS] `gradio_partial_panel` — 
- [PASS] `gradio_segment_table` — 
- [PASS] `gradio_limitations_box` — 
- [PASS] `app_report_formatting_exists` — E:\FYP\release\src\app_report_formatting.py
- [PASS] `formatting_builds_partial_fabrication` — 
- [PASS] `formatting_loads_p6_metadata` — 
- [PASS] `formatting_mentions_module_status` — 
- [PASS] `formatting_mentions_user_facing_message` — 
- [PASS] `formatting_mentions_partial_fabrication` — 
- [PASS] `release_fastapi_imports` — dependency warning: ModuleNotFoundError: No module named 'fastapi'
- [PASS] `release_gradio_imports` — 
- [PASS] `old_partial_segment_not_active_for_demo` — legacy_active=False
- [PASS] `p6_module_active_for_phase9e_demo` — True
- [PASS] `no_models_saved_active_writes` — 
- [PASS] `code_phase9_app_not_primary_path` — Primary app: release/; code/phase9/app is legacy skeleton only.
- [PASS] `legacy_code_phase9_app_exists_as_reference` — E:\FYP\code\phase9\app\fastapi_app.py
- [PASS] `phase9e_app_design_doc_exists` — E:\FYP\reports\phase9\app\phase9e_p1_app_design.md
- [PASS] `design_doc_states_release_primary` — 
- [PASS] `partial_fabrication_section_keys_covered` — 

## Summary

Primary application path: `release/` (FastAPI + Gradio).
P6 partial package: `release/models/partial_fabrication_experimental_p5b/`.
Inference: `release/src/inference_pipeline.py` → `analyze_audio_file()`.
`code/phase9/app/` is a legacy skeleton and not the primary app path.

Does not start servers, retrain models, or modify release model artifacts.
