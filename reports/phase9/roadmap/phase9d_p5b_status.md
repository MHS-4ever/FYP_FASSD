# Phase 9D-P5B Status

## Phase 9D-P5A — Dataset assembly

| Item | Status |
|------|--------|
| Datasets created | **COMPLETE** |
| Validation | **PASS** (user executed) |

## Phase 9D-P5B — Training / evaluation scripts

| Item | Status |
|------|--------|
| `train_phase9d_p5_partial_models.py` | SCRIPT CREATED |
| `phase9d_p5_training_utils.py` | SCRIPT CREATED |
| `validate_phase9d_p5_training_results.py` | SCRIPT CREATED |
| Design doc | CREATED |
| Training execution | **COMPLETE** (user executed) |
| Training validation | **FAIL** (forbidden NaN bug — fixed in P5B-P1) |

## Phase 9D-P5B-P1 — Validator / reporting / cascade fixes

| Item | Status |
|------|--------|
| Forbidden NaN validator bug | **FIXED** |
| Broad activation report (unique partial files, combined @ 0.50) | **FIXED** |
| Cascade localized-evidence simulation | **FIXED** |
| `--reuse_existing_predictions` | **ADDED** |

## Phase 9D-P5B-P2 — Cascade acceptance alignment

| Item | Status |
|------|--------|
| Shared `CASCADE_ACCEPTANCE_CONFIG` (train + report + validator) | **FIXED** |
| NaN recommendation parsing bug (`"nan"` no longer treated as pair) | **FIXED** |
| Report no longer falls back to best-scoring non-recommended row | **FIXED** |
| Cascade acceptance diagnostics in training report | **ADDED** |
| Validator specific PASS/FAIL cascade messages | **ADDED** |
| User recompute + revalidation | **PENDING** (user runs manually) |

## P5B outputs (after user runs training)

| Output | Status |
|--------|--------|
| `phase9d_p5b_file_gate_metrics.csv` | EXISTS (user run) |
| `phase9d_p5b_file_gate_oof_predictions.csv` | EXISTS (user run) |
| `phase9d_p5b_file_gate_threshold_grid.csv` | EXISTS (user run) |
| `phase9d_p5b_segment_localizer_metrics.csv` | EXISTS (user run) |
| `phase9d_p5b_segment_oof_predictions.csv` | EXISTS (user run) |
| `phase9d_p5b_segment_threshold_grid.csv` | EXISTS (user run) |
| `phase9d_p5b_segment_file_localization_metrics.csv` | EXISTS (needs P5B-P1 recompute) |
| `phase9d_p5b_cascade_simulation_results.csv` | EXISTS (needs P5B-P1 recompute) |
| `phase9d_p5b_feature_audit.csv` | EXISTS (user run) |
| `phase9d_p5b_training_report.md` | EXISTS (needs P5B-P1 recompute) |
| `phase9d_p5b_training_validation_report.md` | FAIL (pre-P5B-P1) |

## Safety

- [x] Scripts save only under `reports/phase9/partial_redesign/phase9d_p5b/`
- [x] No writes to `release/models/` or `models_saved/active/`
- [x] No `fake_score` / `real_score`
- [x] Timestamps not used as features
- [x] User ran training (P5B)
- [ ] User reruns recompute + validation (P5B-P1)

## Downstream

| Phase | Status |
|-------|--------|
| Phase 9D-P5C packaging evaluation (if warranted) | NOT STARTED |
| Phase 9E apps | **NOT STARTED** |

## User commands

Initial training (already done):

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py
```

P5B-P1/P5B-P2 recompute from existing OOF (no retraining):

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --reuse_existing_predictions --make_plots
python code/phase9/partial_redesign/validate_phase9d_p5_training_results.py
```

Optional:

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --make_plots --save_artifacts
```
