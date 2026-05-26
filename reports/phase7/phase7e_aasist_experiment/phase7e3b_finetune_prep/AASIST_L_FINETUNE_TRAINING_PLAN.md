# Phase 7E3B — AASIST-L Fine-Tuning Training Plan

**Status:** Plan only — **do not train** until hardened validation is reviewed and training script is implemented.  
**Not training-ready** from manifest PASS alone.

---

## Critical warning — do not use plain weighted CE only

Pretrained AASIST-L already **over-flags clean human** on Phase 7C1:

- `clean_human_false_alarm` = **22/23**
- Only **1/23** clean human accepted

The fine-tune manifest is **risk-positive heavy** even after sample weights:

| Split | Unweighted risk_target=0 | Unweighted risk_target=1 |
|-------|--------------------------|--------------------------|
| Train (approx) | ~298 | ~1022 |
| Train weighted (approx) | ~442 | ~1358 |

**Ordinary weighted cross-entropy will likely stay too risk-positive.** Training **must** combine:

1. **Balanced batch sampler** (`balanced_sampler=true`) — equal exposure to bonafide vs spoof windows per epoch  
2. **Class-balanced loss** (`class_balance=true`) — e.g. weighted CE with effective class priors, focal loss, or pos_weight derived from train distribution  
3. **Per-row `sample_weight`** (`sample_weight=true`) — keep Phase 7C1 clean-human boost (up to 4.0)

Do **not** implement training with weighted CE alone.

---

## 1. Context (Phase 7E3A outcome)

| Finding | Result |
|---------|--------|
| Standalone | **Rejected** |
| Branch-only (current thresholds) | **Rejected** |
| Fine-tune candidate | **Approved** — replay/mixer/partial sensitivity; clean-human domain mismatch |

---

## 2. Required training design

| Flag / component | Required |
|------------------|----------|
| `balanced_sampler` | **true** |
| `class_balance` | **true** (loss-level balance in addition to sampler) |
| `sample_weight` | **true** (from manifest column) |
| `early_stopping` | On **product score**, not loss alone |
| Checkpoints | **`best_loss`** and **`best_product`** (separate files) |
| Pretrained overwrite | **Forbidden** — save under `phase7e3b_finetune_runs/` |

| Item | Setting |
|------|---------|
| Model | AASIST-L (`models.AASIST.Model`) |
| Base checkpoint | Official `models/weights/AASIST-L.pth` |
| Loss | Binary CE on `aasist_label` (0=spoof, 1=bonafide) with class balance + sample weights |
| `risk_target` | Forensic-risk label (not origin truth) |

---

## 3. Recommended first training run (6 GB laptop)

| Parameter | Value |
|-----------|-------|
| `batch_size` | **8** |
| `learning_rate` | **1e-6** or **2e-6** first (not 5e-6 until product score stable) |
| `epochs` | **8–12** |
| `balanced_sampler` | **true** |
| `class_balance` | **true** |
| `sample_weight` | **true** |
| `early_stopping` | **true** — monitor **product score** on val |

---

## 4. Product score (checkpoint selection)

`best_product` must be computed on **validation** (or val + internal 7C1 subset), not loss alone.

Include:

| Axis | Intent |
|------|--------|
| Clean-human false alarm reduction | **Hard penalty** — primary fix target |
| Direct AI detection | Must not collapse vs pretrained (~18/23 segment-aware) |
| AI replay detection | Preserve sensitivity |
| Replay / mixer preservation | No trade that zeros manipulation evidence |
| Partial fabrication preservation | Region-aware signal retained |

### Hard gate — clean-human false alarms

If after fine-tune re-eval on Phase 7C1:

- `clean_human_false_alarm` **> 10/23**

then the checkpoint **cannot** be accepted as standalone or branch improvement (same order of magnitude as branch-only ceiling). Target: **≤ 7/23** for standalone consideration; **≤ 10/23** maximum for branch-only discussion.

Product score formula (implementation detail for future `train_aasist_finetune.py`):

- Heavy negative weight on each clean-human false alarm  
- Positive reward for direct AI / AI replay detections  
- Penalty if replay/mixer/partial metrics drop sharply vs pretrained baseline  

---

## 5. Data

| Split | File |
|-------|------|
| Train | `phase7e3b_finetune_prep/aasist_train_manifest.csv` |
| Val | `phase7e3b_finetune_prep/aasist_val_manifest.csv` |
| Test | `phase7e3b_finetune_prep/aasist_test_manifest.csv` |

Built by: `code/phase7/aasist/integration/build_aasist_finetune_manifest.py`  
Validated by: `code/phase7/aasist/integration/validate_aasist_finetune_manifest.py` (hardened checks)

---

## 6. Implementation order

1. Review hardened validation report (`validation/aasist_finetune_manifest_validation_report.md`)  
2. Review this plan and manifest weighted balance  
3. Implement `train_aasist_finetune.py` with sampler + class balance + product score  
4. Train → `best_product` / `best_loss`  
5. Re-evaluate 7C1 + 7A (new output dirs)  
6. Compare Hybrid + 7C4-v2  

---

## 7. Do not

- Train with plain weighted CE only  
- Start training before hardened validation review  
- Overwrite official `AASIST-L.pth`  
- Accept checkpoint with clean_human_false_alarm > 10/23  
- Tune on Phase 7A holdout for product claims  
