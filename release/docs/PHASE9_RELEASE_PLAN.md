# Phase 9 Release Plan

| Phase | Description | Status |
|---|---|---|
| 9A | Release skeleton (`release/`, configs, docs, CLI/API stubs) | **COMPLETED** |
| 9B | Active model packaging into `release/models/` | **COMPLETED** |
| 9B-R | Reference model copy (inactive) | **COMPLETED** |
| 9C | Live single-audio inference pipeline | **ACCEPTED WITH LIMITATION** |
| 9D | Controlled end-to-end testing scripts | **SCRIPT CREATED / TESTING PENDING** |
| 9E | FastAPI + Gradio local apps | **NOT STARTED** (after 9D review) |
| 9F | Teammate integration documentation | **NOT STARTED** |
| 9G | End-to-end release testing and freeze | **NOT STARTED** |

## Phase 9C (accepted with limitation)

- Audio load, segmentation, features, SSL, active model predict, fusion, and safe reports work on smoke cases.
- Partial localization and replay/mixer arbitration require broader Phase 9D measurement.
- No `fake_score` / `real_score`; evidence axes remain separate.

### Phase 9C manual smoke (user)

```bat
cd release
python analyze_audio_cli.py --audio path\to\audio.wav --case_id demo001
python ..\code\phase9\release\validate_phase9c_inference_pipeline.py --sample_output release\sample_outputs\demo001_analysis.json
```

## Phase 9D (testing pending)

Scripts under `code/phase9/testing/` — **user runs manually**:

```bat
python code/phase9/testing/build_phase9d_test_manifest.py --include_bad_audio_tests
python code/phase9/testing/run_phase9d_batch_inference.py
python code/phase9/testing/summarize_phase9d_results.py --make_plots
python code/phase9/testing/validate_phase9d_end_to_end_tests.py
```

Design: `reports/phase9/testing/phase9d_testing_design.md`

## Phase 9E (after 9D)

- Wire `release/src/inference_pipeline.py` into FastAPI and Gradio skeletons.
- Keep `experimental_forensic_prototype` status and manual-review wording.
- Do not activate reference models in default inference path.

## Safety (all phases)

- Active inference: origin, replay, mixer, partial_segment only.
- AASIST / HybridResNet: reference-only, inactive in live path.
- No final fake/real decision field.
