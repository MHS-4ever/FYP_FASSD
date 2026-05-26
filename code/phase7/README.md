# Phase 7 — Forensic Test Suite & Dataset (Code)

**Sign-off status:** Phase **7A**–**7C2** and **7C4-v2** (prototype) signed off; **7E1** + **7E3A** complete.  
**Active:** Phase **7E3C** — AASIST-L fine-tune scripts + eval harness (**implementation only; do not run training inside Cursor**).  
**Postponed:** Phase **7D** report generator implementation until evidence layer improves.  
**Frozen:** [PHASE7C_FINAL_DECISION_RECORD.md](../../reports/phase7/PHASE7C_FINAL_DECISION_RECORD.md) · **7E hub:** [phase7e_aasist_experiment/](../../reports/phase7/phase7e_aasist_experiment/README.md)

> **Environment:** Use **`python`** inside the activated **`(fassd)`** conda environment. Do **not** use `py -3` (system Python may lack pandas/torch).

| Phase | Scripts | Status |
|-------|---------|--------|
| 7A | `run_forensic_test_suite.py`, `analyze_forensic_test_results.py` | Signed off |
| 7B | `prepare_forensic_dataset.py`, `validate_forensic_labels.py` | Signed off |
| 7C0 | `audit_current_training_dataset.py`, `audit_hdf5_features.py` | Signed off |
| 7C1 | `build_phase7c1_manifest_from_audio.py`, … `analyze_phase7c1_baseline.py` | Signed off |
| 7C2 | `build_phase7c2_training_manifests.py`, … | Signed off |
| 7C3-v1 | `train_phase7c3_hybrid.py`, … | **Rejected** |
| 7C3-R2 | `train_phase7c3_r2_hybrid.py`, … | **Rejected** as standalone checkpoints |
| 7C4-v1 | `apply_phase7c4_decision_layer.py`, … | **Rejected** |
| 7C4-v2 | `apply_phase7c4_v2_decision_layer.py` | **Accepted** as decision-layer prototype only |
| 7D | `build_phase7d_forensic_report.py`, … | Planned / **postponed** |
| 7E0 | (planning docs under `phase7e_aasist_experiment/`) | Planning complete |
| 7E0.5 | `audit_phase7e0_paths.py` | Path audit passed with warnings |
| 7E1 | `aasist/integration/smoke_test_aasist_import.py`, … | Smoke test **passed** |
| 7E2/7E3A | `build_aasist_eval_manifest.py`, `run_aasist_pretrained_eval.py`, … | Complete (pretrained eval) |
| 7E3B | `build_aasist_finetune_manifest.py`, `validate_aasist_finetune_manifest.py` | Complete — PASS_WITH_WARNINGS (weighted ratio ~3.07) |
| 7E3C | `train_aasist_l_finetune.py`, `evaluate_aasist_l_finetuned.py`, `compare_aasist_finetune_results.py` | **Active** — scripts in review (no training in Cursor) |
| 7F | Ensemble | Planned — after 7E |

**Accepted artifact:** `reports/phase7/phase7c4_calibration_v2/` — do not treat as final model.

---

## Phase 7C1 — Round-1 collection manifest

**Status:** Signed off — historical commands below

**Collected:** 23 base IDs × 8 variants = **184** audio files in `data/phase7c1/raw/`.

### 1. Build manifest from audio

```text
python code/phase7/build_phase7c1_manifest_from_audio.py ^
  --audio_dir data/phase7c1/raw ^
  --output_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --timestamp_template reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv
```

### 2. Validate

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --target_counts reports/phase7/phase7c1_collection/phase7c1_target_counts.csv ^
  --output_dir reports/phase7/phase7c1_collection/validation ^
  --allow_missing_audio --allow_warnings
```

### 3. Summary

```text
python code/phase7/summarize_phase7c1_collection.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --target_counts reports/phase7/phase7c1_collection/phase7c1_target_counts.csv ^
  --output_md reports/phase7/phase7c1_collection/phase7c1_collection_status.md
```

Fill `phase7c1_fabricated_timestamps_to_fill.csv` before final `--strict` validation.

See [PHASE7C1_DATA_COLLECTION_PLAN.md](../../reports/phase7/phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md).

### 4. Baseline evaluation (pre fine-tuning — no training)

After collection manifest is validated:

```text
python code/phase7/run_phase7c1_baseline.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --output_dir reports/phase7/phase7c1_baseline/results ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32 ^
  --save_chunk_timeline

