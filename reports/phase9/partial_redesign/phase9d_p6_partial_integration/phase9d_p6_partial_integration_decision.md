# Phase 9D-P6 — Partial cascade integration decision

Generated: 2026-06-02T19:53:03.430+00:00

**Packaging mode:** apply

## Decision summary

The accepted P5B/P5F partial-fabrication cascade is packaged for **experimental / manual-review integration** into the Phase 9 live report contract. This is experimental integration packaging only — not operational deployment packaging.

## Why we stop tuning on the 10 fabricated_20pct files

- The 10 `fabricated_20pct` files are a small, controlled holdout used for evaluation and diagnostics.
- Further threshold tuning on the same 10 files would overfit holdout metrics and inflate claims.
- P5F-P2 documented root causes (file-gate miss, segment-threshold miss) without changing thresholds.

## What is packaged

- Target directory: `E:\FYP\release\models\partial_fabrication_experimental_p5b`
- P5B candidate file gate, segment localizer v2, and cascade config (unchanged thresholds).
- `partial_module_metadata.json`, `partial_report_contract.json`, `partial_validation_summary.json`.
- README and SHA256SUMS for integrity checks.

## What is not claimed

- Operational deployment claim: no.
- Legal-evidence claim: no.
- Conclusive authenticity decision: no.
- Partial-fabrication detection is **not** claimed to be fully solved.

## P5F / P5F-P2 evidence summary

- P5F evaluated files: 35
- failed_files: 0
- partial_file_count: 12
- fabricated_20pct files: 10
- fabricated_20pct recall: 0.7
- fabricated_20pct false negatives: 3
- non-partial false positives: 2
- broad_activation_rate_when_positive: 0.0

## Known limitations (preserved)

- 3/10 new fabricated_20pct false negatives remain (P5F-P1 holdout).
- 2 non-partial false positives remain on direct-labelled testing audio (P5F-P2).
- fabricated_20pct_recall = 0.70 on expanded P5F holdout.
- broad_activation_rate_when_positive = 0.0 in P5F metrics.
- Not optimized or tuned on the current 10 fabricated_20pct examples.
- This module provides an experimental evidence indicator only.
- Manual forensic review is recommended for any candidate segment.
- Top-k localization on detected timestamp-labelled positives is useful but not conclusive proof.

## Report wording contract

- Detected: experimental partial-fabrication evidence; candidate segment for manual review; conclusive authenticity decision: no.
- Not detected: does not prove authenticity; subtle partial manipulations may be missed.
- Unavailable: manual forensic review is recommended if partial manipulation is suspected.
- Overall summaries must use phrasing such as “Forensic evidence indicators were observed”; avoid conclusive synthetic/authentic labels.

See `phase9d_p6_report_contract.json` and `partial_report_contract.json` in the package.

## Phase 9E start condition

Phase 9E implementation is **not started in P6**. After P6 validation PASS, Phase 9E may start using this module as an **experimental/manual-review partial-fabrication evidence axis** only.

## Packaging manifest (planned actions)

- copy: `partial_file_gate__ssl__p5b_experimental_candidate.joblib` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- copy: `partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- copy: `partial_cascade_config__p5b_experimental_candidate.json` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_cascade_config__p5b_experimental_candidate.json`
- write: `partial_module_metadata.json` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_module_metadata.json`
- write: `partial_report_contract.json` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_report_contract.json`
- write: `partial_validation_summary.json` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\partial_validation_summary.json`
- write: `README_partial_fabrication_experimental.md` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\README_partial_fabrication_experimental.md`
- write: `SHA256SUMS.txt` (exists=True) → `E:\FYP\release\models\partial_fabrication_experimental_p5b\SHA256SUMS.txt`
