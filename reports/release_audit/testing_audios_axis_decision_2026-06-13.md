# Testing Audios Axis Decision

Generated: 2026-06-13

## Inputs Reviewed

- `reports/release_audit/testing_audios_origin_augmented_eval_2026-06-13/testing_audios_augmented_origin_eval_report.md`
- `reports/release_audit/testing_audios_replay_mixer_eval_2026-06-13/testing_audios_replay_mixer_metrics.csv`
- `reports/release_audit/testing_audios_replay_mixer_eval_2026-06-13/testing_audios_replay_mixer_errors.csv`
- `reports/release_audit/testing_audios_replay_mixer_eval_2026-06-13/testing_audios_replay_mixer_predictions.csv`
- `reports/release_audit/testing_audios_partial_subset_eval_2026-06-13/testing_audios_partial_subset_predictions.csv`

## Axis Results

### Origin

The augmented origin model is improved but not release-ready.

- Binary human/AI rows: `n=23`
- Accuracy: `0.8696`
- Balanced accuracy: `0.8731`
- AI recall: `0.9000`
- Human specificity: `0.8462`
- Remaining failures:
  - `T1.2`: clean English human false positive.
  - `T4.1`: clean English human false positive.
  - `T4.5`: compressed AI false negative.

Decision:

- Do not replace the release origin model yet.
- Origin needs targeted hard negatives for clean English human speech and hard positives for compressed/platform AI.

### Replay

Replay is imperfect but not the worst axis.

- Supported binary rows: `n=21`
- Accuracy: `0.8095`
- Balanced accuracy: `0.8063`
- Recall: `0.8000`
- Specificity: `0.8125`
- Errors:
  - False positives: `T2.2` human mixer, `T3.4` AI mixer, `T4.1` clean English human.
  - False negative: `T3.2` AI replay.
- Unsupported release I/O cases:
  - `T2.4` MP4 human replay.
  - `T3.3` MP4 AI replay.

Decision:

- Replay needs focused improvement, but not generic augmentation first.
- The failure pattern suggests replay/mixer confusion and AI-replay/channel diversity gaps.
- Add MP4/audio loading support or preprocess MP4 to audio before judging replay coverage as complete.

### Mixer / Channel

Mixer/channel is the clearest file-axis failure.

- Supported binary rows: `n=21`
- Accuracy: `0.8571`
- Balanced accuracy: `0.5000`
- Recall: `0.0000`
- Specificity: `1.0000`
- All three positive cases were missed:
  - `T2.2`: human mixer processed, probability `0.4510` below threshold `0.75`.
  - `T3.4`: AI mixer processed, probability `0.0106`.
  - `T4.5`: WhatsApp compressed AI, probability `0.0041`.

Decision:

- Mixer/channel is the first axis that should be retrained after evaluation.
- It needs more positive examples for real-world mixer, mobile, platform compression, and WhatsApp-style compression.
- It may also need threshold retuning because `T2.2` is near the current decision boundary while `T3.4` and `T4.5` are far below it.

### Partial

Partial has a design failure, not a simple data-augmentation problem.

Subset rows:

- True partials:
  - `T4.3`: raw partial max `1.0`, but global activation, fusion-ineligible. Ground-truth window `35s-58s`; top candidate incorrectly `2s-6s`.
  - `T5_FAB_001`: raw partial max `1.0`, fusion-eligible. Ground-truth window `14s-21s`; top candidate `12s-16s`, partially overlaps.
- Negatives:
  - `T1.2`: clean English human, raw partial max `1.0`, global activation.
  - `T2.3`: human replay, raw partial max near `1.0`, fusion-eligible false positive.
  - `T3.2`: AI replay, raw partial max `1.0`, fusion-eligible false positive.
  - `T3.4`: AI mixer, raw partial max near `1.0`, later blocked by replay/mixer arbitration.

Decision:

- Do not retrain partial with augmentation yet.
- Redesign the partial localization method before training.
- The current raw segment model cannot distinguish true localized AI inserts from replay/channel/clean-speech contrast.

## Recommended Sequence From Here

1. Fix/retrain mixer/channel first, because it has `0.0` recall on positive mixer/compression cases.
2. Keep origin as experimental until hard clean-English human negatives and compressed-AI positives are added.
3. Improve replay after mixer, focusing on replay-vs-mixer confusion and AI replay diversity.
4. Redesign partial localization before retraining partial; simple augmentation is likely to strengthen the wrong behavior.

## Do Not Do Yet

- Do not retrain all models together.
- Do not add augmentation to every axis.
- Do not treat partial raw max probability as reliable file-level partial evidence.
- Do not judge replay coverage complete until MP4 inputs are handled or converted.
