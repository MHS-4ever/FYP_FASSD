# Phase 7 Final Release Matrix — testing_audios

Generated: 2026-06-13T14:10:59.725745+00:00

Current packaged release models + Phase 6 evidence band formatting.

## Axis metrics

   axis  n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity
 origin 18   9   6   2   1    0.8333             0.8250     0.8182  0.9000       0.7500
 replay 25   5  15   3   2    0.8000             0.7738     0.6250  0.7143       0.8333
  mixer 25   0  22   1   2    0.8800             0.4783     0.0000  0.0000       0.9565
partial 25   2  23   0   0    1.0000             1.0000     1.0000  1.0000       1.0000

## Failure table

  axis test_id                 audio_path   manipulation_type ground_truth_origin  target  prediction  origin_probability  replay_probability  mixer_probability  partial_max_segment_probability                partial_gate                                  notes
origin    T1.2 testing_audios/T1/T1.2.mp3        clean_direct               human       0         1.0            0.991797            0.000054           0.000010                         0.897389       low_partial_indicator       Clean studio/podcast human voice
origin    T4.1 testing_audios/T4/T4.1.mp3        clean_direct               human       0         1.0            0.999980            0.963236           0.668543                         1.000000 localized_pattern_supported           Known speaker real reference
origin    T4.5 testing_audios/T4/T4.5.mp3 whatsapp_compressed                  ai       1         0.0            0.081516            0.003228           0.004141                         0.013488       low_partial_indicator           Political/social media clone
replay    T2.2 testing_audios/T2/T2.2.mp3     mixer_processed               human       0         1.0            0.113736            0.977862           0.451023                         0.050806       low_partial_indicator  Human through laptop + mixer + mobile
replay    T3.2 testing_audios/T3/T3.2.mp3           ai_replay                  ai       1         0.0            0.994123            0.218526           0.000201                         0.035153       low_partial_indicator AI played on laptop recorded on mobile
replay    T3.3 testing_audios/T3/T3.3.mp4           ai_replay                  ai       1         0.0            0.992976            0.636298           0.294198                         0.578763       low_partial_indicator           AI through Bluetooth speaker
replay    T3.4 testing_audios/T3/T3.4.mp3     mixer_processed                  ai       0         1.0            0.965491            0.678430           0.010639                         0.039879       low_partial_indicator           AI through mixer then mobile
replay    T4.1 testing_audios/T4/T4.1.mp3        clean_direct               human       0         1.0            0.999980            0.963236           0.668543                         1.000000 localized_pattern_supported           Known speaker real reference
 mixer    T2.2 testing_audios/T2/T2.2.mp3     mixer_processed               human       1         0.0            0.113736            0.977862           0.451023                         0.050806       low_partial_indicator  Human through laptop + mixer + mobile
 mixer    T2.4 testing_audios/T2/T2.4.mp4        human_replay               human       0         1.0            0.005054            0.975861           0.994743                         0.126301       low_partial_indicator         Human Bluetooth speaker replay
 mixer    T3.4 testing_audios/T3/T3.4.mp3     mixer_processed                  ai       1         0.0            0.965491            0.678430           0.010639                         0.039879       low_partial_indicator           AI through mixer then mobile
