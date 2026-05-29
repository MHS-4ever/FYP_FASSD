# Phase 9D-P5C Status

## Phase 9D-P5B-P2 — Cascade alignment

| Item | Status |
|------|--------|
| Shared `CASCADE_ACCEPTANCE_CONFIG` | **COMPLETE** |
| Training validation aligned | **PASS** (user executed) |

## Phase 9D-P5C — Controlled evaluation scripts

| Item | Status |
|------|--------|
| `evaluate_phase9d_p5c_controlled_cascade.py` | SCRIPT CREATED |
| `validate_phase9d_p5c_controlled_evaluation.py` | SCRIPT CREATED |
| `phase9d_p5_training_utils.py` (P5C helpers) | UPDATED |
| `train_phase9d_p5_partial_models.py` (`--fit_final_candidate_models`) | UPDATED |
| Design doc | CREATED |
| Evaluation execution | **PENDING** (user runs manually) |
| Validation execution | **PENDING** (user runs manually) |

## Candidate models

| Artifact | Status |
|----------|--------|
| `phase9d_p5b/candidate_models/partial_file_gate__ssl__p5b_experimental_candidate.joblib` | PENDING (user runs `--fit_final_candidate_models`) |
| `phase9d_p5b/candidate_models/partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib` | PENDING |
| `phase9d_p5b/candidate_models/partial_cascade_config__p5b_experimental_candidate.json` | PENDING |

## P5C outputs (after user run)

| Output | Status |
|--------|--------|
| `phase9d_p5c_controlled_evaluation_report.md` | PENDING |
| `phase9d_p5c_controlled_metrics.csv` | PENDING |
| `phase9d_p5c_file_predictions.csv` | PENDING |
| `phase9d_p5c_overlap_audit.md` | PENDING |
| `phase9d_p5c_error_cases.csv` | PENDING |
| `phase9d_p5c_controlled_evaluation_validation_report.md` | PENDING |

## Safety

- [x] Scripts do not write to `release/models/` or `models_saved/active/`
- [x] No FastAPI/Gradio changes
- [x] No Phase 9E work
- [ ] User runs P5C evaluation

## User commands

Path B (recommended if candidates missing):

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --fit_final_candidate_models
python code/phase9/partial_redesign/evaluate_phase9d_p5c_controlled_cascade.py --input_dir data\phase7c1\raw --make_plots
python code/phase9/partial_redesign/validate_phase9d_p5c_controlled_evaluation.py
```
