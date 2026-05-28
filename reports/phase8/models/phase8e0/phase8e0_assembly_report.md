# Phase 8E-0 Dataset Assembly Report

**Generated:** 2026-05-28 10:26:01 UTC

> Phase 8E-0 is dataset assembly + leakage audit only (no training, no prediction).

## Dataset Summary

- file_master: row_count=184
- file_master: label_count=69
- file_master: label_count=69
- file_master: label_count=46
- file_master: label_count=138
- file_master: label_count=46
- file_master: label_count=138
- file_master: label_count=46
- file_master: label_count=138
- file_master: label_count=46
- file_master: label_count=138
- file_master: label_count=46
- file_master: label_count=92
- file_master: label_count=92
- file_master: label_count=92
- file_master: label_count=92
- file_master: label_count=184
- segment_master: row_count=4189
- segment_master: label_count=4189
- origin_file_dataset: row_count=46
- origin_file_dataset: label_count=23
- origin_file_dataset: label_count=23
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- origin_file_dataset: label_count=46
- replay_file_dataset: row_count=92
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=92
- replay_file_dataset: label_count=92
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=92
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=46
- replay_file_dataset: label_count=92
- mixer_file_dataset: row_count=92
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=92
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=92
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=46
- mixer_file_dataset: label_count=92
- mixer_file_dataset: label_count=92
- partial_localization_prep: row_count=1207
- partial_localization_prep: label_count=1207
- file_master: missing_acoustic_cells=184
- file_master: missing_embedding_cells=0
- segment_master: missing_acoustic_cells=117292
- segment_master: missing_embedding_cells=0
- leakage_audit: blocking_items=0

## Task-Specific Counts

- target_is_clean counts: {'0': 138, '1': 46}
- origin dataset rows: 46
- replay dataset target_is_replay counts: {'0': 46, '1': 46}
- mixer dataset target_is_mixer_channel counts: {'0': 46, '1': 46}
- partial localization prep rows: 1207
- partial segment training blocked rows: 1207

## Leakage Audit

- [info] duplicate_file_id | affected=0 | Duplicate file_id values can leak labels and corrupt joins.
- [info] duplicate_audio_path | affected=0 | Same audio path appears multiple times.
- [info] conflicting_task_labels | affected=0 | Rows marked clean and manipulated simultaneously.
- [info] source_group_multiple_variants | affected=0 | Likely variants share same source and can leak across train/test.
- [info] source_group_cross_split | affected=0 | Same source group appears in multiple splits.
- [warning] segment_same_file_split_risk | affected=184 | Segments from same file can be split apart and leak content.
- [warning] origin_vs_manipulation_coupling | affected=46 | Origin and manipulation can become shortcut features.
- [warning] partial_inherited_label_risk | affected=1207 | Partial fabrication segment labels are inherited, not true timestamps.

## Notes

- `source_group_id` can be heuristic when explicit source metadata is absent.
- `eligible_partial_segment_training` remains false for inherited partial labels.
- No model training, fitting, or predictions are performed in Phase 8E-0.
