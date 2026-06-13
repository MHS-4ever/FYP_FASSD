# Phase 5 Runbook — Partial segment redesign (no F9)

**Scope:** Retrain partial **segment** localizer on existing Phase 7 segment labels. Remove audit-F9 within-file percentile / max-normalized features. No augmentation. Does **not** overwrite `release/models/partial_segment/`.

**Stop rule:** Leakage-safe **test** oracle top-5 hit rate on partial files ≥ **50%**.

---

## Steps (run in `conda activate fassd`)

```powershell
cd E:\FYP\code\release_audit
```

### 1. Prepare dataset + F9 feature audit (fast, ~1–2 min)

```powershell
python prepare_phase5_partial_dataset.py
```

If `phase9d_p5_segment_partial_localizer_dataset.csv` is missing (~121 MB):

```powershell
python prepare_phase5_partial_dataset.py --assemble-if-missing
```

*(Assembly can take 10–30+ min on segment master.)*

### 2. Train segment localizer (long — **you run this**)

```powershell
python train_phase5_partial_segment.py
```

**Exit code 2** = stop rule failed (test top-5 hit &lt; 50%).

### 3. Eval on testing_audios subset (long — WavLM per file — **you run this**)

```powershell
python eval_phase5_partial_oracle_cascade.py
```

Default IDs: `T4.3`, `T5_FAB_001` + negatives `T1.1`, `T1.2`, `T1.3`, `T2.3`, `T3.2`.

Force CPU for long files:

```powershell
python eval_phase5_partial_oracle_cascade.py --cpu-ids T4.3 T5_FAB_001
```

### 4. Smoke compile (agent-safe)

```powershell
python -m py_compile phase5_partial_common.py prepare_phase5_partial_dataset.py train_phase5_partial_segment.py eval_phase5_partial_oracle_cascade.py
```

---

## Outputs (`reports/release_audit/phase5_partial_redesign_2026-06-13/`)

| File | Purpose |
|------|---------|
| `phase5_f9_feature_audit.md` | F9 features removed |
| `phase5_segment_feature_columns_no_f9.json` | Model input list |
| `phase5_partial_segment_localizer.joblib` | Experimental model |
| `phase5_oracle_file_metrics.csv` | Per-file oracle on train/dev/test |
| `phase5_stop_rule.json` | Pass/fail |
| `phase5_testing_audios_oracle_cascade.csv` | T4.3 / T5_FAB + negatives |

---

## After training

1. If **stop rule PASS** → run testing_audios eval, then reconnect Phase 4 arbitration in release (already coded; needs model promotion decision).
2. If **stop rule FAIL** → skip promotion; document in Phase 6 thesis wording.
3. Do **not** promote to `release/models/` without explicit decision.

---

## What Phase 5 does not use

- Phase 3 resampling variants (closed)
- Phase 4 manipulation v3 aug (failed stop rule)
- Augmentation on partial model (explicitly excluded)
