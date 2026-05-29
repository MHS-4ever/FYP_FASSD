# Phase 9D-P4 Partial Timestamp Diagnostic Report

- Generated: 2026-05-29T17:48:37.084083+00:00
- Scope: **evaluation-only timestamp comparison** (timestamps never used as live inference input)

## Purpose

Compare live segment-level partial probabilities against true fabricated timestamp regions
from Phase 7C1 annotations. This is diagnostic architecture verification, not final forensic proof.

## Summary

- Total fabricated files: 46
- AI fabricated: 23
- Human fabricated: 23
- Localized success (top-1 inside region): 0
- Top-5 timestamp hit count: 36
- Broad activation cases: 46
- No timestamp hit: 0

## AI fabricated behavior

- Top-5 hit rate: 65.2%
- Broad activation rate: 100.0%

- `ai_001_fabricated`: label=broad_activation_not_localized, top5_inside=False, gate=global_activation_not_localized
- `ai_002_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `ai_003_fabricated`: label=broad_activation_not_localized, top5_inside=False, gate=global_activation_not_localized
- `ai_004_fabricated`: label=broad_activation_not_localized, top5_inside=False, gate=global_activation_not_localized
- `ai_005_fabricated`: label=broad_activation_not_localized, top5_inside=False, gate=global_activation_not_localized
- `ai_006_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `ai_007_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `ai_008_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized

## Human fabricated behavior

- Top-5 hit rate: 91.3%
- Broad activation rate: 100.0%

- `human_001_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_002_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_003_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_004_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_005_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_006_fabricated`: label=broad_activation_not_localized, top5_inside=False, gate=global_activation_not_localized
- `human_007_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized
- `human_008_fabricated`: label=topk_hits_but_broad_activation, top5_inside=True, gate=global_activation_not_localized

## Top-k timestamp hit results

Timestamp hit rate measures whether high-probability segments overlap the annotated fabricated region.
This supports manual review planning only — not confirmed fake segment claims.

## Broad activation results

Broad activation indicates the partial segment model scores many segments similarly high,
preventing localized partial-fabrication fusion eligibility under current gates.

## Boundary / splice findings

- `p4_ai_fabricated_ai_001_fabricated` start_boundary: nearest_p=0.9999999999999967, strength=0.0
- `p4_ai_fabricated_ai_001_fabricated` end_boundary: nearest_p=0.9999999999999325, strength=0.0
- `p4_ai_fabricated_ai_002_fabricated` start_boundary: nearest_p=1.0, strength=0.0
- `p4_ai_fabricated_ai_002_fabricated` end_boundary: nearest_p=1.0, strength=0.0
- `p4_ai_fabricated_ai_003_fabricated` start_boundary: nearest_p=0.017282971351071028, strength=-0.4091
- `p4_ai_fabricated_ai_003_fabricated` end_boundary: nearest_p=0.999999997290157, strength=0.0
- `p4_ai_fabricated_ai_004_fabricated` start_boundary: nearest_p=0.9999999922847257, strength=0.0
- `p4_ai_fabricated_ai_004_fabricated` end_boundary: nearest_p=1.0, strength=0.0
- `p4_ai_fabricated_ai_005_fabricated` start_boundary: nearest_p=0.9999999999867553, strength=0.0
- `p4_ai_fabricated_ai_005_fabricated` end_boundary: nearest_p=1.0, strength=0.0
- `p4_ai_fabricated_ai_006_fabricated` start_boundary: nearest_p=0.9999999999858504, strength=0.0
- `p4_ai_fabricated_ai_006_fabricated` end_boundary: nearest_p=1.0, strength=0.0

## Conclusion

- **Recommendation:** `segment_retraining_with_non_partial_negatives_and_file_level_partial_candidate`
- Broad activation dominates; segment retraining with non-partial negatives plus a file-level partial candidate model is likely needed.

### Next steps (choose based on diagnostic rates)

- **Gate tuning only:** if localized_success and top-5 hits are frequent but fusion gates are conservative.
- **File-level partial candidate model:** if segment scores vary but file-level localization remains weak.
- **Segment retraining with non-partial negatives:** if broad activation dominates across fabricated files.
- **Splice/boundary indicator:** if boundary_only_signal is frequent near insert_start/end.

Phase 9E apps may proceed after documenting this limitation; optional Phase 9D-P4 follow-up tuning is separate.

## Safety

- No single binary authenticity score was produced.
- Timestamps used for evaluation only, never as model inputs.
- Avoid terms like perfect detector or confirmed fake segment.

