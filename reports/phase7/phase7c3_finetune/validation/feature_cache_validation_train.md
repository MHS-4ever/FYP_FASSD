# Phase 7C3 Feature Cache Validation

- Manifest: `reports\phase7\phase7c2_training_prep\phase7c2_train_manifest.csv`
- Output H5: `reports\phase7\phase7c3_finetune\features\phase7c3_train_features.h5`
- Split: **train**
- Rows read: **1128**
- Rows cached: **1128**
- Rows failed: **0**

## Window selection

- Normal `first_4s` windows: **1096**
- Partial suspicious-region centered: **32**
- Partial centered (clamped to file bounds): **0**
- Partial rows skipped (missing timestamps): **0**

## Class / weight stats

- Origin: human(0)=298, ai/mixed(1)=580, masked(-1)=250
- Attack: bonafide=266, syn=314, conv=250, replay=282, masked=16
- Partial target=1: 32
- sample_weight mean: 1.1172, min: 0.7000, max: 3.2500

## Feature shapes

- logmel: `[N, 64, 400]` float32
- env: `[N, 12]` float32
