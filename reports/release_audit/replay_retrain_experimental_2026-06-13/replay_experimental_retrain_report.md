# Experimental Replay Retrain

Generated: 2026-06-13T09:38:29.020828+00:00

Threshold selected on dev: `0.95`
Hard negatives: `clean_direct`, `mixer_processed`

## Metrics

         scope  n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr    fnr     f1  roc_auc  pr_auc
           dev 30   9  20   0   1    0.9667             0.9500     1.0000  0.9000       1.0000 0.0000 0.1000 0.9474   0.9550  0.9526
     fit_train 78  25  52   0   1    0.9872             0.9808     1.0000  0.9615       1.0000 0.0000 0.0385 0.9804   1.0000  1.0000
          test 30  10  19   1   0    0.9667             0.9750     0.9091  1.0000       0.9500 0.0500 0.0000 0.9524   1.0000  1.0000
testing_audios 23   4  15   3   1    0.8261             0.8167     0.5714  0.8000       0.8333 0.1667 0.2000 0.6667   0.9556  0.8850
train_original 78  25  52   0   1    0.9872             0.9808     1.0000  0.9615       1.0000 0.0000 0.0385 0.9804   1.0000  1.0000

## Testing Audios Errors

prediction_scope sample_id test_id                 audio_path ground_truth_origin manipulation_type language  target_is_replay  replay_probability  replay_prediction feature_status
  testing_audios       NaN    T2.2 testing_audios/T2/T2.2.mp3               human   mixer_processed     urdu                 0              0.9986                1.0             ok
  testing_audios       NaN    T3.2 testing_audios/T3/T3.2.mp3                  ai         ai_replay  english                 1              0.9494                0.0             ok
  testing_audios       NaN    T3.4 testing_audios/T3/T3.4.mp3                  ai   mixer_processed  english                 0              0.9964                1.0             ok
  testing_audios       NaN    T5.5 testing_audios/T5/T5.5.mp3               human    edited_spliced     urdu                 0              0.9666                1.0             ok

## Outputs

- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_acoustic_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_metadata.json`
- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_predictions.csv`
- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_metrics.csv`
- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_errors.csv`
- `E:\FYP\reports\release_audit\replay_retrain_experimental_2026-06-13\replay_experimental_selected_features.csv`