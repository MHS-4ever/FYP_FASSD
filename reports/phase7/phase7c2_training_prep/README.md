# Phase 7C2 — Training Dataset Builder / Fine-Tuning Preparation

**Status:** **Signed off** (2026-05) — manifests approved; **no training** was run in this phase  
**Purpose:** Produce weighted, loss-masked train/val/test manifests for future Phase 7C hybrid fine-tuning.

---

## Strategy (short)

| Component | Role |
|-----------|------|
| **Old balanced subset** | Anti-forgetting only — **1000** train / **200** val / **200** test old rows (250/50/50 per attack) |
| **Phase 7C1 (184 files)** | Teaches local forensic behavior with **higher sample weights** |
| **Phase 7A holdout** | **Never** included — controlled evaluation only |

Do **not** use full 1.8M old rows (drowns 7C1). Do **not** use 7C1-only (catastrophic forgetting risk).

---

## Commands

### Build

```text
python code/phase7/build_phase7c2_training_manifests.py --old_manifest_dir data/manifests --phase7c1_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv --phase7c1_baseline reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --phase7a_holdout reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv --output_dir reports/phase7/phase7c2_training_prep --old_train_per_attack 250 --old_val_per_attack 50 --old_test_per_attack 50 --random_seed 42
```

### Validate

```text
python code/phase7/validate_phase7c2_training_manifests.py --train reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --val reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --test reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --phase7a_holdout reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv --output_dir reports/phase7/phase7c2_training_prep/validation --allow_missing_audio --allow_warnings
```

### Summarize

```text
python code/phase7/summarize_phase7c2_training_prep.py --train reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --val reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --test reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_md reports/phase7/phase7c2_training_prep/phase7c2_dataset_balance_report.md --output_csv reports/phase7/phase7c2_training_prep/phase7c2_manifest_summary.csv
```

---

## Key outputs

| File | Description |
|------|-------------|
| `phase7c2_train_manifest.csv` | Combined train (old balanced + 7C1 train) |
| `phase7c2_val_manifest.csv` | Combined val |
| `phase7c2_test_manifest.csv` | Combined test |
| `phase7c2_holdout_protection_report.md` | Phase 7A overlap check |
| `validation/phase7c2_training_manifest_validation_report.md` | Leakage / label / weight checks |
| `phase7c2_dataset_balance_report.md` | Balance summary |

---

## Review after manual run

Send: terminal summary, train/val/test CSVs, balance report, holdout report, validation report, label/source/weight distribution CSVs, and the three Python scripts.

See also: [PHASE7C2_TRAINING_DATASET_BUILDER_PLAN.md](PHASE7C2_TRAINING_DATASET_BUILDER_PLAN.md)
