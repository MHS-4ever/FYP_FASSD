# Model Registry (Final Release-Audit Packaging)

Release status: **experimental_forensic_prototype**

Artifact status rule:
- Active `.joblib` + metadata JSON under `release/models/` = **packaged experimental evidence axis**.
- No model is a final fake/real or court-ready decision model.
- User-facing scores are Phase 6 evidence bands; raw probabilities remain available only in technical details.

Inventory file (after packaging): `release/models/model_inventory.json`
Calibration file: `release/config/evidence_calibration.json`

## origin_file_model

- evidence axis: origin evidence
- source phase: Release audit Phase 2 origin retrain with processed AI + train-only augmentation
- feature set: ssl
- target: `target_is_ai_synthetic`
- threshold candidate: 0.92
- threshold source: leakage-safe dev split only; `testing_audios` was evaluation-only
- Phase 2 result: leakage-safe test balanced accuracy 0.9500; `testing_audios` binary origin balanced accuracy 0.8731
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
- Phase 4 dev re-derivation recommendation: 0.73 (not promoted; release threshold retained)
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
- Phase 4 dev re-derivation recommendation: 0.94 (not promoted; release threshold retained)
- artifact: `release/models/mixer/mixer_file_model__acoustic__experimental.joblib`
- metadata: `release/models/mixer/mixer_file_model__acoustic__metadata.json`
- important: mixer/channel evidence does **not** mean AI-generated
- allowed use: mixer/channel processing evidence indicator
- forbidden use: claiming mixer means AI-generated; final legal determination

## partial_fabrication_segment_model

- evidence axis: partial fabrication evidence
- source phase: Release audit Phase 5 partial redesign
- feature set: combined_no_f9
- target: fabricated_region vs outside_fabricated_region
- threshold candidate: 0.95
- threshold source: leakage-safe dev oracle grid
- F9 removed features:
  - `acoustic_deviation_percentile_within_file`
  - `ssl_deviation_percentile_within_file`
  - `within_file_acoustic_deviation_score`
  - `within_file_ssl_deviation_score`
  - `combined_within_file_deviation_score`
- Phase 5 result: leakage-safe test oracle top-5 hit 10/10, localized rate 10/10, clean broad activation 0%
- testing_audios primary partial cases: T4.3 and T5_FAB_001 localized with overlap
- known limitation: T1.2/T1.3 showed single-window partial spikes during Phase 5 subset evaluation
- artifact: `release/models/partial_segment/partial_segment_model__combined__experimental.joblib`
- metadata: `release/models/partial_segment/partial_segment_model__combined__metadata.json`
- allowed use: partial segment localization support indicator
- forbidden use: final fabrication proof; court-ready proof

## Phase 6 calibration and wording

- Calibration source: leakage-safe dev split.
- Config: `release/config/evidence_calibration.json`.
- User-facing display: Low / Medium / High evidence.
- Inconclusive / insufficient evidence states are shown when an axis is unavailable or invalid.
- Raw 3-decimal probabilities remain in technical details only and are labeled uncalibrated.

## Final packaging note

The final release packages experimental evidence indicators only. It is a local forensic decision-support demo with manual-review wording, not an operational deployment or legal proof system.

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
