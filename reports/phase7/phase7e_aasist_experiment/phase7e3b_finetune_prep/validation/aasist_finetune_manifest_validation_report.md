# Phase 7E3B — AASIST Fine-Tune Manifest Validation (hardened)

**Generated:** 2026-05-26T20:54:42.440041+00:00
**Verdict:** **PASS_WITH_WARNINGS**

- Issues: **0**
- Warnings: **3**

## Row counts

| split | rows |
| --- | --- |
| train | 1320 |
| val | 260 |
| test | 280 |
| total | 1860 |


## risk_target counts (unweighted)

### train
| risk_target | count |
| --- | --- |
| 0 | 298 |
| 1 | 1022 |


### val
| risk_target | count |
| --- | --- |
| 0 | 59 |
| 1 | 201 |


### test
| risk_target | count |
| --- | --- |
| 0 | 62 |
| 1 | 218 |


## Weighted risk balance (sum of sample_weight)

| split | weighted_risk_0 | weighted_risk_1 | ratio_1_to_0 | ratio_0_to_1 |
| --- | --- | --- | --- | --- |
| train | 442.0 | 1358.0 | 3.07 | 0.33 |
| val | 86.0 | 264.0 | 3.07 | 0.33 |
| test | 98.0 | 302.0 | 3.08 | 0.32 |


Warn if either weighted ratio exceeds **3.0** (class imbalance after weighting).

## Role distribution (train)

| source_branch_role | count |
| --- | --- |
| old_bonafide | 250 |
| old_synthesis | 250 |
| old_conversion | 250 |
| old_replay | 250 |
| direct_ai | 48 |
| ai_mixer | 48 |
| ai_replay | 48 |
| clean_human | 48 |
| human_mixer | 48 |
| human_replay | 48 |
| partial_fabrication | 32 |


## Clean-human window summary

| split | window_count | total_sample_weight |
| --- | --- | --- |
| train | 48 | 192.0 |
| val | 9 | 36.0 |
| test | 12 | 48.0 |


## Training readiness note

Manifest validation PASS does **not** mean training is ready. Review `AASIST_L_FINETUNE_TRAINING_PLAN.md`: **do not use plain weighted CE only** — require balanced sampler and/or class-balanced loss.

## Checks performed

1. Required columns
2. `aasist_label` vs `risk_target` (0→1 bonafide, 1→0 spoof)
3. Weighted class balance per split
4. Clean-human count and weight per split
5. Holdout leak, audio paths, partial timestamps, split leakage

## Warnings

- `{'check': 'weighted_balance', 'split': 'train', 'detail': 'weighted risk_target=1:0 ratio=3.07 > 3.0'}`
- `{'check': 'weighted_balance', 'split': 'val', 'detail': 'weighted risk_target=1:0 ratio=3.07 > 3.0'}`
- `{'check': 'weighted_balance', 'split': 'test', 'detail': 'weighted risk_target=1:0 ratio=3.08 > 3.0'}`

