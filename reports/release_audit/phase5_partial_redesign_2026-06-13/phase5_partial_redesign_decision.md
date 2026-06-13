# Phase 5 — Partial segment redesign decision

- Completed: 2026-06-13
- New audio: **No**
- Augmentation: **No**
- F9 features removed: **Yes** (5 within-file percentile/max-normalized features)
- Release `partial_segment` overwritten at decision time: **No**
- Post-Phase-7 promotion: **Yes** — Phase 5 model promoted to `release/models/partial_segment/partial_segment_model__combined__experimental.joblib`; old model backed up under `release/models/partial_segment/backup_before_phase5_2026-06-13/`

## Stop rule (leakage-safe test oracle)

| Metric | Result | Required |
|--------|--------|----------|
| Partial-file top-5 hit rate (test) | **100%** (10/10) | ≥ 50% |
| Localized rate (top5 + not broad) | **100%** | — |
| Clean-file broad-activation rate (test) | **0%** | — |
| Outcome | **PASS** | — |

Dev oracle: 100% top-5, 100% localized.

**Selected segment threshold (dev grid): `0.95`** — high; scores still saturate on true partials (~1.0) but **broad activation is controlled** (hsf 10% on T4.3 vs 97% on release model).

---

## testing_audios — primary cases (PASS)

| Case | Label region | Phase 5 top segment | Overlap | Gate | vs release baseline |
|------|--------------|---------------------|---------|------|---------------------|
| **T4.3** | 35–58 s | **46–50 s** | 4 s (full segment in label) | `localized_pattern_supported`, fusion eligible | **Fixed** — was `global_activation_not_localized`, 97% broad |
| **T5_FAB_001** | 14–21 s | **18–22 s** | 3 s (75% of seg) | `localized_pattern_supported`, fusion eligible | **Held** — similar to release (12–16 s before) |

Both primary partial forensic cases now pass oracle + cascade gating with the Phase 5 model.

---

## testing_audios — negatives (mixed)

| Case | Expected | max seg prob | high_seg_frac | Gate | Issue |
|------|----------|--------------|---------------|------|-------|
| T1.1 | clean human | 0.015 | 0.0 | weak | OK |
| **T1.2** | clean human | **0.897** | 0.0 | **localized + fusion eligible** | **False partial spike** (studio clean) |
| **T1.3** | clean AI | **0.691** | 0.0 | **localized + fusion eligible** | **False partial spike** (fully synthetic file) |
| T2.3 | human replay | 0.002 | 0.0 | weak | OK |
| T3.2 | AI replay | 0.035 | 0.0 | weak | OK |

F9 removal fixed **broad** false activation (T1.2 was 98% high_seg_frac on release). Remaining risk is **single-segment spikes** on non-partial files — especially fully-AI or studio-clean clips where one window looks “different” without a splice.

---

## Comparison to Phase 4 / other axes

| Axis | Phase outcome |
|------|----------------|
| Phase 4 manipulation v3 | **STOP** (20% Stage-1 recall) — do not ship |
| Phase 5 partial (no F9) | **PASS** oracle stop rule; **primary testing_audios PASS** |
| Resampling / aug research | Did not drive Phase 5; F9 strip + same Phase 7 labels did |

---

## Recommendation

1. **Promoted in Phase 7** after the final release matrix: `partial_segment` now uses the Phase 5 no-F9 model at threshold 0.95.
2. **Accept Phase 5 as thesis evidence** that F9 features caused broad-activation failure; no-F9 localizer localizes T4.3/T5_FAB on held-out audio.
3. **Keep manual-review wording:** the model highlights candidate segments and does not prove fabrication.
4. **Phase 6 wording completed:** user-facing outputs now show Low/Medium/High evidence bands and raw scores only in technical details.

---

## Artifacts

- `phase5_partial_train_report.md`, `phase5_stop_rule.json`
- `phase5_oracle_file_metrics.csv`
- `phase5_testing_audios_oracle_cascade.csv`, `phase5_testing_audios_eval_report.md`
- Model: `phase5_partial_segment_localizer.joblib` (experimental)
