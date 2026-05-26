# Phase 7C4 Threshold Sweep Report

Re-evaluates Phase 7C1 `baseline_status` from existing scores (no model re-run).

- Configurations tested: **324**

## Default baseline metrics (vote=0.70, segment_max=0.95, ratio=0.30)

- Clean human accept: 4 / 23
- Clean human false alarms: 17
- Direct AI detected + segment-suspicious: 0 + 19
- Product score: 0.7522

## Top 10 configurations by product_score (all sources)

| source | vote | seg_max | chunk_ratio | product_score | ch_fp | partial_det |
| --- | --- | --- | --- | --- | --- | --- |
| candidate_ensemble | 0.80 | 0.85 | 0.10 | 0.7913 | 15 | 44 |
| candidate_ensemble | 0.80 | 0.90 | 0.10 | 0.7913 | 15 | 44 |
| baseline | 0.80 | 0.90 | 0.10 | 0.7870 | 14 | 43 |
| baseline | 0.80 | 0.95 | 0.10 | 0.7870 | 14 | 43 |
| baseline | 0.80 | 0.85 | 0.10 | 0.7870 | 14 | 43 |
| candidate_ensemble | 0.75 | 0.85 | 0.10 | 0.7826 | 17 | 44 |
| candidate_ensemble | 0.40 | 0.90 | 0.10 | 0.7826 | 22 | 44 |
| candidate_ensemble | 0.40 | 0.85 | 0.10 | 0.7826 | 22 | 44 |
| candidate_ensemble | 0.80 | 0.85 | 0.30 | 0.7826 | 15 | 44 |
| candidate_ensemble | 0.80 | 0.90 | 0.30 | 0.7826 | 15 | 44 |

## Best for `baseline`

| vote | seg_max | ratio | product | ch_acc | ch_fp | direct_ai+ | partial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.80 | 0.95 | 0.10 | 0.7870 | 7 | 14 | 20 | 43 |
| 0.80 | 0.85 | 0.10 | 0.7870 | 7 | 14 | 20 | 43 |
| 0.80 | 0.90 | 0.10 | 0.7870 | 7 | 14 | 20 | 43 |
| 0.80 | 0.95 | 0.20 | 0.7783 | 7 | 14 | 19 | 43 |
| 0.80 | 0.90 | 0.20 | 0.7783 | 7 | 14 | 19 | 43 |

## Best for `r2_product`

| vote | seg_max | ratio | product | ch_acc | ch_fp | direct_ai+ | partial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.80 | 0.95 | 0.10 | 0.6957 | 17 | 3 | 16 | 33 |
| 0.80 | 0.85 | 0.10 | 0.6957 | 17 | 3 | 16 | 33 |
| 0.80 | 0.90 | 0.10 | 0.6957 | 17 | 3 | 16 | 33 |
| 0.75 | 0.90 | 0.10 | 0.6870 | 16 | 4 | 16 | 33 |
| 0.75 | 0.85 | 0.10 | 0.6870 | 16 | 4 | 16 | 33 |

## Best for `r2_loss`

| vote | seg_max | ratio | product | ch_acc | ch_fp | direct_ai+ | partial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.80 | 0.85 | 0.10 | 0.7087 | 16 | 4 | 17 | 36 |
| 0.80 | 0.85 | 0.20 | 0.7087 | 16 | 4 | 17 | 36 |
| 0.80 | 0.85 | 0.30 | 0.7087 | 16 | 4 | 17 | 36 |
| 0.80 | 0.90 | 0.10 | 0.7087 | 16 | 4 | 17 | 36 |
| 0.80 | 0.95 | 0.10 | 0.7000 | 16 | 4 | 16 | 36 |

## Best for `candidate_ensemble`

| vote | seg_max | ratio | product | ch_acc | ch_fp | direct_ai+ | partial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.80 | 0.85 | 0.10 | 0.7913 | 6 | 15 | 21 | 44 |
| 0.80 | 0.90 | 0.10 | 0.7913 | 6 | 15 | 21 | 44 |
| 0.80 | 0.95 | 0.10 | 0.7826 | 6 | 15 | 20 | 44 |
| 0.40 | 0.90 | 0.10 | 0.7826 | 1 | 22 | 21 | 44 |
| 0.80 | 0.85 | 0.20 | 0.7826 | 6 | 15 | 20 | 44 |


## Notes

- Sweep varies file-level vote and segment thresholds only; chunk spoof scores are fixed from saved CSVs.
- `candidate_ensemble` uses max(decision_score) and max(chunk metrics) across baseline + R2 product + R2 loss.
- Threshold sweep alone cannot recover all baseline partial/replay strength; see decision layer (7C4 script 3).
