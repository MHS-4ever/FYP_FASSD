# Phase 9D-P5F-P2 Status

| Field | Value |
|-------|--------|
| Phase | 9D-P5F-P2 — FN/FP diagnostic analysis |
| Status | **Scripts ready** — run analyzer then validator on P5F-P1 outputs |
| Prior | P5F-P1 PASS: 10/10 timestamp labels, recall 0.70, 3 FN, 2 FP, packaging blocked |

## Goal

Diagnose failure causes for:

- `human_003`, `human_007`, `human_009` (fabricated_20pct false negatives)
- `T1.2.mp3`, `T4.1.mp3` (non-partial false positives)

No model or threshold changes.

## Deliverables

- [x] `analyze_phase9d_p5f_diagnostics.py`
- [x] `validate_phase9d_p5f_diagnostics.py`
- [x] `phase9d_p5f_p2_diagnostic_design.md`
- [x] Output directory: `reports/phase9/partial_redesign/phase9d_p5f_p2_diagnostics/`

## User next steps

1. `py_compile` analyzer + validator.
2. Run `analyze_phase9d_p5f_diagnostics.py --make_plots`.
3. Run `validate_phase9d_p5f_diagnostics.py`.
4. Review `phase9d_p5f_p2_diagnostic_report.md`.

## Constraints

- Analysis only; P5B thresholds and cascade logic unchanged in production artifacts.
- Forensic-safe wording; false positives and false negatives remain visible.
- No release packaging, no Phase 9E.
