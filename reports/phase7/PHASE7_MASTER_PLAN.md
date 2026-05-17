# Phase 7 — Forensic Product Upgrade Master Plan

**Status:** 7A active — no training until 7A reviewed  
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
| **7C** | [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | **Yes** | Fine-tune hybrid on 7A gaps |
| **7D** | [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | No (rules) | **Mandatory** report JSON + wording |
| **7E** | [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) | Yes (exp.) | AASIST → WavLM → wav2vec2 separate |
| **7F** | [PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md](PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md) | Optional | Late fusion after 7E |

**Order:** 7A → 7B → 7C → 7D → 7E → 7F → Phase 8.

---

## 5. What is allowed now

- Documentation and templates  
- Recording T1–T5 test audio  
- Running **existing** Phase 6 inference on test files  
- Filling manifest / results CSV and `FORENSIC_TEST_ANALYSIS.md`  
- Documented threshold **experiments** (not permanent product defaults without analysis)  

---

## 6. What is not allowed yet

| Action | Blocked until |
|--------|----------------|
| Fine-tuning hybrid | 7A reviewed |
| Phase 7B dataset merge into training | 7A reviewed |
| Phase 7C training runs | 7A + 7B ready |
| Phase 7E transformers | 7C reviewed; 7D spec agreed |
| Phase 7F ensemble | 7E comparisons done |
| Phase 6 inference logic changes | Explicit user request |
| Replacing hybrid without 7A/7C baseline | Never without comparison |

---

## 7. Success criteria for moving to 7B / 7C

**Phase 7A complete when:**

- All **T1–T5** priority files are processed through Phase 6.  
- `forensic_test_results.csv` and `FORENSIC_TEST_ANALYSIS.md` exist.  
- False positives and false negatives are documented **per condition group**.  
- **Fabricated** case (`T5_FAB_001` or equivalent): segment **14–21 s** evaluated with inside/outside chunk metrics (not whole-file only).  
- Team agrees **which domains** need 7B labels and 7C fine-tuning.  

**Important rule:** Phase 7A must **measure failure patterns** before any fine-tuning. Do not train on assumptions.

---

## Related

- [README.md](README.md) — index  
- [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md) — T1–T5  
- [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) — labels  
- [../phase7_forensic_tests/](../phase7_forensic_tests/) — manifests and templates  
