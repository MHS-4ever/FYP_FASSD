# Two-Stage Manipulation Prototype Decision

Generated: 2026-06-13

## Prototype

Output directory:

- `reports/release_audit/two_stage_manipulation_prototype_2026-06-13`

The prototype trained:

- Stage 1: clean/direct vs manipulated/channel artifact.
- Stage 2: replay vs mixer_channel vs partial_insert.

`testing_audios` was evaluation-only.

## Stage 1 Result

External `testing_audios`:

- Balanced accuracy: `0.6667`
- Recall on manipulated/channel files: `0.3333`
- Specificity on clean/direct files: `1.0000`

This is safer than the previous replay/mixer binaries because it avoids clean false positives, but it misses too many manipulated examples.

Stage 1 detected:

- `T2.1`: human replay.
- `T2.2`: human mixer/channel.
- `T2.3`: human replay.
- `T3.5`: AI replay.
- `T5_FAB_001`: partial insert.

Stage 1 missed:

- `T2.5`: human replay/noisy.
- `T3.2`: AI replay.
- `T3.4`: AI mixer.
- `T4.3`: partial insert.
- `T4.5`: WhatsApp/platform compression.
- `T5.1`-`T5.5`: edited/spliced or processed human files.

## Stage 2 Result

External `testing_audios` subtype accuracy was `0.3333`.

Stage 2 is not yet ready because Phase 7 training only supplied:

- replay;
- mixer_channel;
- partial_insert.

It did not train real classes for:

- edited_spliced;
- platform_compression;
- unknown_channel_artifact.

Therefore, Stage 2 often forces edited/compression/clean-like artifacts into replay or partial_insert.

## Decision

The two-stage architecture is the right direction, but this first prototype is not release-ready.

Keep the architecture idea. Improve the data/classes before another release integration attempt.

## Next Step

Build a Stage 1 recall-oriented prototype with broader manipulation labels:

- treat edited_spliced and platform_compression as manipulated in evaluation;
- add training proxies for edited/channel artifacts from Phase 7 partial/clean/replay/mixer rows;
- lower Stage 1 threshold constraints while maintaining clean-file safety through an explicit "clean hard negative" check;
- add `unknown_channel_artifact` as a Stage 2 fallback rather than forcing all non-replay artifacts into replay/partial.

This should be the next experiment before touching release integration.
