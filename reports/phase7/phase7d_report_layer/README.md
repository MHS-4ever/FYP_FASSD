# Phase 7D — Forensic Report Layer

**Status:** 7D1 implemented (May 2026)  
**Training:** None  
**Scripts:** `code/phase7/build_phase7d_forensic_report.py`, `code/phase7/validate_phase7d_reports.py`

Phase 7C is frozen. **Phase 7C4-v2** is the upstream decision-layer prototype. Phase 7D converts calibrated outputs into **safe, reviewer-oriented** JSON and Markdown forensic reports (no PDF/UI in 7D1).

---

## Documents in this folder

| Document | Purpose |
|----------|---------|
| [PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md](PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md) | Master plan |
| [PHASE7D_REPORT_OUTPUT_SCHEMA.md](PHASE7D_REPORT_OUTPUT_SCHEMA.md) | JSON field definitions |
| [PHASE7D_DECISION_TO_REPORT_MAPPING.md](PHASE7D_DECISION_TO_REPORT_MAPPING.md) | Status → report mapping |
| [PHASE7D_REPORT_WORDING_GUIDE.md](PHASE7D_REPORT_WORDING_GUIDE.md) | Safe language |
| [PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md](PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md) | Disclaimer + limitations |
| [PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md](PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md) | QA expectations |
| [examples/](examples/) | Illustrative reports (not live output) |

---

## Generate reports (7D1)

Use **`python`** in the **`(fassd)`** environment.

```text
python code/phase7/build_phase7d_forensic_report.py ^
  --decisions_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv ^
  --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv ^
  --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv ^
  --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv ^
  --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv ^
  --baseline_chunk_dir reports/phase7/phase7c1_baseline/results/chunk_timelines ^
  --output_dir reports/phase7/phase7d_report_layer/outputs ^
  --generate_samples ^
  --sample_count 8
```

Optional flags: `--sample_ids human_001_clean,ai_001_direct` · `--limit 20` · `--strict` · `--no_samples`

---

## Validate reports

```text
python code/phase7/validate_phase7d_reports.py ^
  --json_dir reports/phase7/phase7d_report_layer/outputs/json ^
  --markdown_dir reports/phase7/phase7d_report_layer/outputs/markdown ^
  --output_md reports/phase7/phase7d_report_layer/outputs/phase7d_report_validation_report.md ^
  --output_csv reports/phase7/phase7d_report_layer/outputs/phase7d_rejected_or_failed_reports.csv
```

Add `--strict` to exit non-zero on validation failures.

---

## Output layout

```text
reports/phase7/phase7d_report_layer/outputs/
├── json/<sample_id>_forensic_report.json
├── markdown/<sample_id>_forensic_report.md
├── samples/json/
├── samples/markdown/
├── samples/SAMPLE_REPORT_INDEX.md
├── phase7d_report_generation_manifest.csv
├── phase7d_report_summary.md
├── phase7d_report_validation_report.md
└── phase7d_rejected_or_failed_reports.csv
```

---

## Primary inputs

| Input | Path |
|-------|------|
| 7C4-v2 decisions | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` |
| 7C4-v2 errors (optional) | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv` |
| Baseline | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` |
| Partial analysis | `reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv` |
| R2 product / loss | `reports/phase7/phase7c3_finetune_r2/evaluation/.../phase7c1_baseline_results.csv` |
| Chunk timelines | `reports/phase7/phase7c1_baseline/results/chunk_timelines/` |

---

## Related

- Phase 7C freeze: [../PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md)
- Code: [../../code/phase7/README.md](../../code/phase7/README.md)
- Next actions: [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md)

---

## Out of scope

- Training / fine-tuning  
- Changes to 7C4-v2 rules  
- PDF / web UI  
