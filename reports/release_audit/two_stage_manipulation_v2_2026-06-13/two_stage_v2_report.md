# Two-Stage Manipulation Prototype V2

Generated: 2026-06-13T10:01:14.757828+00:00

Stage 1 threshold: `0.45`
Stage 2 min confidence: `0.7`
Proxy rows: `200`
Stage 2 classes: `mixer_channel, partial_insert, replay, unknown_channel_artifact`

## Stage 1 Metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity  fpr    fnr     f1
           dev  40  21   8   2   9    0.7250             0.7500     0.9130  0.7000         0.80 0.20 0.3000 0.7925
     fit_train 304 240  26   0  38    0.8750             0.9317     1.0000  0.8633         1.00 0.00 0.1367 0.9266
          test  40  21   9   1   9    0.7500             0.8000     0.9545  0.7000         0.90 0.10 0.3000 0.8077
testing_audios  23   8   6   2   7    0.6087             0.6417     0.8000  0.5333         0.75 0.25 0.4667 0.6400
         train 104  53  26   0  25    0.7596             0.8397     1.0000  0.6795         1.00 0.00 0.3205 0.8092

## Subtype Metrics

         scope   n  accuracy_exact  unknown_rate  safe_non_clean_rate
         train  78          0.6795        0.0000               0.6795
     fit_train 278          0.8633        0.3129               0.8633
           dev  30          0.6333        0.0333               0.7000
          test  30          0.6667        0.0000               0.7000
testing_audios  15          0.2667        0.1333               0.5333

