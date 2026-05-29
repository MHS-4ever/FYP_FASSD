# Phase 9D-P5D Status

| Field | Value |
|-------|--------|
| Phase | 9D-P5D-P4 — Timestamp error metric |
| Status | **P5D-P4 scripts ready** — re-run evaluator then validator after pull |
| Blocker from P5C | All 184 P5C files were `seen_in_p5_training`; no independent holdout |
| Goal | Evaluate P5B candidate cascade on `testing_audios` (t1–t5, fabricated) |

## P5D-P4 changes

- `candidate_timestamp_error_seconds` on file predictions; median over timestamp-positive files.
- Validator `median_candidate_timestamp_error_rule` (not silent NaN when errors exist).

## P5D-P3 changes

- `unknown_condition_count` + not-applicable `unknown_condition_positive_rate` when count is 0.
- Validator `metrics_finite_where_applicable` uses per-stratum count rules.
- Dynamic partial-positive blocker text in report (matches `partial_file_count`).

## P5D-P2 changes

- Fix `overlap_threshold` TypeError in shared cascade evaluation.
- `phase9d_p5d_run_status.json` + stale-output validation.
- Stricter `evaluate_p5d_release_gates()`; packaging stays blocked on current holdout.
- Artifact-path-only reference model audit (no false fail on safety wording).

## P5D-P1 changes

- Report: P5B-only wording; skipped-file note; explicit release packaging blockers.
- Validator: path/claim/column-based reference-model audit (not substring name ban).
- Validation report: model artifact audit section.

## Deliverables

- [x] `evaluate_phase9d_p5d_independent_cascade.py`
- [x] `validate_phase9d_p5d_independent_evaluation.py`
- [x] `phase9d_p5_evaluation_shared.py` (live extraction + shared inference)
- [x] `assess_p5d_release_readiness` in `phase9d_p5_training_utils.py`
- [x] Design doc: `reports/phase9/partial_redesign/phase9d_p5d_independent_evaluation_design.md`

## Constraints (unchanged)

- No retrain / no fit in P5D
- No `release/models/` or `models_saved/active/` writes
- No FastAPI / Gradio / Phase 9E
- P5B experimental candidates only

## User next steps

1. `py_compile` the three scripts (see design doc).
2. Run evaluator with `--input_root testing_audios` (or `data\testing_audios`).
3. Run validator.
4. Share report, validation report, metrics, predictions, overlap audit, error cases.

## Output directory

`reports/phase9/partial_redesign/phase9d_p5d/` (created on first evaluator run)
