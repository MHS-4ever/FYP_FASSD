# Phase 8E-3 Model Card

- Purpose: experimental timestamp-aligned partial-fabrication segment localization support.
- Allowed use: research/evaluation and fusion-candidate analysis.
- Not allowed use: final forensic decision or fabrication proof claim.
- Training data: `E:\FYP\reports\phase8\models\phase8e2\phase8e2_partial_segment_localization_table.csv` with timestamp-aligned labels only.
- Timestamp labels define target classes only (y_true).
- Label-derived baseline/overlap features are excluded from model inputs.
- Feature sets: ['localization', 'acoustic', 'ssl', 'combined']
- Evaluation method: cross-validation with group-aware splitting by file/source group.
- Limitations: dataset scope, annotation noise, and domain shift risk.
- Safety note: outputs are experimental and not final suspicious-segment decisions.
