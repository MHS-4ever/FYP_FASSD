# Testing Audios Separate Axis Evaluation Checkpoint

Generated: 2026-06-13

## Scope

This checkpoint follows the requested sequence: evaluation first, not retraining. The axes are considered separately:

- Origin: AI vs human on `testing_audios`.
- Replay: replay/rerecording evidence only.
- Mixer/channel: mixer/compression/channel evidence only.
- Partial: segment-level partial localization evidence only.

## Completed Evidence

### Origin Axis

Origin evaluation completed on all 25 testing-audio rows in:

- `reports/release_audit/testing_audios_origin_augmented_eval_2026-06-13/testing_audios_augmented_origin_eval_report.md`
- `reports/release_audit/testing_audios_origin_augmented_eval_2026-06-13/testing_audios_origin_metrics.csv`
- `reports/release_audit/testing_audios_origin_augmented_eval_2026-06-13/testing_audios_augmented_origin_predictions.csv`

Main result on binary human/AI rows:

- Augmented origin model: 23 rows, accuracy `0.8696`, balanced accuracy `0.8731`, recall on AI `0.9000`, specificity on human `0.8462`.
- Remaining errors at threshold `0.5`: `T1.2` clean English human false positive, `T4.1` clean English human false positive, `T4.5` compressed AI false negative.

Interpretation:

- The origin axis improved compared with the packaged release model for processed/replayed AI.
- The origin axis still fails on clean English human hard negatives and compression-aware AI positives.
- Do not retrain all axes because this failure is specific to origin data coverage.

### Replay Axis

Release-pipeline replay outputs were cached for 17 files before the full pipeline became too slow on long/partial cases:

- `reports/release_audit/testing_audios_separate_axis_eval_2026-06-13/raw_pipeline_json/`

Observed replay evidence from cached rows:

- `T2.1` human replay Urdu: replay probability `0.9667`, threshold `0.65`, detected.
- `T2.3` human replay Urdu: replay probability `0.9956`, threshold `0.65`, detected.
- `T3.2` AI replay English: replay probability `0.2185`, threshold `0.65`, missed.
- `T3.5` AI replay English: replay probability `0.9170`, threshold `0.65`, detected.

Interpretation:

- Replay is not uniformly broken: it catches several replay examples strongly.
- It does show at least one AI-replay miss (`T3.2`), so replay should receive a focused evaluation pass next, not immediate retraining.
- If replay retraining becomes necessary, the evidence points toward AI-replay/channel diversity rather than generic augmentation.

### Mixer/Channel Axis

Cached mixer/channel evidence shows low probabilities on several non-mixer and replay files, which is expected. However, the axis still needs a complete run over all mixer/compression testing rows before any retraining decision.

Important origin result related to mixer/channel:

- `T3.4` AI mixer was recovered by the augmented origin model, but the release origin model missed it.
- `T4.5` compressed AI was missed by origin, so compression/channel coverage remains a real weakness.

Interpretation:

- Do not retrain mixer yet from this checkpoint alone.
- The next evaluation should complete mixer/channel scoring specifically for `mixer_processed` and `whatsapp_compressed` rows.

### Partial Axis

Partial evaluation exposed a stronger issue than ordinary model error:

- Full release-pipeline partial evaluation on long/segmented files became impractically slow and had to be stopped.
- Cached partial outputs show very high segment probabilities on non-partial replay/AI files.
- Examples:
  - `T2.3` human replay Urdu: max partial probability approximately `1.0`; fusion later blocks it because replay context is elevated.
  - `T3.2` AI replay English: max partial probability `1.0`; partial is fusion-eligible even though the file is replay, not partial fabrication.
  - `T3.5` AI replay English: max partial probability approximately `1.0`; arbitration blocks it because replay context is elevated.

Interpretation:

- Partial should not be retrained by adding simple audio augmentation.
- The current partial design can convert within-file contrast/replay/channel artifacts into localized partial-looking segment activations.
- The first partial fix should be localization redesign plus stricter negative testing, especially replay, mixer, clean long audio, and compressed audio negatives.

## Axis Failure Decision

Current decision from the completed and cached evidence:

- Origin: failing in a specific way. Needs hard negatives for clean English human and hard positives for compressed AI before replacing release behavior.
- Replay: incomplete but promising. Needs a focused replay-only run before retraining.
- Mixer/channel: incomplete. Needs a focused mixer/channel-only run before retraining.
- Partial: failing by design/runtime behavior. Do not add augmentation first; redesign partial localization and negative controls.

## Next Step

The next work item should be a lightweight replay/mixer-only evaluator that bypasses full WavLM partial segmentation. It should score all supported testing-audio files with the release replay and mixer models, generate CSV metrics, and treat unsupported MP4 inputs explicitly as release I/O coverage gaps.

After that:

1. Retrain origin only if the hard-negative/compressed-AI set is prepared.
2. Retrain replay only if replay-only metrics confirm misses beyond one-off cases.
3. Retrain mixer only if mixer/channel metrics confirm systematic failure.
4. Redesign partial before any partial retraining or augmentation.
