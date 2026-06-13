# Replay vs Channel Overlap Diagnosis

Generated: 2026-06-13T09:41:53.103806+00:00

Purpose: explain why replay retrain still confuses mixer/edited/channel cases with replay.

## Focus Testing Rows

test_id                 audio_path ground_truth_origin manipulation_type        diagnostic_group replay_probability replay_prediction target_is_replay  distance_to_phase7_replay_positive  distance_to_phase7_mixer_negative  distance_to_phase7_clean_negative       nearest_centroid
   T2.2 testing_audios/T2/T2.2.mp3               human   mixer_processed  testing_mixer_negative 0.9986190178695387               1.0                0                              1.3163                             1.4334                             1.8758 phase7_replay_positive
   T3.2 testing_audios/T3/T3.2.mp3                  ai         ai_replay testing_replay_positive 0.9493575196422877               0.0                1                              1.0742                             1.3874                             1.1682 phase7_replay_positive
   T3.4 testing_audios/T3/T3.4.mp3                  ai   mixer_processed  testing_mixer_negative 0.9964201213466788               1.0                0                              0.6192                             1.0870                             1.2711 phase7_replay_positive
   T4.1 testing_audios/T4/T4.1.mp3               human      clean_direct  testing_clean_negative 0.9319173738762814               0.0                0                              1.4229                             1.4316                             1.4955 phase7_replay_positive
   T5.5 testing_audios/T5/T5.5.mp3               human    edited_spliced testing_edited_negative 0.9665786879865593               1.0                0                              0.9768                             1.0421                             1.3082 phase7_replay_positive

## Top False-Positive Feature Gaps

                feature  false_positive_mean_z  phase7_replay_mean_z  phase7_mixer_mean_z  phase7_clean_mean_z  gap_false_positive_vs_phase7_replay_abs  closer_to_replay_than_mixer  closer_to_replay_than_clean
                rms_min                 0.0200                2.0278               0.0003               0.0131                                   2.0078                        False                        False
            mfcc_2_mean                 0.8044               -0.9907               0.5300              -0.0723                                   1.7951                        False                        False
  spectral_rolloff_mean                -0.3637                1.4155              -0.3288               0.0441                                   1.7792                        False                        False
high_freq_rolloff_ratio                -0.3637                1.4155              -0.3288               0.0441                                   1.7792                        False                        False
 spectral_centroid_mean                -0.3788                1.3165              -0.3879              -0.0031                                   1.6953                        False                        False
spectral_bandwidth_mean                -0.4952                1.1558              -0.3502              -0.0636                                   1.6510                        False                        False
 spectral_flatness_mean                -0.3097                1.3334              -0.4187              -0.0116                                   1.6432                        False                        False
zero_crossing_rate_mean                -0.3390                1.2781              -0.3159              -0.1291                                   1.6171                        False                        False
 high_band_energy_ratio                -0.0180                1.4104              -0.0799               0.0127                                   1.4284                        False                        False
  bandwidth_occupied_95                -0.0869                1.3060              -0.1915              -0.0443                                   1.3930                        False                        False
      noise_floor_proxy                 2.5518                1.2306               0.1884              -0.5797                                   1.3211                         True                         True
 zero_crossing_rate_std                -1.1138                0.1967              -0.7503               0.5961                                   1.3105                        False                         True
  spectral_flatness_std                -0.8858                0.2897              -0.7759               0.4422                                   1.1755                        False                         True
            mfcc_8_mean                 1.2097                0.1888              -0.9488               0.5967                                   1.0209                         True                        False
  spectral_centroid_std                -0.9686               -0.0410              -0.7257               0.8461                                   0.9276                        False                         True
            mfcc_3_mean                -1.0312               -0.2132              -0.4172               1.1238                                   0.8180                        False                         True
  spectral_entropy_mean                 0.4698                1.2806              -0.2719              -0.3603                                   0.8108                        False                         True
         mean_amplitude                 0.5509               -0.2351               0.8148              -0.2642                                   0.7861                        False                         True
               rms_mean                 0.3347               -0.3732               0.7508              -0.2268                                   0.7079                        False                        False
           mfcc_10_mean                 0.9271                0.3259              -1.1837               0.1454                                   0.6012                         True                         True
          std_amplitude                -0.2690               -0.8174               0.5617              -0.3517                                   0.5485                         True                        False
            mfcc_12_std                -1.4955               -0.9504              -0.0834               0.7777                                   0.5451                         True                         True
             mfcc_7_std                -1.3456               -0.8311              -0.0450               0.9602                                   0.5145                         True                         True
  low_band_energy_ratio                -0.8039               -1.2705               0.4005               0.4201                                   0.4666                         True                         True
         peak_amplitude                -0.9547               -0.5404               0.2296               0.6412                                   0.4143                         True                         True
             mfcc_3_std                -0.8268               -0.4199              -0.4224               1.0662                                   0.4069                        False                         True
            mfcc_6_mean                 0.6479                0.2410              -0.9923               0.6459                                   0.4068                         True                        False
           mfcc_11_mean                -0.0304               -0.4183              -0.4314               0.9656                                   0.3879                         True                         True
             mfcc_8_std                -1.1078               -0.7462              -0.1855               0.8570                                   0.3616                         True                         True
            mfcc_11_std                -1.0800               -0.7241               0.2980               0.8466                                   0.3559                         True                         True

## Group Probability Summary

       diagnostic_group   manipulation_type  n  mean_replay_probability  detected_rate
                  other           ai_replay 13                   0.9999         1.0000
                  other        clean_direct 26                   0.0116         0.0000
                  other        human_replay 13                   0.9919         0.9231
                  other     mixer_processed 26                   0.0188         0.0000
  phase7_clean_negative        clean_direct 46                   0.0556         0.0217
  phase7_mixer_negative     mixer_processed 46                   0.0587         0.0000
 phase7_replay_positive           ai_replay 23                   0.9999         1.0000
 phase7_replay_positive        human_replay 23                   0.9520         0.9130
 testing_clean_negative        clean_direct  8                   0.2273         0.0000
testing_edited_negative      edited_spliced  5                   0.6990         0.2000
 testing_mixer_negative     mixer_processed  2                   0.9975         1.0000
          testing_other   partial_ai_insert  2                   0.2481         0.0000
          testing_other whatsapp_compressed  1                   0.0008         0.0000
testing_replay_positive           ai_replay  2                   0.9745         0.5000
testing_replay_positive        human_replay  3                   0.9990         1.0000

## Interpretation

- If mixer/edited false positives are nearest to the replay centroid, replay and channel artifacts overlap in the current acoustic feature space.
- If the missed AI replay is near replay but below threshold, threshold/calibration is part of the issue.
- If clean/mixer/edited negatives have high replay probabilities, a two-stage manipulation design is more appropriate than independent replay and mixer binaries.

## Outputs

- `E:\FYP\reports\release_audit\replay_channel_overlap_diagnosis_2026-06-13\replay_testing_audio_centroid_distances.csv`
- `E:\FYP\reports\release_audit\replay_channel_overlap_diagnosis_2026-06-13\replay_focus_failure_rows.csv`
- `E:\FYP\reports\release_audit\replay_channel_overlap_diagnosis_2026-06-13\replay_false_positive_feature_gap_ranked.csv`
- `E:\FYP\reports\release_audit\replay_channel_overlap_diagnosis_2026-06-13\replay_group_probability_summary.csv`