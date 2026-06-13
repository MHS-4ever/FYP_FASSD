# Mixer Feature Gap Diagnosis

Generated: 2026-06-13T09:23:43.346785+00:00

Purpose: explain why mixer/channel retrain v2 scores external mixer/compression examples as non-mixer.

## Testing Mixer Positive Distances

test_id                 audio_path ground_truth_origin   manipulation_type       diagnostic_group     mixer_probability mixer_prediction  distance_to_phase7_mixer_positive  distance_to_phase7_clean_negative  distance_to_phase7_replay_negative       nearest_centroid
   T2.2 testing_audios/T2/T2.2.mp3               human     mixer_processed testing_mixer_positive 0.0011606625094412043              0.0                             1.4334                             1.8758                              1.3163 phase7_replay_negative
   T3.4 testing_audios/T3/T3.4.mp3                  ai     mixer_processed testing_mixer_positive 8.848897376509723e-05              0.0                             1.0870                             1.2711                              0.6192 phase7_replay_negative
   T4.5 testing_audios/T4/T4.5.mp3                  ai whatsapp_compressed testing_mixer_positive   0.06937862125264213              0.0                             1.5700                             1.3232                              1.9902  phase7_clean_negative

## Top Feature Gaps

                feature  phase7_mixer_mean_z  phase7_clean_mean_z  phase7_replay_mean_z  testing_mixer_mean_z  gap_testing_vs_phase7_mixer_abs  closer_to_clean_than_mixer  closer_to_replay_than_mixer
            mfcc_7_mean               0.5211               0.3632               -1.1484               -2.4449                           2.9659                        True                         True
            mfcc_8_mean              -0.9488               0.5967                0.1888                1.2805                           2.2292                        True                         True
  mid_band_energy_ratio              -0.4366              -0.5090                0.7363                1.5318                           1.9684                       False                         True
            mfcc_9_mean               0.7126               0.4002               -0.9491               -1.0134                           1.7260                        True                         True
           mfcc_10_mean              -1.1837               0.1454                0.3259                0.5135                           1.6972                        True                         True
  low_band_energy_ratio               0.4005               0.4201               -1.2705               -1.2945                           1.6950                       False                         True
                rms_std               0.4528              -0.1246               -1.2762               -1.2292                           1.6820                        True                         True
            mfcc_4_mean               0.4515               0.0319               -1.3759               -1.1907                           1.6422                        True                         True
      noise_floor_proxy               0.1884              -0.5797                1.2306                1.7714                           1.5830                       False                         True
            mfcc_5_mean              -0.1117               0.2680               -0.8243               -1.6041                           1.4923                       False                         True
         peak_amplitude               0.2296               0.6412               -0.5404               -1.0600                           1.2896                       False                         True
                rms_max               0.3915              -0.0226               -0.8383               -0.8457                           1.2373                        True                         True
           mfcc_11_mean              -0.4314               0.9656               -0.4183                0.7557                           1.1871                        True                         True
    dynamic_range_proxy               0.3973               0.0047               -0.9825               -0.7744                           1.1717                        True                         True
   spectral_entropy_std               0.0706               0.5608               -1.1073               -1.0875                           1.1581                       False                         True
  spectral_contrast_std               0.3118               0.9288               -1.1267               -0.6865                           0.9983                       False                         True
            mfcc_6_mean              -0.9923               0.6459                0.2410               -0.2065                           0.7858                       False                         True
           mfcc_13_mean              -0.4718               1.1513               -0.1304                0.2990                           0.7708                       False                         True
             mfcc_3_std              -0.4224               1.0662               -0.4199                0.3150                           0.7375                       False                         True
          std_amplitude               0.5617              -0.3517               -0.8174               -0.1708                           0.7325                        True                         True
            mfcc_3_mean              -0.4172               1.1238               -0.2132               -1.0803                           0.6631                       False                        False
             mfcc_9_std               0.1326               0.9934               -0.7352                0.7871                           0.6545                        True                        False
 spectral_contrast_mean               0.8622               0.1949               -0.9019                0.2481                           0.6141                        True                        False
spectral_bandwidth_mean              -0.3502              -0.0636                1.1558               -0.9040                           0.5538                       False                        False
  spectral_flatness_std              -0.7759               0.4422                0.2897               -1.3096                           0.5337                       False                        False
              dc_offset               0.0230               0.5661               -0.1542               -0.5047                           0.5278                       False                         True
  spectral_entropy_mean              -0.2719              -0.3603                1.2806                0.2531                           0.5250                       False                        False
            mfcc_12_std              -0.0834               0.7777               -0.9504                0.4017                           0.4852                        True                        False
             mfcc_1_std               0.0502               1.3576               -0.4981                0.5123                           0.4621                       False                        False
           mfcc_12_mean              -0.7861               0.0693                0.2645               -0.3572                           0.4289                        True                        False

## Group Probability Summary

       diagnostic_group   manipulation_type   n  mean_mixer_probability  detected_rate
                  other           ai_replay  39                  0.0005         0.0000
                  other        clean_direct 104                  0.2646         0.2596
                  other      edited_spliced   5                  0.0005         0.0000
                  other        human_replay  39                  0.0258         0.0256
                  other     mixer_processed 156                  0.9779         1.0000
                  other   partial_ai_insert   2                  0.0001         0.0000
  phase7_clean_negative        clean_direct  46                  0.0157         0.0000
  phase7_mixer_positive     mixer_processed  46                  0.9241         0.9783
 phase7_replay_negative           ai_replay  23                  0.0001         0.0000
 phase7_replay_negative        human_replay  23                  0.0530         0.0435
 testing_clean_negative        clean_direct   8                  0.0011         0.0000
 testing_mixer_positive     mixer_processed   2                  0.0006         0.0000
 testing_mixer_positive whatsapp_compressed   1                  0.0694         0.0000
testing_replay_negative           ai_replay   2                  0.0000         0.0000
testing_replay_negative        human_replay   3                  0.0002         0.0000

## Interpretation Guide

- If testing mixer positives are nearest to clean/replay centroids, the training mixer distribution does not match the external cases.
- Large feature gaps show which acoustic dimensions differ most from Phase 7 mixer positives.
- Features marked closer to clean/replay than mixer indicate likely reasons for missed detection.

## Outputs

- `E:\FYP\reports\release_audit\mixer_feature_gap_diagnosis_2026-06-13\mixer_testing_audio_centroid_distances.csv`
- `E:\FYP\reports\release_audit\mixer_feature_gap_diagnosis_2026-06-13\mixer_feature_gap_ranked.csv`
- `E:\FYP\reports\release_audit\mixer_feature_gap_diagnosis_2026-06-13\mixer_group_probability_summary.csv`