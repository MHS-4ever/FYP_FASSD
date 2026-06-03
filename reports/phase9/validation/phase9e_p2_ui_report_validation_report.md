# Phase 9E-P2 UI & Report Validation Report

Generated: 2026-06-02T21:32:54.274305+00:00

**Overall:** PASS

## Checks

- [PASS] `file_exists_app_gradio.py` — E:\FYP\release\app_gradio.py
- [PASS] `file_exists_app_fastapi.py` — E:\FYP\release\app_fastapi.py
- [PASS] `file_exists_app_report_formatting.py` — E:\FYP\release\src\app_report_formatting.py
- [PASS] `file_exists_app_visualization.py` — E:\FYP\release\src\app_visualization.py
- [PASS] `file_exists_pdf_report_generator.py` — E:\FYP\release\src\pdf_report_generator.py
- [PASS] `p2_design_doc_exists` — E:\FYP\reports\phase9\app\phase9e_p2_ui_report_design.md
- [PASS] `product_title_deepfake_audio_detector` — Expect APP_NAME or literal product title in release UI sources
- [PASS] `forbidden_product_title_absent` — 
- [PASS] `research_name_in_gradio` — 
- [PASS] `gradio_main_result_section` — 
- [PASS] `gradio_evidence_cards_section` — 
- [PASS] `gradio_waveform_output` — 
- [PASS] `gradio_pdf_download` — 
- [PASS] `gradio_json_download` — 
- [PASS] `raw_json_in_advanced_accordion` — 
- [PASS] `gradio_segments_table_title_helper` — 
- [PASS] `dark_card_css_present` — 
- [PASS] `partial_source_mode_fields` — 
- [PASS] `clean_segment_candidate_not_strong_suspicious` — skipped (dependency): ModuleNotFoundError: No module named 'pandas'
- [PASS] `strong_multi_axis_still_suspicious` — skipped (dependency): ModuleNotFoundError: No module named 'pandas'
- [PASS] `formatting_build_user_result_summary` — 
- [PASS] `formatting_build_evidence_axis_cards` — 
- [PASS] `formatting_save_json_report` — 
- [PASS] `visualization_format_time_mmss` — 
- [PASS] `visualization_generate_waveform_highlight` — 
- [PASS] `visualization_generate_timeline_fallback` — 
- [PASS] `pdf_generate_pdf_report` — 
- [PASS] `forbidden_wording_absent` — 
- [PASS] `partial_metadata_status_experimental` — experimental_manual_review_only
- [PASS] `manual_review_required_true` — True
- [PASS] `production_ready_false` — False
- [PASS] `court_ready_false` — False
- [PASS] `final_verdict_model_false` — False
- [PASS] `partial_thresholds_unchanged` — {'file_gate_threshold': 0.5, 'segment_threshold': 0.9, 'contrast_threshold': 0.25, 'broad_limit': 0.45}
- [PASS] `fastapi_route_root` — /
- [PASS] `fastapi_route_health` — /health
- [PASS] `fastapi_route_model-info` — /model-info
- [PASS] `fastapi_route_analyze-audio` — /analyze-audio
- [PASS] `fastapi_route_analyze` — /analyze
- [PASS] `no_models_saved_active_writes` — 
- [PASS] `no_model_artifact_overwrite_logic` — 
- [PASS] `release_primary_path_fastapi` — 
- [PASS] `import_app_gradio` — dependency warning: ModuleNotFoundError: No module named 'pandas'
- [PASS] `import_app_fastapi` — dependency warning: ModuleNotFoundError: No module named 'fastapi'
- [PASS] `import_src_app_report_formatting` — dependency warning: ModuleNotFoundError: No module named 'pandas'
- [PASS] `import_src_app_visualization` — 
- [PASS] `import_src_pdf_report_generator` — dependency warning: ModuleNotFoundError: No module named 'pandas'

## Summary

Phase 9E-P2/P2-P1 adds user-facing Gradio dashboard layout, waveform visualization,
PDF/JSON report export, segment-candidate interpretation fix, and dark-theme cards.
Inference logic and thresholds are unchanged.
Primary application path remains `release/`.

Optional dependency: `reportlab` for PDF output (HTML fallback if missing).
