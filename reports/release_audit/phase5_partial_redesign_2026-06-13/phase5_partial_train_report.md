# Phase 5 — Partial segment localizer (no F9)

Generated: 2026-06-13T13:43:53.052894+00:00

Segment threshold (dev oracle grid): `0.95`
Model features: `791` (F9 removed)
Training segments: `2357` (130 positive)

## Oracle summary (leakage-safe test)

- partial files: 10
- top-5 hit rate: 1.0000
- localized rate (top5 + not broad): 1.0000
- clean broad-activation rate: 0.0000

## Stop rule (test top-5 hit >= 50%)

- **PASS**

## Dev oracle

- top-5 hit: 1.0000
- localized: 1.0000
