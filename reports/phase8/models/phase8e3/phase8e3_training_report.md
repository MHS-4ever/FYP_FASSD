# Phase 8E-3 Training Report

**Generated:** 2026-05-28 12:11:02 UTC

Experimental timestamp-aligned segment modeling only.
No final forensic decisions are produced.
Timestamp labels are used only as y_true targets, not as model input features.
Label-aware inside/outside baseline and overlap fields are analysis-only and excluded from Phase 8E-3 model features.
Expected performance may be lower than leakage-prone setups but is more scientifically valid.

## Dataset Counts

- trainable segments: 1207
- fabricated_region segments: 224
- outside_fabricated_region segments: 983

## Feature Sets

- ['localization', 'acoustic', 'ssl', 'combined']

## Split Method

- ['StratifiedGroupKFold']

## Metrics (experimental means)

- localization: bal_acc=0.868, f1=0.6883, outside_false_fabricated_rate=0.1597
- acoustic: bal_acc=0.4722, f1=0.2421, outside_false_fabricated_rate=0.5127
- ssl: bal_acc=0.5733, f1=0.3308, outside_false_fabricated_rate=0.3581
- combined: bal_acc=0.8815, f1=0.7601, outside_false_fabricated_rate=0.0875

## Threshold Grid Summary

- threshold rows: 68

## File-Level Localization Behavior

- file summary rows: 184

## Limitations

- timestamp-aligned labels are preparation labels, not final forensic proof.
- timestamp labels define target classes only (y_true) and are not feature inputs.
- label-derived inside/outside baseline fields are excluded from model feature sets.
- small/controlled data may overestimate generalization.
- outputs must be reviewed with manual/fusion context.

## Safety Statements

- experimental only
- no final forensic decision
- timestamp labels are target-only
- not proof of fabrication
