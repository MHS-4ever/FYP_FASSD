# Phase 9E-P3 — Release Decision Hierarchy & 8-Variant Validation

## Why Phase 9E (not Phase 10)

The release app and live inference pipeline are still being corrected: main-result hierarchy, partial interpretation, and automated regression against the 8-variant forensic collection. This is release-integration work, not a new research phase.

## Main result hierarchy

1. **Voice origin** (from `origin_evidence` / SSL origin model only)
   - Likely AI-generated / Likely human / Inconclusive
2. **Forensic indicators** (replay, mixer/channel, partial replacement; AI-origin also listed as evidence layer)
3. **Recommendation** (manual review guidance; no conclusive authenticity wording)

Replay, mixer, and partial axes **must not** decide voice origin.

## Partial cascade status

| Field | Release app value |
|-------|-------------------|
| `partial_module_mode` | `segment_candidate_only` when file gate unavailable |
| `full_partial_cascade_available` | `false` |
| Segment-only candidate | Card status **Review candidate**, not **Detected** |
| Full P5B wired | Would allow **Detected** (experimental/manual-review only) |

## 8-variant expected behavior

| Variant | Voice origin | Primary forensic expectation |
|---------|--------------|------------------------------|
| ai_clean | Likely AI-generated or inconclusive | AI-origin detected |
| ai_fabricated | Likely AI-generated or inconclusive | AI-origin + partial candidate/detected if available |
| ai_mixer | Likely AI-generated or inconclusive | Mixer/channel detected |
| ai_replayed | Inconclusive common | Replay detected |
| human_clean | Likely human or inconclusive | No strong manipulation; segment-only partial must not mark suspicious |
| human_fabricated | Likely human or inconclusive | Partial candidate/detected or honest limitation |
| human_mixer | Likely human | Mixer/channel; replay overlap explained if both high |
| human_replayed | Likely human or inconclusive | Replay detected |

## AASIST / ResNet shadow audit policy

- Reference checkpoints under `release/models/reference/` are **audit-only**.
- No safe release wrapper → documented as *present but not runnable*.
- Shadow scores go to `origin_support_models` JSON only; **not** active voice-origin decision unless validation proves improvement.
- **No training** in P3.

## Waveform labeling

| Condition | Label / color |
|-----------|----------------|
| Strong forensic or full partial detection | Highlighted evidence region (orange) |
| Segment-only partial candidate | Candidate region for review (amber) |
| Clean / no strong evidence | No highlight |

## Evaluation modes

```bat
python code\phase9\partial_redesign\run_phase9e_p3_8variant_release_eval.py --mode quick --max_base_audios 1
python code\phase9\partial_redesign\validate_phase9e_p3_release_correctness.py --mode quick

python code\phase9\partial_redesign\run_phase9e_p3_8variant_release_eval.py --mode full
python code\phase9\partial_redesign\validate_phase9e_p3_release_correctness.py --mode full
```

Outputs: `reports/phase9/app/phase9e_p3_8variant_eval/`

**Primary dataset:** `data/phase7c1/raw/` — 184 files (23 speakers × 8 variants). Names follow Phase 7C1 convention (`human_001_clean.wav`, `ai_001_direct.wav`, etc.).

## Terminal / resource cleanup

- `load_all_active_models()` and `load_ssl_extractor()` cached per process (`lru_cache`).
- `safe_nanmean()` in `feature_extraction.py` avoids empty-slice RuntimeWarning.
- Known torch mask deprecation filtered at Gradio entry only.

## What remains model limitation

- Partial fabrication recall on holdout (P5F documented FN/FP).
- Full P5B file-gate cascade not wired in release app path.
- AASIST/ResNet not active without validated wrapper.
- Origin under replay domain shift may read inconclusive (by design).

## How to run release app

```bat
cd release
python app_gradio.py
```

Product title: **Deepfake Audio Detector — Local Demo**  
Research: **Forensic Acoustic for Synthetic Speech Detection**

## P3-P1 final output cleanup

Phase 9E-P3-P1 addresses remaining release-output issues after the 184-file regression (no retrain, no threshold changes, no AASIST/ResNet activation).

### Human-clean wording adjustment

When voice origin is likely human, no AI-origin/replay/mixer detection, and partial is segment-candidate-only:

- `finding_title`: **No strong manipulation indicators detected**
- `forensic_indicator_summary`: segment-level candidate available for **optional** review
- `recommendation_level`: `optional_review`
- `recommendation_text`: optional review wording — **not** “Manual review recommended.”

### JSON output completeness

Per-file saved JSON includes: `voice_origin_result`, `forensic_indicator_summary`, `recommendation`, `recommendation_level`, `evidence_axis_cards`, `axis_interpretation`, `partial_module_mode`, `release_correctness_notes`, and compact `origin_support_models` (`audit_only`).

### Replay/mixer overlap wording

When replay and mixer/channel are both high, cards use **Possible overlap** status and `axis_interpretation.overlap_notes` explain that mixer/channel is dominant; replay is not presented as the sole explanation.

### Origin under replay/channel processing

Low origin score with high replay/mixer → `inconclusive_under_processing` and display text **Voice origin: Inconclusive under replay/channel processing**. High origin with processing → `likely_ai_generated_with_processing`.

### Terminal warning cleanup

`safe_nanmean` guards feature empty slices; terminal audit reports `runtime_warning_count`, `feature_warning_count`, `external_warning_count`, `real_error_count`, `traceback_count`, and `terminal_clean_enough_for_demo`.

### AASIST/ResNet intentionally not activated in P3-P1

Reference models remain `audit_only` with `runnable: false` in JSON; no active fusion use in this phase.
