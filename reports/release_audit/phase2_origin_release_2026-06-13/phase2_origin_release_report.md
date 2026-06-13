# Phase 2 Origin Release Evaluation

Generated: 2026-06-13T10:59:01.720484+00:00

Promoted release origin model evaluated with leakage-safe Phase 7 cached SSL features and fresh testing_audios SSL embeddings.

- Release artifact SHA-256: `5396ddc3758e7b2d046843fc25b53b97ddcce90a4e9c1797c8f4f8a51f94190b`
- Threshold candidate: `0.92`
- Threshold source: Leakage-safe dev split only; reports/release_audit/origin_retrain_processed_ai_augmented_2026-06-13/origin_augmented_dev_threshold_grid.csv
- Testing device: `cpu`

## Phase 7 Leakage-Safe Metrics

                             scope   n  threshold  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity  fpr    fnr     f1  roc_auc  pr_auc
       phase7_train_all_conditions 104       0.92  52  52   0   0    1.0000             1.0000        1.0  1.0000          1.0  0.0 0.0000 1.0000   1.0000  1.0000
phase7_train_origin_training_scope  78       0.92  39  39   0   0    1.0000             1.0000        1.0  1.0000          1.0  0.0 0.0000 1.0000   1.0000  1.0000
         phase7_dev_all_conditions  40       0.92  20  20   0   0    1.0000             1.0000        1.0  1.0000          1.0  0.0 0.0000 1.0000   1.0000  1.0000
  phase7_dev_origin_training_scope  30       0.92  15  15   0   0    1.0000             1.0000        1.0  1.0000          1.0  0.0 0.0000 1.0000   1.0000  1.0000
        phase7_test_all_conditions  40       0.92  18  20   0   2    0.9500             0.9500        1.0  0.9000          1.0  0.0 0.1000 0.9474   1.0000  1.0000
 phase7_test_origin_training_scope  30       0.92  13  15   0   2    0.9333             0.9333        1.0  0.8667          1.0  0.0 0.1333 0.9286   1.0000  1.0000
         phase7_all_all_conditions 184       0.92  90  92   0   2    0.9891             0.9891        1.0  0.9783          1.0  0.0 0.0217 0.9890   0.9998  0.9998
  phase7_all_origin_training_scope 138       0.92  67  69   0   2    0.9855             0.9855        1.0  0.9710          1.0  0.0 0.0290 0.9853   1.0000  1.0000

## Phase 7 Condition Summary

         audit_condition  n  target_ai  mean_probability  detected_rate  threshold
         ai_clean_direct 23          1            0.9995          1.000       0.92
   ai_fabricated_partial 23          1            0.9977          1.000       0.92
      ai_mixer_processed 23          1            0.9962          1.000       0.92
             ai_replayed 23          1            0.9797          0.913       0.92
             human_clean 23          0            0.0807          0.000       0.92
human_fabricated_partial 23          0            0.2251          0.000       0.92
   human_mixer_processed 23          0            0.0075          0.000       0.92
          human_replayed 23          0            0.0059          0.000       0.92

## testing_audios Origin Metrics

                         scope  n  threshold  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr  fnr     f1  roc_auc  pr_auc
testing_audios_binary_human_ai 23       0.92   9  11   2   1    0.8696             0.8731     0.8182     0.9       0.8462 0.1538  0.1 0.8571   0.8769  0.7571

## testing_audios Remaining Origin Failures

test_id ground_truth_origin   manipulation_type language  origin_probability  origin_threshold  origin_pred                  expected_forensic_result
   T1.2               human        clean_direct  english              0.9918              0.92            1       Avoid false positive on clean audio
   T4.1               human        clean_direct  english              1.0000              0.92            1              Should not be called AI fake
   T4.5                  ai whatsapp_compressed  english              0.0815              0.92            0 Should detect spoof with compression note

## Stop Rule

- AI recall >= 0.90: `True`
- No new clean false positives vs current experimental model (<=2 known FPs): `True`
- Phase 2 stop rule pass: `True`

## Output Files

- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_phase7_predictions.csv`
- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_phase7_metrics.csv`
- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_phase7_condition_summary.csv`
- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_testing_audios_predictions.csv`
- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_testing_audios_metrics.csv`
- `E:\FYP\reports\release_audit\phase2_origin_release_2026-06-13\phase2_origin_testing_audios_errors.csv`