# Two-Stage Manipulation Design Decision

Generated: 2026-06-13

## Why This Decision Was Needed

Separate binary replay and mixer models were evaluated and retrained independently.

The external `testing_audios` results show that this structure is not reliable enough:

- Mixer retrain v1/v2/v3 did not generalize to external mixer/compression cases.
- Replay retrain still confuses mixer and edited-channel artifacts with replay.
- Partial localization fires on replay/channel artifacts, confirming broader channel-artifact overlap.

## Replay/Channel Overlap Finding

The replay/channel diagnosis showed:

- `T2.2` human mixer is nearest to Phase 7 replay, not Phase 7 mixer.
- `T3.4` AI mixer is nearest to Phase 7 replay, not Phase 7 mixer.
- `T5.5` edited/processed human is nearest to Phase 7 replay.
- `T3.2` AI replay is nearest to Phase 7 replay but falls just below the selected replay threshold.
- `T4.1` clean English human is also nearest to Phase 7 replay in acoustic distance, although thresholding kept it negative.

This means replay, mixer, edited, and some clean long/reference audio overlap in the current acoustic feature space.

## Decision

Stop treating replay and mixer as fully independent binary detectors.

Move to a two-stage manipulation design:

1. Stage 1: detect whether a file has a channel/manipulation artifact beyond clean/direct audio.
2. Stage 2: classify the manipulation type among replay, mixer/channel, edited/spliced, platform/compression, or unknown/channel-artifact.

This design better matches the evidence:

- It avoids forcing every artifact into replay or mixer.
- It allows ambiguous channel artifacts to be reported as channel/manipulation evidence instead of a precise but wrong replay/mixer label.
- It separates the question "is there manipulation/channel processing?" from "which manipulation type is it?"

## Required Experimental Targets

Stage 1 should detect:

- replay files;
- mixer/channel files;
- edited/spliced files;
- platform-compressed files.

Stage 1 should not detect:

- clean direct human;
- clean direct AI.

Stage 2 should distinguish:

- replay;
- mixer/channel;
- edited/spliced;
- platform/compression;
- unknown channel artifact.

## Acceptance Criteria On Current Testing Audios

Minimum acceptance before release integration:

- `T2.1`, `T2.3`, `T2.5`: channel/manipulation detected; type replay.
- `T3.2`, `T3.5`: channel/manipulation detected; type replay.
- `T2.2`, `T3.4`: channel/manipulation detected; type mixer/channel or unknown-channel, not replay-only.
- `T4.5`: channel/manipulation/compression detected.
- `T5.1`-`T5.5`: edited/channel detected, not AI origin by itself.
- `T1.1`, `T1.2`, `T4.1`: clean/direct negative or low artifact evidence.

## Next Experimental Step

Train a two-stage manipulation prototype from leakage-safe Phase 7 data and evaluate on `testing_audios`.

This is an experiment only. It should not overwrite release models.
