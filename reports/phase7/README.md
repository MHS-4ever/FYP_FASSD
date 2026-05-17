# Phase 7 Documentation Index

**Status:** Canonical planning home for Phase 7 (documentation only until 7A code is requested)  
**Active phase:** **Phase 7A** — controlled forensic testing  
**No training** until Phase 7A analysis is reviewed.

---

## What this folder is

All **Phase 7 planning** (7A–7F) lives here. High-level thesis and product reasoning stay in `reports/` root:

| Root document | Purpose |
|---------------|---------|
| [PHASE7_THESIS_RATIONALE.md](../PHASE7_THESIS_RATIONALE.md) | Why Phase 7 exists (thesis/report style) |
| [FORENSIC_PRODUCT_MASTER_PLAN.md](../FORENSIC_PRODUCT_MASTER_PLAN.md) | Master product plan and output layers |
| [UPDATED_PROJECT_SCOPE.md](../UPDATED_PROJECT_SCOPE.md) | Six official scope areas |
| [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md) | Report field specification |

Legacy paths under `reports/pipeline_phases/` and `reports/FORENSIC_PRODUCT_ROADMAP.md` are **retained for reference** with a redirect note at the top.

---

## Phase 7 documents

| File | Purpose |
|------|---------|
| [PHASE7_MASTER_PLAN.md](PHASE7_MASTER_PLAN.md) | Overall Phase 7 plan, gates, allowed/not allowed |
| [PHASE7A_CONTROLLED_TEST_SUITE.md](PHASE7A_CONTROLLED_TEST_SUITE.md) | Current phase — testing before training |
| [PHASE7B_FORENSIC_DATASET_PREPARATION.md](PHASE7B_FORENSIC_DATASET_PREPARATION.md) | Dataset and labels for fine-tuning |
| [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | Fine-tune current hybrid model |
| [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | Report generation and safe wording |
| [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) | AASIST / WavLM / wav2vec experiments |
| [PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md](PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md) | Late fusion and final decision logic |
| [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md) | T1–T5 test groups and recording rules |
| [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) | Label definitions and allowed values |

---

## Operational assets (7A execution)

Templates and manifests are under **[../phase7_forensic_tests/](../phase7_forensic_tests/)**:

- `forensic_test_manifest_template.csv`  
- `PARTIAL_FABRICATION_CHUNK_ANALYSIS.md`  
- `results/forensic_test_results_template.csv`  

Planned code (not implemented): `code/phase7/README.md`

---

## Gates

| Before… | Requirement |
|---------|-------------|
| **7B / 7C** | Phase 7A complete; `FORENSIC_TEST_ANALYSIS.md` reviewed |
| **7E** | 7C hybrid review; 7D report spec agreed |
| **7F** | 7E standalone model comparisons documented |
| **Any training** | No fine-tuning until 7A signed off |
