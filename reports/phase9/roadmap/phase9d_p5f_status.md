# Phase 9D-P5F Status

| Field | Value |
|-------|--------|
| Phase | 9D-P5F-P1 — Fix fabricated_20pct timestamp loading + rerun localization eval |
| Status | **P5F-P1 evaluator run complete** — re-run validator after gate fix; timestamps 10/10 loaded |
| Prior | P5F initial run: 35 files, 10 fabricated_20pct, recall 0.70, 3 FN; timestamps failed to load (`file=None`) |

## P5F goal

Add **`testing_audios/fabricated_20pct`** (10 labelled 20% partial-fabrication files + timestamp spreadsheet) to the independent testing evaluation without modifying P5D-R2 outputs under `phase9d_p5d/`.

## P5F deliverables

- [x] `evaluate_phase9d_p5f_expanded_independent_cascade.py`
- [x] `validate_phase9d_p5f_expanded_evaluation.py`
- [x] `phase9d_p5f_expanded_evaluation_design.md`
- [x] Outputs directory: `reports/phase9/partial_redesign/phase9d_p5f/`

## Behavior summary

- Scans t1–t5, fabricated, **fabricated_20pct** (not unrelated dataset trees).
- Loads timestamps from `fabricated_20pct_timestamps.xlsx` (or `.csv`) with P5F-P1 column detection, `output_path` matching, and row-order fallback when counts match.
- Writes `phase9d_p5f_timestamp_loading_audit.csv`; manifest/predictions include `timestamp_source` and `timestamp_match_method`.
- Overlap audit includes **seen_in_previous_p5d** vs prior P5D manifest.
- Reuses P5D-R2 robust inference (MP4, SSL chunked fallback, candidate rank integrity).
- P5B experimental candidates only; thresholds unchanged.
- **No** retrain, **no** release packaging, **no** Phase 9E.

## Expected impact

- `expanded_partial_file_count` should increase (target ≥ 5 partial-labelled files after adding 10 new positives).
- `fabricated_20pct_timestamp_label_count` should reach **10** when the spreadsheet has 10 usable rows.
- `fabricated_20pct_top1/top3/top5_hit_rate` computed on partial-evidence-positive files with timestamp labels.
- Release packaging evaluation may improve `timestamp_positive_count` but packaging is **not** performed in P5F-P1 (explicit later decision).

## User next steps

1. `py_compile` shared + P5F evaluator + P5F validator.
2. Run evaluator with `--input_root testing_audios`.
3. Run validator.
4. Review `phase9d_p5f_expanded_evaluation_report.md` and overlap audit.

## Constraints (unchanged)

- No `release/models/` or `models_saved/active/` writes
- Forensic-safe wording only (experimental evidence indicator, manual review recommended)
