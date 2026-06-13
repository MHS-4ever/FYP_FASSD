# Phase 4 — Two-stage manipulation v3 decision

- Completed: 2026-06-13T13:32:09+00:00
- Training runtime: ~8 min (feature cache + 876 synth rows + LR fit)
- New audio collected: **No** (script-only edits + codec aug on existing 184 files)
- Release models overwritten: **No**

## Stop rule

| Metric | Result | Required |
|--------|--------|----------|
| Manipulated `testing_audios` Stage-1 recall | **20%** (3/15) | ≥ 70% |
| Outcome | **FAIL** | — |

**Decision: STOP Phase 4 retraining.** Per roadmap stop rule, do not iterate further on this unified two-stage acoustic axis. Document limitation and proceed to **Phase 6** (honest calibration / UI wording). Keep shipping **separate release axes** (origin @ 0.92, replay, mixer, partial) from Phases 1–2.

## What worked (limited)

| Case | Manipulation | Stage-1 | Final | Notes |
|------|--------------|---------|-------|-------|
| T2.1 | human_replay | ✓ (0.46) | replay | In-distribution replay |
| T2.2 | mixer_processed | ✓ (0.92) | mixer_channel | In-distribution mixer |
| T2.3 | human_replay | ✓ (0.97) | mixer_channel | Stage-1 hit; subtype confused replay→mixer |

Clean negatives (T1.*, T3.1, T4.2): Stage-1 correctly low — **no false manipulation flag** on most clean cases.

## What failed (expected / documented)

| Group | Cases | Stage-1 recall | Stage-2 subtype accuracy (when S1 fired) | Notes |
|-------|-------|----------------|------------------------------------------|-------|
| T3 replay/mixer | T3.2, T3.4, T3.5 | 0/3 | — | Weak channel cues vs Phase 7 training |
| T3.3, T2.4 | mp4 | N/A | — | `unsupported_audio_extension` in v3 feature extract |
| T4 partial/platform | T4.3, T4.5 | 0/2 | Subtype often right but gated | S2 conf 0.94–0.96, S1 prob 0.005–0.08 |
| T5 edited | T5.1–T5.5 | 0/5 | Subtype often right but gated | S2 edited_spliced 0.49–0.92, S1 prob 0.03–0.28 |
| T5_FAB | partial insert | 0/1 | Subtype wrong (edited) | S1 prob 0.07 |
| T2.5 | human_replay | 0/1 | S2 replay 0.99 | S1 prob 0.02 — classic gate failure |
| T4.1 | **clean** | **FP** | mixer_channel | S1 prob 0.99 on clean_direct |

**Stage-2 “hidden signal”:** On 10+ manipulated misses, Stage-2 predicted the expected subtype with confidence ≥ 0.4, but `final_reported_type=clean` because Stage-1 did not fire. The two-stage gate is the bottleneck, not subtype ranking alone.

## Leakage-safe vs synthetic overfit

| Scope | Stage-1 recall | Stage-1 specificity |
|-------|----------------|---------------------|
| fit_train (980 rows, 876 synth) | **83.2%** | 93.9% |
| leakage-safe dev | 46.7% | 100% |
| leakage-safe test | **33.3%** | 100% |
| testing_audios (manipulated only) | **20.0%** | — |

876 synthetic/aug rows inflated train fit but did **not** generalize to held-out Phase 7 test or real-world `testing_audios`. Low dev threshold (0.42) still missed forensic cases.

## Replay/mixer dev thresholds (separate axes, unchanged in release)

Dev-only re-derivation on **packaged** replay/mixer models (not v3):

| Axis | Release threshold | Phase 4 dev recommendation |
|------|-----------------|----------------------------|
| Replay | 0.65 | 0.73 |
| Mixer | 0.75 | 0.94 |

These axes remain viable as **independent evidence**; v3 did not replace them.

## Phase 4 code kept (non-training)

| Change | Status | Ship? |
|--------|--------|-------|
| Partial arbitration coexistence (`coexists_with_replay_or_mixer_context`) | Implemented in `inference_pipeline.py`, `fusion_rules.py`, `app_report_formatting.py` | **Yes** — improves UI honesty when replay/mixer + localized partial co-occur |
| v3 models (`stage1_v3_*.joblib`, `stage2_v3_*.joblib`) | Experimental only | **No** — stop rule failed |
| MP4 in v3 `extract_rows` | Not wired (T2.4, T3.3 skipped) | Fix in app path only (Phase 1 done); optional for future eval scripts |

## Recommended next steps

1. **Phase 6** — Calibration wording: manipulation subtype from unified acoustic LR is **not** production-ready; document in thesis/UI that channel manipulation detection relies on separate replay/mixer/partial axes with manual review.
2. **Do not promote** `train_two_stage_manipulation_v3.py` artifacts to `release/models/`.
3. **Optional Phase 5** — If shipping continues, scope is origin + existing replay/mixer/partial only; no unified manipulation classifier.
4. **Thesis honest outcomes** — T3.4, T4.5, T5.* failures are **acceptable documented limitations** under script-only, no-new-recording constraint.

## Artifact index

- Report: `phase4_two_stage_v3_report.md`
- Stop rule: `two_stage_v3_stop_rule.json`
- Per-case: `two_stage_v3_testing_focus.csv`
- Metrics: `two_stage_v3_stage1_metrics.csv`, `two_stage_v3_subtype_metrics.csv`
- Runbook: `phase4_runbook.md`
