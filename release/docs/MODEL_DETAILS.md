# Model Details (Phase 9B)

All release models are **experimental_forensic_prototype** artifacts for evidence-axis indicators only.

## origin_file_model

- feature set: ssl (`ssl_emb_*`)
- target: `target_is_ai_synthetic` (0=clean human, 1=clean AI synthetic)
- expected input: file-level SSL embedding vector columns
- output meaning: origin-axis synthetic indicator probability (experimental)
- limitations: small dataset; manual review required; not final forensic proof

## replay_file_model

- feature set: acoustic (file-level acoustic features)
- target: `target_is_replay`
- expected input: file-level acoustic feature columns
- output meaning: replay/rerecording indicator probability (experimental)
- limitations: replay evidence is not AI-generation evidence

## mixer_file_model

- feature set: acoustic
- target: `target_is_mixer_channel`
- expected input: file-level acoustic feature columns
- output meaning: mixer/channel processing indicator probability (experimental)
- limitations: mixer/channel evidence is not AI-generation evidence

## partial_fabrication_segment_model

- feature set: combined (segment acoustic + segment ssl + safe localization features)
- target: `target_partial_fabricated` (0=outside, 1=fabricated region)
- expected input: segment-level combined features keyed by `file_id`, `segment_id`
- output meaning: segment candidate localization support indicator
- limitations:
  - timestamp labels are targets only
  - label-derived baseline features are excluded from model inputs
  - not proof of fabrication

## Packaging / runtime notes

- Artifacts are created by `package_phase9b_release_models.py` (manual run).
- Phase 9C will wire live inference using metadata `feature_names` and `threshold_candidate`.
- No model writes to `models_saved/active/`.

## Active models vs reference models

- **Active Phase 9B models:** `origin_file_model`, `replay_file_model`, `mixer_file_model`, `partial_fabrication_segment_model`.
- **Reference models:** AASIST and HybridResNet are copied under `release/models/reference/` for comparison/history only.
- They are **not** used by default in live inference or fusion (`active_in_fusion: false`, `used_by_default: false`).
- Separate validation is required before any active use in Phase 9C or fusion.
- They must **not** reintroduce binary fake/real collapse or replace multi-axis evidence outputs.
