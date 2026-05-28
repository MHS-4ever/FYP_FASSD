# Phase 8E-3 Partial Segment Model Design

## Why Phase 8E-3 Is Allowed Now
Phase 8E-2 provides timestamp-aligned segment labels (`fabricated_region` vs `outside_fabricated_region`) with training-label availability checks and readiness review support.

## Why Timestamp Labels Are Required
Partial fabrication is local within files. Inherited file-level labels are unsafe for segment supervision. Phase 8E-3 therefore uses only timestamp-aligned segment labels with `training_label_available=true`.

## Why Inherited Labels Were Not Enough
- they do not mark exact fabricated intervals
- they create ambiguous positive/negative segment assignment
- they risk severe label leakage and noisy supervision

## Model Pipeline
Phase 8E-3 uses a lightweight scikit-learn pipeline:
- `SimpleImputer(median)`
- `VarianceThreshold`
- `StandardScaler`
- `SelectKBest(f_classif, k=safe_k)`
- `LogisticRegression(l2, balanced, max_iter=2000, liblinear)`

Feature selection is inside CV to reduce leakage risk.

## Feature Inputs
Phase 8E-3 combines:
- Phase 8E-2 engineered localization features
- raw segment acoustic and SSL features from `phase8e0_segment_level_master_dataset.csv` (preferred)
- optional fallback joins from Phase 8C segment acoustic and Phase 8D segment SSL files

Phase 8E-3 uses timestamp labels only to define `y_true` targets.

Explicitly forbidden from model input:
- any feature derived from fabricated/outside baselines (`*fabricated_baseline*`, `*outside_baseline*`)
- inside/outside margins or separations (`*inside_outside_margin*`, `*inside_outside_separation*`)
- timestamp overlap fields (`max_fabricated_overlap_*`, `total_fabricated_overlap_sec`, `overlaps_true_fabricated_region`)

Safe localization features are restricted to within-file deviation and neighbor-transition signals that do not require true fabricated/outside labels.

## Leakage Control
- group-aware split by `source_group_id` when available, else `file_id`
- all segments from the same file should remain in the same fold where feasible
- split method recorded in outputs

## Limitations
- timestamp labels are preparation labels and can still contain annotation noise
- model outputs are experimental localization signals
- outputs are not final suspicious-segment decisions and not proof of fabrication
