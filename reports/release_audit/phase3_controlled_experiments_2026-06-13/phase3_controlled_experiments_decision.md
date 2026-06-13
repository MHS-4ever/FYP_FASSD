# Phase 3 — Controlled experiments (combined decision)

- Started: 2026-06-13T13:10:58.561648+00:00
- Finished: 2026-06-13T13:11:01.674699+00:00
- Order: 3A (resampling) → 3B (window origin) → 3C (dual-resolution replay/mixer)
- New audio collected: **No**

## Experiment decisions

### 3A Resampling ablation

# Phase 3A — Resampling ablation decision

- Started: 2026-06-13T13:11:00.954701+00:00
- Finished: 2026-06-13T13:11:01.548647+00:00
- Fixed model: promoted Phase 2 origin (`threshold=0.92`)
- Fixed split: leakage-safe `base_id` manifest
- Variable: SSL front-end resampling chain (WavLM input always 16 kHz)

## Summary table

| Variant | Phase7 test bal-acc | Testing bal-acc | Phase7 test FPR | Beats 16 kHz? |
|---|---:|---:|---:|---|
| ssl_16k_direct | 0.9500 | 0.8500 | 0.0000 | baseline |
| ssl_chain_8k_16k | 0.9250 | 0.8286 | 0.0000 | no |
| ssl_chain_12k_16k | 0.9500 | 0.8286 | 0.0000 | no |
| ssl_chain_22_05k_16k | 0.9500 | 0.8786 | 0.0000 | no |
| ssl_chain_24k_16k | 0.9500 | 0.8786 | 0.0000 | no |
| ssl_roundtrip_16_8_16 | 0.9250 | 0.8286 | 0.0000 | no |

## Decision

**CLOSE resampling question permanently in thesis.** No alternative chain beat `ssl_16k_direct` on both leakage-safe test and testing_audios.


### 3B Window-level origin

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


### 3C Dual-resolution replay/mixer

# Phase 3C — Dual-resolution replay/mixer decision

- Started: 2026-06-13T11:06:05.442881+00:00
- Finished: 2026-06-13T11:16:47.611037+00:00
- Fixed: leakage-safe split, sklearn LR pipeline, no release model overwrite
- Variable: 16 kHz acoustic only vs 16 kHz + native high-band ratios

| Axis | Feature mode | Phase7 test bal-acc | Testing bal-acc | Beats baseline? |
|---|---|---:|---:|---|
| replay | baseline | 0.9667 | 0.5635 | baseline |
| replay | dual | 0.9667 | 0.5635 | baseline |
| mixer | baseline | 1.0000 | 0.4565 | baseline |
| mixer | dual | 1.0000 | 0.4565 | baseline |

## Decision

**Do not pursue dual-resolution replay/mixer into Phase 4.** Native high-band add-on did not beat 16 kHz-only acoustics on both decision metrics.

