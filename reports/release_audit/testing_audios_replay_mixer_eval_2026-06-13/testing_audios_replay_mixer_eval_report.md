# Testing Audios Replay + Mixer Axis Evaluation

Generated: 2026-06-13T08:41:07.610222+00:00

Fast file-level acoustic evaluation only. No WavLM, no partial segmentation.

Rows: 25 | ok: 23 | unsupported/missing: 2

## Metrics

  axis                       scope  n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity    fpr  fnr     f1  roc_auc  pr_auc
replay supported_human_ai_nonmixed 21   4  13   3   1    0.8095             0.8062     0.5714     0.8       0.8125 0.1875  0.2 0.6667   0.9000  0.7117
 mixer supported_human_ai_nonmixed 21   0  18   0   3    0.8571             0.5000     0.0000     0.0       1.0000 0.0000  1.0 0.0000   0.5926  0.2937

## Errors

  axis test_id ground_truth_origin   manipulation_type language  target  prediction  probability                  expected_forensic_result
replay    T2.2               human     mixer_processed     urdu       0           1       0.9779       Avoid false FAKE on processed human
replay    T3.2                  ai           ai_replay  english       1           0       0.2185        Should detect spoof + replay hints
replay    T3.4                  ai     mixer_processed  english       0           1       0.6784                    Should detect as spoof
replay    T4.1               human        clean_direct  english       0           1       0.9632              Should not be called AI fake
 mixer    T2.2               human     mixer_processed     urdu       1           0       0.4510       Avoid false FAKE on processed human
 mixer    T3.4                  ai     mixer_processed  english       1           0       0.0106                    Should detect as spoof
 mixer    T4.5                  ai whatsapp_compressed  english       1           0       0.0041 Should detect spoof with compression note

## Output files

- `E:\FYP\reports\release_audit\testing_audios_replay_mixer_eval_2026-06-13\testing_audios_replay_mixer_predictions.csv`
- `E:\FYP\reports\release_audit\testing_audios_replay_mixer_eval_2026-06-13\testing_audios_replay_mixer_metrics.csv`
- `E:\FYP\reports\release_audit\testing_audios_replay_mixer_eval_2026-06-13\testing_audios_replay_mixer_errors.csv`
- `E:\FYP\reports\release_audit\testing_audios_replay_mixer_eval_2026-06-13\testing_audios_replay_mixer_unsupported_audio.csv`