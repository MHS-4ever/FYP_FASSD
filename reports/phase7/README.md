# Phase 7 — Reports & Documentation Hub

**Status: CLOSED** — see [PHASE7_FINAL_STATUS_FREEZE.md](PHASE7_FINAL_STATUS_FREEZE.md)  
**Next phase:** [Phase 8 — Multi-Axis Forensic Audio Intelligence](../phase8/PHASE8_START_HERE.md)

All Phase 7 **reports, calibration outputs, evaluation artifacts, and planning docs** live under this folder (read-only archive).

**Code** remains in [`code/phase7/`](../../code/phase7/README.md).

---

## Planning documents (this folder)

| Document | Purpose |
|----------|---------|
| [PHASE7_MASTER_PLAN.md](PHASE7_MASTER_PLAN.md) | Overall plan, gates, sign-off |
| [PHASE7A_CONTROLLED_TEST_SUITE.md](PHASE7A_CONTROLLED_TEST_SUITE.md) | T1–T5 controlled testing |
| [PHASE7B_FORENSIC_DATASET_PREPARATION.md](PHASE7B_FORENSIC_DATASET_PREPARATION.md) | Forensic labels (holdout) |
| [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | Fine-tuning strategy |
| [PHASE7C_FINAL_DECISION_RECORD.md](PHASE7C_FINAL_DECISION_RECORD.md) | **Frozen** Phase 7C decisions |
| [PHASE7C_STATUS_FREEZE.md](PHASE7C_STATUS_FREEZE.md) | One-page 7C status freeze |
| [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md) | Round-1 collection |
| [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | Report layer (legacy overview) |
| [phase7d_report_layer/](phase7d_report_layer/README.md) | **Phase 7D** — report layer planning (implementation **postponed**) |
| [PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md) | **Phase 7E** — AASIST summary |
| [phase7e_aasist_experiment/](phase7e_aasist_experiment/README.md) | **Phase 7E0** — AASIST planning + locked benchmark (**active**) |
| [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) | Transformers (WavLM / wav2vec2 — after AASIST) |
| [PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md](PHASE7F_ENSEMBLE_AND_FINAL_DECISION.md) | Ensemble (planned) |
| [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md) | T1–T5 recording rules |
| [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) | Label definitions |
| [PHASE7_FINAL_CLOSURE_REPORT.md](PHASE7_FINAL_CLOSURE_REPORT.md) | **Phase 7 closure** |
| [PHASE7_TO_PHASE8_TRANSITION.md](PHASE7_TO_PHASE8_TRANSITION.md) | Handoff to Phase 8 |
| [PHASE7_FINAL_STATUS_FREEZE.md](PHASE7_FINAL_STATUS_FREEZE.md) | Status freeze |

Project-wide context: [NEXT_ACTIONS.md](../NEXT_ACTIONS.md), [UPDATED_PROJECT_SCOPE.md](../UPDATED_PROJECT_SCOPE.md).

---

## Operational subfolders

| Subfolder | Phase | Contents |
|-----------|-------|----------|
| [phase7_forensic_tests/](phase7_forensic_tests/) | **7A** | Holdout test suite, results, chunk timelines |
| [phase7_dataset/](phase7_dataset/) | **7B** | Forensic label CSVs |
| [phase7_current_dataset_audit/](phase7_current_dataset_audit/) | **7C0** | Legacy training dataset audit |
| [phase7c1_collection/](phase7c1_collection/) | **7C1** | Collection manifest, validation |
| [phase7c1_baseline/](phase7c1_baseline/) | **7C1** | Pre–fine-tune baseline on 7C1 audio |
| [phase7c2_training_prep/](phase7c2_training_prep/) | **7C2** | Train/val/test manifests |
| [phase7c3_finetune/](phase7c3_finetune/) | **7C3-v1** | v1 fine-tune (rejected; preserved) |
| [phase7c3_finetune_r2/](phase7c3_finetune_r2/) | **7C3-R2** | R2 fine-tune, checkpoints, eval |
| [phase7c4_calibration/](phase7c4_calibration/) | **7C4** | v1 calibration (rejected) |
| [phase7c4_calibration_v2/](phase7c4_calibration_v2/) | **7C4-v2** | Corrected decision layer |
| [phase7d_report_layer/](phase7d_report_layer/) | **7D** | Forensic report layer (planning; implementation postponed) |
| [phase7e_aasist_experiment/](phase7e_aasist_experiment/) | **7E0** | AASIST experiment planning + locked benchmark |

> All Phase 7 documentation stays under **`reports/phase7/`** (not directly under `reports/` root).

---

## Path convention

CLI commands use repo-root paths, for example:

```text
reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv
reports/phase7/phase7c3_finetune_r2/evaluation/best_product/...
```

---

## Current status (summary) — CLOSED

| Item | Status |
|------|--------|
| 7A–7C2 | Signed off |
| 7C3-v1 | **Rejected** |
| 7C3-R2 checkpoints | **Rejected** standalone |
| 7C4-v1 | **Rejected** |
| 7C4-v2 | **Accepted** — decision-layer prototype only |
| 7D | **Postponed** → Phase 8G |
| 7E AASIST | **Rejected** as current solution — [PHASE7_AASIST_NEGATIVE_FINDING.md](PHASE7_AASIST_NEGATIVE_FINDING.md) |
| Phase 7 overall | **Closed** — [PHASE7_FINAL_CLOSURE_REPORT.md](PHASE7_FINAL_CLOSURE_REPORT.md) |

**Do not reopen** Phase 7 experiments without a new controlled plan.

**Phase 8:** [../phase8/PHASE8_START_HERE.md](../phase8/PHASE8_START_HERE.md)

Accepted outputs: [phase7c4_calibration_v2/](phase7c4_calibration_v2/) — not a final product model.

Phase 7D specs (postponed): [phase7d_report_layer/README.md](phase7d_report_layer/README.md).

Phase 7E0 hub: [phase7e_aasist_experiment/README.md](phase7e_aasist_experiment/README.md).

Next actions: [../NEXT_ACTIONS.md](../NEXT_ACTIONS.md).
