# Phase 9D-P4 Status

- **Phase 9D-P4 status:** SCRIPT CREATED / NOT YET EXECUTED
- **Phase 9D batch status:** COMPLETE (43 controlled cases; validation PASS after P3)
- **Phase 9E FastAPI/Gradio status:** NOT STARTED

## Scripts created

| Script | Purpose |
|---|---|
| `code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py` | Live inference + timestamp overlap diagnostics |
| `code/phase9/testing/summarize_phase9d_p4_partial_diagnostics.py` | Summary CSV, report, optional plots |
| `code/phase9/testing/validate_phase9d_p4_partial_diagnostics.py` | Validate P4 artifacts |
| `code/phase9/testing/phase9d_p4_common.py` | Shared overlap/timestamp helpers |

## Inference update

- `analyze_audio_file(..., return_debug=True)` exposes `debug_info.partial_segment_scores` (all segments)
- Normal fusion/output behavior unchanged

## Next action (user, manual)

1. Run diagnostics:
   `python code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py`
2. Summarize:
   `python code/phase9/testing/summarize_phase9d_p4_partial_diagnostics.py --make_plots`
3. Validate:
   `python code/phase9/testing/validate_phase9d_p4_partial_diagnostics.py`
4. Review `reports/phase9/testing/phase9d_p4_partial_diagnostics/phase9d_p4_partial_diagnostic_report.md`

## Notes

- Timestamps are evaluation-only; never model inputs.
- Partial localization weakness documented; P4 measures timestamp hit rate vs broad activation.
- Phase 9E may proceed after reviewing P4 recommendation (optional tuning later).
