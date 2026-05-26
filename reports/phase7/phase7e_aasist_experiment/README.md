# Phase 7E — AASIST Evidence Branch Experiment

**Status:** Phase **7E3C** active — fine-tune scripts + evaluation harness (**implementation only; do not run training inside Cursor**). Phase **7E3B** hardened prep complete.  
**Canonical planning folder:** `reports/phase7/phase7e_aasist_experiment/`  
**Code:** [code/phase7/aasist/](../../../code/phase7/aasist/README.md)

---

## Purpose

Add **AASIST** as a **candidate evidence branch** — not as a assumed final forensic product model. Evaluate against locked benchmarks on Phase 7C1 and Phase 7A holdout before any fusion or report-layer claims.

---

## Phase 7E0 documents (review these first)

| Document | Role |
|----------|------|
| [PHASE7E0_AASIST_EXPERIMENT_PLAN.md](PHASE7E0_AASIST_EXPERIMENT_PLAN.md) | Why AASIST, scope, architecture role, datasets |
| [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) | **Locked** evaluation protocol (do not change without new phase gate) |
| [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md) | Binary forensic-risk labels and wording rules |
| [PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md](PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md) | GPU/RAM policy, batch sizes, what to avoid |
| [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md) | Standalone vs branch-only acceptance |
| [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md) | 7E0 → 7E5 phased path (incl. 7E0.5, 7E3A/7E3B) |
| [audit/](audit/) | **7E0.5** audit outputs (after running script below) |
| [PHASE7E0_DO_NOT_DO.md](PHASE7E0_DO_NOT_DO.md) | Hard stops for this experiment track |
| [PHASE7E1_AASIST_INTEGRATION_PLAN.md](PHASE7E1_AASIST_INTEGRATION_PLAN.md) | **7E1** integration + smoke test |
| [PHASE7E1_SOURCE_REQUIREMENTS.md](PHASE7E1_SOURCE_REQUIREMENTS.md) | Verified source policy |
| [phase7e1_smoke_test/](phase7e1_smoke_test/) | Smoke test outputs |

---

## Parent index

- [PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md) — summary + links  
- [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](../PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) — broader transformer track (WavLM later)  
- [../README.md](../README.md) — Phase 7 hub  
- [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md) — project checklist

---

## Current model context (frozen)

| Component | Status |
|-----------|--------|
| HybridResNet baseline | Evidence source — replay/mixer/partial |
| 7C3-v1 / standalone R2 | Rejected |
| 7C4-v2 | Decision-layer **prototype** only |
| 7D report implementation | **Postponed** until evidence layer improves |

---

## Sub-phases (planned)

| Phase | Name | Training? |
|-------|------|-----------|
| **7E0** | Hardened planning + numeric acceptance gates | **No** |
| **7E0.5** | Path / artifact / environment audit (script) | **No** |
| **7E1** | Source audit + environment + smoke test | **No** |
| **7E2** | Dataset adapter | **No** |
| **7E3A** | Pretrained AASIST eval (7C1 + 7A) | **No** — complete |
| **7E3B** | Hardened manifest prep + training plan | Complete (PASS_WITH_WARNINGS; weighted ratio ~3.07) |
| **7E3C** | Training/eval scripts + run plan | **Active** — review only (do not train in Cursor) |
| **7E4** | Evaluation vs baselines (numeric gates) | Inference |
| **7E5** | Fusion decision layer v3 | Calibration only |

**Order:** Review hardened 7E0 → **7E0.5 audit PASS** → 7E1 → 7E2 → **7E3A** → 7E3B (if needed) → 7E4 → 7E5.

Do **not** fine-tune before **7E3A**. Provide verified AASIST source before 7E2/7E3A.

---

## Phase 7E1 commands

Run from repo root with **`(fassd)`** activated:

