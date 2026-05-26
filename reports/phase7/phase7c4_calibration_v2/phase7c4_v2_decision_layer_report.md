# Phase 7C4-v2 Decision Layer Report

Phase 7C4 **v1** is **rejected** (clean-human false alarms 18/23, worse than baseline 17/23).
v2 uses role-based ensemble: R2 product for clean human, baseline for manipulation sensitivity.

> **Borderline is not accepted as clean** — it means manual review.

## Comparison: baseline vs R2 product vs v1 vs v2

| Source | CH accept | CH borderline | CH false alarm | CH review% | Direct AI det+seg | Direct AI missed | Human replay det | AI replay det+seg | Human mixer det | AI mixer det+seg | Partial det |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | 4/23 | 2/23 | 17/23 | 9% | 0+19 | 4 | 23 | 15+8 | 23 | 23+0 | 43 |
| R2 product | 14/23 | 2/23 | 7/23 | 9% | 0+13 | 10 | 15 | 0+1 | 23 | 23+0 | 33 |
| C4 v1 calibrated | 1/23 | 4/23 | 18/23 | 17% | 0+19 | 4 | 23 | 15+8 | 23 | 23+0 | 0 |
| C4 v2 calibrated | 1/23 | 15/23 | 7/23 | 65% | 0+19 | 4 | 23 | 15+8 | 23 | 23+0 | 44 |


## v2 acceptance criteria

- [PASS] **clean_human_false_alarm_lte_7**: 7 (max 7)
- [PASS] **clean_human_accept_plus_borderline_gte_14**: 16/23 (min 14)
- [PASS] **direct_ai_detect_plus_segment_gte_19**: 19 (min 19)
- [PASS] **human_replay_detected_gte_20**: 23 (min 20)
- [PASS] **ai_replay_detect_plus_segment_gte_15**: 23 (min 15)
- [PASS] **human_mixer_detected_gte_23**: 23
- [PASS] **ai_mixer_detected_gte_23**: 23
- [PASS] **partial_fabrication_detected_gte_43**: 44 (min 43)
- [PASS] **clean_human_accept_reported_separately**: accepted=1/23 borderline=15/23 false_alarm=7/23

- Criteria passed: **8** / 8
- Error cases: **13** (`phase7c4_v2_error_cases.csv`)

## Decision

v2 meets Phase 7C1 minimum targets — **accepted as decision-layer prototype only** (not a final product model). Run Phase 7A holdout review before sign-off.
