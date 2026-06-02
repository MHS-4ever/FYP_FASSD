# Phase 9D-P5D Independent Evaluation Report (Experimental)

Generated: 2026-06-02 18:01:50 UTC

**Production claim:** NO — experimental partial-fabrication evidence indicator only.

**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.

## Purpose

Evaluate whether the accepted P5B partial-fabrication candidate cascade generalizes on independent `testing_audios` holdout (t1–t5 and fabricated) outside P5A/P5B/P5C training reuse.

## Input

- Input root: `E:\FYP\testing_audios`
- Scanned test folders: fabricated, T1, T2, T3, T4, T5
- Files in manifest: 25

## Overlap audit summary

- Evaluation mode: **independent held-out testing audio**
- Independent holdout files: 25
- Seen in P5 training: 0
- Seen in P5C controlled: 0
- Unknown overlap: 0

Overlap with P5 training or P5C is reported explicitly and not hidden.

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

Only P5B experimental candidate artifacts were used for the partial cascade. No release or reference-model artifacts were activated.

## File-level results

- Total files: 25
- Evaluated (ok): 25
- Failed/skipped: 0
- Partial evidence recall: 1.0
- Non-partial false alarm rate: 0.08695652173913043

## Folder-wise results (t1–t5, fabricated)

- **fabricated**: files=1, positive_rate=1.0, partial_recall=1.0
- **t1**: files=5, positive_rate=0.2, partial_recall=nan
- **t2**: files=5, positive_rate=0.0, partial_recall=nan
- **t3**: files=5, positive_rate=0.0, partial_recall=nan
- **t4**: files=4, positive_rate=0.5, partial_recall=1.0
- **t5**: files=5, positive_rate=0.0, partial_recall=nan

## Condition-wise false partial rates

- direct_condition_count: 13
- direct_false_partial_rate: 0.15384615384615385
- replay_condition_count: 7
- replay_false_partial_rate: 0.0
- mixer_condition_count: 3
- mixer_false_partial_rate: 0.0
- unknown_condition_count: 0
- unknown_condition_positive_rate: not_applicable (no files in this condition stratum)

## Localization behavior

- timestamp_positive_count: 1
- timestamp_error_count: 1
- Candidate segment means rank-1 segment by segment-localizer probability.
- median_candidate_timestamp_error_seconds is computed from the corrected rank-1 candidate segment.
- top1_hit_rate_when_positive: 0.0
- top3_hit_rate_when_positive: 1.0
- top5_hit_rate_when_positive: 1.0
- median_candidate_timestamp_error_seconds: 94.222625

## Broad activation behavior

- broad_activation_rate_when_positive: 0.0
- candidate_rank1_consistency_count: 25
- candidate_rank1_consistency_rate: 1.0
- candidate_segment_probability_available_rate: 1.0

## Error handling

- invalid_file_handling_pass_rate: 1.0

## Robustness behavior

- mp4_file_count: 2
- mp4_evaluated_count: 2
- mp4_failed_count: 0
- mp4_load_success_rate: 1.0
- ssl_cuda_oom_count: 1
- ssl_cpu_fallback_attempt_count: 0
- ssl_cpu_fallback_success_count: 0
- ssl_cpu_fallback_failure_count: 0
- ssl_cpu_fallback_skipped_long_audio_count: 1
- ssl_chunked_fallback_attempt_count: 1
- ssl_chunked_fallback_success_count: 1
- ssl_chunked_fallback_failure_count: 0
- ssl_chunked_cpu_fallback_attempt_count: 1
- ssl_chunked_cpu_fallback_success_count: 1
- ssl_chunked_cpu_fallback_failure_count: 0
- ssl_long_audio_file_count: 1
- ssl_long_audio_recovered_count: 1
- ssl_long_audio_failed_count: 0
- ssl_chunked_embedding_used_count: 1
- ssl_chunked_embedding_max_chunks_observed: 7
- robustness_failed_file_count: 0
- robustness_recovered_file_count: 1

Robustness counters are derived from SSL extraction/fallback events and cross-checked against error cases.
P5D-R2 improves memory-safe SSL extraction only; it does not change the partial cascade model, thresholds, or release readiness decision.

The previous long-audio SSL failure was recovered through chunked fallback.

## Examples — partial evidence positives (candidate segments)

- `testing_audios/T4/T4.3.mp3` — experimental partial-fabrication candidate segment 140.0–141.44525s (gate=1.000, candidate_seg_prob=1.000, candidate_rank=1; manual review recommended)
- `testing_audios/fabricated/fabricated.mp3` — experimental partial-fabrication candidate segment 18.0–22.0s (gate=0.886, candidate_seg_prob=0.999, candidate_rank=1; manual review recommended)

## Examples — false partial evidence (if any)

- `testing_audios/T1/T1.2.mp3` (direct) — partial_evidence_positive=True; gate=1.000
- `testing_audios/T4/T4.1.mp3` (direct) — partial_evidence_positive=True; gate=0.877

## Release packaging evaluation assessment

**Assessment:** Independent evaluation completed, but partial recall coverage is too limited for release packaging recommendation (insufficient labelled partial-positive files).

**Candidate acceptable for release packaging evaluation:** no

Blocking or limiting reasons:
- partial_file_count=2 < 5

## Release packaging blockers (explicit)

- Labels/conditions are incomplete or only partially inferred for this holdout.
- Only 2 labelled partial-positive file(s) are available in this testing set, which is below the minimum 5 required for release-packaging evaluation.
- Timestamp localization evidence is limited (timestamp_positive_count=1; insufficient for packaging-quality localization assessment).
- Independent testing set is small; false partial evidence cases (e.g. on direct-condition files) must be reviewed before any packaging step.

## Limitations

- Independent holdout depends on overlap audit; filenames/paths may collide with training.
- Live acoustic/SSL extraction is used when phase8e0 masters lack the file.
- Does not establish legally admissible authentication proof; separate evidence axes remain required.
- Outputs are candidate indicators for manual review, not final authenticity verdicts.

## Recommended next action

Review overlap audit and metrics; address false partial rates or recall before any release packaging evaluation. Manual review of candidate segments remains required.
