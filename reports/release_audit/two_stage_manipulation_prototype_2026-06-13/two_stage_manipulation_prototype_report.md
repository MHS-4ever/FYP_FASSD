# Two-Stage Manipulation Prototype

Generated: 2026-06-13T09:50:38.492603+00:00

Stage 1 threshold: `0.73`
Stage 2 min confidence: `0.55`
Stage 2 trained classes: `mixer_channel, partial_insert, replay`

## Stage 1 Metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity  fpr    fnr     f1
           dev  40  22   9   1   8    0.7750             0.8167     0.9565  0.7333          0.9  0.1 0.2667 0.8302
          test  40  21  10   0   9    0.7750             0.8500     1.0000  0.7000          1.0  0.0 0.3000 0.8235
testing_audios  23   5   8   0  10    0.5652             0.6667     1.0000  0.3333          1.0  0.0 0.6667 0.5000
         train 104  53  26   0  25    0.7596             0.8397     1.0000  0.6795          1.0  0.0 0.3205 0.8092

## Stage 2 Metrics

         scope  n  accuracy  unknown_rate
         train 78    1.0000        0.0000
           dev 30    0.9000        0.0333
          test 30    0.9333        0.0000
testing_audios 15    0.3333        0.0667

## Testing Audios Focus

   test_id                               audio_path ground_truth_origin   manipulation_type  stage1_target_manipulated  stage1_manipulation_probability  stage1_manipulation_prediction stage2_expected_type stage2_raw_type  stage2_confidence     stage2_reported_type              feature_status
      T1.1               testing_audios/T1/T1.1.mp3               human        clean_direct                          0                           0.6850                             0.0                clean          replay             0.9409                   replay                          ok
      T1.2               testing_audios/T1/T1.2.mp3               human        clean_direct                          0                           0.0022                             0.0                clean  partial_insert             0.9999           partial_insert                          ok
      T1.3               testing_audios/T1/T1.3.mp3                  ai        clean_direct                          0                           0.2513                             0.0                clean  partial_insert             1.0000           partial_insert                          ok
      T1.4               testing_audios/T1/T1.4.mp3                  ai        clean_direct                          0                           0.0083                             0.0                clean  partial_insert             0.9996           partial_insert                          ok
      T1.5               testing_audios/T1/T1.5.wav                  ai        clean_direct                          0                           0.2629                             0.0                clean  partial_insert             1.0000           partial_insert                          ok
      T2.1               testing_audios/T2/T2.1.mp3               human        human_replay                          1                           0.9925                             1.0               replay          replay             0.9976                   replay                          ok
      T2.2               testing_audios/T2/T2.2.mp3               human     mixer_processed                          1                           0.9915                             1.0        mixer_channel          replay             0.9993                   replay                          ok
      T2.3               testing_audios/T2/T2.3.mp3               human        human_replay                          1                           0.9993                             1.0               replay          replay             1.0000                   replay                          ok
      T2.4               testing_audios/T2/T2.4.mp4               human        human_replay                          1                              NaN                             NaN               replay                                NaN                          unsupported_audio_extension
      T2.5               testing_audios/T2/T2.5.mp3               human        human_replay                          1                           0.7280                             0.0               replay          replay             0.9989                   replay                          ok
      T3.1               testing_audios/T3/T3.1.mp3                  ai        clean_direct                          0                           0.2513                             0.0                clean  partial_insert             1.0000           partial_insert                          ok
      T3.2               testing_audios/T3/T3.2.mp3                  ai           ai_replay                          1                           0.1252                             0.0               replay  partial_insert             0.7251           partial_insert                          ok
      T3.3               testing_audios/T3/T3.3.mp4                  ai           ai_replay                          1                              NaN                             NaN               replay                                NaN                          unsupported_audio_extension
      T3.4               testing_audios/T3/T3.4.mp3                  ai     mixer_processed                          1                           0.4468                             0.0        mixer_channel          replay             0.9914                   replay                          ok
      T3.5               testing_audios/T3/T3.5.mp3                  ai           ai_replay                          1                           0.9014                             1.0               replay          replay             0.9985                   replay                          ok
      T4.1               testing_audios/T4/T4.1.mp3               human        clean_direct                          0                           0.6329                             0.0                clean          replay             0.7430                   replay                          ok
      T4.2               testing_audios/T4/T4.2.mp3                  ai        clean_direct                          0                           0.0083                             0.0                clean  partial_insert             0.9996           partial_insert                          ok
      T4.3               testing_audios/T4/T4.3.mp3               mixed   partial_ai_insert                          1                           0.0024                             0.0       partial_insert  partial_insert             0.9999           partial_insert                          ok
      T4.5               testing_audios/T4/T4.5.mp3                  ai whatsapp_compressed                          1                           0.4893                             0.0 platform_compression  partial_insert             0.9877           partial_insert                          ok
      T5.1               testing_audios/T5/T5.1.mp3               human      edited_spliced                          1                           0.4533                             0.0       edited_spliced          replay             0.9767                   replay                          ok
      T5.2               testing_audios/T5/T5.2.mp3               human      edited_spliced                          1                           0.2876                             0.0       edited_spliced  partial_insert             0.5721           partial_insert                          ok
      T5.3               testing_audios/T5/T5.3.mp3               human      edited_spliced                          1                           0.4770                             0.0       edited_spliced          replay             0.8930                   replay                          ok
      T5.4               testing_audios/T5/T5.4.mp3               human      edited_spliced                          1                           0.5923                             0.0       edited_spliced          replay             0.7486                   replay                          ok
      T5.5               testing_audios/T5/T5.5.mp3               human      edited_spliced                          1                           0.2291                             0.0       edited_spliced          replay             0.9842                   replay                          ok
T5_FAB_001 testing_audios/fabricated/fabricated.mp3               mixed   partial_ai_insert                          1                           0.7438                             1.0       partial_insert  partial_insert             0.5122 unknown_channel_artifact                          ok

## Classification Report: Testing Stage 2 Known/Expected Types

                          precision    recall  f1-score   support

          edited_spliced       0.00      0.00      0.00         5
           mixer_channel       0.00      0.00      0.00         2
          partial_insert       0.25      0.50      0.33         2
    platform_compression       0.00      0.00      0.00         1
                  replay       0.40      0.80      0.53         5
unknown_channel_artifact       0.00      0.00      0.00         0

                accuracy                           0.33        15
               macro avg       0.11      0.22      0.14        15
            weighted avg       0.17      0.33      0.22        15


## Outputs

- `E:\FYP\reports\release_audit\two_stage_manipulation_prototype_2026-06-13\two_stage_predictions.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_prototype_2026-06-13\two_stage_stage1_metrics.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_prototype_2026-06-13\two_stage_stage2_metrics.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_prototype_2026-06-13\two_stage_testing_audios_focus.csv`
- `E:\FYP\reports\release_audit\two_stage_manipulation_prototype_2026-06-13\two_stage_metadata.json`