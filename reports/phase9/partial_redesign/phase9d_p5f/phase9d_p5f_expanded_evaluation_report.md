# Phase 9D-P5F Expanded Independent Evaluation Report (Experimental)

Generated: 2026-06-02 19:04:29 UTC

**Production claim:** NO — experimental partial-fabrication evidence indicator only.

**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.

## Purpose

Expand independent labelled partial-positive evaluation by adding `fabricated_20pct` (10 new 20% partial-fabrication files with timestamp spreadsheet) to the existing P5D testing holdout (t1–t5, fabricated).

P5F evaluates only; it does not retrain models, change thresholds, or package release artifacts.

## Input folders

- Input root: `E:\FYP\testing_audios`
- Scanned folders: fabricated, fabricated_20pct, T1, T2, T3, T4, T5
- Total manifest files: 35
- New fabricated_20pct files: 10

## fabricated_20pct timestamp loading

- Timestamp file path: `fabricated_20pct_timestamps.csv`
- Sheet used: `csv`
- Detected file column: `output_path`
- Detected start column: `fabricated_start_sec`
- Detected end column: `fabricated_end_sec`
- Matched audio count: 10
- Spreadsheet row count: 10
- fabricated_20pct_timestamp_label_count: 10
- expanded_timestamp_positive_count: 8
- timestamp_positive_count: 8
- timestamp_match_method summary (fabricated_20pct): {'exact_file_name': 10}

## Overlap audit summary

- Independent holdout: 10
- Seen in P5 training: 0
- Seen in P5C controlled: 0
- Seen in previous P5D: 25
- Unknown overlap: 0

Overlap with training, P5C, or prior P5D runs is reported explicitly and not hidden.

## Accepted P5B cascade thresholds

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

- File gate feature set: `ssl`
- Segment localizer feature set: `combined`

## Candidate model artifacts (P5B experimental only)

- File gate: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- Segment localizer v2: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- Cascade config: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5b\candidate_models\partial_cascade_config__p5b_experimental_candidate.json`

Only P5B experimental candidate artifacts were used. No release or reference-model artifacts were activated.

## Expanded partial-fabrication metrics

- expanded_partial_file_count: 12
- expanded_timestamp_positive_count: 8
- partial_evidence_recall: 0.75
- fabricated_20pct_recall: 0.7
- new_partial_positive_count: 10
- new_partial_recall: 0.7
- new_partial_false_negative_count: 3

## fabricated_20pct localization (timestamp-labelled)

- fabricated_20pct_timestamp_label_count: 10
- fabricated_20pct_top1_hit_rate: 0.8571428571428571
- fabricated_20pct_top3_hit_rate: 1.0
- fabricated_20pct_top5_hit_rate: 1.0
- fabricated_20pct_median_candidate_timestamp_error_seconds: 2.2387184999999974

## False partial evidence (non-partial labels)

- `testing_audios/T1/T1.2.mp3` (direct) — experimental partial-fabrication candidate segment flagged; gate=1.000; manual review recommended
- `testing_audios/T4/T4.1.mp3` (direct) — experimental partial-fabrication candidate segment flagged; gate=0.877; manual review recommended

## fabricated_20pct false negatives (expected partial, no evidence)

- `testing_audios/fabricated_20pct/human_003_clean_partial_fake_20pct.wav` — partial_evidence_positive=False; manual review recommended
- `testing_audios/fabricated_20pct/human_007_clean_partial_fake_20pct.wav` — partial_evidence_positive=False; manual review recommended
- `testing_audios/fabricated_20pct/human_009_clean_partial_fake_20pct.wav` — partial_evidence_positive=False; manual review recommended

## Robustness behavior

- mp4_file_count: 2
- mp4_evaluated_count: 2
- ssl_cuda_oom_count: 471
- ssl_chunked_fallback_success_count: 4
- ssl_long_audio_recovered_count: 2
- failed_files: 0

P5F reuses P5D-R2 memory-safe SSL extraction (chunked fallback for long audio).

## Release readiness assessment

**Candidate acceptable for release packaging evaluation: no.**

Assessment: Candidate acceptable for release packaging evaluation: no.

Blocking reasons:
- fabricated_20pct_recall 0.7000 < 0.8000
- new_partial_recall 0.7000 < 0.8000
- new_partial_false_negative_count=3 > 0

Packaging is not performed in P5F-P1 regardless of gate outcome.

## Limitations

- Independent holdout depends on overlap audit; new fabricated_20pct files should be reviewed for training leakage.
- Timestamp labels come from fabricated_20pct_timestamps spreadsheet; alignment quality requires manual review.
- Outputs are experimental evidence indicators and candidate segments — not final authenticity verdicts.
- Small expanded holdout; condition strata remain limited.

## Recommended next action

Proceed to explicit release-packaging review phase if gates pass; otherwise add more independent labelled partial positives and review false partial / false negative cases.

P5F-P1 fixes timestamp spreadsheet loading and reruns localization evaluation only; packaging remains a later explicit decision.
