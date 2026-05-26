# Phase 7E3A — AASIST-L Pretrained Analysis (phase7a holdout)

**Generated:** 2026-05-26T20:24:51.195984+00:00
**Model:** pretrained AASIST-L (no fine-tuning)

## 1. Executive summary

- **Files evaluated:** 25
- **Inference errors:** 2
- **Role recommendation:** **holdout_review** (7A does not use 7C1 standalone/branch-only gates)

## 2. Class convention (from predictions)

- **spoof_class_index_used:** 0
- **bonafide_class_index_used:** 1
- **class_convention_source:** `official_aasist_label_mapping`
- **class_convention_warning:** `nan`

## 3. Holdout category summary

| metric | count |
| --- | --- |
| clean_human_accepted | 1 |
| clean_human_false_alarm | 2 |
| clean_human_borderline | 0 |
| direct_ai_detected | 5 |
| direct_ai_missed | 0 |
| direct_ai_detected_or_segment_suspicious | 5 |
| human_processed_detected | 0 |
| human_processed_missed | 0 |
| ai_processed_detected | 1 |
| ai_processed_missed | 0 |
| ai_processed_detected_or_segment_suspicious | 1 |
| human_replay_detected | 3 |
| human_replay_missed | 0 |
| ai_replay_detected | 2 |
| ai_replay_missed | 0 |
| ai_replay_detected_or_segment_suspicious | 2 |
| ai_processed_detected_or_segment_suspicious | 1 |
| partial_fabrication_detected | 2 |
| partial_fabrication_missed | 0 |
| partial_fabrication_not_evaluable | 0 |


## 4. Full status distribution

| aasist_status | count | % |
| --- | --- | --- |
| direct_ai_detected | 5 | 20.0% |
| unknown_review_required | 5 | 20.0% |
| human_replay_manipulation_detected | 3 | 12.0% |
| clean_human_false_alarm | 2 | 8.0% |
| ai_replay_detected | 2 | 8.0% |
| partial_fabrication_detected | 2 | 8.0% |
| clean_human_accepted | 1 | 4.0% |
| human_mixer_manipulation_detected | 1 | 4.0% |
| ai_mixer_detected | 1 | 4.0% |
| ai_processed_detected | 1 | 4.0% |


## 5. Interpretation

Compare holdout behavior to Phase 7C1 and HybridResNet product CSV before any 7E3B fine-tune decision. Do **not** apply Phase 7C1 numeric acceptance gates directly to this holdout set.

## Status traceability (read before interpreting counts)

- **`direct_ai_detected`** (and `ai_replay_detected`, `ai_mixer_detected`, `ai_processed_detected`): file-level mean spoof score crossed the threshold (`mean_spoof_score >= threshold_used`), or mean score reached the manipulation-detect floor.
- **`*_file_level_missed_but_segment_suspicious`**: file-level mean did **not** cross the threshold, but chunk/window evidence is strong (`max_spoof_score` or `suspicious_window_ratio` rules).
- **`expected_risk_binary=1`** / manifest **`risk_target=1`**: forensic-risk positive — **not** the same as “AI-generated”; includes replay, mixer, partial fabrication, and channel processing.

