# Phase 8 Fusion Summary

## Fusion Inputs
- Phase 8E-1 file-level OOF evidence outputs
- Phase 8E-1A threshold recommendations
- Phase 8E-3 segment-level outputs
- Phase 8E-2 top candidate segments

## Accepted Fusion Statuses
- accept_human_clean_experimental
- suspicious_origin_experimental
- suspicious_replay_experimental
- suspicious_mixer_channel_experimental
- suspicious_partial_fabrication_experimental
- suspicious_mixed_evidence_experimental
- inconclusive_manual_review_experimental

## Risk Levels
- low, medium, high, inconclusive

## Manual Review Rules
Manual review is required for suspicious or inconclusive outcomes, borderline evidence, and multi-axis conflicts.

## Final Phase 8F Distribution
- status_distribution: `{"suspicious_partial_fabrication_experimental": 46, "suspicious_mixer_channel_experimental": 46, "suspicious_replay_experimental": 45, "suspicious_origin_experimental": 23, "accept_human_clean_experimental": 20, "inconclusive_manual_review_experimental": 4}`
- manual_review_required_count: `164`

## Safe Interpretation Notes
- replay high does not mean AI-origin
- mixer high does not mean AI-origin
- partial high needs timestamp/segment context and manual review
- missing axes are `not_evaluated` in retrospective OOF fusion
