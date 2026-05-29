# Phase 9D-P5D — Independent Held-Out Partial-Cascade Evaluation (Design)

## Purpose

Prove whether the **accepted P5B partial-fabrication candidate cascade** generalizes on audio **not** reused from P5A/P5B training or P5C controlled evaluation. This phase is **experimental evidence only** — not production-ready, not court proof, not a final authenticity verdict.

## Scope

| In scope | Out of scope |
|----------|----------------|
| `testing_audios` folders `t1`–`t5`, `fabricated` (or `data/testing_audios/...`) | Retraining or fitting models |
| P5B candidate joblib + JSON under `reports/phase9/partial_redesign/phase9d_p5b/candidate_models/` | Writes to `release/models/` or `models_saved/active/` |
| Overlap audit vs P5 training + P5C manifest | FastAPI / Gradio changes |
| Live acoustic + SSL extraction when phase8e0 masters lack files | Reference-model activation, old release partial model |
| Forensic-safe reporting | Phase 9E, release packaging |

## Accepted cascade (P5B-P2)

- File gate features: `ssl`
- Segment localizer features: `combined`
- `file_gate_threshold = 0.50`
- `segment_threshold = 0.90`
- `contrast_threshold = 0.25`
- `broad_limit = 0.45`

**Partial evidence positive** (file level):

```
file_gate_probability >= 0.50
AND max(segment_probability) >= 0.90
AND high_segment_fraction <= 0.45
AND topk_minus_rest_probability >= 0.25
```

## Input handling

- CLI: `--input_root testing_audios` or `--input_root data\testing_audios`
- Auto-fallback: project `testing_audios`, then `data/testing_audios`
- Recursive scan **only** under: `t1`, `t2`, `t3`, `t4`, `t5`, `fabricated` (case-insensitive folder names, e.g. `T1`)
- Does **not** scan noise_rir, augmented trees, ASVspoof roots, release, or reports

## Label inference (manifest)

| Rule | Value |
|------|--------|
| Under `fabricated/` | `expected_partial_label = 1` |
| Under `t1`–`t5` | `expected_partial_label = 0` unless filename hints fabricated/partial |
| Timestamps | Only from explicit sidecar `.json`; never invented |
| `expected_condition` | `fabricated`, `direct`, `replay`, `mixer_or_channel`, or `unknown_testing_condition` from folder + filename hints |

## Overlap audit

Statuses per file:

- `independent_holdout`
- `seen_in_p5_training` (P5 gate/segment datasets)
- `seen_in_p5c_controlled` (P5C manifest paths)
- `unknown_overlap_status`

If `independent_holdout_count == 0`, release packaging evaluation is **blocked**.

## Outputs

Directory: `reports/phase9/partial_redesign/phase9d_p5d/`

| Artifact | Role |
|----------|------|
| `phase9d_p5d_independent_manifest.csv` | Scanned files + inferred labels |
| `phase9d_p5d_overlap_audit.csv` / `.md` | Training/P5C overlap |
| `phase9d_p5d_file_predictions.csv` | Cascade file-level results |
| `phase9d_p5d_segment_predictions.csv` | Segment probabilities |
| `phase9d_p5d_independent_metrics.csv` / `.json` | Summary metrics |
| `phase9d_p5d_error_cases.csv` | Skipped/failed files |
| `phase9d_p5d_independent_evaluation_report.md` | Human-readable summary |

Validation: `reports/phase9/validation/phase9d_p5d_independent_evaluation_validation_report.md`

## P5D-P4 (timestamp error metric)

- File predictions include `candidate_timestamp_error_seconds` (center-to-center vs known fabricated region).
- Metrics: `timestamp_error_count`, `median_candidate_timestamp_error_seconds`, availability flags.
- Validator requires finite median when `timestamp_error_count > 0`; documents missing reason otherwise.

## P5D-P3 (not-applicable metrics)

- Condition counts: `direct_condition_count`, `replay_condition_count`, `mixer_condition_count`, `unknown_condition_count`.
- `unknown_condition_positive_rate` is `null` / report `not_applicable` when `unknown_condition_count == 0` (not forced to 0.0).
- Validator allows null/NaN for stratum rates only when the corresponding count is zero.
- Report blocker text uses dynamic `partial_file_count` (e.g. 2 < 5 minimum).

## P5D-P2 (crash fix, run status, release gates)

- `segment_overlap_metrics(..., overlap_threshold=0.10)` via `P5D_TIMESTAMP_OVERLAP_THRESHOLD`.
- `phase9d_p5d_run_status.json` marks running/completed/failed; validator rejects stale outputs after crashes.
- Release packaging gates require holdout coverage, ≥5 partial labels, zero failures, complete condition strata, and timestamp-positive localization evidence.
- Validator audits **artifact paths only** (not safety prose mentioning `models_saved/active`).

## P5D-P1 (validator/report correction)

- Report states **P5B-only** experimental candidate usage without naming reference architectures.
- Validator `reference_models_not_activated` audits **artifact paths**, **active-use claims**, and **prediction columns** — not bare name mentions.
- Validation report includes an explicit **model artifact audit** section.
- Release packaging remains blocked when labels are incomplete, partial positives are sparse, timestamps are unscorable, or files fail/skipped.

## Scripts

- `code/phase9/partial_redesign/evaluate_phase9d_p5d_independent_cascade.py`
- `code/phase9/partial_redesign/validate_phase9d_p5d_independent_evaluation.py`
- Shared: `code/phase9/partial_redesign/phase9d_p5_evaluation_shared.py`

## Manual run (user)

```text
python -m py_compile code\phase9\partial_redesign\phase9d_p5_training_utils.py
python -m py_compile code\phase9\partial_redesign\evaluate_phase9d_p5d_independent_cascade.py
python -m py_compile code\phase9\partial_redesign\validate_phase9d_p5d_independent_evaluation.py

python code\phase9\partial_redesign\evaluate_phase9d_p5d_independent_cascade.py --input_root testing_audios --make_plots
python code\phase9\partial_redesign\validate_phase9d_p5d_independent_evaluation.py
```

## Release packaging evaluation gates

“Candidate acceptable for release packaging evaluation” requires among other checks:

- `independent_holdout_count > 0`
- `evaluated_files > 0`
- Thresholds on direct/replay/mixer false partial rates when labels exist
- `partial_evidence_recall >= 0.65` when partial positives exist
- `top5_hit_rate_when_positive >= 0.80` when timestamp positives exist
- Invalid/short/silent files handled without crashing

Incomplete labels or missing partial positives produce **limited** or **blocked** assessments (see `assess_p5d_release_readiness`).
