# Phase 4 Runbook — Two-Stage Manipulation v3 (script-only)

**Scope:** Existing 184 leakage-safe files + `testing_audios` eval. No new recordings.

**Stop rule:** Stage-1 recall on manipulated `testing_audios` cases **≥ 70%**. If below → do not keep retraining; document limitation and move to Phase 6.

---

## What was prepared

| Item | Path |
|------|------|
| v3 training script | `code/release_audit/train_two_stage_manipulation_v3.py` |
| Synthetic aug helpers | `code/release_audit/phase4_synthetic_augmentation.py` |
| Replay/mixer dev thresholds | `code/release_audit/eval_phase4_axis_thresholds_dev.py` |
| Partial arbitration (coexistence) | `release/src/inference_pipeline.py`, `fusion_rules.py`, `app_report_formatting.py` |

**Arbitration change:** Localized partial evidence now **coexists** with replay/mixer context (segment table stays visible for review). Non-localized partial is still blocked from fusion elevation.

---

## Commands (run in `conda activate fassd`)

```powershell
cd E:\FYP\code\release_audit
```

### 1. Replay/mixer threshold grids on dev only (fast, ~minutes if features cached)

```powershell
python eval_phase4_axis_thresholds_dev.py
```

After v3 feature extract, reuse cache:

```powershell
python eval_phase4_axis_thresholds_dev.py --features-csv E:\FYP\reports\release_audit\phase4_two_stage_manipulation_v3_2026-06-13\phase7_features_base.csv
```

Outputs: `phase4_replay_dev_threshold_grid.csv`, `phase4_mixer_dev_threshold_grid.csv`, `phase4_axis_threshold_recommendations.json` (does **not** overwrite `release/models/`).

### 2. Full v3 train (long — run yourself)

```powershell
python train_two_stage_manipulation_v3.py
```

Resume after features are cached:

```powershell
python train_two_stage_manipulation_v3.py --skip-feature-extract
```

**Exit code 2** = stop rule failed (manipulated testing_audios Stage-1 recall &lt; 70%).

### 3. Optional smoke compile (agent-safe)

```powershell
python -m py_compile train_two_stage_manipulation_v3.py phase4_synthetic_augmentation.py eval_phase4_axis_thresholds_dev.py
```

---

## Expected outputs (`reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/`)

- `phase7_features_base.csv`, `testing_audios_features_base.csv`
- `phase4_train_synthetic_rows.csv`, `phase4_fit_train_manifest.csv`
- `two_stage_v3_predictions.csv`, `two_stage_v3_stage1_metrics.csv`, `two_stage_v3_subtype_metrics.csv`
- `two_stage_v3_testing_focus.csv`, `two_stage_v3_stop_rule.json`
- `phase4_two_stage_v3_report.md`
- Models: `stage1_v3_manipulation_detector.joblib`, `stage2_v3_subtype_classifier.joblib` (experimental only)

---

## Honest expectations

- Stage 1 may improve on leakage-safe test with synth aug.
- Forensic cases **T3.4, T4.5, T5.*** may still fail — acceptable to document.
- v3 models are **not** promoted to `release/models/` without explicit Phase 5 decision.

---

## After you run training

Share `phase4_two_stage_v3_report.md` and `two_stage_v3_stop_rule.json`. We will:

1. Interpret stop rule pass/fail.
2. Map testing_audios per-case outcomes vs T3/T4/T5.
3. Decide Phase 4 close → Phase 5 (ship) or Phase 6 (calibration wording).
