# Phase 8E-1 File-Level Model Design

## Purpose
Phase 8E-1 introduces controlled, lightweight, file-level experimental model training for three separate forensic evidence axes:
- origin evidence (`origin_file_model`)
- replay/rerecording evidence (`replay_file_model`)
- mixer/channel evidence (`mixer_file_model`)

This phase does not produce final forensic decisions.

## Why File-Level Only
- Phase 8E-0 created validated file-level datasets with explicit task eligibility and leakage controls.
- Partial fabrication remains unsafe for direct segment supervision with inherited labels.
- File-level training is lower-risk and auditable before deeper fusion stages.

## Why Separate Axes
- Origin, replay, and mixer/channel represent different forensic signals and should not be collapsed into one fake/real classifier.
- Replay-positive output does not imply AI generation.
- Mixer-positive output does not imply AI generation.
- Origin evidence is kept independent from manipulation evidence.

## Exclusions
- No partial fabrication model in Phase 8E-1.
- No segment-level model in Phase 8E-1.
- No single fake/real classifier in Phase 8E-1.

## Model Pipeline
scikit-learn pipeline:
1. `SimpleImputer(strategy="median")`
2. `VarianceThreshold()`
3. `StandardScaler()`
4. `SelectKBest(f_classif, k=safe_k)`
5. `LogisticRegression(penalty="l2", class_weight="balanced", max_iter=2000)`

Feature selection is inside CV to reduce leakage risk.

## Feature Sets
- `acoustic`: Phase 8C acoustic columns.
- `ssl`: Phase 8D `ssl_emb_*` columns.
- `combined`: acoustic + ssl.

Identity/label/provenance fields and forbidden decision/evidence columns are excluded.

## Cross-Validation and Leakage Control
- Prefer `StratifiedGroupKFold` using `source_group_id`.
- Fallback to `GroupKFold` if stratified-group is unavailable.
- Fallback to `StratifiedKFold` only when group-aware split is impossible.
- Fold count is reduced safely (5 -> 3) if needed; below 3 folds raises an error.

## Small-Dataset Limitations
- Dataset sizes are intentionally constrained (46/92/92 rows).
- Metrics are experimental and may vary by fold.
- Results are guidance for later Phase 8F fusion planning, not production claims.
