# Phase 6 Runbook — Calibration + final Gradio wording

**Prerequisite:** Phases 2–5 models frozen (origin @ 0.92, replay/mixer packaged, Phase 5 partial promoted).

## A. Promote Phase 5 partial (one-time)

```powershell
conda activate fassd
cd E:\FYP\code\release_audit
python promote_phase5_partial_to_release.py
```

Backup: `release/models/partial_segment/backup_before_phase5_2026-06-13/`

Restart Gradio/FastAPI after promote (model cache).

## B. Fit evidence bands on leakage-safe dev

```powershell
python fit_phase6_evidence_calibration.py
```

Writes: `release/config/evidence_calibration.json`

## C. Consistency test (mock, fast)

```powershell
python validate_phase6_report_consistency.py
```

Optional live file:

```powershell
python validate_phase6_report_consistency.py --live-audio E:\FYP\testing_audios\T1\T1.1.mp3
```

## D. Manual UI check

```powershell
cd E:\FYP\release
python app_gradio.py
```

Verify on T4.3 / T5_FAB / T1.2:
- Cards show **Evidence strength: Low/Medium/High** (not 0.xxx)
- Inconclusive axes labeled explicitly
- Technical details panel still shows uncalibrated raw scores
- PDF/JSON match Gradio segment table bands

## What changed in release code

| File | Change |
|------|--------|
| `release/src/evidence_calibration.py` | Band mapping + inconclusive states |
| `release/src/app_report_formatting.py` | Cards, segments, voice origin use bands |
| `release/src/pdf_report_generator.py` | PDF segment column = evidence strength |
| `release/config/evidence_calibration.json` | Dev-fitted cutpoints |

## Phase 6 does not

- Retrain any axis model
- Collect new audio
- Change origin/replay/mixer joblibs (only display calibration)
