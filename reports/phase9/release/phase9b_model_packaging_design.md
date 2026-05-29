# Phase 9B Model Packaging Design

## Goal

Package accepted Phase 8 experimental evidence models into `release/models/` for Phase 9C live inference.

## Models

1. `origin_file_model` (ssl, file-level)
2. `replay_file_model` (acoustic, file-level)
3. `mixer_file_model` (acoustic, file-level)
4. `partial_fabrication_segment_model` (combined, segment-level)

## Pipeline (sklearn)

`SimpleImputer(median)` → `VarianceThreshold` → `StandardScaler` → `SelectKBest(f_classif)` → `LogisticRegression(l2, balanced)`

Fit policy: full accepted dataset per task (release packaging fit, not new research CV).

## Safety constraints

- status: `experimental_forensic_prototype`
- no writes to `models_saved/active/`
- no Phase 8 source output modification
- evidence axes remain separate
- no fake/real single-score fields
- partial model excludes label-derived baseline features

## Outputs per model

- `.joblib` artifact
- `_metadata.json`
- optional `_model_card.md`

## Inventory

`release/models/model_inventory.json` lists artifact/metadata paths and missing artifacts.
