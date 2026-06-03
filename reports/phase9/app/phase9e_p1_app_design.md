# Phase 9E-P1 — Local FastAPI + Gradio App Design

> **Note (Phase 9E-P2):** P2 refines the release Gradio/FastAPI **UI and report export only** (dashboard layout, waveform, PDF/JSON downloads, concise summaries). Inference and model packages are unchanged. See `phase9e_p2_ui_report_design.md`.

## Primary application location

**The real app location is `release/`.** Phase 9E uses the existing release application resources:

- `release/app_fastapi.py`
- `release/app_gradio.py`
- `release/run_fastapi.bat`
- `release/run_gradio.bat`
- `release/src/inference_pipeline.py` → `analyze_audio_file()`
- `release/src/app_report_formatting.py` — P6 partial contract formatting

An earlier Phase 9E attempt placed a duplicate skeleton under `code/phase9/app/`. **That path is not the primary app path** and is kept only as a legacy reference.

## Purpose

Expose the **tested Phase 9C live single-audio inference pipeline** through local FastAPI and Gradio apps for supervisor/demo use. Partial-fabrication evidence is presented using the **Phase 9D-P6** experimental package contract (`partial_fabrication_experimental_p5b`) as a separate manual-review axis.

**Conclusive authenticity decision: no.**  
**Operational deployment claim: no.**  
**Legal-evidence claim: no.**

## Architecture

```
release/
  app_fastapi.py
  app_gradio.py
  run_fastapi.bat
  run_gradio.bat
  src/
    inference_pipeline.py    # Phase 9C analyze_audio_file()
    app_report_formatting.py # Phase 9C JSON → P6 partial_fabrication section
    model_loader.py
    report_generator.py
    schemas.py
  models/
    partial_fabrication_experimental_p5b/
      partial_module_metadata.json
      partial_report_contract.json

code/phase9/partial_redesign/
  validate_phase9e_release_apps.py
  phase9d_p6_partial_report_contract.py   # shared wording helpers
```

P6 partial package consumed from:

- `release/models/partial_fabrication_experimental_p5b/`

## FastAPI endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info, endpoints, safety wording |
| GET | `/health` | Health + `models_loaded` + partial module status |
| GET | `/model-info` | Inventory summary, P6 metadata, thresholds, limitations |
| POST | `/analyze-audio` | Upload audio; optional `return_top_segments`, `save_report` |
| POST | `/analyze` | Backward-compatible alias |

Response includes `partial_fabrication` with:

- `module_status`, `evidence_detected`, `evidence_label`
- `file_gate_probability`, `max_segment_probability`, `high_segment_fraction`
- `topk_minus_rest_probability`, `broad_activation_flag`
- `candidate_segment`, `top_segments`, `thresholds`, `limitations`, `user_facing_message`

## Gradio UI

- Audio upload + **Analyze**
- User-facing summary (experimental partial wording)
- Full JSON + `partial_fabrication` panel
- Top candidate segment table
- Limitations box

## Partial fabrication contract

Loaded from:

- `release/models/partial_fabrication_experimental_p5b/partial_module_metadata.json`
- `release/models/partial_fabrication_experimental_p5b/partial_report_contract.json`

Status: `experimental_manual_review_only`  
Manual review required: yes  
Production ready / court ready / final verdict model: **no**

## Safety wording

- Experimental partial-fabrication evidence indicator only
- Manual forensic review recommended
- No detection does not prove authenticity
- Analysis unavailable → manual review if partial manipulation suspected
- Forbidden in app sources: definitely fake/real, final verdict, production-ready, court-ready, court proof

## Validation

```text
python -m py_compile release\app_fastapi.py
python -m py_compile release\app_gradio.py
python -m py_compile release\src\app_report_formatting.py
python -m py_compile code\phase9\partial_redesign\validate_phase9e_release_apps.py

python code\phase9\partial_redesign\validate_phase9e_release_apps.py
```

Report: `reports/phase9/validation/phase9e_release_app_validation_report.md`

## How to run locally (user)

From `release/`:

```text
run_fastapi.bat
run_gradio.bat
```

Requires Phase 9C dependencies and optional `gradio`, `fastapi`, `uvicorn`, `python-multipart`.

## What is not claimed

- Operational deployment readiness
- Legal-evidence readiness
- Conclusive authenticity decision
- Fully solved partial-fabrication detection

## Phase 9F / 9G

Not started in P1.
