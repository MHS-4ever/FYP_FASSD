# Phase 7C4-v2 — Corrected Decision Layer

**Replaces the rejected Phase 7C4 v1 logic.** Does not modify `reports/phase7/phase7c4_calibration/`.

## Quick context

- **v1 rejected:** clean-human false alarms 18/23 (worse than baseline 17/23).  
- **v2:** R2 product for clean human; baseline for replay/mixer/partial; borderline when evidence conflicts.

## Run

From repo root (`E:\FYP`). **Defaults** use `reports/phase7/...` paths:

```text
python code/phase7/apply_phase7c4_v2_decision_layer.py
```

Old pre-reorg paths (`reports/phase7/phase7c1_baseline/...`) are still accepted and auto-mapped.

Explicit:

```text
python code/phase7/apply_phase7c4_v2_decision_layer.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv --r2_product_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --r2_loss_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --output_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv --error_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv --output_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_decision_layer_report.md --final_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md
```

See [PHASE7C4_V2_DECISION_LAYER_PLAN.md](PHASE7C4_V2_DECISION_LAYER_PLAN.md).
