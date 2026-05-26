# Phase 7C4-v2 Final Recommendation

## Context

- **Phase 7C4 v1: REJECTED** — restored replay/mixer/partial but clean-human false alarms increased (18/23 vs baseline 17/23).
- **Standalone R2 checkpoints: not accepted.**
- Phase 7C4-v2 is calibration-only (no training).

## v2 clean human (dynamic)

| Metric | Baseline | v1 (if run) | v2 |
|--------|----------|-------------|-----|
| Accepted | 4/23 | 1/23 | 1/23 |
| Borderline (review) | 2/23 | 4/23 | 15/23 |
| False alarm | 17/23 | 18/23 | 7/23 |

> Borderline is not clean accepted; it is manual review (better than false accusation).

## Recommendation

**Accepted as decision-layer prototype only** — not a final product model.

- Deploy v2 rules in `apply_phase7c4_v2_decision_layer.py`.
- **Phase 7A holdout review is still required** (`check_phase7c4_holdout_impact.py`).
- More external audio beyond T1–T5 / 7C1 is required before any market-level claim.

- v2 criteria passed: **8/8**
