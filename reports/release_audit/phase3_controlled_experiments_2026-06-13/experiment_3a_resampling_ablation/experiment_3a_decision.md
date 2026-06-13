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
