# Phase 7C4 Final Recommendation

## Summary

- Phase 7C3-v1 rejected (binary head as origin proxy; replay/mixer/partial collapsed).
- **Standalone R2 checkpoints (`best_product`, `best_loss`) are not accepted.**
- Phase 7C4 is **calibration only** (no training): threshold sweep + multi-checkpoint decision rules.

## Recommendation

**Accepted for decision-layer prototype only** — not as a final product model.

Use calibrated rules in `apply_phase7c4_decision_layer.py` instead of any single checkpoint file-level REAL/FAKE.

**Required before product sign-off:**
- Run `check_phase7c4_holdout_impact.py` on Phase 7A holdout CSVs.
- Phase 7A impact must be reviewed; prototype is **not** fully accepted until holdout passes.
- Collect more external audio beyond T1–T5 / 7C1 before any market-level performance claim.

## Clean human accounting (Phase 7C1)

- Calibrated **accepted**: 1/23
- Calibrated **borderline** (manual review, not clean): 4/23
- Calibrated **false alarm**: 18/23
- Calibrated review rate (borderline/n): 17.4%
- R2 product accepted (reference): 14/23
- Baseline accepted (reference): 4/23

> Borderline is not accepted as clean; it means manual review.

## Other key metrics (calibrated vs baseline)

- Direct AI segment+detect: 19 → 19
- AI replay detected / segment-suspicious: 15/8 → 15/8
- Partial detected: 43 → 44
- Product score: 0.7522 → 0.7304

- Phase 7C1 acceptance criteria passed: **6/7**
