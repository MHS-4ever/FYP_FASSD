# FASSD Next Actions

**Product:** [Forensic Voice Authenticity Analyzer](UPDATED_PROJECT_SCOPE.md)  
**Canonical Phase 7 docs:** [phase7/README.md](phase7/README.md)  
**Phase 7C frozen:** [phase7/PHASE7C_FINAL_DECISION_RECORD.md](phase7/PHASE7C_FINAL_DECISION_RECORD.md) | [phase7/PHASE7C_STATUS_FREEZE.md](phase7/PHASE7C_STATUS_FREEZE.md)

---

## Current active phase

**Phase 7E3C — AASIST-L fine-tune scripts + evaluation harness (prep)** — implement scripts + run plan; **do not run training yet**

---

## Correct project state

| Point | Status |
|-------|--------|
| Phase **7C** | **Frozen** |
| Phase **7C4-v2** | **Accepted** as decision-layer **prototype** only |
| Phase **7D** report layer | **Planned / spec only** |
| Phase **7D implementation** | **Postponed** until model/evidence layer improves |
| Phase **7E** | **Active** |
| Phase **7E1** | AASIST source smoke test **passed** |
| Phase **7E3A** | Pretrained AASIST-L eval **complete** — rejected standalone and branch-only |
| Phase **7E3B** | Fine-tune prep **hardened** — PASS_WITH_WARNINGS (weighted ratio ~3.07) |
| Phase **7E3C** | Training/eval scripts **in review** — do not run until reviewed |
| AASIST training | **Do not run** until 7E3C scripts reviewed and output dirs are set |
| Report generator / website UI | **Do not implement** yet |

### Phase 7E3A decision (locked)

- Pretrained AASIST-L: **not** standalone; **not** branch-only at current thresholds.
- Approved as **fine-tuning candidate** (sensitive to spoof/replay/mixer/partial; clean-human domain mismatch).
- Optional: re-run Phase 7A eval to `phase7a_after_loader_fix` after MP4 loader fix (do not overwrite original 7E3A outputs).

---

## Immediate next actions

| Step | Action |
|------|--------|
| **1** | Review 7E3B validation report (`phase7e3b_finetune_prep/validation/`) — PASS_WITH_WARNINGS accepted for script prep |
| **2** | Review `phase7e3c_finetune/AASIST_L_FINETUNE_RUN_PLAN.md` (balanced sampler required; **class-balanced loss optional, not default**) |
| **3** | Review scripts: `train_aasist_l_finetune.py`, `evaluate_aasist_l_finetuned.py`, `compare_aasist_finetune_results.py` |
| **4** | After review: run training outside Cursor → save `best_product` and `best_loss` checkpoints |
| **5** | Re-evaluate Phase 7C1 + Phase 7A (new output dirs; do not overwrite 7E3A) |
| **6** | Compare vs Hybrid + 7C4-v2 → Phase 7E4 gate review |

### Commands (`(fassd)` activated, repo root)

Use **`python`**, not `py -3`.

**Build fine-tune manifests:**

```text
python code/phase7/aasist/integration/build_aasist_finetune_manifest.py --train_manifest reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv --val_manifest reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv --test_manifest reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep --phase7c1_windows 3 --partial_window_mode suspicious_region --random_seed 42
```

**Validate:**

```text
python code/phase7/aasist/integration/validate_aasist_finetune_manifest.py --train reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_train_manifest.csv --val reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_val_manifest.csv --test reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_test_manifest.csv --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/validation --rejected_csv reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_finetune_rejected_rows.csv --allow_warnings
```

### Phase 7E3C scripts (review first; do not run training inside Cursor)

**Training (implementation exists; run outside Cursor after review):**

```text
python code/phase7/aasist/integration/train_aasist_l_finetune.py --train_manifest reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_train_manifest.csv --val_manifest reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_val_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --base_checkpoint code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/training --device cuda --batch_size 8 --num_workers 0 --epochs 10 --lr 2e-6 --weight_decay 1e-4 --balanced_sampler --use_sample_weight --patience 4
```

**Evaluate fine-tuned checkpoint on fine-tune test windows:**

```text
python code/phase7/aasist/integration/evaluate_aasist_l_finetuned.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_test_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/training/checkpoints/aasist_l_phase7e3c_best_product.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/evaluation/test --device cuda --batch_size 16 --window_mode manifest_windows --save_chunk_timeline --spoof_class_index 0
```

**Optional Phase 7A re-eval after loader fix (new output dir):**

```text
python code/phase7/aasist/integration/run_aasist_pretrained_eval.py --eval_manifest reports/phase7/phase7e_aasist_experiment/phase7e2_dataset_adapter/phase7a_aasist_eval_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --checkpoint_path code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7a_after_loader_fix --device cuda --batch_size 16 --window_mode chunks --save_chunk_timeline --spoof_class_index 0
```

Hub: [phase7/phase7e_aasist_experiment/README.md](phase7/phase7e_aasist_experiment/README.md)

---

## Signed off

- **Phase 7A–7C2**, **7C4-v2** (prototype), **7E0**, **7E0.5**, **7E1**, **7E3A** (pretrained eval complete)

---

## Do not do yet

- Do **not** run AASIST training inside Cursor; scripts are for review first.  
- Do **not** overwrite pretrained `AASIST-L.pth` or original 7E3A eval outputs.  
- Do **not** build final report generator or website UI as priority.

---

## Quick links

| Doc | Use |
|-----|-----|
| [phase7e_aasist_experiment/README.md](phase7/phase7e_aasist_experiment/README.md) | 7E hub |
| [AASIST_L_FINETUNE_TRAINING_PLAN.md](phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/AASIST_L_FINETUNE_TRAINING_PLAN.md) | Training plan (no script yet) |
| [PHASE7E0_ACCEPTANCE_CRITERIA.md](phase7/phase7e_aasist_experiment/PHASE7E0_ACCEPTANCE_CRITERIA.md) | Post fine-tune gates |
