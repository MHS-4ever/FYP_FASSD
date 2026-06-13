# Phase 3B — Window-level origin decision

- Started: 2026-06-13T11:04:32.020602+00:00
- Finished: 2026-06-13T11:05:49.807962+00:00
- Fixed: promoted origin model, threshold=0.92, cached segment SSL
- Variable: segment-to-file aggregation

| Aggregator | Phase7 test bal-acc | Testing bal-acc | Beats file mean? |
|---|---:|---:|---|
| file_mean_ssl | 0.9500 | nan | baseline |
| segment_max_prob | 0.8500 | nan | no |
| segment_top3_mean_prob | 0.9000 | nan | no |
| segment_noisy_or_max | 0.8500 | nan | no |

## Decision

**Do not pursue window-level origin into Phase 4.** No aggregator beat file-mean SSL on both decision metrics.
