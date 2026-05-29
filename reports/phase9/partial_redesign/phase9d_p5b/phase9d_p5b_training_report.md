# Phase 9D-P5B Training Report (Experimental)

Generated: 2026-05-29 18:46:22 UTC

**Training performed:** NO — reused existing OOF predictions (P5B-P1 recompute only)

**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.

**Production claim:** NO — these are experimental redesign candidates only.

## Purpose of P5B

Train and evaluate redesigned partial-fabrication models to address Phase 9D-P4 broad activation:
- Stage 1 file gate: `partial_file_candidate_model`
- Stage 2 segment localizer v2: `partial_segment_localizer_v2`
- Cascade simulation to estimate two-stage live behavior

## Why the old partial model failed (P4 reference)

- Top-5 timestamp hit: 36/46 fabricated files
- Localized success: 0/46
- Broad activation: 46/46 fabricated files

## File gate results (OOF mean)

| feature_set | balanced_accuracy | average_precision | roc_auc | f1 |
|---|---:|---:|---:|---:|
| acoustic | 0.7534 | 0.5626 | 0.8415 | 0.5962 |
| ssl | 0.8575 | 0.8241 | 0.9324 | 0.7418 |
| combined | 0.8313 | 0.7433 | 0.9103 | 0.7064 |

## Segment localizer v2 results (OOF mean)

| feature_set | balanced_accuracy | average_precision | roc_auc | f1 |
|---|---:|---:|---:|---:|
| acoustic | 0.6776 | 0.1169 | 0.7420 | 0.1823 |
| ssl | 0.6853 | 0.2681 | 0.7950 | 0.2224 |
| localization | 0.8605 | 0.3632 | 0.9232 | 0.3689 |
| combined | 0.8934 | 0.7288 | 0.9721 | 0.6448 |

## Cascade simulation (selected feature sets)

Release-ready pair: file_gate=0.5,segment=0.9,contrast=0.25,broad_limit=0.45 — partial recall=0.783, non-partial FA=0.058, top5 hit (cascade+)=1.000, broad activation (cascade+)=0.000, direct FP=0.174

## Cascade acceptance diagnostics

### Chosen acceptance thresholds

| Rule | Threshold |
|------|----------:|
| direct_false_partial_rate <= | 0.2000 |
| replay_false_partial_rate <= | 0.0500 |
| mixer_false_partial_rate <= | 0.0500 |
| broad_activation_rate_when_positive <= | 0.1000 |
| file_gate_threshold >= | 0.5000 |
| non_partial_false_alarm_rate <= | not enforced |
| partial_file_recall >= | not enforced |

| Diagnostic | Value |
|------------|------:|
| Release-ready pair found | yes |
| Minimum observed direct_false_partial_rate (grid) | 0.1087 |
| Minimum observed non_partial_false_alarm_rate (grid) | 0.0362 |
| Best recall with replay/mixer/broad safety | 0.9565 (file_gate=0.30, segment=0.50, contrast=0.15, broad_limit=0.35) |
| Best candidate under acceptance rules | file_gate=0.50, segment=0.90, contrast=0.25, broad_limit=0.45 |
| Best candidate passed acceptance | yes |
| Failed conditions (best/recommended) | none |
| CSV recommended pair | file_gate=0.50, segment=0.90, contrast=0.25, broad_limit=0.45 |

## Broad activation comparison (selected segment model only)

Selected configuration: feature_set=`combined`, segment_threshold=`0.5`

| Metric | Value |
|--------|------:|
| Partial file count (unique) | 46 |
| Broad activation count | 0 |
| Localized pattern supported | 46 |
| Top-1 hit count | 40 |
| Top-3 hit count | 45 |
| Top-5 hit count | 46 |

- P4 broad activation reference: 46/46 (Phase 9D-P4)
- P5B broad activation (selected): 0/46

## False positives on replay / mixer / direct (cascade)

See cascade simulation columns `replay_false_partial_rate`, `mixer_false_partial_rate`, `direct_false_partial_rate`.

## Recommended next action

Experimental cascade thresholds pass shared acceptance rules. Outputs remain manual-review support only — do not package into release yet without P5C evaluation.

## Limitations

- Logistic regression on hand-crafted features only; no end-to-end audio modeling.
- Cross-validated OOF estimates; no held-out deployment set in this phase.
- Cascade simulation uses OOF probabilities (optimistic bias vs nested deployment).
- Timestamp labels used for segment targets/evaluation only — never as model features.

## Configuration

- CV folds: 5
- File feature sets: acoustic,ssl,combined
- Segment feature sets: acoustic,ssl,localization,combined
- Model type: logistic_regression_l2
- Random seed: 42
