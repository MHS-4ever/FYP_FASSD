# Phase 7D — Forensic Report Layer (Planning Hub)

**Status:** Planning / specification only (May 2026)  
**Training:** None  
**Implementation:** Phase **7D1** — `code/phase7/build_phase7d_forensic_report.py` (not started)

Phase 7C is frozen. The accepted upstream artifact is **Phase 7C4-v2** (decision-layer prototype only). Phase 7D converts those calibrated outputs into **safe, reviewer-oriented forensic reports** — JSON and Markdown first; PDF and web UI later.

---

## Documents in this folder

| Document | Purpose |
|----------|---------|
| [PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md](PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md) | Master plan, scope, phases, success criteria |
| [PHASE7D_REPORT_OUTPUT_SCHEMA.md](PHASE7D_REPORT_OUTPUT_SCHEMA.md) | Field definitions and types |
| [PHASE7D_REPORT_WORDING_GUIDE.md](PHASE7D_REPORT_WORDING_GUIDE.md) | Approved / forbidden language |
| [PHASE7D_DECISION_TO_REPORT_MAPPING.md](PHASE7D_DECISION_TO_REPORT_MAPPING.md) | `calibrated_status` → report fields |
| [PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md](PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md) | Standard limitations and disclaimer blocks |
| [PHASE7D_JSON_SCHEMA_EXAMPLE.json](PHASE7D_JSON_SCHEMA_EXAMPLE.json) | Example machine-readable report |
| [PHASE7D_MARKDOWN_REPORT_TEMPLATE.md](PHASE7D_MARKDOWN_REPORT_TEMPLATE.md) | Human-readable report template |
| [PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md](PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md) | Expected behavior by case type |
| [examples/](examples/) | Illustrative Markdown reports (not live inference) |

---

## Primary inputs (canonical paths)

| Input | Path |
|-------|------|
| 7C4-v2 decisions | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` |
| 7C4-v2 error cases | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv` |
| 7C4-v2 decision report | `reports/phase7/phase7c4_calibration_v2/phase7c4_v2_decision_layer_report.md` |
| 7C1 baseline results | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` |
| Partial fabrication analysis | `reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv` |
| R2 best_product (7C1) | `reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv` |
| R2 best_loss (7C1) | `reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv` |
| Chunk timelines (baseline) | `reports/phase7/phase7c1_baseline/results/chunk_timelines/` |
| Chunk timelines (R2 product) | `reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/chunk_timelines/` |
| Chunk timelines (R2 loss) | `reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/chunk_timelines/` |

---

## Planned outputs (7D1)

| Output | Location (planned) |
|--------|-------------------|
| Per-file JSON reports | `reports/phase7/phase7d_report_layer/outputs/json/` |
| Per-file Markdown reports | `reports/phase7/phase7d_report_layer/outputs/markdown/` |
| Sample pack (6–8 cases) | `reports/phase7/phase7d_report_layer/outputs/samples/` |

---

## Related project docs

- Phase 7C freeze: [../PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md)
- Legacy 7D overview: [../PHASE7D_FORENSIC_REPORT_LAYER.md](../PHASE7D_FORENSIC_REPORT_LAYER.md)
- Root report spec: [../../FORENSIC_REPORT_OUTPUT_SPEC.md](../../FORENSIC_REPORT_OUTPUT_SPEC.md)
- Next actions: [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md)

---

## Out of scope (this phase)

- Model training / fine-tuning  
- Changes to Phase 7C4-v2 decision rules  
- Website UI  
- PDF generation code  
