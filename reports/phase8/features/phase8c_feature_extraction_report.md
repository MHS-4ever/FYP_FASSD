# Phase 8C Feature Extraction Report

**Generated:** 2026-05-27 21:44:03 UTC
**Schema version:** phase8c_v1

## Runtime summary

- Total runtime: **200.4 s**
- Files processed (this run): 184
- Segments processed (this run): 4189
- Files skipped (resume): 0
- Segments skipped (resume): 0
- Segment feature mode: `fast`
- Progress method: `tqdm`
- Warnings (this run): 0

## Output row totals (on disk)

- File feature rows: 184
- Segment feature rows: 4189

## Extraction status (file-level, all rows on disk)

- `ok`: 184

## Extraction status (this run only)

- `ok`: 184

## Segment modes

- **fast** (default): MFCC and spectral_contrast left blank; suitable for first full-table pass.
- **full**: all segment columns computed (slower).

## What Phase 8C did NOT do

- No model training or checkpoint inference
- No evidence score columns filled
- No fake/real decisions

## Outputs

- `reports/phase8/features/phase8c_file_acoustic_features.csv`
- `reports/phase8/features/phase8c_segment_acoustic_features.csv`

