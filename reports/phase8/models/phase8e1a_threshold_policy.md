# Phase 8E-1A Threshold Policy

## Policy Scope
This policy defines candidate-threshold selection for Phase 8E-1A analysis outputs. It does not define final deployment thresholds.

## Candidate Selection Rules
- Thresholds are reviewed on a predefined grid in [0, 1].
- Candidate selection prioritizes clean-side protection first, then positive detection and balanced accuracy.
- If no threshold satisfies clean-side protection, use `manual_review_only`.

## Origin Threshold Policy
- Objective: reduce clean-human false-AI evidence outputs.
- Constraint: `clean_human_false_ai_rate <= target_clean_fp_rate_origin`.
- Among qualifying thresholds, prefer higher balanced accuracy.

## Replay Threshold Policy
- Objective: reduce clean false replay outputs.
- Constraint: `clean_false_replay_rate <= target_clean_fp_rate_manipulation`.
- Among qualifying thresholds, prefer higher balanced accuracy while preserving replay detection.

## Mixer/Channel Threshold Policy
- Objective: reduce clean false mixer/channel outputs.
- Constraint: `clean_false_mixer_rate <= target_clean_fp_rate_manipulation`.
- Among qualifying thresholds, prefer higher balanced accuracy while preserving mixer detection.

## Abstention and Manual Review
- Low-confidence or conflicting evidence should trigger manual review, not hard automated claims.
- Candidate thresholds should be paired with abstention logic in later fusion planning.

## Anti-Collapse Principle
This policy explicitly prevents collapsing multi-axis evidence into binary fake/real decisions. Origin, replay, and mixer/channel axes remain distinct.
