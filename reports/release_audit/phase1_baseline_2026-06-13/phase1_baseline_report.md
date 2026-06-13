# Phase 1 Baseline Snapshot (Current Release Models)

Generated: 2026-06-13T10:48:27.522806+00:00

Full release pipeline on frozen `testing_audios` manifest.
UI integrity fixes from Phase 1 are applied via `enrich_phase9c_response`.

Rows: 25 | ok: 25 | failed: 0
Supported extensions: ['.aac', '.flac', '.m4a', '.mkv', '.mov', '.mp3', '.mp4', '.ogg', '.wav', '.webm']

## Metrics

                 scope  n  tp  tn  fp  fn  accuracy  balanced_accuracy  precision  recall  specificity     f1  roc_auc  pr_auc
origin_binary_human_ai 15   7   6   2   0    0.8667             0.8750     0.7778  1.0000       0.7500 0.8750   0.9286  0.9119
 replay_axis_supported 25   5  15   3   2    0.8000             0.7738     0.6250  0.7143       0.8333 0.6667   0.9048  0.7378
  mixer_axis_supported 25   0  21   1   3    0.8400             0.4773     0.0000  0.0000       0.9545 0.0000   0.5606  0.2144

## Partial UI consistency

Contradictions (not_detected + segments listed): 0

   test_id partial_ui_state  partial_show_segments_table  partial_segments_listed               partial_block_reason evidence_sources
      T1.1         detected                         True                        5                               none ssl_origin_model
      T1.2     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T1.3     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T1.4     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T1.5     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T2.1     not_detected                        False                        0 blocked_by_replay_or_mixer_context ssl_origin_model
      T2.2         detected                         True                        5                               none ssl_origin_model
      T2.3         detected                         True                        5                               none ssl_origin_model
      T2.4     not_detected                        False                        0 blocked_by_replay_or_mixer_context ssl_origin_model
      T2.5         detected                         True                        5                               none ssl_origin_model
      T3.1     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T3.2         detected                         True                        5                               none ssl_origin_model
      T3.3         detected                         True                        5                               none ssl_origin_model
      T3.4     not_detected                        False                        0 blocked_by_replay_or_mixer_context ssl_origin_model
      T3.5     not_detected                        False                        0 blocked_by_replay_or_mixer_context ssl_origin_model
      T4.1     not_detected                        False                        0 blocked_by_replay_or_mixer_context ssl_origin_model
      T4.2     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T4.3     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T4.5     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T5.1         detected                         True                        5                               none ssl_origin_model
      T5.2     not_detected                        False                        0    global_activation_not_localized ssl_origin_model
      T5.3         detected                         True                        5                               none ssl_origin_model
      T5.4         detected                         True                        5                               none ssl_origin_model
      T5.5         detected                         True                        5                               none ssl_origin_model
T5_FAB_001         detected                         True                        5                               none ssl_origin_model

## Output files

- `E:\FYP\reports\release_audit\phase1_baseline_2026-06-13\phase1_baseline_predictions.csv`
- `E:\FYP\reports\release_audit\phase1_baseline_2026-06-13\phase1_baseline_metrics.csv`
- `E:\FYP\reports\release_audit\phase1_baseline_2026-06-13\phase1_baseline_ui_checks.csv`
- `E:\FYP\reports\release_audit\phase1_baseline_2026-06-13\phase1_baseline_partial_ui_contradictions.csv`
- `E:\FYP\reports\release_audit\phase1_baseline_2026-06-13\raw_pipeline_json`