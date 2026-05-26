# Phase 7C4 — Phase 7A Holdout Impact

Compares `product_status` on the **controlled holdout** (T1–T5) across:
- Original baseline model
- R2 `best_product`
- R2 `best_loss`

**Note:** The calibrated decision layer (`apply_phase7c4_decision_layer.py`) is evaluated on Phase 7C1 in this phase. This report compares checkpoint outputs on holdout only. **A decision-layer prototype is not fully accepted until holdout impact is reviewed.**

> Borderline is not accepted as clean; it means manual review.

## Clean human (holdout)

| Source | Counts |
| --- | --- |
| Baseline | accepted=1, borderline=2, false_alarm=0 |
| R2 best_product | accepted=3, borderline=0, false_alarm=0 |
| R2 best_loss | accepted=3, borderline=0, false_alarm=0 |

## Direct AI

| Group | direct ai detected | direct ai missed | direct ai file level mis | direct ai borderline |
| --- | --- | --- | --- | --- |
| Baseline | 2 | 0 | 3 | 0 |
| R2 product | 0 | 3 | 2 | 0 |
| R2 loss | 0 | 2 | 3 | 0 |

## Processed human manipulation

| Group | processed human manipula | processed human missed |
| --- | --- | --- |
| Baseline | 9 | 1 |
| R2 product | 4 | 6 |
| R2 loss | 4 | 6 |

## AI replay / processed AI

| Group | ai replay or processed d | ai replay or processed m | ai replay file level mis | processed ai file level  |
| --- | --- | --- | --- | --- |
| Baseline | 4 | 0 | 1 | 0 |
| R2 product | 2 | 1 | 1 | 1 |
| R2 loss | 3 | 1 | 0 | 1 |

## Partial fabrication

| Group | partial fabrication dete | partial fabrication miss | partial not evaluated mi | partial fabrication not  |
| --- | --- | --- | --- | --- |
| Baseline | 2 | 0 | 0 | 0 |
| R2 product | 2 | 0 | 0 | 0 |
| R2 loss | 2 | 0 | 0 | 0 |


## Acceptance note

- Do **not** treat R2 holdout numbers as product sign-off without comparing to baseline segment-suspicious counts.
- If R2 collapses direct-AI segment-suspicious or processed-human detection vs baseline, keep baseline segment rules in the decision layer.
- More external audio beyond T1–T5 is required before market-level claims.
