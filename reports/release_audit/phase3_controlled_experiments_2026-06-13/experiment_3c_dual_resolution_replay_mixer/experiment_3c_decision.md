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
