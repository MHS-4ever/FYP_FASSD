# Replay Retrain Decision

Generated: 2026-06-13

## Summary

An experimental replay retrain was run after mixer retrain attempts were frozen.

Output directory:

- `reports/release_audit/replay_retrain_experimental_2026-06-13`

The retrain used leakage-safe Phase 7 data and treated `clean_direct` and `mixer_processed` as replay negatives. `testing_audios` was evaluation-only.

## Result

Internal Phase 7 metrics were strong:

- Dev balanced accuracy: `0.9500`
- Test balanced accuracy: `0.9750`
- Test replay recall: `1.0000`
- Test specificity: `0.9500`

External `testing_audios` remained imperfect:

- Balanced accuracy: `0.8167`
- Replay recall: `0.8000`
- Specificity: `0.8333`
- Precision: `0.5714`

## External Errors

- `T2.2`: human mixer processed, false replay positive, probability `0.9986`.
- `T3.2`: AI replay, false negative, probability `0.9494` below selected threshold `0.95`.
- `T3.4`: AI mixer processed, false replay positive, probability `0.9964`.
- `T5.5`: human edited/processed, false replay positive, probability `0.9666`.

## Decision

Do not replace the release replay model with this experimental retrain.

This result shows the replay model still confuses real-world mixer/edited-channel artifacts with replay, while the one missed AI replay is mostly a threshold-margin issue.

## Recommended Next Step

Do not continue blind replay retraining yet.

The next technical step should be a joint replay-vs-channel diagnosis:

- Compare failed replay positives/negatives against replay, mixer, clean, and edited groups.
- Add `edited_spliced` and stronger mixer/channel negatives to replay training.
- Consider a two-stage manipulation classifier: first detect "channel/manipulation present", then separate replay vs mixer/channel vs edit.

MP4 files remain unevaluated by the release audio I/O and should be handled separately.
