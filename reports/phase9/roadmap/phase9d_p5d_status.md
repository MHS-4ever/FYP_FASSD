# Phase 9D-P5D Status

| Field | Value |
|-------|--------|
| Phase | 9D-P5D-R2-P1 — Validator recovery-path logic for chunked SSL |
| Status | **P5D-R2-P1 validator fix ready** — validate existing R2 outputs, then optional re-run |
| Blocker from P5C | All 184 P5C files were `seen_in_p5_training`; no independent holdout |
| Goal | Evaluate P5B candidate cascade on `testing_audios` (t1–t5, fabricated) |

## P5D-R2-P1 changes

- Validator accepts CUDA OOM recovery via chunked fallback (`ssl_chunked_fallback_*`) when full CPU fallback was skipped for long audio.
- `ssl_oom_fallback_reported` detail now includes CPU and chunked attempt/success/failure counters.
- No evaluator/SSL/chunking/threshold changes; release packaging remains blocked.

## P5D-R2 changes

- Memory-safe chunked SSL fallback for long audio after CUDA OOM (targets `testing_audios/T4/T4.1.mp3` recovery).
- Preserves 45s full-audio CPU fallback cap; long files use chunked CPU fallback instead of silent skip.
- Adds chunked/long-audio robustness metrics, file-level SSL mode columns, and validator checks.
- Thresholds, cascade logic, and release packaging gates unchanged; need more independent partial-positive files before release packaging.

## P5D-R1-P1 changes

- Fixes robustness stats propagation (`robustness_stats is None` guard instead of truthy replacement).
- Adds explicit SSL counter increment helper and long-audio fallback skip counter.
- Validator cross-checks SSL OOM/fallback counters against error cases.
- Reporting/metrics consistency fix only; thresholds and cascade behavior are unchanged.
- Long-audio chunking is deferred to P5D-R2. Release packaging remains blocked.

## P5D-R1 changes

- MP4/M4A robustness handling with explicit decoder/container failure classification.
- SSL CUDA OOM handling with optional CPU fallback and explicit fallback counters.
- Robustness metrics + report section added; failed files remain visible and classified.
- Release packaging remains blocked when robustness blockers remain.

## P5D-P5 changes

- Fix candidate segment selection to always use rank-1 segment after probability sorting.
- Add `candidate_segment_probability` and `candidate_segment_rank` to file outputs.
- Separate chronological segment index from probability rank (`segment_index_chronological` vs `segment_rank`).
- Add validator checks for candidate/rank matching and segment index/rank integrity.
- Reporting only; no threshold/model behavior change. Release packaging remains blocked.

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
