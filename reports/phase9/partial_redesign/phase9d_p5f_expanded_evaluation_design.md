# Phase 9D-P5F — Expanded Independent Partial-Positive Evaluation (Design)

## Purpose

Expand independent labelled partial-fabrication evaluation by adding **`testing_audios/fabricated_20pct`** (10 new 20% partial-fake WAV files with timestamp spreadsheet) to the existing P5D holdout (`t1`–`t5`, `fabricated`).

P5F is **evaluation only** — no retrain, no threshold changes, no release packaging.

## Scope

| In scope | Out of scope |
|----------|----------------|
| Scan t1–t5, fabricated, **fabricated_20pct** | Retrain / fit models |
| Load `fabricated_20pct_timestamps.xlsx` (or `.csv`) | Writes to `release/models/` or `models_saved/active/` |
| P5B experimental candidate cascade (accepted thresholds) | FastAPI / Gradio / Phase 9E |
| Separate outputs under `phase9d_p5f/` (preserves `phase9d_p5d/`) | Old release partial / reference models |

## Input folders

- `testing_audios/t1` … `t5`
- `testing_audios/fabricated`
- `testing_audios/fabricated_20pct`
- Fallback: `data/testing_audios/...`

## fabricated_20pct labelling

| Field | Value |
|-------|--------|
| `test_group` | `fabricated_20pct` |
| `expected_partial_label` | `1` |
| `expected_condition` | `fabricated` |
| `expected_origin_label` | `human_likely` (unless spreadsheet overrides) |
| Timestamps | From `fabricated_20pct_timestamps.xlsx` / `.csv` when readable |
| `timestamp_match_method` | `exact_file_name`, `loose_audio_filename_column`, `row_order_fallback`, `sidecar_json`, or `missing` |

If the spreadsheet is missing or a row is unmatched, files remain partial-positive with `has_timestamp_label=false` and a report warning (no crash).

### P5F-P1 timestamp loading (evaluation-only rerun)

P5F-P1 fixes spreadsheet loading for `fabricated_20pct` without retraining or changing P5B thresholds:

- **XLSX/CSV**: normalize column names; try each sheet until start/end columns parse.
- **Filename columns**: explicit names (`output_path`, `file_name`, …) plus loose detection (`.wav` paths, `human_*_partial_fake_20pct` stems).
- **Row-order fallback**: only when start/end exist, no filename column, and `row_count ==` audio file count (10); match sorted spreadsheet rows to `human_001`…`human_010` audio order. Documented in report and `phase9d_p5f_timestamp_loading_audit.csv` — manual verification recommended.
- **No invented timestamps**; row-order fallback is never used when counts differ.

Release packaging is **not** performed in P5F-P1; localization metrics are recomputed only.

## Overlap audit statuses

- `independent_holdout`
- `seen_in_p5_training`
- `seen_in_p5c_controlled`
- `seen_in_previous_p5d` (vs prior P5D manifest)
- `unknown_overlap_status`

## Accepted cascade (unchanged P5B-P2)

- `file_gate_threshold = 0.50`
- `segment_threshold = 0.90`
- `contrast_threshold = 0.25`
- `broad_limit = 0.45`

## Outputs

Directory: `reports/phase9/partial_redesign/phase9d_p5f/`

| Artifact | Role |
|----------|------|
| `phase9d_p5f_expanded_manifest.csv` | All scanned files + timestamp metadata |
| `phase9d_p5f_overlap_audit.csv` / `.md` | Training / P5C / P5D overlap |
| `phase9d_p5f_file_predictions.csv` | File-level cascade + SSL robustness columns |
| `phase9d_p5f_segment_predictions.csv` | Segment probabilities and ranks |
| `phase9d_p5f_expanded_metrics.csv` / `.json` | P5D metrics + fabricated_20pct / expanded counts |
| `phase9d_p5f_error_cases.csv` | Failed/skipped files |
| `phase9d_p5f_expanded_evaluation_report.md` | Human-readable summary |
| `phase9d_p5f_run_status.json` | Run lifecycle / stale-output guard |
| `phase9d_p5f_timestamp_loading_audit.csv` | Spreadsheet column detection, match counts, row-order fallback |

Validation: `reports/phase9/validation/phase9d_p5f_expanded_evaluation_validation_report.md`

## P5F-specific metrics

- `fabricated_20pct_*` recall / localization on new folder
- `expanded_partial_file_count`, `expanded_timestamp_positive_count`
- `new_partial_*` counters for the 10 new files
- All P5D-R2 robustness metrics (MP4, SSL OOM, chunked fallback)

## Release packaging evaluation gates (P5F report only)

Packaging is **not performed** in P5F. The report states whether the candidate would be acceptable for a **later** packaging review, including:

- `partial_file_count >= 5`
- `timestamp_positive_count >= 5`
- `failed_files == 0`
- Aggregate recall / false-alarm / localization thresholds (see evaluator `evaluate_p5f_release_gates`)
- P5F expanded holdout: `fabricated_20pct_recall >= 0.80`, `new_partial_recall >= 0.80`, `new_partial_false_negative_count == 0`

Release packaging remains an explicit later decision even if numeric gates pass.

## Scripts

- `code/phase9/partial_redesign/evaluate_phase9d_p5f_expanded_independent_cascade.py`
- `code/phase9/partial_redesign/validate_phase9d_p5f_expanded_evaluation.py`
- Reuses: `phase9d_p5_evaluation_shared.py`, P5D cascade helpers

## Manual run (user)

```text
python -m py_compile code\phase9\partial_redesign\phase9d_p5_evaluation_shared.py
python -m py_compile code\phase9\partial_redesign\evaluate_phase9d_p5f_expanded_independent_cascade.py
python -m py_compile code\phase9\partial_redesign\validate_phase9d_p5f_expanded_evaluation.py

python code\phase9\partial_redesign\evaluate_phase9d_p5f_expanded_independent_cascade.py --input_root testing_audios --make_plots
python code\phase9\partial_redesign\validate_phase9d_p5f_expanded_evaluation.py
```
