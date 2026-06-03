# Phase 9F — Release File Map

Layout of the active **`release/`** demo app path for teammate orientation.

---

## Top level

| Path | Purpose |
|------|---------|
| `release/app_gradio.py` | Gradio UI entrypoint |
| `release/app_fastapi.py` | FastAPI REST entrypoint |
| `release/run_gradio.bat` | Launch Gradio |
| `release/run_fastapi.bat` | Launch uvicorn on port 8000 |
| `release/requirements_release.txt` | Python dependencies |
| `release/README.md` | Legacy structure notes |
| `release/README_RELEASE.md` | Phase 9 release status notes |

---

## Source code — `release/src/`

| File | Role |
|------|------|
| `app_report_formatting.py` | API/Gradio response formatting, wording, cards |
| `inference_pipeline.py` | Phase 9C analyze pipeline |
| `model_loader.py` | Load active packaged models |
| `fusion_rules.py` | Multi-axis fusion rules |
| `feature_extraction.py` | Acoustic / SSL features |
| `ssl_embeddings.py` | SSL embedding extraction |
| `segmentation.py` | Audio segmentation |
| `audio_io.py` | Audio I/O |
| `report_generator.py` | Markdown report helpers |
| `pdf_report_generator.py` | PDF export |
| `app_visualization.py` | Waveform highlight images |
| `origin_support_models.py` | AASIST/ResNet shadow wrappers (inactive) |
| `schemas.py` | Data schemas |
| `utils.py` | YAML/path helpers |

---

## Configuration — `release/config/`

| File | Role |
|------|------|
| `model_paths.yaml` | Active model artifact paths |
| `fusion_thresholds.yaml` | Fusion thresholds (frozen) |
| `runtime_config.yaml` | Runtime defaults |
| `label_schema.yaml` | Label definitions |

---

## Models — `release/models/`

| Path | Contents |
|------|----------|
| `model_inventory.json` | Active model registry + integration modules |
| `origin/` | SSL origin file model + metadata |
| `replay/` | Replay file model + metadata |
| `mixer/` | Mixer file model + metadata |
| `partial_segment/` | Legacy partial segment model (deprecated for P5B cascade) |
| `partial_fabrication_experimental_p5b/` | P5B partial module package (active for demo) |
| `reference/` | AASIST / HybridResNet reference artifacts (inactive) |

---

## Runtime outputs (local only, excluded from handoff zip)

| Path | Notes |
|------|-------|
| `release/gradio_outputs/` | Gradio JSON/PDF/waveform temp files |
| `release/sample_outputs/` | CLI sample outputs |
| `reports/phase9/app/sample_outputs/` | API `save_report=true` outputs |

---

## Integration documentation — Phase 9F

| Path | Document |
|------|----------|
| `reports/phase9/integration_docs/phase9f_teammate_handoff.md` | Main handoff |
| `reports/phase9/integration_docs/phase9f_api_contract.md` | REST contract |
| `reports/phase9/integration_docs/phase9f_model_registry_guide.md` | Models |
| `reports/phase9/integration_docs/phase9f_report_wording_guide.md` | Wording |
| `reports/phase9/integration_docs/phase9f_local_demo_runbook.md` | Run commands |
| `reports/phase9/integration_docs/phase9f_integration_examples.md` | curl/Python |
| `reports/phase9/integration_docs/phase9f_known_limitations.md` | Limitations |
| `reports/phase9/integration_docs/phase9f_release_file_map.md` | This file |

---

## Validation and demo evidence reports

| Path | Purpose |
|------|---------|
| `reports/phase9/validation/phase9e_p3_release_correctness_validation_report.md` | P3 PASS |
| `reports/phase9/validation/phase9e_p4a_origin_support_validation_report.md` | P4A PASS |
| `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md` | P4B PASS |
| `reports/phase9/validation/phase9f_integration_docs_validation_report.md` | Phase 9F validator output |
| `reports/phase9/app/phase9e_p4b_demo_freeze/` | Demo freeze CSV + checklist (included in handoff) |
| `reports/phase9/app/phase9e_p3_8variant_eval/` | Full 184 regression metrics (repo only; not full per-file tree in zip) |

---

## Final handoff package — Phase 9G

| Path | Purpose |
|------|---------|
| `release_packages/phase9g_deepfake_audio_detector_demo_handoff.zip` | Demo/handoff archive |
| `reports/phase9/final_release/phase9g_final_release_report.md` | Release summary |
| `reports/phase9/final_release/phase9g_final_release_manifest.csv` | Package file list |
| `reports/phase9/final_release/phase9g_final_checksums_sha256.txt` | SHA-256 checksums |

---

## Explicitly excluded from handoff package

- `data/` — research datasets
- `testing_audios/` — large test audio
- `__pycache__/`, `.git/`, `.venv/`, env folders
- Large `gradio_outputs/` history
- Full 184 per-file P3 output tree (metrics/reports referenced instead)
- `models_saved/active/` — not part of release path
