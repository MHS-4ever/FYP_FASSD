# Mixer Retrain Attempts Decision

Generated: 2026-06-13

## Summary

The mixer/channel axis remains the correct axis to fix, but the current available training data is not sufficient for a release-quality retrain.

Three experimental retrain attempts were run:

- `mixer_retrain_experimental_2026-06-13`
- `mixer_retrain_experimental_v2_2026-06-13`
- `mixer_retrain_experimental_v3_2026-06-13`

None passed external validation on `testing_audios`.

## Attempt Results

### V1

- Improved internal Phase 7 dev/test performance.
- External `testing_audios` recall: `0.3333`.
- Detected only `1/3` external mixer/compression positives.
- Introduced false positives on replay/clean examples.

### V2

- Reduced false positives.
- External `testing_audios` recall: `0.0000`.
- Missed all external mixer/compression positives.
- Showed the model had become too conservative.

### V3

- Used targeted mobile/mixer/platform-style augmentation.
- External `testing_audios` recall: `0.3333`.
- Recovered only one external positive.
- Reintroduced false positives on:
  - `T2.3`: human replay.
  - `T4.1`: clean English human reference.

## Feature Gap Finding

`mixer_feature_gap_diagnosis_2026-06-13` showed:

- `T2.2` human mixer is nearest to Phase 7 replay, not Phase 7 mixer.
- `T3.4` AI mixer is nearest to Phase 7 replay, not Phase 7 mixer.
- `T4.5` WhatsApp compressed AI is nearest to Phase 7 clean, not Phase 7 mixer.

This means the external mixer/compression cases are outside the Phase 7 mixer training distribution.

## Decision

Do not replace the release mixer model with v1, v2, or v3.

Do not continue blind synthetic mixer augmentation.

Mixer v4 should wait for better data:

- Real laptop-mixer-mobile examples close to `T2.2`.
- AI mixer/mobile examples close to `T3.4`.
- WhatsApp/platform-compressed AI examples close to `T4.5`.
- Replay hard negatives like `T2.3`.
- Clean public/studio human hard negatives like `T4.1`.

## Next Axis

Move to replay improvement next.

Replay currently has usable but imperfect performance. Its main failures are:

- false positives on mixer/channel and clean reference audio;
- one AI replay false negative;
- unsupported MP4 inputs.

The next replay retrain should include mixer/channel rows as hard negatives rather than treating replay as only clean-vs-replay.
