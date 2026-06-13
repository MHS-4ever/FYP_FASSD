# Experimental Mixer/Channel Retrain

Generated: 2026-06-13T09:32:14.610542+00:00

Threshold selected on dev: `0.51`
Compression augmentation enabled: `True`
Augmentation policy: `v3_targeted`
Minimum dev specificity preference: `0.9`

## Metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr    fnr     f1  roc_auc  pr_auc
           dev  30   9  18   2   1    0.9000             0.9000     0.8182  0.9000       0.9000 0.1000 0.1000 0.8571   0.9250  0.7572
     fit_train 728 556 155   1  16    0.9766             0.9828     0.9982  0.9720       0.9936 0.0064 0.0280 0.9849   0.9990  0.9997
          test  30   7  19   1   3    0.8667             0.8250     0.8750  0.7000       0.9500 0.0500 0.3000 0.7778   0.9350  0.9265
testing_audios  23   1  18   2   2    0.8261             0.6167     0.3333  0.3333       0.9000 0.1000 0.6667 0.3333   0.8167  0.4000
train_original  78  24  52   0   2    0.9744             0.9615     1.0000  0.9231       1.0000 0.0000 0.0769 0.9600   1.0000  1.0000

## Testing Audios Errors

prediction_scope sample_id test_id                 audio_path ground_truth_origin   manipulation_type language  target_is_mixer_channel  mixer_probability  mixer_prediction feature_status
  testing_audios       NaN    T2.3 testing_audios/T2/T2.3.mp3               human        human_replay     urdu                        0             0.7703               1.0             ok
  testing_audios       NaN    T3.4 testing_audios/T3/T3.4.mp3                  ai     mixer_processed  english                        1             0.0025               0.0             ok
  testing_audios       NaN    T4.1 testing_audios/T4/T4.1.mp3               human        clean_direct  english                        0             0.9967               1.0             ok
  testing_audios       NaN    T4.5 testing_audios/T4/T4.5.mp3                  ai whatsapp_compressed  english                        1             0.0247               0.0             ok

## Outputs

- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_channel_experimental_acoustic_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_channel_experimental_metadata.json`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_experimental_predictions.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_experimental_metrics.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_experimental_errors.csv`
- `E:\FYP\reports\release_audit\mixer_retrain_experimental_v3_2026-06-13\mixer_experimental_selected_features.csv`