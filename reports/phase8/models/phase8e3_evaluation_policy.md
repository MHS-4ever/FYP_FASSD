# Phase 8E-3 Evaluation Policy

## Evaluation Scope
Phase 8E-3 evaluates one task only:
- `partial_fabrication_segment_model`

Label definition:
- positive: `fabricated_region`
- negative: `outside_fabricated_region`

## Segment-Level Metrics
Report:
- accuracy, balanced_accuracy, precision, recall, f1
- roc_auc, average_precision, brier_score
- confusion matrix counts (tn/fp/fn/tp)
- fabricated/outside detection and false-positive rates

## File-Level Localization Review
For each file, compute top-k localization behavior:
- whether top-k captures fabricated segments
- max/mean probabilities in fabricated vs outside regions
- review note for manual localization interpretation

## Threshold Analysis
Threshold grid (0.10 to 0.90, step 0.05) is for candidate review only. No final deployment threshold is selected in Phase 8E-3.

## Safety Policy
- no final forensic decision fields
- no `suspicious_segment_flag`
- no fake/real collapse
- outputs are experimental and must be interpreted with caution
- acoustic/ssl/localization feature availability is checked before CV and unusable features are excluded with audit counts
- timestamp labels are target-only (`y_true`) and not model input features
- label-derived inside/outside baseline and overlap features are excluded and leakage-audited in the training manifest

## Not-Proof Statement
Phase 8E-3 outputs are timestamp-aligned experimental localization indicators. They are not conclusive proof of fabrication.
