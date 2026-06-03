# Phase 9F — Teammate Handoff

**Product name:** Deepfake Audio Detector — Local Demo  
**Research / FYP name:** Forensic Acoustic for Synthetic Speech Detection  
**Frozen app phase:** Phase 9E-P4B (demo freeze accepted)  
**Active app path:** `release/`

This handoff covers the local experimental forensic demo after Phase 9E-P3/P4A/P4B validation. It is documentation and packaging only — no model behavior changes in Phase 9F/9G.

---

## What this is

A multi-axis **evidence review** prototype for audio files. It reports experimental indicators for:

- Voice origin (SSL model)
- Replay / rerecording
- Mixer / channel processing
- Partial fabrication (segment candidate only, experimental)

**Conclusive authenticity decision: no.** Manual forensic review is recommended when strong indicators are present.

---

## How to run locally

### Gradio UI

```bat
cd /d E:\FYP\release
conda activate fassd
python app_gradio.py
```

Default URL: `http://127.0.0.1:7860`

### FastAPI

```bat
cd /d E:\FYP\release
conda activate fassd
python app_fastapi.py
```

Or:

```bat
cd /d E:\FYP\release
run_fastapi.bat
```

Default URL: `http://127.0.0.1:8000`  
Interactive docs: `http://127.0.0.1:8000/docs`

See [phase9f_local_demo_runbook.md](phase9f_local_demo_runbook.md) for environment, dependencies, and troubleshooting.

---

## Active vs inactive models

### Active (release inference path)

| Model | Role |
|-------|------|
| `origin_file_model` | Voice origin (SSL) |
| `replay_file_model` | Replay / rerecording evidence |
| `mixer_file_model` | Mixer / channel processing evidence |
| `partial_fabrication_experimental_p5b` | Partial fabrication segment candidate (experimental, manual review) |

Legacy `partial_fabrication_segment_model` remains in inventory for compatibility but is **not** the active P5B cascade.

### Inactive / reference only

| Model | Decision |
|-------|----------|
| AASIST | `reject_for_now` — shadow-tested Phase 9E-P4A, not active |
| HybridResNet / ResNet | `reject_for_now` — shadow-tested Phase 9E-P4A, not active |

See [phase9f_model_registry_guide.md](phase9f_model_registry_guide.md).

---

## How to call the API

Primary endpoint: `POST /analyze-audio`

- Multipart field: `audio_file` (required)
- Optional form field: `case_id`
- Query params: `return_top_segments`, `save_report`, `generate_report`, `generate_visual`

Legacy alias: `POST /analyze` (same upload, default query flags).

Full contract: [phase9f_api_contract.md](phase9f_api_contract.md)  
Examples: [phase9f_integration_examples.md](phase9f_integration_examples.md)

---

## How to interpret responses

### JSON report

Key top-level fields:

- `voice_origin_result` — display text such as *Voice origin: Likely AI-generated* or *Voice origin: Inconclusive under replay/channel processing*
- `forensic_indicator_summary` — short bullet-style summary of detected axes
- `recommendation` / `recommendation_level` — `none`, `optional_review`, `review_recommended`, or `unavailable`
- `evidence_axis_cards` — per-axis cards for UI
- `partial_fabrication` — experimental partial module output; **segment candidate only**
- `partial_module_mode` — typically `segment_candidate_only`
- `limitations` / `safety` — always surface these in UI
- `conclusive_authenticity_decision` — always `false`

Optional paths when requested:

- `pdf_report_path` — if `generate_report=true`
- `waveform_image_path` — if `generate_visual=true`
- `saved_report_path` — if `save_report=true`

See [phase9f_report_wording_guide.md](phase9f_report_wording_guide.md).

### PDF report

Generated when `generate_report=true` or via Gradio download. PDF uses the same cautious wording as JSON — no conclusive fake/real label. Show disclaimer from `safety.wording`.

---

## What not to claim

- Do **not** claim operational deployment readiness
- Do **not** claim legal-evidence or courtroom readiness
- Do **not** claim conclusive authenticity (fake vs real)
- Do **not** use forbidden verdict wording listed in the wording guide
- Do **not** treat partial fabrication as guaranteed full replacement detection
- Do **not** activate AASIST/ResNet without a new validation phase

---

## Known limitations

Summary — full list in [phase9f_known_limitations.md](phase9f_known_limitations.md):

- Partial fabrication is experimental / manual-review candidate only
- Full partial replacement detection is not guaranteed
- Replay/channel processing reduces origin reliability
- Replay and mixer artifacts may overlap
- AASIST/ResNet rejected for now (`reject_for_now`)
- Local demo only

---

## Validation baseline

| Phase | Status |
|-------|--------|
| Phase 9E-P3 release correctness | PASS (184/184) |
| Phase 9E-P4A origin support shadow | PASS (`reject_for_now`) |
| Phase 9E-P4B demo freeze | PASS |
| Phase 9F integration docs | See validation report |

P4B validation: `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`

---

## Documentation index

| Document | Purpose |
|----------|---------|
| [phase9f_api_contract.md](phase9f_api_contract.md) | REST endpoints and response schema |
| [phase9f_model_registry_guide.md](phase9f_model_registry_guide.md) | Active/inactive models and thresholds |
| [phase9f_report_wording_guide.md](phase9f_report_wording_guide.md) | Allowed vs forbidden UI text |
| [phase9f_local_demo_runbook.md](phase9f_local_demo_runbook.md) | Setup and run commands |
| [phase9f_integration_examples.md](phase9f_integration_examples.md) | curl / Python / frontend notes |
| [phase9f_known_limitations.md](phase9f_known_limitations.md) | Honest scope limits |
| [phase9f_release_file_map.md](phase9f_release_file_map.md) | Release folder layout |

---

## Next phase handoff notes

1. **Phase 9G** packages this demo into `release_packages/phase9g_deepfake_audio_detector_demo_handoff.zip` after Phase 9F validation PASS.
2. Frontend teammates should integrate against `POST /analyze-audio` and render cards from `voice_origin_result` + `evidence_axis_cards`; hide raw JSON under an advanced panel.
3. Any model swap, threshold change, or AASIST/ResNet activation requires a **new validation phase** — do not edit `release/models/` artifacts casually.
4. Datasets and raw audio under `data/` and `testing_audios/` are **not** included in the handoff package.
