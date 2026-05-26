# Phase 7C3 Feature Cache Validation

- Manifest: `reports\phase7\phase7c2_training_prep\phase7c2_val_manifest.csv`
- Output H5: `reports\phase7\phase7c3_finetune\features\phase7c3_val_features.h5`
- Split: **val**
- Rows read: **224**
- Rows cached: **224**
- Rows failed: **0**

## Window selection

- Normal `first_4s` windows: **218**
- Partial suspicious-region centered: **6**
- Partial centered (clamped to file bounds): **0**
- Partial rows skipped (missing timestamps): **0**

## Class / weight stats

- Origin: human(0)=59, ai/mixed(1)=115, masked(-1)=50
- Attack: bonafide=53, syn=62, conv=50, replay=56, masked=3
- Partial target=1: 6
- sample_weight mean: 1.1049, min: 0.7000, max: 3.0000

## Feature shapes

- logmel: `[N, 64, 400]` float32
- env: `[N, 12]` float32
