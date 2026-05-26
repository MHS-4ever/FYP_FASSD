# Phase 7C2 test — Fine-tuned Model Evaluation (clip cache)

- Rows: **232**

## Overall (masked)

- Origin accuracy: `0.5659340659340659`
- Attack accuracy: `0.37280701754385964`

## By data_source

### old (n=200)
- Origin acc: `0.6133333333333333`
- Attack acc: `0.39`

### phase7c1 (n=32)
- Origin acc: `0.34375`
- Attack acc: `0.25`

## Category metrics (7C1-style on 4s window)

## Limits

- Not full-file pct_vote; partial region eval needs 7C1 baseline runner.

### old
- clean_human_acceptance: 0.94
- clean_human_n: 50
- direct_ai_detection: 0.45
- direct_ai_n: 100

### phase7c1
- clean_human_acceptance: 0.5
- clean_human_n: 4
- direct_ai_detection: 0.75
- direct_ai_n: 4
- human_replay_origin_not_fake: 0.75
