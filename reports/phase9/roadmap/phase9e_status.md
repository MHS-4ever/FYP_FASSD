# Phase 9E Status

| Field | Value |
|-------|--------|
| Phase | **9E-P4B** — Demo freeze (accepted) |
| Product | **Deepfake Audio Detector — Local Demo** |
| Research / FYP | **Forensic Acoustic for Synthetic Speech Detection** |
| Next | **Phase 9F** (may start after P4B validator PASS) |

## Phase acceptance timeline

| Sub-phase | Status | Summary |
|-----------|--------|---------|
| 9E-P1 / P1-P1 | Accepted | Release app + P6 partial contract integration |
| 9E-P2 / P2-P1 | Accepted | UI redesign, waveform, PDF/JSON, clean-human wording fix |
| 9E-P3 | **PASS** | Voice-origin-first hierarchy; 184-file regression |
| 9E-P3-P1 | **PASS** | Optional review wording; JSON completeness; terminal audit |
| 9E-P4A | **PASS** | AASIST/HybridResNet shadow eval; both **reject_for_now** |
| 9E-P4B | **PASS** | Demo freeze — naming, docs, samples, validator |

## Primary app path

**`release/`** — not `code/phase9/app/`.

| Component | Path |
|-----------|------|
| Gradio | `release/app_gradio.py` / `run_gradio.bat` |
| FastAPI | `release/app_fastapi.py` / `run_fastapi.bat` |
| Formatting | `release/src/app_report_formatting.py` |
| Inference | `release/src/inference_pipeline.py` |
| P6 package | `release/models/partial_fabrication_experimental_p5b/` |
| P3 validator | `code/phase9/partial_redesign/validate_phase9e_p3_release_correctness.py` |
| P4A validator | `code/phase9/partial_redesign/validate_phase9e_p4a_origin_support.py` |
| P4B validator | `code/phase9/partial_redesign/validate_phase9e_p4b_demo_freeze.py` |

## Run demo

```bat
cd /d E:\FYP\release
conda activate fassd
python app_gradio.py
```

## Active vs reference models

**Active (voice origin + forensic axes):**

- SSL `origin_file_model` — voice origin decision
- `replay_file_model`, `mixer_file_model`
- `partial_fabrication_experimental_p5b` — segment candidate / experimental manual review only

**Reference (inactive):**

- AASIST — P4A **reject_for_now**
- HybridResNet — P4A **reject_for_now**

## Regression baseline

- P3 full: 184/184 files, 0 failures, `human_clean_false_suspicious_rate = 0.0`
- P4A full: 184/184 shadow eval, SSL remains baseline

## P4B deliverables

- `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_demo_freeze_report.md`
- `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_demo_checklist.md`
- `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_final_demo_samples.csv`
- `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_known_limitations.md`
- `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`

## Out of scope (frozen)

- Retraining or threshold changes
- AASIST/ResNet activation
- Writing to `models_saved/active` or overwriting `release/models`
- Operational or legal-evidence claims
- Phase 9F/9G implementation inside P4B

## Validate freeze

```bat
python code\phase9\partial_redesign\validate_phase9e_p4b_demo_freeze.py
```
