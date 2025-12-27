# Release (Local Demo App)

This folder is the **final, runnable local demo** for the project UI (Gradio).  
It is designed so you can:
- run the app locally with one command
- swap the deployed model by replacing one file in `release/model/`
- keep demo inputs/outputs organized for screenshots and submission

> Phase 6 will implement the actual Gradio app + explanation pipeline.  
> This document defines the intended final structure now, so packaging is easy later.

## Folder structure (planned)

```
release/
├── README.md
├── app.py                      # Gradio entrypoint (created in Phase 6)
├── model/
│   ├── hybrid_resnet_environmental_best.pth  # "current" deployed model
│   └── model_info.json          # optional: metadata (date, metrics, notes)
├── inputs/
│   ├── demo_real.wav            # optional small demo file(s)
│   └── demo_fake.wav
├── outputs/
│   ├── last_run.json            # latest prediction/explanation (optional)
│   └── exports/                 # saved reports/figures per run
└── assets/
    └── screenshots/             # thesis/report screenshots (optional)
```

## Model update workflow (planned)

When you train a new model/checkpoint:
1. Copy the new checkpoint into `release/model/`
2. Rename it to the expected deployed filename (recommended):
   - `hybrid_resnet_environmental_best.pth`
3. (Optional) Update `release/model/model_info.json` with:
   - source checkpoint path
   - Phase 5 metrics summary
   - date/version

This keeps the Gradio app configuration stable while the model evolves.

## Inputs: where to put your Trump demos

Recommendation:
- Keep the full set in `testing_audios/` (research artifact)
- Copy a small subset (shorter clips) into `release/inputs/` for demos

Reason: your Trump wavs are large (50–150MB). Smaller clips make the UI faster and easier to share.

## How the app will run (planned)

From repo root:

```powershell
cd E:\FYP
conda activate fassd
python release/app.py
```

The app will:
- accept an uploaded `.wav` (or select from `release/inputs/`)
- run chunked inference for long audio
- show:
  - prediction (REAL/FAKE)
  - confidence
  - predicted attack type
  - explanation (environment feature contributions + spectrogram visualization)
- optionally export a JSON report into `release/outputs/`

## Dependencies

Your project already includes most required packages in `requirements.txt`.  
Phase 6 will add/confirm UI dependencies (e.g., Gradio).