python code/phase7/analyze_phase7c1_baseline.py ^
  --results_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv ^
  --output_md reports/phase7/phase7c1_baseline/results/PHASE7C1_BASELINE_ANALYSIS.md ^
  --category_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_category_summary.csv ^
  --error_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_error_cases.csv ^
  --partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv
```

See [phase7c1_baseline/README.md](../../reports/phase7/phase7c1_baseline/README.md).

---

## Phase 7C2 — Training dataset builder (signed off)

**Status:** Signed off — approved manifests use **250/50/50** old per-attack caps (not 1000/200/200)

```text
python code/phase7/build_phase7c2_training_manifests.py ^
  --old_manifest_dir data/manifests ^
  --phase7c1_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --phase7c1_baseline reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv ^
  --phase7a_holdout reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --output_dir reports/phase7/phase7c2_training_prep ^
  --old_train_per_attack 250 --old_val_per_attack 50 --old_test_per_attack 50 --random_seed 42

python code/phase7/validate_phase7c2_training_manifests.py ^
  --train reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv ^
  --val reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv ^
  --test reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv ^
  --phase7a_holdout reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --output_dir reports/phase7/phase7c2_training_prep/validation --allow_missing_audio --allow_warnings

python code/phase7/summarize_phase7c2_training_prep.py ^
  --train reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv ^
  --val reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv ^
  --test reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv ^
  --output_md reports/phase7/phase7c2_training_prep/phase7c2_dataset_balance_report.md ^
  --output_csv reports/phase7/phase7c2_training_prep/phase7c2_manifest_summary.csv
```

See [phase7c2_training_prep/README.md](../../reports/phase7/phase7c2_training_prep/README.md).

---

## Phase 7C3-v1 — Hybrid fine-tuning (archived)

**Status:** Rejected after forensic-risk collapse; kept for reference only.

---

## Phase 7C3-R2 — Forensic-risk correction

**Status:** Complete — checkpoints **rejected as standalone**; preserved for evidence / 7C4-v2 fusion only

**Performance defaults (≈12 GB VRAM):**

- `batch_size=16` training; `num_workers=0` (Windows-safe; try `2`/`4` only if stable)
- Feature cache: single-process extraction; `--force` to overwrite H5
- Optional `--amp` on CUDA training if stable
- Partial-fabrication rows: 4s window **centered on suspicious region** (not first 4s)

```text
python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_train_features.h5 --split train --phase7c1_windows 3 --force

python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --split val --phase7c1_windows 3 --force

python code/phase7/build_phase7c3_r2_feature_cache.py --manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_test_features.h5 --split test --phase7c1_windows 3 --force

python code/phase7/train_phase7c3_r2_hybrid.py --train_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_train_features.h5 --val_h5 reports/phase7/phase7c3_finetune_r2/features/phase7c3_r2_val_features.h5 --base_ckpt models_saved/hybrid_resnet_environmental_best.pth --output_dir reports/phase7/phase7c3_finetune_r2/training --epochs 12 --batch_size 16 --num_workers 0 --lr 5e-6 --weight_decay 1e-4 --freeze_backbone_epochs 1 --patience 4 --device cuda
```

See [phase7c3_finetune_r2/README.md](../../reports/phase7/phase7c3_finetune_r2/README.md).

---

## Phase 7C0 — Current training dataset audit

**Status:** Implemented (audit only — **no training**)

Audits manifests and HDF5 features used to train **HybridResNetEnvironmental** before Phase 7C fine-tuning.

```text
python code/phase7/audit_current_training_dataset.py ^
  --manifest_dir data/manifests ^
  --output_dir reports/phase7/phase7_current_dataset_audit ^
  --sample_per_group 20 ^
  --check_audio_exists_sample 5000

python code/phase7/audit_hdf5_features.py ^
  --features_dir data/features ^
  --output_dir reports/phase7/phase7_current_dataset_audit
