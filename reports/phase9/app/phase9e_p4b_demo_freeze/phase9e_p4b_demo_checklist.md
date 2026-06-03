# Phase 9E-P4B — Demo Readiness Checklist

Use this checklist before presenting the frozen release demo.

## Environment

- [ ] Conda env `fassd` activated (pandas, torch, gradio, fastapi available)
- [ ] Working directory: `E:\FYP\release`
- [ ] Phase 7C1 sample audio available under `data/phase7c1/raw/` (optional; any supported WAV works)

## Launch

- [ ] Gradio: `python app_gradio.py` or `run_gradio.bat`
- [ ] FastAPI (optional): `run_fastapi.bat` → http://127.0.0.1:8000/health

## UI walkthrough (Gradio)

- [ ] Title shows **Deepfake Audio Detector — Local Demo**
- [ ] Research line shows **Forensic Acoustic for Synthetic Speech Detection**
- [ ] Upload audio → **Analyze**
- [ ] Main result shows **voice origin first**, then forensic indicators, then recommendation
- [ ] Evidence indicator cards visible (AI-origin, Replay, Channel/mixer, Partial)
- [ ] Waveform/timeline image renders
- [ ] PDF and JSON download buttons work
- [ ] Advanced details / Raw JSON collapsed by default

## Representative demo samples (base 001)

| Variant | File | Expected highlight |
|---------|------|-------------------|
| ai_clean | `ai_001_direct.wav` | Likely AI-generated |
| ai_fabricated | `ai_001_fabricated.wav` | Likely AI-generated + indicators |
| ai_mixer | `ai_001_mixer_processed.wav` | AI with processing indicators |
| ai_replayed | `ai_001_replay_laptop_mobile.wav` | Inconclusive under replay |
| human_clean | `human_001_clean.wav` | Likely human + **optional** segment review |
| human_fabricated | `human_001_fabricated.wav` | Likely human, no strong indicators |
| human_mixer | `human_001_mixer_processed.wav` | Inconclusive + overlap wording |
| human_replayed | `human_001_replay_laptop_mobile.wav` | Inconclusive + replay detected |

Full paths and artifact locations: `phase9e_p4b_final_demo_samples.csv`

## Safety wording (must appear)

- [ ] Conclusive authenticity decision: **no**
- [ ] Experimental evidence indicators only
- [ ] Manual forensic review recommended when indicators present
- [ ] No “definitely fake/real”, “final verdict”, “court proof”, “production ready”

## What NOT to claim

- [ ] Do not claim AASIST/ResNet are active
- [ ] Do not claim partial module is a strong detector
- [ ] Do not claim operational or legal-evidence readiness

## Validation

- [ ] `python code\phase9\partial_redesign\validate_phase9e_p4b_demo_freeze.py` → PASS
