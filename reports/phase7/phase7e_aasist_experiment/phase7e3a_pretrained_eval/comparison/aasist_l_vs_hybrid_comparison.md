# Phase 7E3A — AASIST-L vs HybridResNet (Phase 7C1)

**Generated:** 2026-05-26T20:24:58.075899+00:00

## Aggregate metrics

| metric | hybrid_baseline | aasist_l | delta (AASIST − Hybrid) |
| --- | --- | --- | --- |
| clean_human_false_alarm | 17 | 22 | 5 |
| clean_human_accepted | 4 | 1 | -3 |
| direct_ai_detected_or_segment_suspicious | 19 | 18 | -1 |
| ai_replay_detected_or_segment_suspicious | 23 | 23 | 0 |
| human_replay_detected | 23 | 23 | 0 |
| human_mixer_detected | 23 | 23 | 0 |
| ai_mixer_detected | 23 | 23 | 0 |
| partial_fabrication_detected | 43 | 45 | 2 |

## Per-sample highlights

- AASIST better on direct AI (hybrid missed): **3**
- AASIST worse on clean human (new false alarm): **5**
- Hybrid better on direct AI (AASIST missed): **4**