## Testing Focus

   test_id                               audio_path ground_truth_origin   manipulation_type  stage1_target_manipulated  stage1_manipulation_probability  stage1_manipulation_prediction stage2_expected_type          stage2_raw_type  stage2_confidence     stage2_reported_type      final_reported_type              feature_status
      T1.1               testing_audios/T1/T1.1.mp3               human        clean_direct                          0                           0.5604                             1.0                clean                   replay             0.9314                   replay                   replay                          ok
      T1.2               testing_audios/T1/T1.2.mp3               human        clean_direct                          0                           0.0039                             0.0                clean unknown_channel_artifact             0.7935 unknown_channel_artifact                    clean                          ok
      T1.3               testing_audios/T1/T1.3.mp3                  ai        clean_direct                          0                           0.0294                             0.0                clean           partial_insert             0.9987           partial_insert                    clean                          ok
      T1.4               testing_audios/T1/T1.4.mp3                  ai        clean_direct                          0                           0.0035                             0.0                clean           partial_insert             0.5132 unknown_channel_artifact                    clean                          ok
      T1.5               testing_audios/T1/T1.5.wav                  ai        clean_direct                          0                           0.0294                             0.0                clean           partial_insert             0.9987           partial_insert                    clean                          ok
      T2.1               testing_audios/T2/T2.1.mp3               human        human_replay                          1                           0.9035                             1.0               replay                   replay             0.9997                   replay                   replay                          ok
      T2.2               testing_audios/T2/T2.2.mp3               human     mixer_processed                          1                           0.8874                             1.0        mixer_channel                   replay             0.9963                   replay                   replay                          ok
      T2.3               testing_audios/T2/T2.3.mp3               human        human_replay                          1                           0.9752                             1.0               replay                   replay             1.0000                   replay                   replay                          ok
      T2.4               testing_audios/T2/T2.4.mp4               human        human_replay                          1                              NaN                             NaN               replay                                         NaN                                             clean unsupported_audio_extension
      T2.5               testing_audios/T2/T2.5.mp3               human        human_replay                          1                           0.4884                             1.0               replay                   replay             0.9999                   replay                   replay                          ok
      T3.1               testing_audios/T3/T3.1.mp3                  ai        clean_direct                          0                           0.0294                             0.0                clean           partial_insert             0.9987           partial_insert                    clean                          ok
      T3.2               testing_audios/T3/T3.2.mp3                  ai           ai_replay                          1                           0.2304                             0.0               replay unknown_channel_artifact             0.6047 unknown_channel_artifact                    clean                          ok
      T3.3               testing_audios/T3/T3.3.mp4                  ai           ai_replay                          1                              NaN                             NaN               replay                                         NaN                                             clean unsupported_audio_extension
      T3.4               testing_audios/T3/T3.4.mp3                  ai     mixer_processed                          1                           0.3704                             0.0        mixer_channel                   replay             0.9898                   replay                    clean                          ok
      T3.5               testing_audios/T3/T3.5.mp3                  ai           ai_replay                          1                           0.8947                             1.0               replay                   replay             0.9997                   replay                   replay                          ok
      T4.1               testing_audios/T4/T4.1.mp3               human        clean_direct                          0                           0.8689                             1.0                clean unknown_channel_artifact             0.6643 unknown_channel_artifact unknown_channel_artifact                          ok
      T4.2               testing_audios/T4/T4.2.mp3                  ai        clean_direct                          0                           0.0035                             0.0                clean           partial_insert             0.5132 unknown_channel_artifact                    clean                          ok
      T4.3               testing_audios/T4/T4.3.mp3               mixed   partial_ai_insert                          1                           0.0042                             0.0       partial_insert unknown_channel_artifact             0.7821 unknown_channel_artifact                    clean                          ok
      T4.5               testing_audios/T4/T4.5.mp3                  ai whatsapp_compressed                          1                           0.1130                             0.0 platform_compression unknown_channel_artifact             0.6581 unknown_channel_artifact                    clean                          ok
      T5.1               testing_audios/T5/T5.1.mp3               human      edited_spliced                          1                           0.4684                             1.0       edited_spliced                   replay             0.9065                   replay                   replay                          ok
      T5.2               testing_audios/T5/T5.2.mp3               human      edited_spliced                          1                           0.1663                             0.0       edited_spliced unknown_channel_artifact             0.9637 unknown_channel_artifact                    clean                          ok
      T5.3               testing_audios/T5/T5.3.mp3               human      edited_spliced                          1                           0.4632                             1.0       edited_spliced unknown_channel_artifact             0.7390 unknown_channel_artifact unknown_channel_artifact                          ok
      T5.4               testing_audios/T5/T5.4.mp3               human      edited_spliced                          1                           0.3984                             0.0       edited_spliced unknown_channel_artifact             0.5980 unknown_channel_artifact                    clean                          ok
      T5.5               testing_audios/T5/T5.5.mp3               human      edited_spliced                          1                           0.3611                             0.0       edited_spliced                   replay             0.9663                   replay                    clean                          ok
T5_FAB_001 testing_audios/fabricated/fabricated.mp3               mixed   partial_ai_insert                          1                           0.5096                             1.0       partial_insert unknown_channel_artifact             0.7341 unknown_channel_artifact unknown_channel_artifact                          ok

## Testing Classification Report

                          precision    recall  f1-score   support

                   clean       0.00      0.00      0.00         0
          edited_spliced       0.00      0.00      0.00         5
           mixer_channel       0.00      0.00      0.00         2
          partial_insert       0.00      0.00      0.00         2
    platform_compression       0.00      0.00      0.00         1
                  replay       0.67      0.80      0.73         5
unknown_channel_artifact       0.00      0.00      0.00         0

                accuracy                           0.27        15
               macro avg       0.10      0.11      0.10        15
            weighted avg       0.22      0.27      0.24        15


## Outputs

- `E:\FYP\reports\release_audit\two_stage_manipulation_v2_2026-06-13\two_stage_v2_predictions.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_v2_2026-06-13\two_stage_v2_stage1_metrics.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_v2_2026-06-13\two_stage_v2_subtype_metrics.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_v2_2026-06-13\two_stage_v2_testing_focus.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_v2_2026-06-13\two_stage_v2_metadata.json`