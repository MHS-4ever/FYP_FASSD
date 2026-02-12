# Phase 5: Comprehensive Evaluation

This folder evaluates the **Phase 4 trained hybrid model** on the **speaker-independent test set** and produces a full report with per-domain, per-attack breakdowns and a **threshold sweep** (detail evaluation) at multiple operating points.

## What you will get (outputs)

By default, outputs are written to `reports/evaluation/` (do not change this folder for Phase 6 organization):

- `reports/evaluation/comprehensive_evaluation_report.md` (includes **Threshold sweep** table)
- `reports/evaluation/overall_metrics.csv`
- `reports/evaluation/threshold_sweep.csv` — accuracy and bonafide FPR at each threshold (default: 0.5, 0.65, 0.70)
- `reports/evaluation/asvspoof_evaluation.csv`
- `reports/evaluation/realworld_evaluation.csv`
- `reports/evaluation/per_domain_metrics.csv`
- `reports/evaluation/per_attack_metrics.csv`
- `reports/evaluation/confusion_matrices/overall_binary_cm.png`
- `reports/evaluation/confusion_matrices/overall_multiclass_cm.png`
- `reports/evaluation/figures/roc_overall.png`
- `reports/evaluation/figures/roc_asvspoof.png`
- `reports/evaluation/figures/roc_realworld.png`

## Recommended command (Laptop)

Run from project root (`E:\FYP`). Use **E:/FYP** or **D:/FYP** for the feature H5 paths depending on where your data lives:

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 E:/FYP/data/features/logmel_chunked.h5 --environmental_h5 E:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

### Threshold sweep (detail evaluation)

The script runs a **threshold sweep** by default at `0.5 0.65 0.70` and writes:

- **`threshold_sweep.csv`**: columns `threshold`, `accuracy_pct`, `bonafide_fpr_pct`
- A **Threshold sweep (detail evaluation)** section in the markdown report

To use different thresholds:

```powershell
python code/phase5/evaluate_hybrid_model.py ... --thresholds "0.5 0.6 0.65 0.7 0.75"
```

### Optional: speaker overlap verification

If you pass the training manifest, the script reports whether any `speaker_id` overlaps with the test set.

**Note:** EER/AUC are undefined for subsets containing only one class (e.g., some per-attack slices). The report/CSVs will show EER/AUC as blank/NaN for that subset.


