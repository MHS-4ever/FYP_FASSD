# Phase 8E-2 Partial Localization Report

**Generated:** 2026-05-28 11:44:28 UTC

Phase 8E-2 prepares partial-fabrication localization evidence tables only.
No training, no predictions, and no final forensic decisions are produced.

## Why Partial Fabrication Is Not Trained Yet

- Inherited file-level partial labels do not identify true fabricated segment boundaries.
- Segment-level supervised training remains unsafe without reliable timestamp labels.

## Timestamp Label Audit

- partial files: 46
- partial segments: 1207
- files with true timestamp labels: 46
- files usable for supervised segment training: 46
- loaded timestamp annotation rows: 46
- matched timestamp annotation rows: 46

## Candidate Ranking Method

- within-file deviation indicators from acoustic/ssl distance-to-file-median features
- neighbor transition indicators from prev/next segment deltas
- candidate ranks are descriptive and prioritized for manual review/fusion context
- inside/outside baseline distances compare fabricated vs outside regions within each file

## Top Candidate Examples

- file `phase7c1_collection_manifest_000093_human_012_fabricated` top candidate segments: ['phase7c1_collection_manifest_000093_human_012_fabricated_w0021', 'phase7c1_collection_manifest_000093_human_012_fabricated_w0024', 'phase7c1_collection_manifest_000093_human_012_fabricated_w0022']
- file `phase7c1_collection_manifest_000009_ai_002_fabricated` top candidate segments: ['phase7c1_collection_manifest_000009_ai_002_fabricated_w0019', 'phase7c1_collection_manifest_000009_ai_002_fabricated_w0018', 'phase7c1_collection_manifest_000009_ai_002_fabricated_w0017']
- file `phase7c1_collection_manifest_000021_human_003_fabricated` top candidate segments: ['phase7c1_collection_manifest_000021_human_003_fabricated_w0000', 'phase7c1_collection_manifest_000021_human_003_fabricated_w0002', 'phase7c1_collection_manifest_000021_human_003_fabricated_w0001']
- file `phase7c1_collection_manifest_000037_human_005_fabricated` top candidate segments: ['phase7c1_collection_manifest_000037_human_005_fabricated_w0016', 'phase7c1_collection_manifest_000037_human_005_fabricated_w0014', 'phase7c1_collection_manifest_000037_human_005_fabricated_w0015']
- file `phase7c1_collection_manifest_000177_ai_023_fabricated` top candidate segments: ['phase7c1_collection_manifest_000177_ai_023_fabricated_w0009', 'phase7c1_collection_manifest_000177_ai_023_fabricated_w0010', 'phase7c1_collection_manifest_000177_ai_023_fabricated_w0008']

## Phase 8E-3 Readiness

- ready_for_supervised_partial_segment_training: **yes**
- current outputs are candidate segment indicators for manual review and possible Phase 8F fusion context.

## Limitations

- localized anomaly indicators are not confirmed fabricated segments.
- small and weakly labeled partial data requires cautious interpretation.
- candidate thresholds/indicators require validation and manual review.

## Safety Statements

- no training was performed
- no predictions were produced
- no hard suspicious labels were created
- no final forensic decisions were produced
- candidate segment indicators are not a confirmed fabricated segment
