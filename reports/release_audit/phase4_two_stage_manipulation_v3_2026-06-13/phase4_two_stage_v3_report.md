# Phase 4 — Two-Stage Manipulation v3

Generated: 2026-06-13T13:32:09.559419+00:00

Stage 1 threshold (dev): `0.42`
Stage 2 min confidence (dev): `0.4`
Synthetic/aug train rows: `876`
Stage 2 classes: `edited_spliced, mixer_channel, partial_insert, platform_compression, replay, unknown_channel_artifact`

## Stop rule (manipulated testing_audios Stage-1 recall >= 70%)

- n_manipulated: 15
- recall: 0.2000
- **FAIL**

## Stage 1 metrics

         scope   n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr    fnr     f1
           dev  40  14  10   0  16    0.6000             0.7333     1.0000  0.4667       1.0000 0.0000 0.5333 0.6364
     fit_train 980 707 122   8 143    0.8459             0.8851     0.9888  0.8318       0.9385 0.0615 0.1682 0.9035
          test  40  10  10   0  20    0.5000             0.6667     1.0000  0.3333       1.0000 0.0000 0.6667 0.5000
testing_audios  23   3   7   1  12    0.4348             0.5375     0.7500  0.2000       0.8750 0.1250 0.8000 0.3158
         train 104  29  25   1  49    0.5192             0.6667     0.9667  0.3718       0.9615 0.0385 0.6282 0.5370

## Stage 2 subtype metrics

         scope   n  accuracy_exact  unknown_rate  safe_non_clean_rate
         train  78          0.3205        0.0256               0.3718
     fit_train 954          0.6080        0.1006               0.7484
           dev  30          0.3667        0.0000               0.4667
          test  30          0.2667        0.0000               0.3333
testing_audios  15          0.1333        0.0000               0.2000

## Testing audios focus

   test_id                               audio_path   manipulation_type  stage1_target_manipulated  stage1_manipulation_probability  stage1_manipulation_prediction stage2_expected_type          stage2_raw_type  stage2_confidence     stage2_reported_type final_reported_type              feature_status
      T1.1               testing_audios/T1/T1.1.mp3        clean_direct                          0                           0.0285                             0.0                clean           edited_spliced             0.6622           edited_spliced               clean                          ok
      T1.2               testing_audios/T1/T1.2.mp3        clean_direct                          0                           0.0021                             0.0                clean           edited_spliced             0.5708           edited_spliced               clean                          ok
      T1.3               testing_audios/T1/T1.3.mp3        clean_direct                          0                           0.0245                             0.0                clean           partial_insert             0.9999           partial_insert               clean                          ok
      T1.4               testing_audios/T1/T1.4.mp3        clean_direct                          0                           0.1481                             0.0                clean unknown_channel_artifact             0.5664 unknown_channel_artifact               clean                          ok
      T1.5               testing_audios/T1/T1.5.wav        clean_direct                          0                           0.0248                             0.0                clean           partial_insert             0.9999           partial_insert               clean                          ok
      T2.1               testing_audios/T2/T2.1.mp3        human_replay                          1                           0.4593                             1.0               replay                   replay             0.8077                   replay              replay                          ok
      T2.2               testing_audios/T2/T2.2.mp3     mixer_processed                          1                           0.9186                             1.0        mixer_channel            mixer_channel             0.5460            mixer_channel       mixer_channel                          ok
      T2.3               testing_audios/T2/T2.3.mp3        human_replay                          1                           0.9706                             1.0               replay            mixer_channel             0.7073            mixer_channel       mixer_channel                          ok
      T2.4               testing_audios/T2/T2.4.mp4        human_replay                          1                              NaN                             NaN               replay                                         NaN                                        clean unsupported_audio_extension
      T2.5               testing_audios/T2/T2.5.mp3        human_replay                          1                           0.0228                             0.0               replay                   replay             0.9864                   replay               clean                          ok
      T3.1               testing_audios/T3/T3.1.mp3        clean_direct                          0                           0.0245                             0.0                clean           partial_insert             0.9999           partial_insert               clean                          ok
      T3.2               testing_audios/T3/T3.2.mp3           ai_replay                          1                           0.0545                             0.0               replay unknown_channel_artifact             0.7133 unknown_channel_artifact               clean                          ok
      T3.3               testing_audios/T3/T3.3.mp4           ai_replay                          1                              NaN                             NaN               replay                                         NaN                                        clean unsupported_audio_extension
      T3.4               testing_audios/T3/T3.4.mp3     mixer_processed                          1                           0.1548                             0.0        mixer_channel                   replay             0.8269                   replay               clean                          ok
      T3.5               testing_audios/T3/T3.5.mp3           ai_replay                          1                           0.1627                             0.0               replay                   replay             0.6498                   replay               clean                          ok
      T4.1               testing_audios/T4/T4.1.mp3        clean_direct                          0                           0.9947                             1.0                clean            mixer_channel             0.8448            mixer_channel       mixer_channel                          ok
      T4.2               testing_audios/T4/T4.2.mp3        clean_direct                          0                           0.1481                             0.0                clean unknown_channel_artifact             0.5664 unknown_channel_artifact               clean                          ok
      T4.3               testing_audios/T4/T4.3.mp3   partial_ai_insert                          1                           0.0050                             0.0       partial_insert           partial_insert             0.9619           partial_insert               clean                          ok
      T4.5               testing_audios/T4/T4.5.mp3 whatsapp_compressed                          1                           0.0800                             0.0 platform_compression unknown_channel_artifact             0.9423 unknown_channel_artifact               clean                          ok
      T5.1               testing_audios/T5/T5.1.mp3      edited_spliced                          1                           0.0570                             0.0       edited_spliced           edited_spliced             0.9202           edited_spliced               clean                          ok
      T5.2               testing_audios/T5/T5.2.mp3      edited_spliced                          1                           0.0702                             0.0       edited_spliced           edited_spliced             0.9093           edited_spliced               clean                          ok
      T5.3               testing_audios/T5/T5.3.mp3      edited_spliced                          1                           0.2807                             0.0       edited_spliced           edited_spliced             0.4880           edited_spliced               clean                          ok
      T5.4               testing_audios/T5/T5.4.mp3      edited_spliced                          1                           0.0384                             0.0       edited_spliced unknown_channel_artifact             0.8204 unknown_channel_artifact               clean                          ok
      T5.5               testing_audios/T5/T5.5.mp3      edited_spliced                          1                           0.0321                             0.0       edited_spliced           edited_spliced             0.8355           edited_spliced               clean                          ok
T5_FAB_001 testing_audios/fabricated/fabricated.mp3   partial_ai_insert                          1                           0.0706                             0.0       partial_insert           edited_spliced             0.8135           edited_spliced               clean                          ok

## Stop-rule guidance

Stage-1 recall on manipulated `testing_audios` is below 70%. Do not keep retraining this axis in Phase 4; document the limitation and proceed to Phase 6 calibration / honest UI wording.
