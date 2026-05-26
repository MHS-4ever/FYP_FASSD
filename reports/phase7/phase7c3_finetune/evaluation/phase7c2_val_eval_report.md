# Phase 7C2 val — Fine-tuned Model Evaluation (clip cache)

- Rows: **224**

## Overall (masked)

- Origin accuracy: `0.6379310344827587`
- Attack accuracy: `0.4343891402714932`

## By data_source

### old (n=200)
- Origin acc: `0.6733333333333333`
- Attack acc: `0.44`

### phase7c1 (n=24)
- Origin acc: `0.4166666666666667`
- Attack acc: `0.38095238095238093`

## Category metrics (7C1-style on 4s window)

## Limits

- Not full-file pct_vote; partial region eval needs 7C1 baseline runner.

### old
- clean_human_acceptance: 0.96
- clean_human_n: 50
- direct_ai_detection: 0.53
- direct_ai_n: 100

### phase7c1
- clean_human_acceptance: 0.6666666666666666
- clean_human_n: 3
- direct_ai_detection: 0.3333333333333333
- direct_ai_n: 3
- human_replay_origin_not_fake: 0.6666666666666666
