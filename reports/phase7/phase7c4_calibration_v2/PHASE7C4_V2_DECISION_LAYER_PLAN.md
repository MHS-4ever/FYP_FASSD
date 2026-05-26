# Phase 7C4-v2 Decision Layer Plan

**Calibration only — no training, no fine-tuning, no architecture changes.**

Outputs go to `reports/phase7/phase7c4_calibration_v2/` only. **Do not overwrite** `reports/phase7/phase7c4_calibration/` (v1).

## Why v1 was rejected

Phase 7C4 v1 restored replay/mixer/partial sensitivity but **over-flagged clean human**:

| Source | Clean human false alarms |
|--------|--------------------------|
| Original baseline | 17/23 |
| R2 best_product | 7/23 |
| **C4 v1 calibrated** | **18/23** |

v1 treated baseline file-level FAKE / high spoof on clean human as confirmed false alarms. That is wrong when R2 product shows low forensic risk — those cases should be **borderline (manual review)**, not false accusation.

v1’s “accepted for prototype” recommendation was **too optimistic** and is withdrawn.

## v2 design: use each checkpoint where it is strongest

| Role | Checkpoint | Use for |
|------|------------|---------|
| Clean human acceptance | **R2 best_product** (+ R2 loss agreement) | Low false accusations |
| Manipulation sensitivity | **Original baseline** | Human/AI replay, mixer, segment spoof |
| Direct AI | Baseline segment + R2 scores | Segment-suspicious first, then R2 detect |
| Conflict | Ensemble | Borderline / manual review |

## v2 rules (summary)

### A) Clean human

- **R2 product low-risk:** `decision_score < 0.70` OR `prediction == REAL`
- **R2 loss low-risk:** `decision_score < 0.75` OR `prediction == REAL`
- **Baseline extreme:** `max_chunk_spoof >= 0.995` OR `suspicious_chunk_ratio >= 0.50`

| Condition | Status |
|-----------|--------|
| R2 product low + R2 loss low + not extreme | `clean_human_accepted` |
| R2 product low + extreme baseline | `clean_human_borderline` (review) |
| R2 product low + R2 loss not low | `clean_human_borderline` |
| R2 product high + R2 loss high + baseline high | `clean_human_false_alarm` |
| Other conflicts | `clean_human_borderline` (not false alarm) |

### B) Direct AI

1. Baseline segment (`max_chunk_spoof >= 0.95` or `ratio >= 0.20`) → segment-suspicious  
2. Else R2 loss or product `score >= 0.55` → detected  
3. Else missed  

### C–E) Replay / mixer

Baseline `FAKE` or `score >= 0.65` first; else R2 loss `>= 0.55`. AI replay/mixer keep segment-suspicious when only chunk evidence.

### F) Partial fabrication

Baseline or R2 loss `partial_region_detected`, or `inside_region_max_spoof >= 0.65`, or `region_delta >= 0.10`.

## v2 acceptance (Phase 7C1 minimum)

| Criterion | Target |
|-----------|--------|
| Clean human false alarm | ≤ 7 |
| Accept + borderline | ≥ 14 |
| Direct AI detect + segment-suspicious | ≥ 19 |
| Human replay detected | ≥ 20 |
| AI replay detect + segment-suspicious | ≥ 15 |
| Human mixer detected | ≥ 23 |
| AI mixer detected | ≥ 23 |
| Partial detected | ≥ 43 |

**Borderline is not clean accepted** — manual review only.

Passing all targets → **prototype only**, not final product model. Phase 7A holdout + more external data still required.

## Deliverables

| File | Description |
|------|-------------|
| `code/phase7/apply_phase7c4_v2_decision_layer.py` | v2 decision layer |
| `calibration_outputs/phase7c4_v2_candidate_decisions.csv` | Per-sample decisions |
| `calibration_outputs/phase7c4_v2_error_cases.csv` | Regressions / misses |
| `calibration_outputs/phase7c4_v2_acceptance_matrix.csv` | Criteria pass/fail |
| `phase7c4_v2_decision_layer_report.md` | Baseline / R2 / v1 / v2 comparison |
| `phase7c4_v2_final_recommendation.md` | Accept or reject v2 |

## Manual command

```text
python code/phase7/apply_phase7c4_v2_decision_layer.py --baseline_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv --r2_product_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv --r2_loss_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv --baseline_partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv --r2_product_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --r2_loss_partial_csv reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv --output_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv --error_csv reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv --output_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_decision_layer_report.md --final_md reports/phase7/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md
```

On Windows use `py -3` if `python` lacks pandas.

## Next steps

1. Run v2 script.  
2. If v2 passes → prototype + Phase 7A holdout (`check_phase7c4_holdout_impact.py`).  
3. If v2 fails → 7C3-R3 or further rule tuning.
