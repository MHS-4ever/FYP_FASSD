# Phase 7E3A — Run Readiness Check

**Generated:** 2026-05-26T20:24:27.695831+00:00
**READY_TO_RUN:** `True`

## Checks

- `aasist_src_exists`: **PASS**
- `config_exists`: **PASS**
- `checkpoint_exists`: **PASS**
- `eval_manifest_exists`: **PASS**
- `output_dir_writable`: **PASS**
- `class_convention_detected`: **PASS**
- `class_convention_verified`: **PASS**

## Class convention

- **spoof_class_index_used:** 0
- **bonafide_class_index_used:** 1
- **class_convention_source:** `official_aasist_label_mapping`
- **class_convention_warning:** `(none)`
- **audit notes:** data_utils.py: training label 1=bonafide, 0=spoof; main.py produce_evaluation_file: evaluation score = logits[:, 1] (bonafide)

