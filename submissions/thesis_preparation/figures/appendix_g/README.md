# Appendix G — Thesis Figures (Model Evaluation)

| Thesis figure | File in this folder | Original source in repo | Notes |
|---------------|---------------------|-------------------------|-------|
| **G.1** Baseline CNN/LCNN confusion matrix | `G1_baseline_lcnn_confusion_matrix.png` | Regenerated 2026-06-21 via `code/evaluate_model.py` logic / `code/generate_thesis_appendix_g_figures.py` | LFCC robust model, **augmented** test split, n=611,829. EER≈15.64%, AUC≈0.924 |
| **G.2** ResNet evaluation confusion matrix | `G2_resnet_confusion_matrix.png` | Plotted from documented counts in `reports/previous_phases/PHASE4_2_RESULTS.md` | Log-mel ResNet robust, **augmented** test. EER=2.61%, AUC=0.997. Cell values match Phase 4.2 report |
| **G.3** HybridResNetEnvironmental ROC curve | `G3_hybrid_roc_curve.png` | `reports/evaluation/figures/roc_overall.png` | From Phase 5 eval (`code/phase5/evaluate_hybrid_model.py`), generated **2026-02-13**. AUC=0.917 |
| **G.4** HybridResNetEnvironmental confusion matrix | `G4_hybrid_multiclass_confusion_matrix.png` | `reports/evaluation/confusion_matrices/overall_multiclass_cm.png` | Multiclass attack-type CM, speaker-independent test n=254,574. Multiclass acc=64.36% |

## Related files (same Phase 5 run)

- Binary CM: `reports/evaluation/confusion_matrices/overall_binary_cm.png`
- Report: `reports/evaluation/comprehensive_evaluation_report.md`
- Runner: `code/phase5/run_phase5.py` or `code/phase5/evaluate_hybrid_model.py`

## Regenerate hybrid figures (if needed)

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 E:/FYP/data/features/logmel_chunked.h5 --environmental_h5 E:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

Then copy `roc_overall.png` and `overall_multiclass_cm.png` into this folder as G3/G4.
