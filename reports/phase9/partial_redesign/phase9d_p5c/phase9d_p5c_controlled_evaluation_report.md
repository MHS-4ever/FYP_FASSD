# Phase 9D-P5C Controlled Evaluation Report (Experimental)

Generated: 2026-05-29 19:02:32 UTC

**Production claim:** NO — experimental partial-fabrication evidence only.

**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.

## Purpose

Evaluate whether the accepted P5B two-stage cascade produces useful partial-fabrication evidence indicators on controlled audio without unacceptable false partial alerts on direct, replay, and mixer files.

## Input

- Controlled audio directory: `data\phase7c1\raw`
- Files in manifest: 184

## Overlap audit summary

- Evaluation mode: **controlled reuse/sanity evaluation (NOT independent held-out)**
- Independent holdout files: 0
- Seen in P5 training: 184
- Unknown overlap: 0

This phase does not hide overlap with P5A/P5B training data.

## Accepted cascade thresholds (P5B-P2)

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

- File gate feature set: `ssl`
- Segment localizer feature set: `combined`

## Model artifacts used (experimental candidates only)

- File gate: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- Segment localizer v2: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- Cascade config: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_cascade_config__p5b_experimental_candidate.json`

## File-level results

- Total files: 184
- Evaluated (ok): 184
- Failed/skipped: 0
- Partial evidence recall (partial files): 1.0
- Non-partial false alarm rate: 0.021739130434782608

## Condition-wise false partial rates

- direct_false_partial_rate: 0.06521739130434782
- replay_false_partial_rate: 0.0
- mixer_false_partial_rate: 0.0

## Localization quality (when cascade positive)

- broad_activation_rate_when_positive: 0.0
- top1_hit_rate_when_positive: nan
- top3_hit_rate_when_positive: nan
- top5_hit_rate_when_positive: nan

## Error handling

- invalid_file_handling_pass_rate: 1.0

## Examples — successful candidate localization

- `data/phase7c1/raw/human_fabricated/human_001_fabricated.wav` — partial evidence indicator at 42.0–46.0s (gate=0.959, max_seg=1.000)
- `data/phase7c1/raw/human_fabricated/human_021_fabricated.wav` — partial evidence indicator at 8.0–12.0s (gate=0.944, max_seg=1.000)
- `data/phase7c1/raw/human_fabricated/human_006_fabricated.wav` — partial evidence indicator at 0.0–4.0s (gate=0.912, max_seg=1.000)
- `data/phase7c1/raw/human_fabricated/human_004_fabricated.wav` — partial evidence indicator at 0.0–4.0s (gate=0.842, max_seg=1.000)
- `data/phase7c1/raw/human_fabricated/human_002_fabricated.wav` — partial evidence indicator at 10.0–14.0s (gate=0.981, max_seg=1.000)

## Examples — false partial evidence

- `data/phase7c1/raw/ai_direct/ai_002_direct.wav` (direct) — partial_evidence_positive=True with gate=0.697
- `data/phase7c1/raw/human_clean/human_012_clean.wav` (direct) — partial_evidence_positive=True with gate=0.576
- `data/phase7c1/raw/human_clean/human_014_clean.wav` (direct) — partial_evidence_positive=True with gate=0.505

## Release readiness assessment

**Candidate acceptable for release packaging evaluation:** no

Reasons:
- independent_holdout_count 0 < 1

## Limitations

- Uses phase8e0 precomputed features when available; not a fully live feature-extraction deployment test.
- Does not use release partial model, AASIST, or HybridResNet.
- Evidence axes remain separated (origin, replay, mixer, partial fabrication).
- Outputs are candidate indicators for manual review, not final authenticity verdicts.

## Recommended next action

P5C controlled evaluation completed, but release packaging is not recommended because no independent held-out files were available.
