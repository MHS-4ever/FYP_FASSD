# Phase 7C Status Freeze

**Frozen:** May 2026 — do not overwrite this decision unless a new controlled evaluation is completed.

| Item | Status |
|------|--------|
| Phase 7C3-v1 | **Rejected** |
| Phase 7C3-R2 `best_product` | **Rejected** as standalone checkpoint |
| Phase 7C3-R2 `best_loss` | **Rejected** as standalone checkpoint |
| Phase 7C4-v1 | **Rejected** |
| Phase 7C4-v2 | **Accepted** as decision-layer prototype only |

## Accepted artifact

`reports/phase7/phase7c4_calibration_v2/`

- `calibration_outputs/phase7c4_v2_candidate_decisions.csv`
- `phase7c4_v2_final_recommendation.md`
- `phase7c4_v2_decision_layer_report.md`

## Evidence model (not final product)

- `models_saved/hybrid_resnet_environmental_best.pth` — baseline evidence source
- R2 checkpoints under `reports/phase7/phase7c3_finetune_r2/training/checkpoints/` — evidence only if fused by 7C4-v2 rules

## Next

**Phase 7D — Forensic Report Layer**

Full record: [PHASE7C_FINAL_DECISION_RECORD.md](PHASE7C_FINAL_DECISION_RECORD.md)
