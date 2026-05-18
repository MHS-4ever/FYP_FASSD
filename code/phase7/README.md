# Phase 7 — Forensic Test Suite & Dataset (Code)

**Sign-off status:** Phase **7A**, **7B**, **7C0** signed off.  
**Next:** Phase **7C1** Round-1 recording (~120 files) → validate manifest → then Phase **7C** fine-tuning.

| Phase | Scripts | Status |
|-------|---------|--------|
| 7A | `run_forensic_test_suite.py`, `analyze_forensic_test_results.py` | Signed off |
| 7B | `prepare_forensic_dataset.py`, `validate_forensic_labels.py` | Signed off |
| 7C0 | `audit_current_training_dataset.py`, `audit_hdf5_features.py` | Signed off |
| 7C1 | `validate_phase7c1_collection_manifest.py` + [phase7c1_collection/](../../reports/phase7c1_collection/) | **Active** (Round-1: 15+ × 8 ≈ 120 files) |
| 7C | (existing `train_hybrid_fast.py` in phase4) | Blocked |

---

## Phase 7C1 — Round-1 collection manifest

**Status:** Active (docs + validation — **no training**)

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --input reports/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --output reports/phase7c1_collection/phase7c1_validation_report.md ^
  --allow_warnings
```

Copy `reports/phase7c1_collection/phase7c1_collection_manifest_template.csv` → `phase7c1_collection_manifest.csv` when recording.

**Round-1:** 15+ speakers × **8 variants** ≈ **120 files**. See [PHASE7C1_DATA_COLLECTION_PLAN.md](../../reports/phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md).

---

## Phase 7C0 — Current training dataset audit

**Status:** Implemented (audit only — **no training**)

Audits manifests and HDF5 features used to train **HybridResNetEnvironmental** before Phase 7C fine-tuning.

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

**Outputs:** `reports/phase7_current_dataset_audit/` — see [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](../../reports/phase7/PHASE7C_HYBRID_MODEL_FINE_TUNING.md) (7C0 section).

**Review files:** `CURRENT_TRAINING_DATASET_AUDIT.md`, `dataset_risk_assessment.md`, `phase7c_data_collection_recommendations.md`

---

## Phase 7B — Dataset preparation

**Status:** Implemented (labels only; no training)

**Safety:** All 25 Phase 7A/T1–T5 files are `dataset_role=controlled_holdout` with `use_for_training=false`. `forensic_training_manifest_preview.csv` is a **future CSV format preview** only — not an actual 7C training manifest.

```text
python code/phase7/prepare_forensic_dataset.py ^
  --manifest reports/phase7_forensic_tests/forensic_test_manifest.csv ^
  --product_results reports/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --output_dir reports/phase7_dataset

python code/phase7/validate_forensic_labels.py ^
  --input reports/phase7_dataset/forensic_labeled_master.csv ^
  --output reports/phase7_dataset/forensic_dataset_validation_report.md ^
  --allow_warnings
```

**Outputs:** `reports/phase7_dataset/` — see [PHASE7B_FORENSIC_DATASET_PREPARATION.md](../../reports/phase7/PHASE7B_FORENSIC_DATASET_PREPARATION.md)

**Review files:** `forensic_labeled_master.csv`, `forensic_file_level_labels.csv`, `forensic_segment_labels.csv`, `forensic_training_manifest_preview.csv`, `forensic_dataset_gap_analysis.md`, `rejected_or_needs_review.csv`

---

# Phase 7A — Forensic Test Suite (Code)

**Status:** Implemented (inference + dual analysis: legacy binary + product-level)

Runs the existing Phase 6 hybrid model on controlled forensic test cases (manifest T1–T5).

**Docs:** [reports/phase7/PHASE7A_CONTROLLED_TEST_SUITE.md](../../reports/phase7/PHASE7A_CONTROLLED_TEST_SUITE.md)

---

## Scripts

| Script | Role |
|--------|------|
| `run_forensic_test_suite.py` | Manifest → Phase 6 inference → JSON + `forensic_test_results.csv` |
| `analyze_forensic_test_results.py` | Legacy + **product-level** CSV and markdown |

Phase 6: file-level inference unchanged. With `--save_chunk_timeline`, timelines list all chunks; model scores on **VAD-kept** chunks only.

---

## 1. Run inference (once per manifest / settings change)

```text
cd /d E:\FYP

python code/phase7/run_forensic_test_suite.py ^
  --manifest reports/phase7_forensic_tests/forensic_test_manifest.csv ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --output_dir reports/phase7_forensic_tests/results ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32 ^
  --save_chunk_timeline
```

---

## 2. Run product-level analysis (main review)

```text
python code/phase7/analyze_forensic_test_results.py ^
  --results_csv reports/phase7_forensic_tests/results/forensic_test_results.csv ^
  --product_csv reports/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --product_md reports/phase7_forensic_tests/results/PHASE7A_PRODUCT_LEVEL_ANALYSIS.md
```

Also writes legacy `FORENSIC_TEST_ANALYSIS.md` unless `--skip_legacy_md`.

**Re-run analysis only** after manifest timestamp updates (e.g. T4.3) — no need to re-infer unless audio or model settings changed.

---

## Product-level concepts

| Idea | Detail |
|------|--------|
| **File-level REAL ≠ safe** | Chunks may still have high spoof scores (`segment_suspicious`) |
| **Segment-suspicious miss** | `max_chunk_spoof ≥ 0.95` OR `suspicious_chunk_ratio ≥ 0.30` while whole-file REAL |
| **Statuses** | `direct_ai_file_level_missed_but_segment_suspicious`, `ai_replay_file_level_missed_but_segment_suspicious`, `processed_ai_file_level_missed_but_segment_suspicious` |
| **Clean human borderline** | \|decision_score − threshold\| ≤ 0.05 — review, not confirmed false alarm |
| **Partial fab** | Segment metrics in product CSV; T4.3 timestamps **35.0–58.0 s** (evaluated) |

---

## Files to send for review

1. **`PHASE7A_PRODUCT_LEVEL_ANALYSIS.md`** — main interpretation  
2. **`forensic_test_results_product.csv`** — per-file product metrics + partial segment columns  
3. `forensic_test_results.csv` — optional raw inference reference  
4. `code/phase7/analyze_forensic_test_results.py` — if logic review needed  

Chunk timelines only if debugging a specific case (e.g. T5_FAB_001, T4.3 after timestamps added).

---

## Legacy binary analysis

```text
python code/phase7/analyze_forensic_test_results.py ^
  --results_csv reports/phase7_forensic_tests/results/forensic_test_results.csv ^
  --output_md reports/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md ^
  --skip_legacy_md
```

Use `--no_rewrite_csv` to avoid updating the base results CSV.

---

## What this phase does **not** do

- Train or fine-tune (7C), transformers (7E), ensemble (7F), or Phase 7B labels
