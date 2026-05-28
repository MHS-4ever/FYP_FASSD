# Phase 8E-0 Dataset Validation Report

**Generated:** 2026-05-28 10:26:06 UTC
**Status:** **PASS**

> Phase 8E-0 validates assembled datasets only. It does not train models.

## Row Counts

- file master rows: 184
- segment master rows: 4189
- origin task rows: 46
- replay task rows: 92
- mixer task rows: 92
- partial localization prep rows: 1207

## Label Distributions

- target_is_clean: {'0': 138, '1': 46}
- origin: {'ai_synthetic': np.int64(23), 'human': np.int64(23)}
- replay: {'0': np.int64(46), '1': np.int64(46)}
- mixer: {'0': np.int64(46), '1': np.int64(46)}
- partial eligibility: {'false': np.int64(1207)}

## Leakage Summary

- blocking leakage items: 0

## Notes

- No model artifacts/checkpoints should be created in Phase 8E-0.
- No prediction columns or evidence score filling is allowed.
- Partial fabrication segment training remains blocked unless true segment timestamps exist.
