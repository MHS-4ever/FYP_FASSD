# Phase 8E-1 Evaluation Policy

## Evaluation Scope
Phase 8E-1 reports cross-validated experimental metrics for file-level evidence models only:
- origin (`clean_human` vs `clean_ai_synthetic`)
- replay (`clean` vs `replay_rerecorded`)
- mixer/channel (`clean` vs `mixer_channel_processed`)

## Metric Interpretation Rules
- Metrics are experimental CV estimates, not final product claims.
- Model outputs are evidence signals, not forensic proof.
- Replay/mixer positives do not imply AI origin.

## Clean-Human Protection Focus
For origin modeling, special attention is required for:
- clean-human false-as-AI count
- clean-human false-as-AI rate

This reduces unsafe false accusation risk in early experimentation.

## Manipulation False Positive Focus
For replay and mixer models, report:
- clean false positive count
- clean false positive rate

This tracks how often clean audio is incorrectly flagged for manipulation evidence.

## Probability and OOF Outputs
Out-of-fold probabilities/predictions are saved strictly for experimental validation and error analysis. They must not be copied into final evidence tables or interpreted as final forensic decisions.

## Policy Boundaries
- No partial fabrication training in this phase.
- No segment-level training in this phase.
- No fake/real classifier in this phase.
- No model promotion to active deployment paths.

## How Phase 8E-1 Guides Phase 8F
Phase 8E-1 metrics help decide:
- which feature sets remain useful
- which axes need calibration or abstention logic
- where fusion safeguards are needed in later Phase 8F work
