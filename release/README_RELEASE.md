# Phase 9 Release (Experimental Forensic Prototype)

This `release/` folder contains the local experimental forensic prototype.

## Status

- Phase 9A: skeleton — **COMPLETED**
- Phase 9B: active model packaging — **COMPLETED**
- Phase 9B-R: reference models (inactive) — **COMPLETED**
- Phase 9C: live inference CLI — **SCRIPT CREATED** (P1: aligns to `feature_names_in_`)

## Phase 9C CLI (manual run)

From repository root, after dependencies and packaged models are in place:

```bat
cd release
python analyze_audio_cli.py --audio sample_audio\your_file.wav --case_id demo001
```

Outputs:
- `release/sample_outputs/<case_id>_analysis.json`
- `release/sample_outputs/<case_id>_report.md`

Options:
- `--device auto|cpu|cuda`
- `--debug` for step trace

## Web apps (later)

- FastAPI: `run_fastapi.bat` (Phase 9D+)
- Gradio: `run_gradio.bat` (Phase 9E+)

## Safety

- Active models only: origin / replay / mixer / partial_segment
- AASIST and HybridResNet are reference-only and inactive
- No fake_score / real_score / final fake-real decision
- Manual review recommended

Torch/transformers install may depend on local CPU/CUDA setup.
