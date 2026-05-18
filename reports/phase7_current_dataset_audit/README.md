# Phase 7C0 — Current Training Dataset Audit

Audit of manifests and HDF5 features used to train **HybridResNetEnvironmental**.

## Main documents

- [CURRENT_TRAINING_DATASET_AUDIT.md](CURRENT_TRAINING_DATASET_AUDIT.md)
- [dataset_risk_assessment.md](dataset_risk_assessment.md)
- [phase7c_data_collection_recommendations.md](phase7c_data_collection_recommendations.md)
- [feature_hdf5_audit.md](feature_hdf5_audit.md)

## File-level balance CSVs

- `file_level_balance_summary.csv`
- `file_level_attack_distribution.csv`
- `file_level_domain_distribution.csv`
- `chunk_vs_file_balance_comparison.csv`

## Regenerate

```text
python code/phase7/audit_current_training_dataset.py ^
  --manifest_dir data/manifests ^
  --output_dir reports/phase7_current_dataset_audit ^
  --sample_per_group 20 ^
  --check_audio_exists_sample 5000

python code/phase7/audit_hdf5_features.py ^
  --features_dir data/features ^
  --output_dir reports/phase7_current_dataset_audit
```
