# Phase 8E-0 Dataset Assembly Design

## Purpose
Phase 8E-0 prepares safe multi-axis datasets for later lightweight classifiers and fusion research. This phase is strictly data assembly and validation; it does not train models, fit classifiers, or produce predictions.

## Why Assembly Comes Before Training
Phase 8B, 8C, and 8D outputs exist as separate evidence, acoustic-feature, and SSL-embedding tables. Before any supervised Phase 8E modeling can happen, these tables must be joined into consistent master datasets with:
- stable identities (`file_id`, `segment_id`)
- clear feature-vs-label separation
- explicit task eligibility flags
- leakage-aware grouping metadata

## Join Strategy
- File-level join: Phase 8B file evidence + Phase 8C file acoustic features + Phase 8D file SSL embeddings by `file_id`.
- Segment-level join: Phase 8B segment evidence + Phase 8C segment acoustic features + Phase 8D segment SSL embeddings by (`segment_id`, `file_id`).
- Row-count checks run before/after joins to ensure no silent row drops.

## Task Separation
Phase 8E-0 builds three safe supervised file-level datasets:
- origin (`human` vs `ai_synthetic`) using clean rows only
- replay (`clean` negatives vs `replay_rerecorded` positives)
- mixer/channel (`clean` negatives vs `mixer_channel_processed` positives)

Partial fabrication is not treated as a normal segment-level classifier target in this phase.

## Why No Fake/Real Classifier
This repository uses multi-axis forensic evidence (origin, replay, mixer/channel, partial/splice context). A single fake/real classifier can hide forensic provenance and create invalid shortcuts. Phase 8E-0 therefore avoids binary fake/real task creation and preserves separate task targets.

## Partial Fabrication Handling
Inherited file-level partial labels do not identify which segments are fabricated. As a result:
- segment-level inherited partial labels are marked unsafe for supervised training
- `eligible_partial_segment_training` is blocked for inherited labels
- output is localization preparation only
- inherited-label risk remains visible in leakage audit and validation notes

## Leakage Risks and `source_group_id`
The assembly adds `source_group_id` to support group-aware future splitting.
- Preferred source grouping uses explicit metadata columns when available (`source_id`, `base_id`, `original_file_id`, etc.).
- If unavailable, a conservative heuristic from `file_id`/`audio_path` is used.
- Heuristic grouping is helpful but not perfect; manual review is required before final evaluation.

## Outputs Produced
Phase 8E-0 scripts produce:
- file and segment master datasets
- origin/replay/mixer task datasets
- partial-fabrication localization-prep dataset
- leakage audit CSV
- dataset summary CSV
- assembly report and validation report

These artifacts are preparation assets for Phase 8E-1 and later, not modeling outputs.
No model fitting, classifier training, or prediction is performed in this phase.
