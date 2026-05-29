# Model Registry (Phase 9B Packaging-Aware)

Release status: **experimental_forensic_prototype**

Artifact status rule:
- If the `.joblib` and metadata JSON exist under `release/models/`, status = **packaged (experimental)**.
- Otherwise status = **pending until user runs** `code/phase9/release/package_phase9b_release_models.py`.

Inventory file (after packaging): `release/models/model_inventory.json`

## origin_file_model

- evidence axis: origin evidence
- source phase: Phase 8E-1 / 8E-1A
- feature set: ssl
- target: `target_is_ai_synthetic`
- threshold candidate: 0.20
- artifact: `release/models/origin/origin_file_model__ssl__experimental.joblib`
- metadata: `release/models/origin/origin_file_model__ssl__metadata.json`
- allowed use: origin evidence indicator (experimental review workflow)
- forbidden use: final fake/real decision; court-ready proof; production deployment without validation

## replay_file_model

- evidence axis: replay evidence
- source phase: Phase 8E-1 / 8E-1A
- feature set: acoustic
- target: `target_is_replay`
- threshold candidate: 0.65
- artifact: `release/models/replay/replay_file_model__acoustic__experimental.joblib`
- metadata: `release/models/replay/replay_file_model__acoustic__metadata.json`
- important: replay evidence does **not** mean AI-generated
- allowed use: replay/rerecording evidence indicator
- forbidden use: claiming replay means AI-generated; final legal determination

## mixer_file_model

- evidence axis: mixer/channel evidence
- source phase: Phase 8E-1 / 8E-1A
- feature set: acoustic
- target: `target_is_mixer_channel`
- threshold candidate: 0.75
- artifact: `release/models/mixer/mixer_file_model__acoustic__experimental.joblib`
- metadata: `release/models/mixer/mixer_file_model__acoustic__metadata.json`
- important: mixer/channel evidence does **not** mean AI-generated
- allowed use: mixer/channel processing evidence indicator
- forbidden use: claiming mixer means AI-generated; final legal determination

## partial_fabrication_segment_model

- evidence axis: partial fabrication evidence
- source phase: Phase 8E-3
- feature set: combined
- target: fabricated_region vs outside_fabricated_region
- threshold candidate: 0.50 (verify in Phase 9C/9G)
- artifact: `release/models/partial_segment/partial_segment_model__combined__experimental.joblib`
- metadata: `release/models/partial_segment/partial_segment_model__combined__metadata.json`
- allowed use: partial segment localization support indicator
- forbidden use: final fabrication proof; court-ready proof

## Phase 9B note

Phase 9B packages experimental models only. No active/production promotion.

## Legacy/reference models

### AASIST reference model

- path: `release/models/reference/aasist/`
- status: legacy_reference_experimental
- active_in_fusion: false
- used_by_default: false
- purpose: legacy/reference anti-spoofing/deepfake-audio baseline
- allowed use: comparison, historical baseline, future validation candidate
- forbidden use: active Phase 9C inference without validation, final fake/real decision, replacement for multi-axis fusion

### HybridResNet reference model

- path: `release/models/reference/hybrid_resnet/`
- status: legacy_reference_experimental
- active_in_fusion: false
- used_by_default: false
- purpose: legacy/reference environmental/acoustic baseline
- allowed use: comparison, historical baseline, future validation candidate
- forbidden use: active Phase 9C inference without validation, final fake/real decision, replacement for multi-axis fusion
