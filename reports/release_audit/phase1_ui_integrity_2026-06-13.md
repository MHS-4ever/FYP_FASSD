# Phase 1 — UI Integrity Fixes

Generated: 2026-06-13

## Scope

Trust fixes without retraining, applied to the active release presentation layer.

## Changes

### 1. Partial panel state machine

- Added `resolve_partial_display_state()` and `apply_partial_display_state()` in `release/src/app_report_formatting.py`.
- When partial evidence is **not detected** (including `global_activation_not_localized` and `blocked_by_replay_or_mixer_context`):
  - axis card shows **Not detected** with no saturated segment score text;
  - segment table is hidden;
  - waveform highlight uses no partial region.
- When partial evidence is **detected** or an **optional candidate** is allowed, the segment table and highlight remain visible with consistent recommendation labels.

### 2. Phantom ensemble sources removed

- `build_voice_origin_result()` now lists only executed models in `evidence_sources`.
- Removed automatic inclusion of `aasist_shadow` and `hybrid_resnet_shadow` from registry status.
- Removed `ensemble_if_available` label unless multiple models are actually executed (currently SSL origin only).

### 3. Score wording

- User-facing label renamed from “Evidence score” / “confidence” presentation to **Uncalibrated model score**.
- Origin line now reads `Origin uncalibrated model score: <value>`.
- Gradio/PDF segment table header updated accordingly.

### 4. MP4 / video-container loading

- `release/src/audio_io.py` now supports `.mp4`, `.webm`, `.mkv`, `.mov`.
- Uses librosa when available; falls back to `ffmpeg` audio extraction for video containers.

## Validation

- Baseline eval script: `code/release_audit/eval_testing_audios_phase1_baseline.py`
- Output directory: `reports/release_audit/phase1_baseline_2026-06-13/`
- UI consistency check: `phase1_baseline_partial_ui_contradictions.csv` is empty (0 contradictions).
- Full baseline snapshot: 25/25 `testing_audios` rows on CPU (`--device cpu` default for 6 GB GPU stability).
- MP4 loading verified on `T2.4` and `T3.3`.

### Baseline metrics (current release models, pre-origin swap)

| Axis | Balanced accuracy | Recall | Specificity |
|---|---|---|---|
| Origin (binary human/AI, n=15) | 0.875 | 1.000 | 0.750 |
| Replay (n=25) | 0.774 | 0.714 | 0.833 |
| Mixer (n=25) | 0.477 | 0.000 | 0.955 |

## Next step

Phase 2: promote experimental origin model into release and re-derive dev-only threshold.
