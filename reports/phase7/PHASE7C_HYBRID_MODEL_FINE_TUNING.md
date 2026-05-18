# Phase 7C — Hybrid Model Fine-Tuning

**Status:** **Blocked** — after 7A, 7B, 7C0 sign-off; **active prerequisite: Phase 7C1**  
**Training:** **Yes** (when unblocked) — hybrid only; **no transformers** in this phase

---

## Phase 7C0 — Current Training Dataset Audit Results

**Status:** **Signed off.**

| Metric | Result |
|--------|--------|
| Total rows | **1,893,919** |
| Unique files | **1,893,919** |
| Avg rows per file | **1.0** |
| Chunk/file weighting bias | **low** |
| Speaker leakage (train∩val, train∩test) | **0** |
| Missing audio (stratified sample) | **0** missing |
| Duplicate filepath report | **0** major issue |
| Label conflict report | **0** major issue |
| HDF5 feature shapes | **log-mel** `[64,400]` / `[1,64,400]`; **environmental** **12-D** |

**Audit outputs:**

| Document | Path |
|----------|------|
| Main audit report | [CURRENT_TRAINING_DATASET_AUDIT.md](../phase7_current_dataset_audit/CURRENT_TRAINING_DATASET_AUDIT.md) |
| Risk assessment | [dataset_risk_assessment.md](../phase7_current_dataset_audit/dataset_risk_assessment.md) |
| Data collection recommendations | [phase7c_data_collection_recommendations.md](../phase7_current_dataset_audit/phase7c_data_collection_recommendations.md) |
| File-level balance CSVs | `file_level_balance_summary.csv`, `chunk_vs_file_balance_comparison.csv` |

**Regenerate audit:**

```text
python code/phase7/audit_current_training_dataset.py ^
  --manifest_dir data/manifests ^
  --output_dir reports/phase7_current_dataset_audit ^
  --sample_per_group 20 ^
  --check_audio_exists_sample 5000
```

---

## Why Phase 7C Fine-Tuning Cannot Start Yet

The legacy dataset is **technically clean** (speaker-independent splits, valid features, no major duplicates/conflicts) but **not aligned with the forensic product goal**:

- **Spoof-heavy** (~83% spoof rows)
- **Replay / PA-heavy** (PA ~50%, replay attack ~43%)
- **Studio-domain-heavy** (~96% studio domain)
- **Weak Urdu/Pakistani** local coverage
- **Weak phone / WhatsApp / social compression** forensic conditions
- **No separate origin + manipulation** training labels (only `label` + `attack_type`)
- **No partial AI insertion** segment timestamp labels

**Rule:** Do **not** start Phase 7C fine-tuning until **[Phase 7C1](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md)** is completed and new data is **collected and validated** (Phase 7B label schema).

**Next active phase:** [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md).

---

## 1. Goal

Fine-tune the existing **HybridResNetEnvironmental** model on local forensic conditions identified in Phase 7A, **before** considering replacement by transformer models.

---

## 2. Why this phase exists

The baseline already combines spectrogram and environmental branches. Measured 7A gaps (Urdu, phone, replay, mixer, WhatsApp, partial insert) may be addressable by **targeted fine-tuning** with lower risk than swapping architecture.

Fine-tune the **current hybrid first**; compare 7E models only after a strong 7C checkpoint exists.

---

## 3. Inputs

| Input | Source |
|-------|--------|
| Base checkpoint | `hybrid_resnet_environmental_best.pth` |
| 7B forensic manifest + splits | Phase 7B |
| 7A test manifest (held-out) | Same files as 7A for before/after comparison |
| Training script | `code/phase4/train_hybrid_fast.py` (or successor) |

---

## 4. Outputs

| Output | Description |
|--------|-------------|
| Fine-tuned checkpoint | e.g. `hybrid_resnet_environmental_finetuned.pth` |
| Training log | Loss, EER, per-domain metrics |
| Before/after table | Same 7A manifest, baseline vs fine-tuned |
| Decision note | Whether 7E is still required per condition |

---

## 5. Tasks

### Focus domains (from 7A)

- Urdu / Pakistani speech  
- Phone-recorded human audio  
- Human replay (speaker → phone)  
- AI replay  
- Mixer / channel processed (human and AI)  
- WhatsApp / platform compression  
- Partial AI insertion (if labeled in 7B)  

### Possible strategies

| Strategy | When to use |
|----------|-------------|
| Freeze early ResNet layers; train fusion + heads | Limited VRAM; small local set |
| Low learning rate full fine-tune | Larger 7B set; monitor ASVspoof holdout |
| Balanced sampling per `manipulation_type` | Reduce majority-class bias |
| Mix ASVspoof + local forensic data | Reduce catastrophic forgetting |
| Validation on **untouched** 7A test set | No leakage from training speakers |

### Evaluation

- Re-run Phase 6 (or 7A batch script) on full 7A manifest.  
- Compare EER, FPR on bonafide, and **partial_region_detected** for T5.  
- Do not claim forensic proof — report layered metrics only.

---

## 6. Success criteria

- [ ] Fine-tuned model improves **agreed priority metrics** on 7A holdout without unacceptable ASVspoof regression.  
- [ ] Partial-fabrication cases show improved **in-region** chunk scores where 7A failed.  
- [ ] Checkpoint and hyperparameters documented.  
- [ ] Sign-off before **7E** experiments.  

---

## 7. What not to do in this phase

- Train AASIST, WavLM, or wav2vec2 (7E)  
- Build ensemble (7F)  
- Replace hybrid entirely without comparison table  
- Skip 7A before/after evaluation  

---

## 8. Connection to next phase

| Phase | Relationship |
|-------|----------------|
| **7D** | Map fine-tuned scores through report layer; update thresholds if needed |
| **7E** | Compare transformers against **7C hybrid**, not only pre-7C baseline |
| **7F** | May include 7C hybrid as primary fused scorer |
