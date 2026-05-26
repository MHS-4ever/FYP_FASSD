# Phase 7C4 Decision Layer Report

## Calibrated layer metrics (Phase 7C1)

| Metric | Baseline | R2 product | Calibrated |
|--------|----------|------------|------------|
| Clean human accepted | 4 | 14 | 1 |
| Clean human borderline (review) | 2 | 2 | 4 |
| Clean human false alarm | 17 | 7 | 18 |
| Clean human review rate | — | — | 17.4% |
| Direct AI detected | 0 | 0 | 0 |
| Direct AI segment-suspicious | 19 | 13 | 19 |
| Human replay detected | 23 | 15 | 23 |
| AI replay detected | 15 | 0 | 15 |
| Partial fabrication detected | 43 | 33 | 44 |
| Product score | 0.7522 | 0.6435 | 0.7304 |

## Acceptance criteria

- [FAIL] **clean_human_false_alarms_lower_than_baseline**: 17 -> 18
- [PASS] **clean_human_accepted_or_borderline_gte_baseline_accepted**: baseline_accept=4 cal_accept+borderline=5 (accept=1, borderline=4)
- [PASS] **clean_human_accept_reported_separately**: accepted=1/23 (borderline=4, false_alarm=18, review_rate=17.39%)
- [PASS] **direct_ai_suspicious_higher_than_r2_product_alone**: segment+detect vs R2-only
- [PASS] **human_replay_detection_close_to_baseline**: 23 -> 23
- [PASS] **mixer_detection_close_to_baseline**: human+ai mixer
- [PASS] **partial_fabrication_close_to_baseline**: 43 -> 44
- [PASS] **product_score_improves_over_r2_product**: 0.6435 -> 0.7304

- Criteria passed: **6** / 7 (informational row excluded)
- Error cases flagged: **24** (see `phase7c4_error_cases.csv`)

## Decision


> **Borderline is not accepted as clean** — it means manual review. Only `clean_human_accepted` counts as bonafide acceptance.

Phase 7C1 criteria suggest the calibrated layer is a **decision-layer prototype** (not a final product model). Run `check_phase7c4_holdout_impact.py` on Phase 7A before any sign-off.
