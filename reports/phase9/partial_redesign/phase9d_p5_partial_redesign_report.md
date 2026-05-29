# Phase 9D-P5 Partial Redesign Report

Generated: 2026-05-29 18:04 UTC

**Training performed:** NO — dataset assembly only.

## Why P5 is needed

Phase 9D-P4 timestamp diagnostics showed that the current partial segment model carries ranking signal
(top-5 timestamp hit 36/46 fabricated files) but **localized_success_count = 0** and **broad_activation_count = 46/46**.
Broad activation across segments prevents reliable live localization. P5 introduces a two-stage design:

1. **File-level partial candidate gate** — does this file likely contain partial fabrication?
2. **Improved segment localizer v2** — which segments are fabricated, trained with stronger non-partial negatives.

## P4 diagnostic findings (reference)

| Metric | Value |
|--------|-------|
| Fabricated files tested | 46 |
| Top-5 timestamp hit | 36/46 |
| Localized success | 0 |
| Broad activation | 46/46 |
| Human fabricated top-5 | Better than AI fabricated |

## Two-stage design

### Stage 1: `partial_file_candidate_model`

- Dataset: `phase9d_p5_file_partial_gate_dataset.csv`
- Target: `target_is_partial_fabrication_file`
- Positives: ai_fabricated, human_fabricated
- Negatives: direct, replay/repeat, mixer controlled files
- Timestamps identify positives but **timestamp values are not file-model features**.

### Stage 2: `partial_segment_localizer_model_v2`

- Dataset: `phase9d_p5_segment_partial_localizer_dataset.csv`
- Target: `target_is_fabricated_segment`
- Positives: segments overlapping fabricated timestamp region
- Negatives: outside segments from partial files + direct + replay + mixer segments
- Negative sampling: `cap_per_category` (max 1000 per category)

## File-level gate dataset summary

| Metric | Count |
|--------|------:|
| Total rows | 184 |
| Positive (partial) | 46 |
| Negative (controlled) | 138 |

## Segment localizer dataset summary

| Metric | Count |
|--------|------:|
| Total rows | 4143 |
| Positive segments | 224 |
| Negative segments | 3919 |
| Outside same partial negatives | 983 |
| Clean direct negatives | 1000 |
| Replay negatives | 936 |
| Mixer negatives | 1000 |
| AI fabricated positives | 117 |
| Human fabricated positives | 107 |

## Timestamp usage policy

- Timestamps loaded from Phase 7C1 insertion_stamps.csv (AI + human fabricated).
- Used **only** for target construction (`target_is_fabricated_segment`, audit labels) and evaluation metadata.
- Timestamp overlap fields are metadata columns, **excluded** from `model_feature_columns_json`.
- Timestamp match audit: 46/46 matched rows.

## Leakage prevention

- Forbidden columns audited in `phase9d_p5_feature_leakage_audit.csv`.
- Separate feature column JSON files for file gate and segment localizer.
- No `fake_score`, `real_score`, fusion outputs, or prior model probabilities as features.

## Class balance warnings

none

## Risks and limitations

- Segment localizer still depends on file-level gate in live pipeline (not trained here).
- Negative sampling caps may exclude rare edge segments; adjust `--max_negative_segments_per_category` if needed.
- Unmatched timestamp rows reduce positive segment labels for affected files.
- Broad activation issue may persist until v2 model is trained and evaluated in P5B.

## Next recommended phase

**Phase 9D-P5B** — train and evaluate file-level partial gate and segment localizer v2 using these datasets.
Do **not** start Phase 9E apps until P5B validation passes.
