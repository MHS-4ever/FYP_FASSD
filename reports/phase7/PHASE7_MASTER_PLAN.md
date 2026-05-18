# Phase 7 — Forensic Product Upgrade Master Plan

**Status:** 7A, 7B, 7C0 **signed off** — **next active: Phase 7C1** (data collection plan; no fine-tuning yet)  
**Product:** Forensic Voice Authenticity Analyzer  
**Baseline:** `HybridResNetEnvironmental` + Phase 6 inference (unchanged in 7A)

---

## 1. Phase 7 goal

Upgrade FASSD from **binary AI-vs-human detection** to a **forensic authenticity analyzer** that:

- Measures baseline failures on **controlled local conditions** (7A)  
- Builds **forensic labels and datasets** (7B)  
- **Fine-tunes** the hybrid where gaps are proven (7C)  
- Produces **safe forensic reports** with timelines (7D)  
- **Optionally** adds transformer models, evaluated separately (7E)  
- **Optionally** fuses best models late (7F)  

---

## 2. Why Phase 7 exists

See [PHASE7_THESIS_RATIONALE.md](../PHASE7_THESIS_RATIONALE.md). Summary:

- REAL/FAKE does not express replay, compression, editing, or partial fabrication.  
- Stakeholders need **reports**, not only labels.  
- Urdu/Pakistani, phone, replay, and platform chains are under-tested on the current baseline.  

---

## 3. Current baseline model

| Item | Value |
|------|--------|
| Architecture | `code/phase3/hybrid_resnet_environmental.py` |
| Checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` |
| Inference | `code/phase6/explain_prediction.py` |
| Chunking | 4 s chunks, 1 s overlap, VAD, pooling |

Phase 7A runs this stack **unchanged** to document failure patterns.

---

## 4. Phase 7A–7F summary

| Phase | Doc | Training | Summary |
|-------|-----|----------|---------|
| **7A** | [PHASE7A_CONTROLLED_TEST_SUITE.md](PHASE7A_CONTROLLED_TEST_SUITE.md) | **No** | T1–T5 controlled tests; CSV + analysis |
| **7B** | [PHASE7B_FORENSIC_DATASET_PREPARATION.md](PHASE7B_FORENSIC_DATASET_PREPARATION.md) | Labels only | Manifest → training CSV with forensic fields |
| **7C0** | [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) (audit) | **No** | Audit legacy training corpus — **signed off** |
| **7C1** | [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md) | **No** | Collection plan before fine-tuning — **active** |
| **7C** | [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | **Yes** | Fine-tune hybrid (after 7C1 collection + validation) |
| **7D** | [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | No (rules) | **Mandatory** report JSON + wording |
| **7E** | [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) | Yes (exp.) | AASIST → WavLM → wav2vec2 separate |
| **7F** | [PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md](PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md) | Optional | Late fusion after 7E |

**Order:** 7A → 7B → 7C0 → **7C1** → 7C → 7D → 7E → 7F → Phase 8.

---

## Signed-off progress so far

### Phase 7A — Controlled Forensic Testing

**Status:** Signed off.

**Main finding:** The current hybrid model is **manipulation-sensitive** but **confuses processed human manipulation with AI-origin spoofing**. Segment-level analysis is necessary; binary REAL/FAKE alone is insufficient for product decisions.

### Phase 7B — Forensic Label Preparation

**Status:** Signed off.

**Main finding:** The T1–T5 controlled set is labeled with file-level and segment-level forensic labels but is kept as **`controlled_holdout`** — **not training data** (`use_for_training=false` on all 25 rows).

### Phase 7C0 — Current Training Dataset Audit

**Status:** Signed off.

**Main finding:** The old training dataset (~1.89M rows) is **technically clean** and **speaker-independent**, but **product-mismatched** due to spoof/replay/studio dominance and missing local forensic conditions (Urdu/Pakistani, phone, WhatsApp, origin/manipulation dual labels, partial-insert timestamps).

**Next active phase:** [Phase 7C1 — New Forensic Data Collection Plan](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md).

---

## 5. What is allowed now

- Phase **7C1** documentation, collection manifest design, and recording planning  
- New forensic audio collection per [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md)  
- Re-running 7A/7B/7C0 audit scripts for verification (no logic changes without request)  
- Phase **7D** report-layer **documentation** (rules/schema only — no training)  

---

## 6. What is not allowed yet

| Action | Blocked until |
|--------|----------------|
| Fine-tuning hybrid (Phase 7C) | 7C1 collection plan complete + new data collected and validated |
| Merging Phase 7A T1–T5 into training | **Never** (controlled holdout) |
| Fine-tuning on legacy unified corpus alone | 7C0 sign-off + 7C1 new data |
| Phase 7E transformers | 7C reviewed; 7D spec agreed |
| Phase 7F ensemble | 7E comparisons done |
| Phase 6 inference logic changes | Explicit user request |
| Replacing hybrid without 7A/7C baseline | Never without comparison |

---

## 7. Success criteria — completed vs next

**Signed off:** 7A (controlled testing), 7B (label schema + holdout labels), 7C0 (legacy dataset audit).

**Phase 7C1 complete when:**

- Collection manifest schema and naming rules are fixed  
- Minimum per-category counts are defined  
- Split strategy (speaker/file-level, paired variants) is documented  
- Quality-check plan exists before any 7C fine-tuning  

**Phase 7C fine-tuning** starts only after 7C1 data is collected, labeled (Phase 7B schema), and validated.

---

## Related

- [README.md](README.md) — index  
- [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md) — T1–T5  
- [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) — labels  
- [../phase7_forensic_tests/](../phase7_forensic_tests/) — manifests and templates  
