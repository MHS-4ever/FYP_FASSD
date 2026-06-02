# Partial fabrication experimental module (P5B / P5F)

**Status:** `experimental_manual_review_only`  
**Module:** `partial_fabrication_experimental_p5b`

## What this package is

This directory contains the **accepted P5B experimental partial-fabrication cascade** packaged for
Phase 9 live/demo integration as one **evidence axis**. This module provides an experimental evidence
indicator only. Manual forensic review is recommended.

## Deployment and evidence claims

- Operational deployment claim: no.
- Legal-evidence claim: no.
- Conclusive authenticity decision: no.

## What this package is not

- Not tuned further on the 10 `fabricated_20pct` holdout files in P5F-P1.
- Not a claim that partial-fabrication detection is fully solved.
- Not a replacement for manual forensic review.

## Artifacts

- File gate (SSL): `partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- Segment localizer v2 (combined): `partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- Cascade config: `partial_cascade_config__p5b_experimental_candidate.json`
- `partial_module_metadata.json`, `partial_report_contract.json`, `partial_validation_summary.json`

## Accepted thresholds (unchanged)

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

## Known limitations (P5F / P5F-P2)

- fabricated_20pct recall ≈ 0.7
- fabricated_20pct false negatives: 3
- non-partial false positives: 2
- broad_activation_rate_when_positive: 0.0

## Report contract

See `partial_report_contract.json` for the `partial_fabrication` JSON section used by Phase 9E demo
integration. User-facing wording avoids conclusive authenticity decisions.

Packaged by Phase 9D-P6 on 2026-06-02T19:53:03.493+00:00.
