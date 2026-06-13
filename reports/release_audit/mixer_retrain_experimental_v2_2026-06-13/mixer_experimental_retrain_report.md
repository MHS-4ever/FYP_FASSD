# Experimental Mixer/Channel Retrain

Generated: 2026-06-13T09:21:32.343031+00:00

Threshold selected on dev: `0.23`
Compression augmentation enabled: `True`
Augmentation policy: `v2_balanced`
Minimum dev specificity preference: `0.9`

## Metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr  fnr     f1  roc_auc  pr_auc
           dev  30  10  19   1   0    0.9667             0.9750     0.9091     1.0       0.9500 0.0500  0.0 0.9524   0.9550  0.8480
     fit_train 338 182 154   2   0    0.9941             0.9936     0.9891     1.0       0.9872 0.0128  0.0 0.9945   1.0000  1.0000
          test  30   9  20   0   1    0.9667             0.9500     1.0000     0.9       1.0000 0.0000  0.1 0.9474   1.0000  1.0000
testing_audios  23   0  20   0   3    0.8696             0.5000     0.0000     0.0       1.0000 0.0000  1.0 0.0000   0.7667  0.6181
train_original  78  26  52   0   0    1.0000             1.0000     1.0000     1.0       1.0000 0.0000  0.0 1.0000   1.0000  1.0000

## Testing Audios Errors

prediction_scope sample_id test_id                 audio_path ground_truth_origin   manipulation_type language  target_is_mixer_channel  mixer_probability  mixer_prediction feature_status
  testing_audios       NaN    T2.2 testing_audios/T2/T2.2.mp3               human     mixer_processed     urdu                        1             0.0012               0.0             ok
  testing_audios       NaN    T3.4 testing_audios/T3/T3.4.mp3                  ai     mixer_processed  english                        1             0.0001               0.0             ok
  testing_audios       NaN    T4.5 testing_audios/T4/T4.5.mp3                  ai whatsapp_compressed  english                        1             0.0694               0.0             ok

## Outputs

- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_channel_experimental_acoustic_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_channel_experimental_metadata.json`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_experimental_predictions.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_experimental_metrics.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_experimental_errors.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v2_2026-06-13\mixer_experimental_selected_features.csv`