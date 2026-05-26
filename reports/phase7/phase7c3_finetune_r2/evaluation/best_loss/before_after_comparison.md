# Phase 7C3 — Before / After Fine-Tuning Comparison

Phase 7C1 uses `baseline_status`; Phase 7A holdout uses `product_status`.

## Phase 7C1 (baseline_status)

| status | before | after | delta |
| --- | --- | --- | --- |
| ai_mixer_detected | 23 | 23 | 0 |
| ai_replay_detected | 15 | 0 | -15 |
| ai_replay_file_level_missed_but_segment_suspicious | 8 | 4 | -4 |
| ai_replay_missed | 0 | 19 | 19 |
| clean_human_accepted | 4 | 12 | 8 |
| clean_human_borderline | 2 | 2 | 0 |
| clean_human_false_alarm | 17 | 9 | -8 |
| direct_ai_file_level_missed_but_segment_suspicious | 19 | 15 | -4 |
| direct_ai_missed | 4 | 8 | 4 |
| human_mixer_manipulation_detected | 23 | 23 | 0 |
| human_replay_manipulation_detected | 23 | 15 | -8 |
| human_replay_missed | 0 | 8 | 8 |
| partial_fabrication_detected | 43 | 36 | -7 |
| partial_fabrication_missed | 3 | 10 | 7 |

## Phase 7A holdout (product_status)

| status | before | after | delta |
| --- | --- | --- | --- |
| ai_replay_file_level_missed_but_segment_suspicious | 1 | 0 | -1 |
| ai_replay_or_processed_detected | 4 | 3 | -1 |
| ai_replay_or_processed_missed | 0 | 1 | 1 |
| clean_human_accepted | 1 | 3 | 2 |
| clean_human_borderline | 2 | 0 | -2 |
| direct_ai_detected | 2 | 0 | -2 |
| direct_ai_file_level_missed_but_segment_suspicious | 3 | 3 | 0 |
| direct_ai_missed | 0 | 2 | 2 |
| partial_fabrication_detected | 2 | 2 | 0 |
| processed_ai_file_level_missed_but_segment_suspicious | 0 | 1 | 1 |
| processed_human_manipulation_detected | 9 | 4 | -5 |
| processed_human_missed | 1 | 6 | 5 |

## Acceptance assessment (heuristic)

- [x] Clean human false alarms decrease: 17 -> 9
- [ ] Direct AI detected increases: 0 -> 0
- [ ] Partial fabrication detection stable: 43 -> 36

Review Phase 7A `product_status` table above before accepting checkpoint.
