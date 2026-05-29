# Phase 9D Manifest Build Report

- Generated: 2026-05-29T13:42:40.914820+00:00
- audio_root: `E:\FYP\data\phase7c1\raw`
- scan_mode: `controlled_folders`
- output_manifest: `E:\FYP\reports\phase9\testing\phase9d_test_manifest.csv`

## Summary

- folders_scanned: 8
- folders_missing: 12
- folders_skipped: 0
- files_considered: 184
- rows_written: 43
- scan_stopped_early: False

## Categories found (candidates before sampling)

- `ai_direct`: 15
- `ai_fabricated`: 15
- `ai_mixer`: 15
- `ai_replay`: 15
- `bad_audio_invalid`: 1
- `bad_audio_short`: 1
- `bad_audio_silent`: 1
- `human_direct`: 15
- `human_fabricated`: 15
- `human_mixer`: 15
- `human_replay`: 15

## Folders scanned

- `ai_direct`
- `human_clean`
- `ai_repeat`
- `human_replay`
- `ai_mixer`
- `human_mixer`
- `ai_fabricated`
- `human_fabricated`

## Folders missing (not under audio_root)

- `human_direct`
- `human_repeat`
- `ai_replay`
- `ai_replay_laptop_mobile`
- `human_replay_laptop_mobile`
- `ai_mixer_processed`
- `human_mixer_processed`
- `replay`
- `mixer`
- `fabricated`
- `direct`
- `clean`

## Note

Phase 9D controlled testing scans Phase 7C1 raw category folders only.
Augmented, RIR, noise, features, embeddings, and other massive datasets are
**excluded by default** from this first architecture verification pass.
Large-scale stress testing can be added in a later phase after the local pipeline is stable.

