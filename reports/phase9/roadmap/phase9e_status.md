# Phase 9E Status

| Field | Value |
|-------|--------|
| Phase | 9E-P1-P1 — Release app integration (correct placement) |
| Status | **Release app updated** — run `validate_phase9e_release_apps.py` |
| Prior | Phase 9D-P6-P1 PASS — `partial_fabrication_experimental_p5b` packaged |

## Primary app path

**`release/`** — not `code/phase9/app/`.

| Component | Path |
|-----------|------|
| FastAPI | `release/app_fastapi.py` |
| Gradio | `release/app_gradio.py` |
| Formatting | `release/src/app_report_formatting.py` |
| Inference | `release/src/inference_pipeline.py` |
| P6 package | `release/models/partial_fabrication_experimental_p5b/` |
| Validator | `code/phase9/partial_redesign/validate_phase9e_release_apps.py` |

Legacy skeleton (`code/phase9/app/`) remains for reference only.

## P1-P1 deliverables

- [x] `release/src/app_report_formatting.py`
- [x] `release/app_fastapi.py` — P6 partial section, `/analyze-audio`
- [x] `release/app_gradio.py` — partial panel + segment table
- [x] `code/phase9/partial_redesign/validate_phase9e_release_apps.py`
- [x] `reports/phase9/app/phase9e_p1_app_design.md` (release-primary)

## Behavior

- Calls Phase 9C `analyze_audio_file()` (no retrain, no threshold changes).
- Maps output to P6 `partial_fabrication` contract via `app_report_formatting.py`.
- `manual_review_required` always true; `conclusive_authenticity_decision`: no.
- Old partial segment model not active for Phase 9E demo (inventory check).

## User next steps

1. `py_compile` release app files + validator
2. `python code/phase9/partial_redesign/validate_phase9e_release_apps.py`
3. Manually run `release/run_fastapi.bat` or `release/run_gradio.bat` when ready

## Out of scope

- Retraining or threshold changes
- Writing to `models_saved/active`
- Operational or legal-evidence claims
- Phase 9F / 9G
