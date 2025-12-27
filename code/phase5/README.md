# Phase 5: Comprehensive Evaluation

This folder evaluates the **Phase 4 trained hybrid model** on the **speaker-independent test set** and produces a full report with per-domain and per-attack breakdowns.

## What you will get (outputs)

By default, outputs are written to `reports/evaluation/`:

- `reports/evaluation/comprehensive_evaluation_report.md`
- `reports/evaluation/overall_metrics.csv`
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

Run from project root (`E:\FYP`):

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_chunked.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

### Optional: speaker overlap verification

If you also pass the training manifest, the script will report whether any `speaker_id` overlaps with the test set:

```powershell
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_chunked.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

**Note:** EER/AUC are undefined for subsets containing only one class (e.g., some per-attack slices). In that case the report/CSVs will show EER/AUC as blank/NaN for that subset.


