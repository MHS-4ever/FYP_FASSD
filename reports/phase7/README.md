# Phase 7 Documentation Index

**Status:** Phase **7A**, **7B**, **7C0** signed off  
**Active phase:** **Phase 7C1** — new forensic data collection plan  
**No Phase 7C fine-tuning** until 7C1 data is collected and validated.

---

## What this folder is

All **Phase 7 planning** (7A–7F, 7C0, 7C1) lives here. High-level thesis and product reasoning stay in `reports/` root:

| Root document | Purpose |
|---------------|---------|
| [PHASE7_THESIS_RATIONALE.md](../PHASE7_THESIS_RATIONALE.md) | Why Phase 7 exists (thesis/report style) |
| [FORENSIC_PRODUCT_MASTER_PLAN.md](../FORENSIC_PRODUCT_MASTER_PLAN.md) | Master product plan and output layers |
| [NEXT_ACTIONS.md](../NEXT_ACTIONS.md) | Current next steps |
| [CURSOR_WORKFLOW_GUIDE.md](../CURSOR_WORKFLOW_GUIDE.md) | Token-efficient Cursor workflow |

---

## Phase 7 documents

| File | Purpose | Status |
|------|---------|--------|
| [PHASE7_MASTER_PLAN.md](PHASE7_MASTER_PLAN.md) | Overall plan, gates, sign-off summary | Updated |
| [PHASE7A_CONTROLLED_TEST_SUITE.md](PHASE7A_CONTROLLED_TEST_SUITE.md) | Controlled T1–T5 testing | **Signed off** |
| [PHASE7B_FORENSIC_DATASET_PREPARATION.md](PHASE7B_FORENSIC_DATASET_PREPARATION.md) | Forensic labels (holdout) | **Signed off** |
| [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | Fine-tune hybrid (includes 7C0 audit) | 7C0 signed off; 7C blocked |
| [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md) | Round-1 plan (15+ × 8 ≈ 120 files) | **Active** |
| [../phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md](../phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md) | Templates, protocols, manifest | **Active** |
| [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | Report generation and safe wording | Planned |
| [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) | Transformer experiments | Planned |
| [PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md](PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md) | Late fusion | Planned |
| [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md) | T1–T5 recording rules | Reference |
| [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) | Label definitions | Reference |

---

## Operational assets

| Area | Path |
|------|------|
| **7C1 collection** | [../phase7c1_collection/](../phase7c1_collection/) (Round-1: 15+ × 8 ≈ 120 files) |
| 7A tests | [../phase7_forensic_tests/](../phase7_forensic_tests/) |
| 7B labels | [../phase7_dataset/](../phase7_dataset/) |
| 7C0 audit | [../phase7_current_dataset_audit/](../phase7_current_dataset_audit/) |
| Code | [../../code/phase7/README.md](../../code/phase7/README.md) |

---

## Gates

| Before… | Requirement |
|---------|-------------|
| **7C1 collection** | 7A + 7B + 7C0 signed off |
| **7C fine-tuning** | 7C1 plan complete + new data collected and validated |
| **7E** | 7C hybrid review; 7D spec agreed |
| **7F** | 7E comparisons documented |
| **Training on T1–T5** | **Never** — `controlled_holdout` |
