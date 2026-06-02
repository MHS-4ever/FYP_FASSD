# Phase 9D-P5F-P2 Diagnostic Report (Experimental)

**Production claim:** NO — experimental partial-fabrication evidence indicator only.

**Retraining performed:** NO

**Thresholds changed:** NO — counterfactual tables are diagnostic-only.

**Release packaging performed:** NO

## Purpose

Diagnose why the P5F-P1 expanded evaluation still has fabricated_20pct false negatives and non-partial false positives, without changing models, thresholds, or cascade logic.

## Input P5F run

- Input directory: `E:\FYP\reports\phase9\partial_redesign\phase9d_p5f`
- Total evaluated files (metrics): 35
- fabricated_20pct_recall: 0.7
- timestamp_positive_count: 8

## Accepted cascade thresholds (unchanged)

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

## Case counts

- fabricated_20pct false negatives (computed): 3
- non-partial false positives (computed): 2
- metrics new_partial_false_negative_count: 3
- metrics false_partial_count (non-partial positives): 2

## False negative summary

- `testing_audios/fabricated_20pct/human_003_clean_partial_fake_20pct.wav` — primary: **segment_threshold_miss**; flags: segment_threshold_miss; near-miss: none; file_gate=0.9722, max_seg=0.6080, contrast=0.3166, high_frac=0.0000
  - Localization note: top-1 timestamp overlap among ranked segments despite cascade miss
- `testing_audios/fabricated_20pct/human_007_clean_partial_fake_20pct.wav` — primary: **file_gate_miss**; flags: file_gate_miss; near-miss: none; file_gate=0.3865, max_seg=0.9990, contrast=0.7549, high_frac=0.1875
  - Localization note: top-1 timestamp overlap among ranked segments despite cascade miss
- `testing_audios/fabricated_20pct/human_009_clean_partial_fake_20pct.wav` — primary: **file_gate_miss**; flags: file_gate_miss; near-miss: none; file_gate=0.1343, max_seg=0.9861, contrast=0.8858, high_frac=0.1200
  - Localization note: top-1 timestamp overlap among ranked segments despite cascade miss

## False positive summary

- `testing_audios/T1/T1.2.mp3` (direct) — pattern: **strong_file_gate_plus_strong_segment**; file_gate=0.9999, max_seg=1.0000, broad_flag=False; manual label/audio review recommended.
- `testing_audios/T4/T4.1.mp3` (direct) — pattern: **high_contrast_artifact_like_pattern**; file_gate=0.8771, max_seg=1.0000, broad_flag=False; manual label/audio review recommended.

## Timestamp localization diagnostic

- detected_top1_localized: 6 file(s)
- detected_top3_localized: 1 file(s)
- missed_but_timestamp_region_has_signal: 2 file(s)
- missed_no_timestamp_region_signal: 1 file(s)

## Threshold counterfactual diagnostic

Counterfactual thresholds show what would be required for each false negative file to pass **if only that file were considered**. Global sensitivity grid is in `phase9d_p5f_p2_threshold_sensitivity_summary.csv` (diagnostic_only=True). **These are not recommended threshold changes.**

- `human_003_clean_partial_fake_20pct.wav`: recover via single-gate relaxation: segment; risk note: segment_relaxation_new_fp=0
- `human_007_clean_partial_fake_20pct.wav`: recover via single-gate relaxation: file_gate; risk note: file_gate_relaxation_new_fp=3
- `human_009_clean_partial_fake_20pct.wav`: recover via single-gate relaxation: file_gate; risk note: file_gate_relaxation_new_fp=3

## Probability distribution comparison

```text
                          group  count  median_file_gate_probability  median_max_segment_probability  median_high_segment_fraction  median_topk_minus_rest_probability  min_file_gate_probability  max_file_gate_probability  min_max_segment_probability  max_max_segment_probability  min_high_segment_fraction  max_high_segment_fraction  min_topk_minus_rest_probability  max_topk_minus_rest_probability
fabricated_20pct_false_negative      3                      0.386460                        0.986054                      0.120000                            0.754929                   0.134288                   0.972230                     0.608011                        0.999                   0.000000                   0.187500                         0.316632                         0.885793
      nonpartial_false_positive      2                      0.938530                        1.000000                      0.302837                            0.598598                   0.877136                   0.999924                     1.000000                        1.000                   0.233333                   0.372340                         0.515502                         0.681694
       nonpartial_true_negative     21                      0.042239                        0.559801                      0.000000                            0.135670                   0.000007                   0.485855                     0.001542                        1.000                   0.000000                   0.166667                         0.000344                         0.827033
          true_partial_detected      9                      0.944090                        0.999942                      0.181818                            0.844768                   0.720510                   0.996895                     0.997089                        1.000                   0.157895                   0.267606                         0.558721                         0.904044
```

## Robustness note

- P5F run failed_files: 0
- SSL OOM events (metrics): 471

## Release readiness implication

Release packaging evaluation remains **blocked** in P5F-P1 (fabricated_20pct recall below 0.80, false negatives remain). This diagnostic phase does not change that assessment and does not recommend release packaging.

## Recommended next action

- Review false negative gate failures (file gate vs segment threshold) with segment CSVs.
- Review false positives on direct-labelled files; manual label/audio review recommended.
- Do not tune thresholds based solely on counterfactual tables without independent holdout review.

