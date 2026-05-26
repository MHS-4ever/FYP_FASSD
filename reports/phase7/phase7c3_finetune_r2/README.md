# Phase 7C3-R2 — Forensic-Risk Fine-Tuning Correction

Phase 7C3-v1 is preserved and **rejected**.  
R2 runs in a separate folder: `reports/phase7/phase7c3_finetune_r2/`.

## Why R2

v1 used binary as pure origin proxy and caused forensic collapse (replay/mixer/partial/holdout).  
R2 trains binary as **forensic risk**:

- `0` = clean/bonafide low-risk
- `1` = AI/replay/mixer/edited/partial/suspicious manipulated

## Manual commands

### Build R2 caches

```text
python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_train_features.h5 --split train --phase7c1_windows 3 --force

python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --split val --phase7c1_windows 3 --force

python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_test_features.h5 --split test --phase7c1_windows 3 --force
```

### Train R2

```text
python code/phase7/train_phase7c3_r2_hybrid.py --train_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_train_features.h5 --val_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --base_ckpt models_saved/hybrid_resnet_environmental_best.pth --output_dir reports/phase7/phase7c3_finetune_r2/training --epochs 12 --batch_size 16 --num_workers 0 --lr 5e-6 --weight_decay 1e-4 --freeze_backbone_epochs 1 --patience 4 --device cuda
```

### Evaluate checkpoints

```text
python code/phase7/evaluate_phase7c3_r2_hybrid.py --test_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --ckpt reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth --output_csv reports/phase7/phase7c3_finetune_r2/evaluation/phase7c2_val_predictions_best_loss.csv --output_md reports/phase7/phase7c3_finetune_r2/evaluation/phase7c2_val_eval_best_loss.md --device cuda

python code/phase7/evaluate_phase7c3_r2_hybrid.py --test_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --ckpt reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth --output_csv reports/phase7/phase7c3_finetune_r2/evaluation/phase7c2_val_predictions_best_product.csv --output_md reports/phase7/phase7c3_finetune_r2/evaluation/phase7c2_val_eval_best_product.md --device cuda
```

## Notes

- Base checkpoint is read-only: `models_saved/hybrid_resnet_environmental_best.pth`
- v1 outputs remain untouched in `reports/phase7/phase7c3_finetune/`
- Final acceptance still depends on full Phase7C1 + Phase7A before/after checks.

