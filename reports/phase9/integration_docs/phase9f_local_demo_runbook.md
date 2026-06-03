# Phase 9F — Local Demo Runbook

**Environment:** conda env `fassd`  
**App root:** `E:\FYP\release`

---

## Prerequisites

1. Clone or extract the FYP repo (or Phase 9G handoff zip) with `release/models/` artifacts intact.
2. Activate conda environment:

```bat
conda activate fassd
```

3. Install Python dependencies (from repo root or `release/`):

```bat
pip install fastapi uvicorn gradio python-multipart reportlab
pip install -r release\requirements_release.txt
```

Core packages: `fastapi`, `uvicorn`, `gradio`, `python-multipart`, `torch`, `librosa`, `joblib`, `pandas`, `matplotlib`.  
Add `reportlab` if PDF generation is required (`generate_report=true` or Gradio PDF download).

---

## Run Gradio UI

```bat
cd /d E:\FYP\release
conda activate fassd
python app_gradio.py
```

Or double-click `run_gradio.bat` (same directory).

**Expected URL:** `http://127.0.0.1:7860`

Upload an audio file, review cards, download JSON/PDF/waveform from the UI.

---

## Run FastAPI

**Option A — uvicorn via batch file (recommended):**

```bat
cd /d E:\FYP\release
run_fastapi.bat
```

**Option B — direct Python module:**

```bat
cd /d E:\FYP\release
conda activate fassd
python -m uvicorn app_fastapi:app --host 127.0.0.1 --port 8000
```

**Expected URLs:**

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:8000/` | Root metadata |
| `http://127.0.0.1:8000/health` | Health check |
| `http://127.0.0.1:8000/model-info` | Model inventory |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/analyze-audio` | POST analyze |

---

## Verify models loaded

```bat
curl http://127.0.0.1:8000/health
```

Expect `"models_loaded": true`. If `false`, read `models_load_error` and confirm:

- `release/models/origin/`, `replay/`, `mixer/`, `partial_segment/` joblib files exist
- `release/config/model_paths.yaml` paths resolve
- conda env has `torch`, `joblib`, `librosa`

---

## Quick analyze test

```bat
curl -X POST "http://127.0.0.1:8000/analyze-audio?generate_visual=false&generate_report=false" ^
  -F "audio_file=@E:\FYP\release\sample_audio\your_clip.wav" ^
  -F "case_id=demo001"
```

Replace the audio path with any small local `.wav` file.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `models_loaded: false` | Missing joblib artifacts | Restore `release/models/` from handoff package; do not retrain |
| ImportError for `gradio` / `fastapi` | Wrong env | `conda activate fassd` and reinstall requirements |
| CUDA errors | GPU driver / torch mismatch | Set device to CPU in CLI paths; API uses `device="auto"` |
| Port already in use | Previous server still running | Stop other uvicorn/gradio processes or change port |
| PDF generation fails | Missing `reportlab` | `pip install reportlab` |
| Deprecation warning spam | torch attention mask | P4B filters specific `key_padding_mask` warning only — other warnings may still appear |
| Slow first request | Model load + SSL embed warmup | Normal; subsequent requests faster |
| Gradio file access error | Path outside allowed_paths | Run from `release/`; app allows `release_root()` |

---

## Output locations

| Output | Location |
|--------|----------|
| Gradio temp JSON/PDF/waveform | `release/gradio_outputs/` |
| API save_report JSON | `reports/phase9/app/sample_outputs/` |
| PDF/waveform from API flags | Paths returned in response fields |

Handoff package excludes large `gradio_outputs/` temp history — fresh runs create new files locally.

---

## What this runbook does not cover

- Production deployment, scaling, or authentication
- Legal evidence workflows
- Model retraining or threshold tuning

For integration details see [phase9f_integration_examples.md](phase9f_integration_examples.md) and [phase9f_api_contract.md](phase9f_api_contract.md).
