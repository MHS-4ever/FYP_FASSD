# Phase 7E3B — AASIST Fine-Tune Manifest Summary

**Generated:** 2026-05-26T20:36:56.431412+00:00

## Row counts (training windows)

- **Train:** 1320
- **Val:** 260
- **Test:** 280
- **Rejected parent rows:** 0

## risk_target balance (all splits)

- risk_target=0: **419**
- risk_target=1: **1441**

## Notes

- `risk_target=1` = forensic-risk positive, **not** AI-generated.
- `aasist_label`: 1=bonafide (low risk), 0=spoof (forensic positive) per official AASIST convention.
- Phase 7C1 clean-human windows use elevated `sample_weight` (up to 4.0) to reduce false alarms.
- **Do not train** until manifests pass validation.

