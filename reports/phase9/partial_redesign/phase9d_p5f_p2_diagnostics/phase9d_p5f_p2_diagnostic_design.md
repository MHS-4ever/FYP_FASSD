# Phase 9D-P5F-P2 — False Negative / False Positive Diagnostic Analysis (Design)

## Purpose

Explain why P5F-P1 still reports:

- 3 `fabricated_20pct` false negatives (partial-evidence miss on labelled partial files)
- 2 non-partial false positives (experimental partial evidence on `expected_partial_label=0` files)

This phase is **analysis only**. It reads existing P5F CSV/JSON outputs and writes diagnostic tables and a report.

## Out of scope

| Forbidden | Notes |
|-----------|--------|
| Retrain / fit models | No `train_phase9d_p5_partial_models.py` |
| Threshold changes | Counterfactual tables are diagnostic-only |
| Cascade logic changes | Uses `apply_p5c_cascade_rule` for replay only |
| Release packaging | No writes to `release/models/` or `models_saved/active/` |
| Phase 9E / FastAPI / Gradio | Not started or modified |

## Inputs

Directory: `reports/phase9/partial_redesign/phase9d_p5f/`

- `phase9d_p5f_file_predictions.csv`
- `phase9d_p5f_segment_predictions.csv`
- `phase9d_p5f_expanded_manifest.csv`
- `phase9d_p5f_expanded_metrics.json`
- `phase9d_p5f_timestamp_loading_audit.csv` (optional)

## Outputs

Directory: `reports/phase9/partial_redesign/phase9d_p5f_p2_diagnostics/`

| File | Role |
|------|------|
| `phase9d_p5f_p2_case_summary.csv` | Per-case cascade metrics and failure/explanation labels |
| `phase9d_p5f_p2_top_segments_for_cases.csv` | Top-10 segments per FN/FP |
| `phase9d_p5f_p2_timestamp_localization_diagnostics.csv` | Per-file timestamp vs segment probability analysis |
| `phase9d_p5f_p2_threshold_counterfactual.csv` | Per-FN required thresholds (diagnostic) |
| `phase9d_p5f_p2_threshold_sensitivity_summary.csv` | Grid sensitivity (`diagnostic_only=True`) |
| `phase9d_p5f_p2_probability_distribution_summary.csv` | Grouped probability medians |
| `phase9d_p5f_p2_diagnostic_report.md` | Human-readable summary |
| `plots/` | Optional matplotlib plots when `--make_plots` |

Validation: `reports/phase9/validation/phase9d_p5f_p2_diagnostics_validation_report.md`

## Cascade diagnosis (false negatives)

Accepted P5B thresholds (unchanged):

- `file_gate_threshold = 0.50`
- `segment_threshold = 0.90`
- `high_segment_fraction <= 0.45` (broad limit)
- `topk_minus_rest_probability >= 0.25`

Primary failure priority: file gate → segment → broad → contrast.

## False positive patterns

Heuristic labels only (e.g. `strong_file_gate_plus_strong_segment`); never assert label error — use “manual label/audio review recommended.”

## Scripts

- `code/phase9/partial_redesign/analyze_phase9d_p5f_diagnostics.py`
- `code/phase9/partial_redesign/validate_phase9d_p5f_diagnostics.py`

## Manual run (user)

```text
python -m py_compile code\phase9\partial_redesign\analyze_phase9d_p5f_diagnostics.py
python -m py_compile code\phase9\partial_redesign\validate_phase9d_p5f_diagnostics.py

python code\phase9\partial_redesign\analyze_phase9d_p5f_diagnostics.py --make_plots
python code\phase9\partial_redesign\validate_phase9d_p5f_diagnostics.py
```
