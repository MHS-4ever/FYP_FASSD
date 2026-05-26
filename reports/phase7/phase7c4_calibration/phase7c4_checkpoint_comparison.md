# Phase 7C4 Checkpoint Comparison

- Samples compared: **184**

## Status counts (Phase 7C1 `baseline_status`)

### Original baseline

- partial_fabrication_detected: 43
- ai_mixer_detected: 23
- human_mixer_manipulation_detected: 23
- human_replay_manipulation_detected: 23
- direct_ai_file_level_missed_but_segment_suspicious: 19
- clean_human_false_alarm: 17
- ai_replay_detected: 15
- ai_replay_file_level_missed_but_segment_suspicious: 8
- clean_human_accepted: 4
- direct_ai_missed: 4
- partial_fabrication_missed: 3
- clean_human_borderline: 2

### R2 best_product

- partial_fabrication_detected: 33
- ai_mixer_detected: 23
- human_mixer_manipulation_detected: 23
- ai_replay_missed: 22
- human_replay_manipulation_detected: 15
- clean_human_accepted: 14
- direct_ai_file_level_missed_but_segment_suspicious: 13
- partial_fabrication_missed: 13
- direct_ai_missed: 10
- human_replay_missed: 8
- clean_human_false_alarm: 7
- clean_human_borderline: 2
- ai_replay_file_level_missed_but_segment_suspicious: 1

### R2 best_loss

- partial_fabrication_detected: 36
- ai_mixer_detected: 23
- human_mixer_manipulation_detected: 23
- ai_replay_missed: 19
- direct_ai_file_level_missed_but_segment_suspicious: 15
- human_replay_manipulation_detected: 15
- clean_human_accepted: 12
- partial_fabrication_missed: 10
- clean_human_false_alarm: 9
- direct_ai_missed: 8
- human_replay_missed: 8
- ai_replay_file_level_missed_but_segment_suspicious: 4
- clean_human_borderline: 2

## Per-category summary

_Status counts per manipulation category (not generic acc/fp)._

| Category | Baseline | R2 product | R2 loss |
| --- | --- | --- | --- |
| Clean human | accepted=4, false_alarm=17, borderline=2 | accepted=14, false_alarm=7, borderline=2 | accepted=12, false_alarm=9, borderline=2 |
| Direct AI | detected=0, missed=4, segment_suspicious=19 | detected=0, missed=10, segment_suspicious=13 | detected=0, missed=8, segment_suspicious=15 |
| Human replay | detected=23, missed=0 | detected=15, missed=8 | detected=15, missed=8 |
| AI replay | detected=15, missed=0, segment_suspicious=8 | detected=0, missed=22, segment_suspicious=1 | detected=0, missed=19, segment_suspicious=4 |
| Human mixer | detected=23, missed=0 | detected=23, missed=0 | detected=23, missed=0 |
| AI mixer | detected=23, missed=0, segment_suspicious=0 | detected=23, missed=0, segment_suspicious=0 | detected=23, missed=0, segment_suspicious=0 |
| Partial fabrication | detected=43, missed=3, not_evaluable=0 | detected=33, missed=13, not_evaluable=0 | detected=36, missed=10, not_evaluable=0 |


## Clean human (23 samples)

- R2 product better than baseline: **12**
- R2 loss better than baseline: **10**
- Baseline better than R2 product: **1**

## Disagreement types

- agreement: 124
- mixed_disagreement: 36
- partial_disagreement: 10
- replay_mixer_disagreement: 8
- direct_ai_disagreement: 6

## Where R2 helps

- Clean human false alarms: R2 product/loss reduce false alarms vs original baseline (14/23 vs 4/23 accepted; 7 vs 17 false alarms).
- Forensic-risk binary head (R2) is better calibrated for bonafide acceptance than v1 origin proxy.

## Where original baseline remains stronger

- **Direct AI:** baseline segment-suspicious signal (19/23) vs R2 file-level 0/23 detected.
- **AI replay:** baseline 15/23 detected vs R2 0/23.
- **Partial fabrication:** baseline 43/46 vs R2 product 33/46, R2 loss 36/46.

## Conclusion

No fine-tuned checkpoint is accepted standalone. Phase 7C4 threshold sweep and calibrated decision layer are required.
