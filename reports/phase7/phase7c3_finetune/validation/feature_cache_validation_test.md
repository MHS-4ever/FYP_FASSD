# Phase 7C3 Feature Cache Validation

- Manifest: `reports\phase7\phase7c2_training_prep\phase7c2_test_manifest.csv`
- Output H5: `reports\phase7\phase7c3_finetune\features\phase7c3_test_features.h5`
- Split: **test**
- Rows read: **232**
- Rows cached: **232**
- Rows failed: **0**

## Window selection

- Normal `first_4s` windows: **224**
- Partial suspicious-region centered: **8**
- Partial centered (clamped to file bounds): **0**
- Partial rows skipped (missing timestamps): **0**

## Class / weight stats

- Origin: human(0)=62, ai/mixed(1)=120, masked(-1)=50
- Attack: bonafide=54, syn=66, conv=50, replay=58, masked=4
- Partial target=1: 8
- sample_weight mean: 1.1659, min: 0.7000, max: 3.7500

## Feature shapes

- logmel: `[N, 64, 400]` float32
- env: `[N, 12]` float32