```text
python code/phase7/aasist/integration/check_phase7e1_environment.py --output_dir reports/phase7/phase7e_aasist_experiment/audit

python code/phase7/aasist/integration/audit_aasist_source.py --aasist_src code/phase7/aasist/vendor/AASIST --output_dir reports/phase7/phase7e_aasist_experiment/audit --allow_missing_source

python code/phase7/aasist/integration/inspect_aasist_expected_io.py --aasist_src code/phase7/aasist/vendor/AASIST --output_dir reports/phase7/phase7e_aasist_experiment/audit --allow_missing_source

python code/phase7/aasist/integration/smoke_test_aasist_import.py --aasist_src code/phase7/aasist/vendor/AASIST --output_dir reports/phase7/phase7e_aasist_experiment/phase7e1_smoke_test --device cuda --model_variant AASIST-L --dummy_only
```

Optional second variant:

```text
python code/phase7/aasist/integration/smoke_test_aasist_import.py --aasist_src code/phase7/aasist/vendor/AASIST --output_dir reports/phase7/phase7e_aasist_experiment/phase7e1_smoke_test --device cuda --model_variant AASIST --dummy_only
```

With official source present, expect smoke **`PASS`** (loads `config/AASIST-L.conf`, `models/weights/AASIST-L.pth`, `models.AASIST.Model`, forward shape `[1, 2]`).
```

---

## Phase 7E0.5 audit command

Run from repo root with **`(fassd)`** activated:

```text
python code/phase7/audit_phase7e0_paths.py --output_dir reports/phase7/phase7e_aasist_experiment/audit
```

Then review:

- `audit/phase7e0_path_artifact_audit.md` — verdict  
- `audit/phase7e0_selected_paths.json` — paths for 7E1/7E2  

Proceed to **7E1** only if verdict is `PASS` or `PASS_WITH_WARNINGS`.

---

## Review files (7E2/7E3A)

| File | Role |
|------|------|
| `code/phase7/aasist/integration/_common.py` | Paths, I/O, GPU helpers |
| `code/phase7/aasist/integration/aasist_eval_common.py` | Model load, class convention, audio/windows, partial metrics |
| `code/phase7/aasist/integration/build_aasist_eval_manifest.py` | Manifest adapter |
| `code/phase7/aasist/integration/run_aasist_pretrained_eval.py` | Pretrained inference |
| `code/phase7/aasist/integration/analyze_aasist_pretrained_eval.py` | Analysis (7C1 gates vs 7A holdout) |
| `code/phase7/aasist/integration/compare_aasist_with_hybrid.py` | vs HybridResNet |

**Class convention:** default `--spoof_class_index 0` (ASVspoof: 0=spoof, 1=bonafide). Verified from `vendor/AASIST/data_utils.py` + `main.py` when source present. Outputs include `prob_class_0`, `prob_class_1`, `spoof_score`, `bonafide_score`, `class_convention_source`, `class_convention_warning`.

---

## Phase 7E2 — Build eval manifests

Uses explicit `--input_manifest` by default. Add `--use_selected_paths` to override from `phase7e0_selected_paths.json`.

```text
python code/phase7/aasist/integration/build_aasist_eval_manifest.py --input_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv --dataset_name phase7c1 --output_csv reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7c1_aasist_eval_manifest.csv

