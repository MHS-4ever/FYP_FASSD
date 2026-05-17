# Phase 7C — Hybrid Model Fine-Tuning

**Status:** Planned (after Phase 7A + 7B + **7C0 audit**)  
**Training:** **Yes** — hybrid only; **no transformers** in this phase

---

## Phase 7C0 — Current Dataset Audit Before Fine-Tuning

Before collecting new training data or fine-tuning, the **existing** HybridResNetEnvironmental training corpus must be audited for:

- Label balance (bonafide vs spoof)
- Attack-type balance (synthesis, conversion, replay)
- Domain balance (studio vs real-world / social / phone)
- Speaker-independent split integrity
- Language and product-domain gaps (Urdu/Pakistani, phone, WhatsApp)
- HDF5 feature consistency (`logmel_chunked.h5`, `environmental_packed.h5`)

**Audit outputs:**

| Document | Path |
|----------|------|
| Main audit report | [CURRENT_TRAINING_DATASET_AUDIT.md](../phase7_current_dataset_audit/CURRENT_TRAINING_DATASET_AUDIT.md) |
| Risk assessment | [dataset_risk_assessment.md](../phase7_current_dataset_audit/dataset_risk_assessment.md) |
| Data collection plan | [phase7c_data_collection_recommendations.md](../phase7_current_dataset_audit/phase7c_data_collection_recommendations.md) |

**Regenerate audit:**

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

**Rule:** **No Phase 7C fine-tuning should begin until this audit is reviewed** and minimum new forensic data (see recommendations doc) is collected and labeled.

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
