# Experimental Mixer/Channel Retrain

Generated: 2026-06-13T09:14:21.957840+00:00

Threshold selected on dev: `0.1`
Compression augmentation enabled: `True`

## Metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr    fnr     f1  roc_auc  pr_auc
           dev  30  10  17   3   0    0.9000             0.9250     0.7692  1.0000       0.8500 0.1500 0.0000 0.8696   0.9250  0.8230
     fit_train 312 260  44   8   0    0.9744             0.9231     0.9701  1.0000       0.8462 0.1538 0.0000 0.9848   0.9997  0.9999
          test  30  10  16   4   0    0.8667             0.9000     0.7143  1.0000       0.8000 0.2000 0.0000 0.8333   0.9900  0.9833
testing_audios  23   1  18   2   2    0.8261             0.6167     0.3333  0.3333       0.9000 0.1000 0.6667 0.3333   0.5000  0.4276
train_original  78  26  44   8   0    0.8974             0.9231     0.7647  1.0000       0.8462 0.1538 0.0000 0.8667   1.0000  1.0000

## Testing Audios Errors

prediction_scope sample_id test_id                 audio_path ground_truth_origin manipulation_type language  target_is_mixer_channel  mixer_probability  mixer_prediction feature_status
  testing_audios       NaN    T2.2 testing_audios/T2/T2.2.mp3               human   mixer_processed     urdu                        1             0.0010               0.0             ok
  testing_audios       NaN    T3.2 testing_audios/T3/T3.2.mp3                  ai         ai_replay  english                        0             0.1191               1.0             ok
  testing_audios       NaN    T3.4 testing_audios/T3/T3.4.mp3                  ai   mixer_processed  english                        1             0.0034               0.0             ok
  testing_audios       NaN    T4.1 testing_audios/T4/T4.1.mp3               human      clean_direct  english                        0             0.2538               1.0             ok

## Outputs

- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_channel_experimental_acoustic_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_channel_experimental_metadata.json`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_experimental_predictions.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_experimental_metrics.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_experimental_errors.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_2026-06-13\mixer_experimental_selected_features.csv`