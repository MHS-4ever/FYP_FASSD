# Phase 7C3 — Before / After Fine-Tuning Comparison

Phase 7C1 uses `baseline_status`; Phase 7A holdout uses `product_status`.

## Phase 7C1 (baseline_status)

| status | before | after | delta |
| --- | --- | --- | --- |
| ai_mixer_detected | 23 | 0 | -23 |
| ai_mixer_file_level_missed_but_segment_suspicious | 0 | 2 | 2 |
| ai_mixer_missed | 0 | 21 | 21 |
| ai_replay_detected | 15 | 0 | -15 |
| ai_replay_file_level_missed_but_segment_suspicious | 8 | 0 | -8 |
| ai_replay_missed | 0 | 23 | 23 |
| clean_human_accepted | 4 | 23 | 19 |
| clean_human_borderline | 2 | 0 | -2 |
| clean_human_false_alarm | 17 | 0 | -17 |
| direct_ai_file_level_missed_but_segment_suspicious | 19 | 3 | -16 |
| direct_ai_missed | 4 | 20 | 16 |
| human_mixer_manipulation_detected | 23 | 6 | -17 |
| human_mixer_missed | 0 | 17 | 17 |
| human_replay_manipulation_detected | 23 | 0 | -23 |
| human_replay_missed | 0 | 23 | 23 |
| partial_fabrication_detected | 43 | 6 | -37 |
| partial_fabrication_missed | 3 | 40 | 37 |

## Phase 7A holdout (product_status)

| status | before | after | delta |
| --- | --- | --- | --- |
| ai_replay_file_level_missed_but_segment_suspicious | 1 | 0 | -1 |
| ai_replay_or_processed_detected | 4 | 0 | -4 |
| ai_replay_or_processed_missed | 0 | 5 | 5 |
| clean_human_accepted | 1 | 3 | 2 |
| clean_human_borderline | 2 | 0 | -2 |
| direct_ai_detected | 2 | 0 | -2 |
| direct_ai_file_level_missed_but_segment_suspicious | 3 | 0 | -3 |
| direct_ai_missed | 0 | 5 | 5 |
| partial_fabrication_detected | 2 | 0 | -2 |
| partial_fabrication_missed | 0 | 2 | 2 |
| processed_human_manipulation_detected | 9 | 0 | -9 |
| processed_human_missed | 1 | 10 | 9 |

## Acceptance assessment (heuristic)

- [x] Clean human false alarms decrease: 17 -> 0
- [ ] Direct AI detected increases: 0 -> 0
- [ ] Partial fabrication detection stable: 43 -> 6

Review Phase 7A `product_status` table above before accepting checkpoint.
