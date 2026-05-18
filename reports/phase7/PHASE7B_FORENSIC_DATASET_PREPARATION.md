# Phase 7B — Forensic Dataset Preparation

**Status:** **Signed off** (label normalization + manifests; **no training**)  
**Depends on:** Phase 7A complete (`forensic_test_results_product.csv`, product analysis)

---

## 1. Goal

Convert Phase 7A controlled tests into a **structured forensic label dataset** for future Phase 7C fine-tuning and Phase 7D report mapping.

**Not REAL/FAKE only** — separate `origin_label`, `manipulation_label`, `attack_hint`, `risk_level`, and segment labels.

---

## 2. What was implemented

| Component | Location |
|-----------|----------|
| Preparation script | `code/phase7/prepare_forensic_dataset.py` |
| Validation script | `code/phase7/validate_forensic_labels.py` |
| Dataset outputs | `reports/phase7_dataset/` |
| Label rules doc | `reports/phase7_dataset/label_mapping_rules.md` |
| Gap analysis | `reports/phase7_dataset/forensic_dataset_gap_analysis.md` |

---

## 3. Inputs

| File | Role |
|------|------|
| `reports/phase7_forensic_tests/forensic_test_manifest.csv` | Ground truth + metadata |
| `reports/phase7_forensic_tests/results/forensic_test_results_product.csv` | Phase 7A product metrics |
| `reports/phase7/PHASE7_LABEL_SCHEMA.md` | Allowed label enums |

---

## 4. Outputs (`reports/phase7_dataset/`)

| File | Description |
|------|-------------|
| `forensic_labeled_master.csv` | Joined master (manifest + product + labels + flags) |
| `forensic_file_level_labels.csv` | One row per file (training/review columns) |
| `forensic_segment_labels.csv` | Segment rows (T5_FAB_001 pre/insert/post + full-file segments) |
| `forensic_training_manifest_preview.csv` | Preview for 7C (**not** final training set) |
| `rejected_or_needs_review.csv` | Review-required files (e.g. **T1.1**, **T4.1**) |
| `forensic_dataset_validation_report.md` | Schema / path validation |
| `forensic_dataset_gap_analysis.md` | What to collect before 7C |
| `label_mapping_rules.md` | Mapping documentation |
| `README.md` | Folder index |

---

## 5. How to run

From repo root `E:\FYP`:

```text
python code/phase7/prepare_forensic_dataset.py ^
  --manifest reports/phase7_forensic_tests/forensic_test_manifest.csv ^
  --product_results reports/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --output_dir reports/phase7_dataset
```

```text
python code/phase7/validate_forensic_labels.py ^
  --input reports/phase7_dataset/forensic_labeled_master.csv ^
  --output reports/phase7_dataset/forensic_dataset_validation_report.md ^
  --allow_warnings
```

T4.3 timestamps: **35.0–58.0 s** (filled and validated).

---

## 6. Label mapping summary

| Condition | origin_label | manipulation_label |
|-----------|--------------|-------------------|
| Clean human direct | human_likely | clean_original |
| Direct AI | ai_likely | clean_original |
| Human replay | human_likely | replayed_or_re_recorded |
| AI replay | ai_likely | replayed_or_re_recorded |
| Mixer processed | human/ai_likely | channel_processed |
| WhatsApp | human/ai_likely | platform_compressed |
| Edited/spliced | human_likely | edited_or_spliced |
| Partial AI insert | mixed_or_partial_ai | edited_or_spliced |

**Review flags (current):**
- `T1.1`, `T4.1` → `needs_review` (`clean_human_borderline`)
- `T4.3` → **approved** (timestamps 35.0–58.0 s; segment rows generated)
- `T5_FAB_001` → approved with 3 segment rows (14–21 s insert)

---

## 7. Why this is not training yet

- Only **25** Phase 7A files — **`controlled_holdout`** diagnostic set; **`use_for_training=false` on every row**.
- Columns: `dataset_role`, `training_readiness`, `training_warning` on all file-level CSVs.
- `forensic_training_manifest_preview.csv` is a **future format preview** only (`eligible_for_future_training` + `holdout_training_warning=controlled_holdout_do_not_train`); not actual 7C training data.
- Approved rows: `use_for_validation=true`, `use_for_testing=true`.
- Minimum counts before 7C: see `forensic_dataset_gap_analysis.md` (50–100 clean human, 50–100 direct AI, etc.).

---

## 8. Files to review after Phase 7B

1. `forensic_labeled_master.csv`
2. `forensic_file_level_labels.csv`
3. `forensic_segment_labels.csv`
4. `forensic_training_manifest_preview.csv`
5. `forensic_dataset_validation_report.md`
6. `forensic_dataset_gap_analysis.md`
7. `rejected_or_needs_review.csv`

---

## 9. Success criteria

- [x] File-level labels with origin + manipulation (not binary-only)
- [x] Segment labels for T5_FAB_001 and T4.3
- [x] All 25 rows `controlled_holdout`; `use_for_training=false`
- [x] Validation: **0 errors**, **0 warnings**
- [x] Team sign-off — Phase 7B complete
- [ ] Expanded dataset per gap analysis → **Phase 7C1**

---

## Final Phase 7B findings

- **File-level labels** created: `origin_label`, `manipulation_label`, `attack_hint`, `risk_level`, binary preview fields.
- **Segment-level labels** created with parent context (`T5_FAB_001`, **T4.3** pre/insert/post).
- **T5_FAB_001** and **T4.3** have partial insertion timestamps and segment rows.
- All **25** T1–T5 samples are **`controlled_holdout`** — **`use_for_training=false`** on every row.
- This set is a **label-schema prototype / validation holdout**, **not** fine-tuning data.
- **Validation:** errors = **0**, warnings = **0**.
- **Needs review:** **T1.1**, **T4.1** only.
- **T4.3** is no longer blocked.

**Final status:** Phase 7B is **signed off**. Reuse this label schema for **Phase 7C1** data collection.

---

## 10. What not to do in this phase

- Fine-tune (7C), transformers (7E), change Phase 6 inference, change 7A analysis logic

---

## 11. Connection to next phases

- **7C1:** Collect new forensic data using this label schema ([PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md))
- **7C:** Fine-tune only after 7C1 collection is validated
- **7D:** Report mapping validated against same labels