```

**Outputs:** `reports/phase7/phase7_current_dataset_audit/` — see [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](../../reports/phase7/PHASE7C_HYBRID_MODEL_FINE_TUNING.md) (7C0 section).

**Review files:** `CURRENT_TRAINING_DATASET_AUDIT.md`, `dataset_risk_assessment.md`, `phase7c_data_collection_recommendations.md`

---

## Phase 7B — Dataset preparation

**Status:** Implemented (labels only; no training)

**Safety:** All 25 Phase 7A/T1–T5 files are `dataset_role=controlled_holdout` with `use_for_training=false`. `forensic_training_manifest_preview.csv` is a **future CSV format preview** only — not an actual 7C training manifest.

```text
python code/phase7/prepare_forensic_dataset.py ^
  --manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --product_results reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --output_dir reports/phase7/phase7_dataset

python code/phase7/validate_forensic_labels.py ^
  --input reports/phase7/phase7_dataset/forensic_labeled_master.csv ^
  --output reports/phase7/phase7_dataset/forensic_dataset_validation_report.md ^
  --allow_warnings
```

**Outputs:** `reports/phase7/phase7_dataset/` — see [PHASE7B_FORENSIC_DATASET_PREPARATION.md](../../reports/phase7/PHASE7B_FORENSIC_DATASET_PREPARATION.md)

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
  --manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --output_dir reports/phase7/phase7_forensic_tests/results ^
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
  --results_csv reports/phase7/phase7_forensic_tests/results/forensic_test_results.csv ^
  --product_csv reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --product_md reports/phase7/phase7_forensic_tests/results/PHASE7A_PRODUCT_LEVEL_ANALYSIS.md
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
  --results_csv reports/phase7/phase7_forensic_tests/results/forensic_test_results.csv ^
  --output_md reports/phase7/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md ^
  --skip_legacy_md
```

Use `--no_rewrite_csv` to avoid updating the base results CSV.

---

## Phase 7C4 — Calibration & decision layer (no training)

Compare baseline vs R2 checkpoints; sweep thresholds; apply calibrated forensic rules. **Standalone R2 checkpoints are not accepted** — only a decision-layer prototype if Phase 7C1 + 7A holdout checks pass.

Shared helpers: `phase7c4_common.py`. See [reports/phase7/phase7c4_calibration/README.md](../../reports/phase7/phase7c4_calibration/README.md).

```text
py -3 code/phase7/compare_phase7c4_checkpoints.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --output_csv reports/phase7/phase7c4_calibration/calibration_outputs/phase7c4_checkpoint_comparison.csv --output_md reports/phase7/phase7c4_calibration/phase7c4_checkpoint_comparison.md

py -3 code/phase7/sweep_phase7c4_thresholds.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv --r2_product_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --r2_loss_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --output_csv reports/phase7/phase7c4_calibration/calibration_outputs/phase7c4_threshold_sweep.csv --output_md reports/phase7/phase7c4_calibration/phase7c4_threshold_sweep_report.md

py -3 code/phase7/apply_phase7c4_decision_layer.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv --r2_product_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --r2_loss_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --output_csv reports/phase7/phase7c4_calibration/calibration_outputs/phase7c4_candidate_decisions.csv --error_csv reports/phase7/phase7c4_calibration/calibration_outputs/phase7c4_error_cases.csv   --output_md reports/phase7/phase7c4_calibration/phase7c4_decision_layer_report.md

py -3 code/phase7/check_phase7c4_holdout_impact.py --baseline_csv reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7a_holdout_after_r2/forensic_test_results_product.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7a_holdout_after_r2/forensic_test_results_product.csv --output_csv reports/phase7/phase7c4_calibration/calibration_outputs/phase7c4_phase7a_holdout_impact.csv --output_md reports/phase7/phase7c4_calibration/phase7c4_phase7a_holdout_impact.md
```

## Phase 7C4-v2 — Corrected decision layer

v1 rejected (clean-human false alarms 18/23). v2 uses R2 product for clean human and baseline for manipulation. Outputs: `reports/phase7/phase7c4_calibration_v2/`.

```text
py -3 code/phase7/apply_phase7c4_v2_decision_layer.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv --r2_product_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --r2_loss_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --output_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv --error_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv --output_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_decision_layer_report.md --final_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md
```

See [phase7c4_calibration_v2/README.md](../../reports/phase7/phase7c4_calibration_v2/README.md).

---

## Phase 7E0.5 — Path / artifact / environment audit

```text
python code/phase7/audit_phase7e0_paths.py --output_dir reports/phase7/phase7e_aasist_experiment/audit
```

---

## Phase 7E2 + 7E3A — AASIST adapter + pretrained eval

