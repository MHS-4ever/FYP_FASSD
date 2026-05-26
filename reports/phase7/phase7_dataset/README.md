# Phase 7B Forensic Dataset

**Status:** Label preparation complete (no training in this phase).

## Critical safety rule

**All 25 Phase 7A/T1–T5 files are `controlled_holdout`.**

- `use_for_training` = **false** on every row (`25/25` verified in file-level CSV)
- `training_readiness` = `not_ready_for_training`
- Use for **validation / testing / label schema design** only
- **Do not fine-tune** on this set (Phase 7C needs a larger collected dataset)

## Contents

| File | Description |
|------|-------------|
| `forensic_labeled_master.csv` | Joined manifest + 7A product + normalized labels |
| `forensic_file_level_labels.csv` | One row per audio file |
| `forensic_segment_labels.csv` | Segment rows with parent_* context columns |
| `forensic_training_manifest_preview.csv` | **Format preview only** (25 rows; 23 eligible_for_future_training; **use_for_training always false**) |
| `rejected_or_needs_review.csv` | Current review-required files (e.g. **T1.1**, **T4.1** — `needs_review`, not approved) |
| `forensic_dataset_validation_report.md` | Validation summary |
| `forensic_dataset_gap_analysis.md` | What to collect before 7C |
| `label_mapping_rules.md` | Mapping documentation |

## Warning

The Phase 7A set has only **25** files. It is **not** enough for fine-tuning. See gap analysis for minimum counts before Phase 7C.

## Regenerate

```text
python code/phase7/prepare_forensic_dataset.py ^
  --manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --product_results reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --output_dir reports/phase7/phase7_dataset
```

```text
python code/phase7/validate_forensic_labels.py ^
  --input reports/phase7/phase7_dataset/forensic_labeled_master.csv ^
  --output reports/phase7/phase7_dataset/forensic_dataset_validation_report.md ^
  --allow_warnings
```

