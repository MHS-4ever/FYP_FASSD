# Phase 7E3A — AASIST-L Pretrained Analysis (phase7c1)

**Generated:** 2026-05-26T20:24:41.809274+00:00
**Model:** pretrained AASIST-L (no fine-tuning)

## 1. Executive summary

- **Files evaluated:** 184
- **Inference errors:** 0
- **Role recommendation:** **reject**

- **Clean human accepted:** 1 (false alarms: 22, borderline: 0)
- **Direct AI detected / segment-suspicious:** 18
- **Partial fabrication detected:** 45

## 2. Class convention (from predictions)

- **spoof_class_index_used:** 0
- **bonafide_class_index_used:** 1
- **class_convention_source:** `official_aasist_label_mapping`
- **class_convention_warning:** `nan`

## 3. Phase 7E0 standalone gates

| metric | value | threshold | pass |
| --- | --- | --- | --- |
| clean_human_false_alarm | 22 | <= 7/23 | NO |
| direct_ai_detected_or_segment_suspicious | 18 | >= 15/23 | YES |
| ai_replay_detected_or_segment_suspicious | 23 | >= 15/23 | YES |
| human_replay_detected | 23 | >= 20/23 | YES |
| human_mixer_detected | 23 | >= 20/23 | YES |
| ai_mixer_detected | 23 | >= 20/23 | YES |
| partial_fabrication_detected | 45 | >= 40/46 | YES |


## 4. Branch-only gates

| metric | value | threshold | pass |
| --- | --- | --- | --- |
| direct_ai_detected_or_segment_suspicious | 18 | >= 15/23 | YES |
| clean_human_false_alarm | 22 | <= 10/23 | NO |


## 5. Status distribution

| aasist_status | count | % |
| --- | --- | --- |
| partial_fabrication_detected | 45 | 24.5% |
| ai_mixer_detected | 23 | 12.5% |
| ai_replay_detected | 23 | 12.5% |
| human_mixer_manipulation_detected | 23 | 12.5% |
| human_replay_manipulation_detected | 23 | 12.5% |
| clean_human_false_alarm | 22 | 12.0% |
| direct_ai_detected | 11 | 6.0% |
| direct_ai_file_level_missed_but_segment_suspicious | 7 | 3.8% |
| direct_ai_missed | 5 | 2.7% |
| partial_fabrication_missed | 1 | 0.5% |
| clean_human_accepted | 1 | 0.5% |


## Status traceability (read before interpreting counts)

- **`direct_ai_detected`** (and `ai_replay_detected`, `ai_mixer_detected`, `ai_processed_detected`): file-level mean spoof score crossed the threshold (`mean_spoof_score >= threshold_used`), or mean score reached the manipulation-detect floor.
- **`*_file_level_missed_but_segment_suspicious`**: file-level mean did **not** cross the threshold, but chunk/window evidence is strong (`max_spoof_score` or `suspicious_window_ratio` rules).
- **`expected_risk_binary=1`** / manifest **`risk_target=1`**: forensic-risk positive — **not** the same as “AI-generated”; includes replay, mixer, partial fabrication, and channel processing.

