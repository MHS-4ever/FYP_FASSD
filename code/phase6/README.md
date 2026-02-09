# Phase 6: Explanation System

Generate explanations for the Phase 4 hybrid model on raw audio (e.g., your `testing_audios/` Trump set). The script chunks long audio, extracts log-mel + environmental features, runs the trained hybrid checkpoint, and saves per-file JSON/CSV summaries plus optional plots (coming later if needed).

## Quick start (Laptop paths)

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_dir E:/FYP/testing_audios --output_dir reports/explanation_examples --batch_size 32 --threshold 0.5
```

Outputs (one run):
- `reports/explanation_examples/results.csv` (per-file scores + decisions)
- `reports/explanation_examples/{filename}.json` (per-file explanation)

## Run on the labeled test manifest (validation)

Use this when you want explanations for the **same distribution** used in Phase 5 evaluation.

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --output_dir reports/explanations_test --batch_size 32 --threshold 0.5 --max_files 100
```

## Options (common)
- `--audio_dir` / `--audio_path` : folder or single file
- `--ckpt` : Phase 4 best checkpoint (`models_saved/hybrid_resnet_environmental_best.pth`)
- `--test_manifest` : CSV manifest with a `filepath` column (bulk validation run)
- `--chunk_duration` (default 4s), `--overlap` (default 1s) — defaults match the Phase 4 training window
- `--threshold` (default 0.5) : decision threshold on spoof prob
- `--batch_size` (default 32) : chunk batch size for inference

## Notes
- Uses on-the-fly feature extraction (log-mel 64×400 with per-sample norm; environmental 12-D with per-sample norm) to match Phase 4 training.
- Log-mel extraction parameters match Phase 2 (`n_fft=512, hop=160, win=400`) so the Phase 4 checkpoint is compatible.

