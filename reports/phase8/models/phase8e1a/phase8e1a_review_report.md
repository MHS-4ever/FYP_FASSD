# Phase 8E-1A Error / Threshold Review Report

Phase 8E-1A performs analysis only on existing out-of-fold predictions.
No model training/refitting/calibration fitting is performed.

## Inputs Used

- predictions: `reports/phase8/models/phase8e1/phase8e1_out_of_fold_predictions.csv`
- metrics: `reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv`
- confusions: `reports/phase8/models/phase8e1/phase8e1_confusion_matrices.csv`
- training_manifest: `reports/phase8/models/phase8e1/phase8e1_training_manifest.csv`

## Task Summary

- mixer_file_model: analyzed feature sets ['acoustic', 'combined', 'ssl']
- origin_file_model: analyzed feature sets ['acoustic', 'combined', 'ssl']
- replay_file_model: analyzed feature sets ['acoustic', 'combined', 'ssl']

## Error Case Summary

- total error rows: 690 (includes TP/TN/FP/FN labels)
- false positives: 13
- false negatives: 3

## Threshold Grid Summary

- threshold points analyzed per task/feature_set: 17
- total threshold rows: 153

## Calibration Summary

- mixer_file_model / acoustic: brier=0.0121, ece=0.0431
- mixer_file_model / combined: brier=0.0165, ece=0.025
- mixer_file_model / ssl: brier=0.031, ece=0.022
- origin_file_model / acoustic: brier=0.0582, ece=0.0615
- origin_file_model / combined: brier=0.0016, ece=0.0146
- origin_file_model / ssl: brier=0.001, ece=0.013
- replay_file_model / acoustic: brier=0.0197, ece=0.0359
- replay_file_model / combined: brier=0.0268, ece=0.0233
- replay_file_model / ssl: brier=0.0267, ece=0.026

## Threshold Recommendations

- mixer_file_model / acoustic: candidate=0.75 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- mixer_file_model / combined: candidate=0.45 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- mixer_file_model / ssl: candidate=0.25 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- origin_file_model / acoustic: candidate=0.85 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- origin_file_model / combined: candidate=0.25 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- origin_file_model / ssl: candidate=0.2 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- replay_file_model / acoustic: candidate=0.65 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- replay_file_model / combined: candidate=0.65 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.
- replay_file_model / ssl: candidate=0.4 | use=candidate_for_phase8f_review | Candidate threshold only; requires validation and manual review.

## Clean False-Positive Analysis

- Origin axis prioritizes clean-human protection.
- Replay and mixer axes prioritize clean-negative protection.

## Phase 8F Candidate Notes

- mixer_file_model / acoustic: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)
- mixer_file_model / combined: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)
- mixer_file_model / ssl: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)
- origin_file_model / acoustic: caution_candidate (usable with caution and stronger validation)
- origin_file_model / combined: caution_candidate (perfect result on small dataset requires caution)
- origin_file_model / ssl: caution_candidate (perfect result on small dataset requires caution)
- replay_file_model / acoustic: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)
- replay_file_model / combined: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)
- replay_file_model / ssl: yes_candidate (clean false-positive behavior acceptable at default candidate threshold)

## Safety and Limitations

- Results are from a small controlled dataset and require validation.
- Candidate thresholds are not final deployment thresholds.
- Outputs are not final forensic decisions.
- No partial fabrication training or segment model analysis was performed.
- Manual review recommended for low-confidence or conflicting evidence.
