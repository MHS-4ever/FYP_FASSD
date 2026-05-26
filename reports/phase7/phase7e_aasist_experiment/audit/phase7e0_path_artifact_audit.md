# Phase 7E0.5 — Path, Artifact, and Environment Audit

**Generated:** 2026-05-26T19:16:11.805648+00:00  
**Verdict:** `PASS_WITH_WARNINGS`  
**Output directory:** `reports/phase7/phase7e_aasist_experiment/audit`  

## Summary

### Notes
- optional_artifacts_missing:aasist_code_workspace,phase7e_outputs_dir

## Environment

| Item | Value |
|------|-------|
| Python | `3.10.19` |
| Executable | `C:\Users\mhasn\miniconda3\envs\fassd\python.exe` |
| CWD | `E:\FYP` |
| Repo root | `E:\FYP` |
| Conda env | `fassd` |
| PyTorch | `2.5.1+cu121` |
| CUDA available | `True` |
| GPU | `NVIDIA GeForce RTX 3050 6GB Laptop GPU` |

## Artifact audit

| artifact_id | status | selected_path | critical | notes |
|-------------|--------|---------------|----------|-------|
| phase7c2_train_manifest | found_canonical | `reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv` | True |  |
| phase7c2_val_manifest | found_canonical | `reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv` | True |  |
| phase7c2_test_manifest | found_canonical | `reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv` | True |  |
| phase7c1_collection_manifest | found_canonical | `reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv` | True |  |
| phase7c1_baseline_results | found_canonical | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` | True |  |
| phase7c1_partial_fabrication_analysis | found_canonical | `reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv` | False |  |
| phase7a_forensic_test_manifest | found_canonical | `reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv` | True |  |
| phase7a_forensic_test_results_product | found_canonical | `reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv` | True |  |
| phase7c4_v2_candidate_decisions | found_canonical | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` | True |  |
| phase7c4_v2_error_cases | found_canonical | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv` | False |  |
| phase7c4_v2_final_recommendation | found_canonical | `reports/phase7/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md` | False |  |
| phase7c3_r2_best_product_ckpt | found_canonical | `reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth` | False |  |
| phase7c3_r2_best_loss_ckpt | found_canonical | `reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth` | False |  |
| hybrid_resnet_environmental_best | found_canonical | `models_saved/hybrid_resnet_environmental_best.pth` | True |  |
| aasist_code_workspace | missing | `-` | False | expected_missing_before_7e1 |
| phase7e_experiment_root | found_canonical | `reports/phase7/phase7e_aasist_experiment` | False | directory_exists |
| phase7e_audit_dir | found_canonical | `reports/phase7/phase7e_aasist_experiment/audit` | False | directory_exists |
| phase7e_outputs_dir | missing | `-` | False |  |

## CSV inspection (selected files)

### phase7c2_train_manifest

- Rows: 1128
- Columns: 41
- Size (MB): 0.5513
- First 5 columns: `row_id, data_source, source_subset, audio_path, filepath`

### phase7c2_val_manifest

- Rows: 224
- Columns: 41
- Size (MB): 0.1093
- First 5 columns: `row_id, data_source, source_subset, audio_path, filepath`

### phase7c2_test_manifest

- Rows: 232
- Columns: 41
- Size (MB): 0.1136
- First 5 columns: `row_id, data_source, source_subset, audio_path, filepath`

### phase7c1_collection_manifest

- Rows: 184
- Columns: 33
- Size (MB): 0.0789
- First 5 columns: `sample_id, audio_path, base_id, variant_id, speaker_id`

### phase7c1_baseline_results

- Rows: 184
- Columns: 50
- Size (MB): 0.103
- First 5 columns: `sample_id, audio_path, base_id, variant_id, speaker_id`

### phase7c1_partial_fabrication_analysis

- Rows: 46
- Columns: 17
- Size (MB): 0.0105
- First 5 columns: `sample_id, audio_path, base_id, variant_id, suspicious_start_time`

### phase7a_forensic_test_manifest

- Rows: 25
- Columns: 22
- Size (MB): 0.0068
- First 5 columns: `test_id, priority, audio_path, source_origin, manipulation_type`

### phase7a_forensic_test_results_product

- Rows: 25
- Columns: 64
- Size (MB): 0.0279
- First 5 columns: `test_id, filename, audio_path, priority, source_origin`

### phase7c4_v2_candidate_decisions

- Rows: 184
- Columns: 17
- Size (MB): 0.048
- First 5 columns: `sample_id, manipulation_type, source_origin, variant_id, calibrated_status`

### phase7c4_v2_error_cases

- Rows: 13
- Columns: 18
- Size (MB): 0.0035
- First 5 columns: `sample_id, manipulation_type, source_origin, variant_id, calibrated_status`

## Outputs

- `phase7e0_path_artifact_audit.csv`
- `phase7e0_selected_paths.json`
- `phase7e0_environment_report.json`
- `phase7e0_missing_or_warning_items.csv`

## Next step

If verdict is `PASS` or `PASS_WITH_WARNINGS`, review `phase7e0_selected_paths.json` before Phase **7E1**.