**Status:** Active preparation — **no training, no fine-tuning**

See [phase7e_aasist_experiment/README.md](../../reports/phase7/phase7e_aasist_experiment/README.md). Analysis reports include **status traceability** (file-level vs segment-suspicious; `risk_target=1` ≠ AI-generated).

### 1. Build eval manifests

```text
python code/phase7/aasist/integration/build_aasist_eval_manifest.py --input_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv --dataset_name phase7c1 --output_csv reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7c1_aasist_eval_manifest.csv

python code/phase7/aasist/integration/build_aasist_eval_manifest.py --input_manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv --dataset_name phase7a --output_csv reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv
```

### 2. Run pretrained AASIST-L (readiness check first)

```text
python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7c1_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1 --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0

python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0
```

### 3. Analyze

```text
python code/phase7/aasist/integration/analyze_aasist_pretrained_eval.py --predictions_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv --output_md reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_phase7c1_analysis.md --output_summary_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_phase7c1_summary.csv

python code/phase7/aasist/integration/analyze_aasist_pretrained_eval.py --predictions_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_predictions.csv --output_md reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_phase7a_analysis.md --output_summary_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_phase7a_summary.csv
```

### 4. Compare with HybridResNet + 7C4-v2

```text
python code/phase7/aasist/integration/compare_aasist_with_hybrid.py --aasist_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv --hybrid_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --decision_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/comparison
```

| Script | Role |
|--------|------|
| `aasist_eval_common.py` | Model load, class convention, windows, `evaluate_aasist_status` |
| `build_aasist_eval_manifest.py` | Normalize 7C1/7A CSVs → AASIST eval manifest |
| `run_aasist_pretrained_eval.py` | Pretrained AASIST-L inference + chunk timelines |
| `analyze_aasist_pretrained_eval.py` | 7C1 gates + 7A holdout summary |
| `compare_aasist_with_hybrid.py` | AASIST vs HybridResNet + 7C4-v2 |

---

## Phase 7E3B — AASIST-L fine-tune prep (hardened; no training)

Use **`build_aasist_finetune_manifest.py`** (not `build_aasist_eval_manifest.py`).

```text
python code/phase7/aasist/integration/build_aasist_finetune_manifest.py --train_manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --val_manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --test_manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep --phase7c1_windows 3 --partial_window_mode suspicious_region --random_seed 42

python code/phase7/aasist/integration/validate_aasist_finetune_manifest.py --train reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_train_manifest.csv --val reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_val_manifest.csv --test reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/validation --rejected_csv reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_finetune_rejected_rows.csv --allow_warnings
```

| Script | Role |
|--------|------|
| `build_aasist_finetune_manifest.py` | **Fine-tune** manifest builder (7C2 → train/val/test windows) |
| `validate_aasist_finetune_manifest.py` | Hardened checks: label mapping, weighted balance, clean-human, leakage |

Plan: [AASIST_L_FINETUNE_TRAINING_PLAN.md](../../reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/AASIST_L_FINETUNE_TRAINING_PLAN.md)

---

## Phase 7D1 — Forensic report generator (no training; postponed for product priority)

Reads Phase 7C4-v2 decisions and evidence; writes JSON + Markdown reports. Shared mapping/lint: `phase7d_common.py`.

Spec: [reports/phase7/phase7d_report_layer/README.md](../../reports/phase7/phase7d_report_layer/README.md)

```text
python code/phase7/build_phase7d_forensic_report.py ^
  --decisions_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv ^
  --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv ^
  --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv ^
  --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv ^
  --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv ^
  --baseline_chunk_dir reports/phase7/phase7c1_baseline/results/chunk_timelines ^
  --output_dir reports/phase7/phase7d_report_layer/outputs ^
  --generate_samples ^
  --sample_count 8

python code/phase7/validate_phase7d_reports.py ^
  --json_dir reports/phase7/phase7d_report_layer/outputs/json ^
  --markdown_dir reports/phase7/phase7d_report_layer/outputs/markdown ^
  --output_md reports/phase7/phase7d_report_layer/outputs/phase7d_report_validation_report.md ^
  --output_csv reports/phase7/phase7d_report_layer/outputs/phase7d_rejected_or_failed_reports.csv
```

---

## What this phase does **not** do

- Train or fine-tune (7C3 scripts only when explicitly running training), transformers (7E), ensemble (7F), or Phase 7B labels
