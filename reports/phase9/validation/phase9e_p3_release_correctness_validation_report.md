# Phase 9E-P3 Release Correctness Validation Report

Generated: 2026-06-03T20:05:46.875772+00:00
Mode: full

**Overall:** PASS

## Checks

- [PASS] `design_doc_exists` — E:\FYP\reports\phase9\app\phase9e_p3_release_decision_hierarchy_design.md
- [PASS] `build_voice_origin_result` — 
- [PASS] `build_recommendation_level` — 
- [PASS] `build_axis_interpretation` — 
- [PASS] `voice_origin_text_in_summary` — 
- [PASS] `forensic_indicator_summary` — 
- [PASS] `partial_module_mode_field` — 
- [PASS] `models_lru_cache` — 
- [PASS] `ssl_lru_cache` — 
- [PASS] `safe_nanmean_feature_fix` — 
- [PASS] `origin_support_models_module` — 
- [PASS] `no_vague_suspicious_primary_in_render` — 
- [PASS] `gradio_voice_origin_first` — 
- [PASS] `forbidden_wording_absent` — 
- [PASS] `partial_thresholds_unchanged` — {'file_gate_threshold': 0.5, 'segment_threshold': 0.9, 'contrast_threshold': 0.25, 'broad_limit': 0.45}
- [PASS] `json_fields_complete` — 
- [PASS] `human_clean_optional_review_wording` — Optional review of the candidate segment may be useful for sensitive cases.
- [PASS] `human_clean_not_strong_suspicious` — Voice origin: Likely human
- [PASS] `human_clean_voice_likely_human_or_inconclusive` — {'origin_label': 'likely_human', 'display_text': 'Voice origin: Likely human', 'confidence_text': 'Origin evidence score: 0.100', 'evidence_source': 'ssl_origin_model', 'evidence_sources': ['ssl_origin_model'], 'explanation': 'The active SSL origin model does not show strong AI-origin indicators. This does not prove authenticity.', 'ssl_origin_detected': False}
- [PASS] `partial_review_candidate_status` — {'axis_name': 'Partial replacement evidence', 'status': 'Review candidate', 'user_text': 'A segment-level candidate was highlighted by the experimental partial module. This alone is not enough to mark the full audio as suspicious.', 'score_text': '', 'severity': 'candidate'}
- [PASS] `replay_mixer_overlap_wording_present` — ['Replay-like artifacts overlap with channel/mixer processing evidence. Mixer/channel processing should be reviewed as the dominant indicator.', 'Mixer/channel processing evidence is dominant; replay-like artifacts may overlap.']
- [PASS] `origin_processing_inconclusive_rule` — Voice origin: Inconclusive under replay/channel processing
- [PASS] `no_aasist_resnet_activation` — 
- [PASS] `eval_output_phase9e_p3_8variant_results.csv` — E:\FYP\reports\phase9\app\phase9e_p3_8variant_eval\phase9e_p3_8variant_results.csv
- [PASS] `eval_output_phase9e_p3_release_correctness_report.md` — E:\FYP\reports\phase9\app\phase9e_p3_8variant_eval\phase9e_p3_release_correctness_report.md
- [PASS] `eval_output_phase9e_p3_reference_model_audit.md` — E:\FYP\reports\phase9\app\phase9e_p3_8variant_eval\phase9e_p3_reference_model_audit.md
- [PASS] `eval_output_phase9e_p3_terminal_resource_audit.md` — E:\FYP\reports\phase9\app\phase9e_p3_8variant_eval\phase9e_p3_terminal_resource_audit.md
- [PASS] `human_clean_false_suspicious_rate_low` — 0.0
- [PASS] `full_mode_metrics_present` — 184
- [PASS] `terminal_audit_models_cached` — 
- [PASS] `terminal_audit_feature_fix` — 
- [PASS] `terminal_warning_cleanup` — # phase 9e-p3-p1 terminal & resource audit

- models cached (lru_cache): yes
- ssl extractor cached: yes
- repeated weight loading lines observed: 2
- repeated weight loading reduced: yes
- feature empty-slice warning fixed (safe_nanmean): yes
- runtime_warning_count: 0
- feature_warning_count: 0
- external_warning_count: 0
- real_error_count: 0
- traceback_count: 0
- files evaluated: 184
- termin
- [PASS] `terminal_clean_enough_for_demo` — 
- [PASS] `human_clean_optional_review_human_001_clean.wav` — rec=Optional review of the candidate segment may be useful for sensitive cases. level=optional_review
- [PASS] `human_clean_optional_review_human_004_clean.wav` — rec=Optional review of the candidate segment may be useful for sensitive cases. level=optional_review
- [PASS] `human_clean_optional_review_human_021_clean.wav` — rec=Optional review of the candidate segment may be useful for sensitive cases. level=optional_review

## Notes

Phase 9E-P3-P1 adds optional-review wording for clean segment candidates,
complete JSON report fields, replay/mixer overlap interpretation,
origin-under-processing wording, terminal warning audit, and validator gates.
No model retraining or threshold changes.
AASIST/ResNet remain audit_only in P3-P1.
