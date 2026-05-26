# Phase 7C3 — Hybrid Fine-Tuning

**Scripts implemented** — run manually in `fassd` env.  
**Do not overwrite** `models_saved/hybrid_resnet_environmental_best.pth`.

---

## Pipeline

1. Build feature caches (train / val / test)  
2. Train fine-tune → new checkpoints under `training/checkpoints/`  
3. Evaluate val/test H5  
4. Run Phase 7C1 + 7A holdout with fine-tuned ckpt  
5. Compare before/after  

Full plan: [PHASE7C3_FINE_TUNING_PLAN.md](PHASE7C3_FINE_TUNING_PLAN.md)  
Config: [config/phase7c3_finetune_config.yaml](config/phase7c3_finetune_config.yaml)

---

## 1. Feature caches

```text
python code/phase7/build_phase7c3_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --output_h5 reports/phase7/phase7c3_finetune/features/phase7c3_train_features.h5 --split train

python code/phase7/build_phase7c3_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --output_h5 reports/phase7/phase7c3_finetune/features/phase7c3_val_features.h5 --split val

python code/phase7/build_phase7c3_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_h5 reports/phase7/phase7c3_finetune/features/phase7c3_test_features.h5 --split test
```

---

## 2. Train

```text
python code/phase7/train_phase7c3_hybrid.py --train_h5 reports/phase7/phase7c3_finetune/features/phase7c3_train_features.h5 --val_h5 reports/phase7/phase7c3_finetune/features/phase7c3_val_features.h5 --base_ckpt models_saved/hybrid_resnet_environmental_best.pth --output_dir reports/phase7/phase7c3_finetune/training --epochs 12 --batch_size 16 --lr 1e-5 --weight_decay 1e-4 --freeze_backbone_epochs 2 --patience 4 --device cuda
```

---

## 3. Evaluate val/test (clip-level)

```text
python code/phase7/evaluate_phase7c3_hybrid.py --test_h5 reports/phase7/phase7c3_finetune/features/phase7c3_val_features.h5 --ckpt reports/phase7/phase7c3_finetune/training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth --output_csv reports/phase7/phase7c3_finetune/evaluation/phase7c2_val_predictions.csv --output_md reports/phase7/phase7c3_finetune/evaluation/phase7c2_val_eval_report.md --device cuda

python code/phase7/evaluate_phase7c3_hybrid.py --test_h5 reports/phase7/phase7c3_finetune/features/phase7c3_test_features.h5 --ckpt reports/phase7/phase7c3_finetune/training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth --output_csv reports/phase7/phase7c3_finetune/evaluation/phase7c2_test_predictions.csv --output_md reports/phase7/phase7c3_finetune/evaluation/phase7c2_eval_report.md --device cuda
```

---

## 4. Phase 7C1 after fine-tune (full-file pct_vote)

```text
python code/phase7/run_phase7c1_baseline.py --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv --ckpt reports/phase7/phase7c3_finetune/training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth --output_dir reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune --pooling pct_vote --chunk_threshold 0.65 --vote_threshold 0.70 --vad_mode file_percentile --vad_rms_percentile 40 --vad_min_speech_ratio 0.40 --batch_size 32 --save_chunk_timeline

python code/phase7/analyze_phase7c1_baseline.py --results_csv reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/phase7c1_baseline_results.csv --output_md reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/PHASE7C1_AFTER_FINETUNE_ANALYSIS.md --category_csv reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/phase7c1_category_summary.csv --error_csv reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/phase7c1_error_cases.csv --partial_csv reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/phase7c1_partial_fabrication_analysis.csv
```

---

## 5. Phase 7A holdout after fine-tune

```text
python code/phase7/run_forensic_test_suite.py --manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv --ckpt reports/phase7/phase7c3_finetune/training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth --output_dir reports/phase7/phase7c3_finetune/evaluation/phase7a_holdout_after_finetune --pooling pct_vote --chunk_threshold 0.65 --vote_threshold 0.70 --vad_mode file_percentile --vad_rms_percentile 40 --vad_min_speech_ratio 0.40 --batch_size 32 --save_chunk_timeline

python code/phase7/analyze_forensic_test_results.py --results_csv reports/phase7/phase7c3_finetune/evaluation/phase7a_holdout_after_finetune/forensic_test_results.csv --product_csv reports/phase7/phase7c3_finetune/evaluation/phase7a_holdout_after_finetune/forensic_test_results_product.csv --product_md reports/phase7/phase7c3_finetune/evaluation/phase7a_holdout_after_finetune/PHASE7A_AFTER_FINETUNE_PRODUCT_ANALYSIS.md --skip_legacy_md --no_rewrite_csv
```

---

## 6. Before/after comparison

```text
python code/phase7/compare_phase7c3_before_after.py --before_phase7c1 reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --after_phase7c1 reports/phase7/phase7c3_finetune/evaluation/phase7c1_after_finetune/phase7c1_baseline_results.csv --before_phase7a reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv --after_phase7a reports/phase7/phase7c3_finetune/evaluation/phase7a_holdout_after_finetune/forensic_test_results_product.csv --output_md reports/phase7/phase7c3_finetune/evaluation/before_after_comparison.md
```

---

## Outputs

| Path | Description |
|------|-------------|
| `features/phase7c3_*_features.h5` | Cached log-mel + env + labels |
| `training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth` | Best fine-tuned model |
| `evaluation/before_after_comparison.md` | Accept/reject summary |
