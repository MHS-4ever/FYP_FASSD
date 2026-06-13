# Two-Stage Manipulation V2 Decision

Generated: 2026-06-13

## Prototype

Output directory:

- `reports/release_audit/two_stage_manipulation_v2_2026-06-13`

V2 added:

- train-only proxy rows for `unknown_channel_artifact`;
- lower Stage 1 threshold (`0.45`);
- final `clean` output when Stage 1 does not fire;
- `unknown_channel_artifact` fallback in Stage 2.

## Result

External `testing_audios` Stage 1:

- Balanced accuracy: `0.6417`
- Recall on manipulated/channel files: `0.5333`
- Specificity on clean/direct files: `0.7500`

Compared with v1:

- Recall improved from `0.3333` to `0.5333`.
- Specificity dropped from `1.0000` to `0.7500`.

## What Improved

V2 detected more manipulated/channel examples:

- `T2.1`: replay detected.
- `T2.2`: mixer/channel detected as manipulated, but subtype incorrectly replay.
- `T2.3`: replay detected.
- `T2.5`: replay detected.
- `T3.5`: AI replay detected.
- `T5.1`: edited/spliced detected as manipulated, but subtype incorrectly replay.
- `T5.3`: edited/spliced detected as unknown channel artifact.
- `T5_FAB_001`: partial insert detected as unknown channel artifact.

## What Still Failed

Clean false positives:

- `T1.1`: clean human flagged as replay.
- `T4.1`: clean human flagged as unknown channel artifact.

Manipulated false negatives:

- `T3.2`: AI replay missed.
- `T3.4`: AI mixer missed.
- `T4.3`: partial insert missed.
- `T4.5`: WhatsApp/platform compression missed.
- `T5.2`, `T5.4`, `T5.5`: edited/spliced missed.

Subtype failures:

- `T2.2` mixer is still reported as replay.
- `T5.1` edited/spliced is reported as replay.
- `T3.4` would be replay if Stage 1 fired, but Stage 1 misses it.
- Platform compression has no reliable subtype detection.

## Decision

Two-stage v2 is better as a research direction, but still not release-ready.

The key lesson is that the project now needs more representative external-style data, not more threshold tuning:

- clean public/studio/reference human negatives;
- replay examples across devices and languages;
- mixer/mobile-chain examples matching `T2.2` and `T3.4`;
- platform/compression examples matching `T4.5`;
- edited/spliced examples matching `T5.*`;
- partial examples with accurate localization.

## Recommended Next Step

Stop iterative model retraining for now.

Create a data expansion and acceptance plan, then collect/generate the needed examples before training two-stage v3.

The next model-training run should only happen after those data gaps are addressed.
