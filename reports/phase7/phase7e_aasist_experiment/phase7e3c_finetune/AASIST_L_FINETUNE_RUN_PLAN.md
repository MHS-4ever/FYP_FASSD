# Phase 7E3C — AASIST-L Fine-Tune Run Plan (scripts + harness only)

**Status:** Script preparation + review only. **Do not train inside Cursor.**  
**Inputs validated:** Phase 7E3B manifests **PASS_WITH_WARNINGS** (weighted ratio ~3.07 supports balanced sampling).

---

## Why training is now allowed (outside Cursor, after review)

- Phase 7E3A confirmed pretrained AASIST-L is **useful** on spoof/replay/mixer/partial but **fails clean-human** (22/23 false alarms).
- Phase 7E3B prepared a reproducible fine-tune dataset and hardened validation.
- Phase 7E3C adds the missing **training script + evaluation harness** to run controlled fine-tune experiments.

Training is allowed **only after**:
- scripts are reviewed
- outputs are directed to `phase7e3c_finetune/` (no overwrites)
- base checkpoint remains untouched

---

## Critical design decision (imbalance handling)

Default first run must **not** enable every imbalance fix simultaneously.

**Default (first run):**
- `balanced_sampler=true`
- `use_sample_weight=true`
- `class_balanced_loss=false` (**optional** flag exists, default disabled)

**Reason:** balanced sampler + class-balanced loss + sample weights together may over-correct toward `risk_target=0` / bonafide and damage spoof/direct-AI sensitivity. We start with the minimum required correction: **balanced exposure** (sampler) while preserving the clean-human emphasis via `sample_weight`.

---

## Output structure (must be used)

All outputs must live under:

`reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/`

- `training/`
  - `checkpoints/` (epoch + best_loss + best_product)
  - `training_log.csv`
  - `training_summary.md`
  - `best_checkpoint_metrics.json`
- `evaluation/`
  - `val/`
  - `test/`
  - `phase7c1_after_finetune/`
  - `phase7a_after_finetune/`
  - `comparison/`
- `config/`
  - `aasist_l_finetune_config.json`

---

## First run hyperparameters (recommended)

- `batch_size=8`
- `lr=2e-6`
- `epochs=10`
- `weight_decay=1e-4`
- `balanced_sampler=true`
- `use_sample_weight=true`
- `class_balanced_loss=false`
- `patience=4` (early stopping on **product score**, not loss)
- `random_seed=42`

---

## Acceptance criteria (post-training evaluation)

After training, evaluate **Phase 7C1** (and Phase 7A holdout for safety):

- **Clean-human false alarms** must drop substantially vs pretrained baseline.
- Do **not** destroy:
  - direct AI detection
  - AI replay / mixer sensitivity
  - partial fabrication region usefulness

### Failure criteria

- If Phase 7C1 `clean_human_false_alarm > 10/23`, checkpoint must be treated as **reject** for standalone/branch improvement.
- If direct AI detection collapses materially relative to pretrained (~18/23 segment-aware), checkpoint is not acceptable as evidence branch improvement.

---

## What to run after training (outside Cursor)

### 1) Train (writes to `phase7e3c_finetune/training/`)

```text
python code/phase7/aasist/integration/train_aasist_l_finetune.py --train_manifest reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_train_manifest.csv --val_manifest reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/aasist_val_manifest.csv --aasist_src code/phase7/aasist/vendor/AASIST --config_path code/phase7/aasist/vendor/AASIST/config/AASIST-L.conf --base_checkpoint code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth --output_dir reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/training --device cuda --batch_size 8 --num_workers 0 --epochs 10 --lr 2e-6 --weight_decay 1e-4 --balanced_sampler --use_sample_weight --patience 4 --random_seed 42
```

Optional:
- add `--class_balanced_loss` only if clean-human improves but weighted skew persists without hurting spoof.

### 2) Evaluate best checkpoints on Phase 7C1 + Phase 7A (new output dirs)

Use `evaluate_aasist_l_finetuned.py` with:
- `--window_mode chunks` for Phase 7C1 / Phase 7A eval manifests
- `--window_mode manifest_windows` for fine-tune val/test manifests

### 3) Compare vs pretrained + gates

Run `compare_aasist_finetune_results.py` to generate:
- `evaluation/comparison/aasist_finetune_comparison.csv`
- `evaluation/comparison/aasist_finetune_recommendation.md`

---

## Hard stops

- Do not overwrite `code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth`
- Do not overwrite `phase7e3a_pretrained_eval/` outputs
- Do not tune thresholds on Phase 7A holdout for product claims

