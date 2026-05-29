# Phase 9D-P5C Controlled Evaluation Design (Experimental)

## Purpose

Test the **accepted P5B partial-fabrication cascade** on controlled Phase 7C1 audio before any release packaging. This phase answers:

> Does the cascade produce useful partial-fabrication evidence without unacceptable false partial alerts on direct, replay, and mixer files?

**Not production.** No writes to `release/models/` or `models_saved/active/`.

## Accepted cascade (from P5B-P2 validation)

| Parameter | Value |
|-----------|------:|
| `file_gate_threshold` | 0.50 |
| `segment_threshold` | 0.90 |
| `contrast_threshold` | 0.25 |
| `broad_limit` | 0.45 |

| Model | Feature set |
|-------|-------------|
| File gate (`partial_file_candidate_model`) | `ssl` |
| Segment localizer v2 | `combined` |

Cascade positive requires **all** of:

1. `file_gate_probability >= 0.50`
2. At least one `segment_probability >= 0.90`
3. `high_segment_fraction <= 0.45`
4. `topk_minus_rest_probability >= 0.25`

## Candidate model artifacts

Saved only under `reports/phase9/partial_redesign/phase9d_p5b/candidate_models/`:

- `partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- `partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- `partial_cascade_config__p5b_experimental_candidate.json`

Fit manually with:

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --fit_final_candidate_models
```

Do **not** use the old release partial model, AASIST, or HybridResNet.

## Controlled input

Default: `data/phase7c1/raw` (one level of category folders only).

**Not scanned:** `noise_rir`, `augmented`, or other huge unrelated trees.

## Overlap audit

Each evaluated file is classified:

- `independent_holdout` — not found in P5A/P5B training datasets
- `seen_in_p5_training` — path/name/stem match
- `unknown_overlap_status`

If most files are `seen_in_p5_training`, the report states this is **controlled reuse/sanity evaluation**, not true held-out evaluation.

## Features for inference

Uses **phase8e0** precomputed file/segment features joined by normalized `audio_path` (live-style scoring path without retraining). Localization features are recomputed per file from segment rows via `compute_live_localization_features`.

## Outputs (`reports/phase9/partial_redesign/phase9d_p5c/`)

| File | Content |
|------|---------|
| `phase9d_p5c_controlled_manifest.csv` | Evaluation manifest |
| `phase9d_p5c_overlap_audit.csv` / `.md` | Training overlap audit |
| `phase9d_p5c_file_predictions.csv` | File-level cascade outputs |
| `phase9d_p5c_segment_predictions.csv` | Segment-level probabilities |
| `phase9d_p5c_controlled_metrics.csv` / `.json` | Aggregated metrics |
| `phase9d_p5c_error_cases.csv` | Load/feature failures |
| `phase9d_p5c_controlled_evaluation_report.md` | Summary + release readiness |

## Release readiness (P5C)

Recommends **release packaging evaluation** only if:

- `independent_holdout_count > 0`
- `direct_false_partial_rate <= 0.20`
- `replay_false_partial_rate <= 0.05`
- `mixer_false_partial_rate <= 0.05`
- `broad_activation_rate_when_positive <= 0.10`
- `partial_evidence_recall >= 0.65` (when partial positives exist)
- `top5_hit_rate_when_positive >= 0.80` (when timestamp labels exist)
- Invalid/short/silent files handled without crashing

Otherwise: manual-review support only; **no packaging**.

## User commands

Path A — candidate models already exist:

```text
python code/phase9/partial_redesign/evaluate_phase9d_p5c_controlled_cascade.py --input_dir data\phase7c1\raw --make_plots
python code/phase9/partial_redesign/validate_phase9d_p5c_controlled_evaluation.py
```

Path B — fit candidates first:

```text
python code/phase9/partial_redesign/train_phase9d_p5_partial_models.py --fit_final_candidate_models
python code/phase9/partial_redesign/evaluate_phase9d_p5c_controlled_cascade.py --input_dir data\phase7c1\raw --make_plots
python code/phase9/partial_redesign/validate_phase9d_p5c_controlled_evaluation.py
```

## Phase 9E

**NOT STARTED.**
