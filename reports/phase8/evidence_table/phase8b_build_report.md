# Phase 8B Build Report

**Generated:** 2026-05-27 21:00:07 UTC
**Schema version:** phase8b_v1

## Summary

- File rows: **184**
- Segment rows: **4189**
- Input manifests: 1

## What this build did

- Loaded manifest CSV(s) and normalized column names
- Mapped known ground-truth labels to frozen Phase 8 vocabulary
- Left all evidence score columns **empty** (not copied from labels)
- Left fusion/calibration placeholders **empty** for Phase 8F
- Created segment windows where `duration_sec` was available

## What this build did NOT do

- No model training or inference
- No binary fake/real score
- No filling of evidence scores from known labels

## Outputs

- `reports/phase8/evidence_table/phase8b_file_evidence_table.csv`
- `reports/phase8/evidence_table/phase8b_segment_evidence_table.csv`

## Parameters

- segment_length_sec: 4.0
- segment_hop_sec: 2.0
- allow_missing_audio: True
