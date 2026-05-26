# Phase 7E0 — Resource and Training Constraints (AASIST)

**Status:** Locked policy for Phase 7E3+  
**Applies when:** Training/fine-tuning starts (after 7E1–7E2 review)

---

## 1. Hardware inventory

| Environment | GPU | System RAM | OS / env |
|-------------|-----|------------|----------|
| **Primary laptop** | NVIDIA GeForce RTX 3050 Laptop GPU **6 GB** VRAM | **16 GB** | Windows; miniconda **`(fassd)`**; PyTorch with CUDA |
| **Optional PC** | **12 GB** VRAM GPU | TBD | Use for larger batches or faster feature extraction when available |

**Command rule:** Use `python` inside activated **`(fassd)`** — not system `py -3`.

---

## 2. Resource policy (conservative first)

| Policy | Rationale |
|--------|-----------|
| Start with **small batch size** (e.g. 4–8 on 6GB; tune in 7E1 VRAM probe) | Avoid OOM on laptop |
| Prefer **gradient accumulation** over large batch if needed | Stable updates on 6GB |
| **num_workers=0** on Windows unless stability proven | Match 7C3-R2 practice |
| Stream or chunk-load long audio | 16GB RAM limit |
| No massive WavLM-style models in 7E | Defer to later phase |
| No multi-model **joint** training in 7E3 | Single AASIST checkpoint per run |
| Save checkpoints under `reports/phase7/phase7e_aasist_experiment/` or `models_saved/` with **distinct prefix** | Must not overwrite `hybrid_resnet_environmental_best.pth` |

---

## 3. VRAM smoke test (7E1)

Before 7E3, 7E1 must record:

| Check | Pass criterion |
|-------|----------------|
| Import AASIST / dependencies | No missing modules in `(fassd)` |
| Forward pass on dummy batch | Completes on CUDA |
| Peak VRAM at planned batch | Fits in 6GB with documented headroom, or documents 12GB-only training |
| Inference-only peak | Fits for 7E4 eval batch |

Document results in `reports/phase7/phase7e_aasist_experiment/phase7e1_smoke_test.md` (created in 7E1).

---

## 4. Training constraints (7E3)

| Constraint | Detail |
|------------|--------|
| Data | 7C2 train/val manifests + label strategy; **no 7A** |
| Checkpoints | Separate directory, e.g. `models_saved/aasist_phase7e/` or experiment subfolder |
| Epochs | Start low (e.g. ≤ 15) with early stopping; document in run config |
| Learning rate | Conservative; fine-tune from pretrained anti-spoof weights when used |
| Mixed precision | Optional `--amp` only if stable on 3050 |
| Feature cache | If used, single-process build; `--force` documented |
| Reproducibility | Log `random_seed`, manifest hashes, git commit in run README |

---

## 5. Download policy

| Item | 7E0 | 7E1+ |
|------|-----|------|
| Large pretrained weights | **Do not** download in 7E0 | Allowed in 7E1 smoke / 7E3 with documented URL and size |
| Full ASVspoof re-download | Avoid if project copies exist | Use existing `data/` paths from manifests |

---

## 6. What not to run yet

- Multi-GPU distributed training  
- Simultaneous HybridResNet + AASIST training jobs on 6GB  
- WavLM / wav2vec2 experiments in parallel with 7E3  
- Ensemble fusion training (7E5 is calibration-only, after 7E4)

---

## 7. Failure handling

| Situation | Action |
|-----------|--------|
| OOM at planned batch | Reduce batch, enable accumulation, or restrict to 12GB PC with documented flag |
| CUDA unavailable | Block 7E3; complete CPU-only feasibility note — do not claim GPU eval |
| Run exceeds RAM | Reduce workers, shorter clips, or manifest subsample for **debug only** (not for acceptance) |

---

## 8. Related

- [PHASE7E0_DO_NOT_DO.md](PHASE7E0_DO_NOT_DO.md)  
- [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md)  
- [../../code/phase7/README.md](../../../code/phase7/README.md)
