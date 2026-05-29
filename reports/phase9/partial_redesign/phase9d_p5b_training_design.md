# Phase 9D-P5B Training Design (Experimental)

## Purpose

Phase 9D-P5B trains and evaluates two **experimental** sklearn models on P5A datasets to address Phase 9D-P4 broad activation:

| Model | Task | Target |
|-------|------|--------|
| `partial_file_candidate_model` | File gate | `target_is_partial_fabrication_file` |
| `partial_segment_localizer_v2` | Segment localizer | `target_is_fabricated_segment` |

**Not production.** Nothing is written to `release/models/` or `models_saved/active/`.

## Inputs

| Artifact | Path |
|----------|------|
| File gate dataset | `phase9d_p5_file_partial_gate_dataset.csv` |
| Segment dataset | `phase9d_p5_segment_partial_localizer_dataset.csv` |
| File features JSON | `phase9d_p5_file_gate_feature_columns.json` |
| Segment features JSON | `phase9d_p5_segment_localizer_feature_columns.json` |

## Pipeline (sklearn only)

```
SimpleImputer(median) → VarianceThreshold → StandardScaler → SelectKBest(f_classif) → LogisticRegression(L2, balanced)
```

Feature selection runs **inside** each CV fold.

## Cross-validation

- **File gate:** group by `leakage_group_id` (fallback `split_group_id`, `file_id`)
- **Segment:** group by `file_id` (fallback `leakage_group_id`)
- Prefer `StratifiedGroupKFold`; fallback `GroupKFold`
- Error if group-aware split is infeasible

## Feature sets

### File gate

| Set | Features |
|-----|----------|
| acoustic | File acoustic columns from JSON |
| ssl | `ssl_emb_*` |
| combined | acoustic + ssl |

### Segment localizer v2

| Set | Features |
|-----|----------|
| acoustic | Segment acoustic columns |
| ssl | `ssl_emb_*` |
| localization | Safe within-file / neighbor features only |
| combined | acoustic + ssl + localization |

Timestamps and overlap metadata are **never** model inputs.

## Outputs (`reports/phase9/partial_redesign/phase9d_p5b/`)

| File | Content |
|------|---------|
| `phase9d_p5b_file_gate_metrics.csv` | Per-fold + OOF aggregate file gate metrics |
| `phase9d_p5b_file_gate_oof_predictions.csv` | OOF file probabilities |
| `phase9d_p5b_file_gate_threshold_grid.csv` | Threshold sweep 0.10–0.90 |
| `phase9d_p5b_segment_localizer_metrics.csv` | Segment metrics incl. AP, precision@top5 |
| `phase9d_p5b_segment_oof_predictions.csv` | OOF segment probabilities |
| `phase9d_p5b_segment_threshold_grid.csv` | Segment threshold grid |
| `phase9d_p5b_segment_file_localization_metrics.csv` | Per-file top-k / broad activation |
| `phase9d_p5b_cascade_simulation_results.csv` | Two-stage threshold simulation |
| `phase9d_p5b_feature_audit.csv` | Leakage + group integrity audit |
| `phase9d_p5b_training_report.md` | Summary + recommendation |
| `figures/` | Optional ROC/PR plots (`--make_plots`) |
| `artifacts/` | Optional full-fit joblib (`--save_artifacts`) |

## Cascade simulation (P5B-P1)

Two-stage positive requires **both**:

1. File gate: `file_gate_probability >= file_gate_threshold`
2. Segment localized evidence on that file:
   - at least one segment `>= segment_threshold`
   - `high_segment_fraction <= broad_limit`
   - `topk_minus_rest_probability >= contrast_threshold`

Threshold grids:

| Parameter | Values |
|-----------|--------|
| `file_gate_threshold` | 0.30, 0.40, 0.50, 0.60, 0.70, 0.80 |
| `segment_threshold` | 0.50, 0.60, 0.70, 0.80, 0.85, 0.90 |
| `contrast_threshold` | 0.15, 0.25, 0.35 |
| `broad_limit` | 0.25, 0.35, 0.45 |

Output columns include partial recall, category-specific false partial rates, top-k hit rates when cascade-positive, broad activation when cascade-positive, and `recommended_threshold_pair`.

Recommendation constraints (must all pass for release-ready pair):

- `direct_false_partial_rate <= 0.20`
- `replay_false_partial_rate <= 0.05`
- `mixer_false_partial_rate <= 0.05`
- `broad_activation_rate_when_positive <= 0.10`
- `file_gate_threshold >= 0.50`

If no candidate satisfies all constraints: *"No release-ready threshold pair found; use as manual-review support only."*

## Shared cascade acceptance config (P5B-P2)

`CASCADE_ACCEPTANCE_CONFIG` in `phase9d_p5_training_utils.py` is the single source of truth for:

- cascade recommendation (`_apply_cascade_recommendations`)
- training report diagnostics and wording
- validation (`assess_cascade_release_ready`)

| Key | Default | Enforced |
|-----|---------|----------|
| `max_direct_false_partial_rate` | 0.20 | yes |
| `max_replay_false_partial_rate` | 0.05 | yes |
| `max_mixer_false_partial_rate` | 0.05 | yes |
| `max_broad_activation_rate_when_positive` | 0.10 | yes |
| `min_file_gate_threshold` | 0.50 | yes |
| `max_non_partial_false_alarm_rate` | None | optional (not enforced) |
| `min_partial_file_recall` | None | optional (not enforced) |

No hidden validator-only thresholds. Empty CSV `recommended_threshold_pair` cells (NaN) are **not** treated as recommendations.

When no release-ready pair exists, the training report uses manual-review-only wording and does **not** suggest packaging evaluation.

## Broad activation reporting (P5B-P1)

Report broad activation for the **selected model only**:

- segment `feature_set = combined` (default)
- segment threshold = 0.50 (default, overridable via CLI)

Counts are **unique partial files** only — not aggregated across feature sets or thresholds.

## Recompute without retraining (P5B-P1)

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --reuse_existing_predictions
```

Loads existing OOF CSVs, reruns cascade simulation and report generation. Does **not** retrain.

## User commands

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py
python code/phase9/partial_redesign/validate_phase9d_p5_training_results.py
```

After P5B-P1 fixes on existing OOF:

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --reuse_existing_predictions
python code/phase9/partial_redesign/validate_phase9d_p5_training_results.py
```

Optional flags: `--make_plots`, `--save_artifacts`, `--cv_folds`, `--selected_segment_feature_set`, `--selected_segment_threshold`, feature set overrides.

## Next steps after P5B

- If cascade metrics improve broad activation vs P4: consider **P5C packaging evaluation** (still not production)
- If not: further redesign before any release integration
- **Phase 9E NOT STARTED**