python code/phase7/aasist/integration/build_aasist_eval_manifest.py --input_manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv --dataset_name phase7a --output_csv reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv
```

Outputs:

- `phase7e2_dataset_adapter/phase7c1_aasist_eval_manifest.csv`
- `phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv`
- `phase7e2_dataset_adapter/*_aasist_eval_manifest_validation.md`

---

## Phase 7E3A — Pretrained AASIST-L evaluation

**No training. No fine-tuning.** Run only after script review. Pre-flight prints `READY_TO_RUN=true/false` and writes `phase7e3a_run_readiness.md`.

```text
python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7c1_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1 --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0

python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0
```

Predictions (exact names):

- `phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv`
- `phase7e3a_pretrained_eval/phase7a/aasist_l_predictions.csv`

### Status traceability (analysis reports)

Generated analysis markdown includes:

- **`direct_ai_detected`**: file-level mean spoof score crossed threshold.
- **`*_file_level_missed_but_segment_suspicious`**: file-level mean below threshold, but max-window/chunk ratio rules fired.
- **`expected_risk_binary=1`**: forensic-risk positive — **not** equivalent to “AI-generated”.

### Analyze

```text
python code/phase7/aasist/integration/analyze_aasist_pretrained_eval.py --predictions_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv --output_md reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_phase7c1_analysis.md --output_summary_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_phase7c1_summary.csv

python code/phase7/aasist/integration/analyze_aasist_pretrained_eval.py --predictions_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_predictions.csv --output_md reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_phase7a_analysis.md --output_summary_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a/aasist_l_phase7a_summary.csv
```

### Compare with HybridResNet + 7C4-v2

```text
python code/phase7/aasist/integration/compare_aasist_with_hybrid.py --aasist_csv reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/aasist_l_predictions.csv --hybrid_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --decision_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/comparison
```

Outputs:

- `phase7e3a_pretrained_eval/comparison/aasist_l_vs_hybrid_comparison.csv`
- `phase7e3a_pretrained_eval/comparison/aasist_l_vs_hybrid_comparison.md`
- `phase7e3a_pretrained_eval/comparison/aasist_l_decision_recommendation.md`

---

## Phase 7E3B — Fine-tune preparation (hardened; complete)

**No training in this phase.** Use **`build_aasist_finetune_manifest.py`** (not the eval manifest builder). Status: **PASS_WITH_WARNINGS** (weighted ratio ~3.07 supports balanced sampling).

```text
python code/phase7/aasist/integration/build_aasist_finetune_manifest.py --train_manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --val_manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --test_manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep --phase7c1_windows 3 --partial_window_mode suspicious_region --random_seed 42

python code/phase7/aasist/integration/validate_aasist_finetune_manifest.py --train reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_train_manifest.csv --val reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_val_manifest.csv --test reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/validation --rejected_csv reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_finetune_rejected_rows.csv --allow_warnings
```

Outputs: `phase7e3b_finetune_prep/` · Validation: `phase7e3b_finetune_prep/validation/` · Plan: [AASIST_L_FINETUNE_TRAINING_PLAN.md](phase7e3b_finetune_prep/AASIST_L_FINETUNE_TRAINING_PLAN.md) (**no plain weighted CE**)

---

## Phase 7E3C — Fine-tune scripts + evaluation harness (active; review only)

**Do not train inside Cursor.** This phase adds scripts + run plan under:

- `phase7e3c_finetune/` (outputs)
- `code/phase7/aasist/integration/train_aasist_l_finetune.py`
- `code/phase7/aasist/integration/evaluate_aasist_l_finetuned.py`
- `code/phase7/aasist/integration/compare_aasist_finetune_results.py`

Run plan: [phase7e3c_finetune/AASIST_L_FINETUNE_RUN_PLAN.md](phase7e3c_finetune/AASIST_L_FINETUNE_RUN_PLAN.md)

**Optional** Phase 7A re-eval after MP4 loader fix (new folder, do not overwrite 7E3A):

```text
python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a_after_loader_fix --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0
```

## Next steps (current)

1. Review `phase7e3c_finetune/AASIST_L_FINETUNE_RUN_PLAN.md` (balanced sampler required; **class-balanced loss optional, not default**).
2. Review scripts (7E3C) and confirm output dirs.
3. Run training outside Cursor → save `best_product` + `best_loss`.
4. Re-evaluate Phase 7C1 + Phase 7A in **new** output dirs; do not overwrite 7E3A.
5. Compare vs Hybrid + 7C4-v2 → Phase 7E4 gate review.
