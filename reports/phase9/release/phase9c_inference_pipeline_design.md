# Phase 9C Inference Pipeline Design

## Purpose

Prove local architecture can process one new audio file end-to-end using packaged Phase 9B active models.

## Flow

1. Load and validate audio (mono, 16 kHz)
2. Segment audio (4 s window, 2 s hop)
3. Extract file/segment acoustic features (Phase 8C utils)
4. Extract frozen WavLM SSL embeddings (Phase 8D utils)
5. Compute safe live localization features for partial segment model
6. Load active packaged sklearn pipelines (origin/replay/mixer/partial)
7. Align features to metadata `feature_names`
8. Predict probabilities and apply threshold candidates
9. Fuse axes with Phase 8F rules (no fake/real collapse)
10. Generate JSON + Markdown safe reports

## Model loading

Active artifacts only from `release/models/{origin,replay,mixer,partial_segment}/`.
Reference models under `release/models/reference/` are excluded.

## Feature alignment

Packaged sklearn pipelines require the **fit-time input columns** (`model.feature_names_in_`),
not only `metadata["feature_names"]` (which often lists SelectKBest-selected features).

Resolution order (`get_model_input_feature_names`):
1. `model.feature_names_in_`
2. first fitted pipeline step with `feature_names_in_`
3. metadata `input_feature_names` / `training_input_feature_names` / `fit_feature_names`
4. reconstructed fit-time schema from feature_set (e.g. full `ssl_emb_000..767`, file acoustic schema, segment combined schema)
5. `metadata["feature_names"]` only as last fallback, and **not** when that list is clearly the SelectKBest-selected subset

`metadata["feature_names"]` remains documentation for selected/top features unless explicitly stored as fit-time input names.

Missing model features are filled with NaN (pipeline imputer handles them).
Extra live features are ignored.

## SSL extraction

- `microsoft/wavlm-base-plus`
- frozen eval mode, mean pooling, safetensors preferred
- no training/fine-tuning

## Fusion and reporting

- axes remain separate
- replay/mixer high does not imply AI-generated
- partial segment model is **sensitive** and must be gated; it is localization support only (fabricated_region vs outside), not a general file-level partial detector
- replay/mixer/channel effects can create segment-level score changes that resemble partial fabrication
- live inference applies **partial localization gating** before arbitration:
  - broad/global segment activation (`high_segment_fraction >= 0.60`) is **not** treated as localized partial fabrication evidence
  - localized pattern requires threshold pass **and** `topk_minus_rest_probability >= 0.15`
- **partial evidence arbitration** (Phase 9C-P3) runs before fusion:
  - when replay or mixer evidence is moderate/high, partial must pass **stricter** localization criteria to be fusion-eligible:
    - `partial_localization_gate = localized_pattern_supported`
    - `high_segment_fraction <= 0.35`
    - `topk_minus_rest_probability >= 0.35`
    - `probability_std >= 0.25`
  - otherwise `partial_fusion_eligible = false`, `partial_fusion_block_reason = blocked_by_replay_or_mixer_context`, and fusion strength is downgraded to borderline
- all arbitration fields are set in `inference_pipeline.py` before fusion (never left null when prediction succeeds)
- fusion uses `partial_fusion_eligible` and `partial_evidence_strength_for_fusion` only; `_resolve_live_fusion_status` enforces single-axis outcomes when partial is blocked
- partial must be **localized and fusion-eligible** before it can drive `suspicious_mixed_evidence_experimental` or partial-only fusion statuses
- partial JSON includes diagnostics: `top_segment_ranges`, `high_probability_ranges`, `broad_activation_warning`, `localization_confidence_note`, `partial_fusion_block_reason`, `partial_arbitration_note`
- safe wording only (evidence indicator, candidate segment)

## Phase 9D testing

Phase 9D will run a larger controlled test set to tune arbitration thresholds further. Until then, validate clean/AI-direct/replay/mixer/partial cases separately with sample-output validation.

## Limitations

- experimental prototype only
- manual review recommended
- not court-ready proof

## Inactive reference models

AASIST and HybridResNet remain legacy/reference only and are not called by Phase 9C.

## Next: Phase 9D

End-to-end CLI testing, sample outputs, and validation on real audio files.
