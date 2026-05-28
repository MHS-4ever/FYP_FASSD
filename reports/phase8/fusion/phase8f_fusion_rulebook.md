# Phase 8F Fusion Rulebook

## Evidence Strength Levels
Allowed strength values:
- `not_evaluated`
- `low`
- `borderline`
- `moderate`
- `high`
- `unknown`

Interpretation:
- missing probability -> `not_evaluated`
- missing threshold -> `unknown`
- clearly below threshold -> `low`
- near threshold band -> `borderline`
- above threshold -> `moderate`
- well above threshold -> `high`

## Threshold and Margin Interpretation
- candidate thresholds come from Phase 8E-1A (file axes) and Phase 8E-3 threshold grid (segment axis)
- default margin band for borderline handling: `0.10`
- thresholds are experimental review parameters, not deployment locks

## Fusion Statuses
Allowed experimental statuses:
- `accept_human_clean_experimental`
- `suspicious_origin_experimental`
- `suspicious_replay_experimental`
- `suspicious_mixer_channel_experimental`
- `suspicious_partial_fabrication_experimental`
- `suspicious_mixed_evidence_experimental`
- `inconclusive_manual_review_experimental`

## Risk Levels
Allowed risk levels:
- `low`
- `medium`
- `high`
- `inconclusive`

## Manual Review Triggers
Manual review is required when:
- any axis is `borderline`
- partial axis is `moderate` or `high`
- multiple axes are elevated simultaneously
- status is `inconclusive_manual_review_experimental`
- risk is `inconclusive`
- any `suspicious_*_experimental` status is assigned
- reason contains `insufficient_evidence_review`

Manual review is not required solely because an axis is `not_evaluated` in retrospective OOF fusion.

Manual review may be `false` only when all are true:
- status is `accept_human_clean_experimental`
- risk is `low`
- no evaluated axis is elevated or borderline
- reason is `none`

## Conflict Rules
- replay evidence does not imply AI-origin by itself
- mixer/channel evidence does not imply AI-origin by itself
- high replay or high mixer with low origin AI should remain manipulation-focused, not auto-origin-AI
- multiple elevated axes map to mixed-evidence status and manual review

## Examples
- **AI-origin only:** origin high, replay/mixer/partial low -> `suspicious_origin_experimental`
- **Replay only:** replay high, origin low -> `suspicious_replay_experimental`
- **Mixer only:** mixer high, origin low -> `suspicious_mixer_channel_experimental`
- **Partial only:** partial high -> `suspicious_partial_fabrication_experimental` + manual review
- **Mixed:** origin high + replay high, or partial + another high axis -> `suspicious_mixed_evidence_experimental`
- **Inconclusive:** mostly missing/borderline evidence -> `inconclusive_manual_review_experimental`

## Retrospective OOF Note
Phase 8F retrospective fusion merges model outputs from task-specific evaluation sets.  
Therefore, missing axis values are valid and must remain `not_evaluated` rather than being promoted to suspicious evidence.
