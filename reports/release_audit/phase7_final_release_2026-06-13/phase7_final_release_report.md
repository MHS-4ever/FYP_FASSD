# Phase 7 — Final Release Packaging + Thesis Evidence

- Completed: 2026-06-13
- New audio collected: **No**
- Release package updated: **Yes**
- Final app status: **experimental forensic decision-support demo**
- Final claim level: **multi-axis evidence indicators only; no conclusive authenticity decision**

## Final Packaged Components

| Axis / component | Final source | Active artifact / config | Threshold / display |
|---|---|---|---|
| Origin | Release audit Phase 2 processed-AI retrain + train-only augmentation | `release/models/origin/origin_file_model__ssl__experimental.joblib` | threshold `0.92` |
| Replay | Phase 8E-1 / 8E-1A acoustic model | `release/models/replay/replay_file_model__acoustic__experimental.joblib` | threshold `0.65` |
| Mixer/channel | Phase 8E-1 / 8E-1A acoustic model | `release/models/mixer/mixer_file_model__acoustic__experimental.joblib` | threshold `0.75` |
| Partial segment | Release audit Phase 5 no-F9 retrain | `release/models/partial_segment/partial_segment_model__combined__experimental.joblib` | threshold `0.95` |
| UI calibration | Release audit Phase 6 | `release/config/evidence_calibration.json` | Low / Medium / High evidence bands |

Release docs updated:

- `release/MODEL_REGISTRY.md`
- `release/models/model_inventory.json`
- `release/config/evidence_calibration.json`
- `reports/release_audit/phase6_calibration_2026-06-13/phase6_runbook.md`

## Leakage-Safe Test Evidence

| Axis | Leakage-safe evidence | Result |
|---|---|---|
| Origin | Phase 2 promoted model on leakage-safe test | balanced accuracy **0.9500**, recall **0.9000**, specificity **1.0000** |
| Replay | Phase 3C baseline acoustic replay axis | Phase 7 test balanced accuracy **0.9667** |
| Mixer | Phase 3C baseline acoustic mixer axis | Phase 7 test balanced accuracy **1.0000** |
| Partial | Phase 5 no-F9 oracle on leakage-safe test partial files | top-5 hit **10/10**, localized **10/10**, clean broad activation **0%** |

The leakage-safe split remains the strongest internal evidence. Claims must still be limited because `testing_audios` is deliberately more external and heterogeneous.

## Final Matrix: `testing_audios` (25 files, all axes)

Output files:

- `phase7_final_testing_audios_predictions.csv`
- `phase7_final_testing_audios_metrics.csv`
- `phase7_final_testing_audios_failures.csv`
- `phase7_final_testing_audios_matrix.md`

| Axis | n | TP | TN | FP | FN | Balanced accuracy | Recall | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Origin | 18 | 9 | 6 | 2 | 1 | **0.8250** | 0.9000 | 0.7500 |
| Replay | 25 | 5 | 15 | 3 | 2 | **0.7738** | 0.7143 | 0.8333 |
| Mixer | 25 | 0 | 22 | 1 | 2 | **0.4783** | 0.0000 | 0.9565 |
| Partial | 25 | 2 | 23 | 0 | 0 | **1.0000** | 1.0000 | 1.0000 |

Origin uses only rows with human/AI ground-truth origin. Mixed partial-origin rows are excluded from binary origin metrics.

## Per-Axis Failure Table

| Axis | File IDs | Failure mode |
|---|---|---|
| Origin | T1.2, T4.1 | clean human false positives |
| Origin | T4.5 | WhatsApp-compressed AI false negative |
| Replay | T3.2, T3.3 | AI replay false negatives |
| Replay | T2.2, T3.4, T4.1 | replay false positives on mixer/clean cases |
| Mixer | T2.2, T3.4 | mixer false negatives |
| Mixer | T2.4 | mixer false positive on human Bluetooth replay |
| Partial | none in final gated matrix | T4.3 and T5_FAB_001 detected; non-partials gated off |

The final matrix confirms the roadmap decision: the partial axis improved after Phase 5, while unified manipulation/mixer generalization remains limited after Phase 4 failed.

## Old Release vs New Release

| Area | Old release behavior | Final release-audit behavior |
|---|---|---|
| Origin on processed AI | Old origin missed replayed AI systematically (`ai_replayed` detection 0/23 at old threshold) | Phase 2 origin detects `ai_replayed` at **91.3%** on Phase 7 all-condition matrix; `testing_audios` origin recall **90%** |
| Partial T4.3 | Broad activation (`global_activation_not_localized`), hidden/contradictory segment evidence | Phase 5 no-F9 localizer highlights **46–50 s** inside the 35–58 s label region |
| Partial T5_FAB_001 | Localized candidate existed but saturated raw-score wording remained | Phase 5 keeps a valid candidate (**18–22 s**, overlaps 14–21 s) with evidence-band wording |
| UI scores | Raw 3-decimal scores in main cards; saturation looked hardcoded | Phase 6 cards show **Low / Medium / High evidence**; raw scores moved to technical details |
| Report consistency | Gradio/PDF/JSON could disagree on segment display | Phase 6 consistency check **PASS** for card bands and segment table formatting |
| Evaluation honesty | Earlier release did not clearly separate internal leakage-safe and external test results | Final report separates leakage-safe test, `testing_audios`, and per-condition failures |

## What Improved

- Origin no longer treats processed AI as out-of-scope clean audio in the internal Phase 7 corpus.
- Partial broad activation from F9 features was fixed for the key external partial cases.
- Partial evidence is no longer silently hidden when localized evidence coexists with replay/mixer context.
- User-facing output now says evidence strength bands instead of pretending raw model probabilities are calibrated confidence.
- Final reports include failure file IDs and explicit miss/false-positive modes.

## What Remains Limited

- Phase 4 unified manipulation v3 failed its stop rule: `testing_audios` manipulated Stage-1 recall was **20%**. It is **not shipped**.
- Mixer/channel evidence is weak on external `testing_audios`: final matrix recall **0%** for the two mixer labels.
- Replay remains imperfect externally: final matrix recall **71.4%**, with misses on T3.2 and T3.3.
- Origin still has external clean-human false positives (T1.2, T4.1) and a WhatsApp-compressed AI miss (T4.5).
- Partial is improved, but it is still a manual-review segment indicator, not proof of fabrication.

## Final Disclaimers to Use in Thesis / Demo

1. This release is an **experimental forensic evidence demo**, not a court-ready authenticity system.
2. Each axis is independent evidence. Replay or mixer/channel evidence does **not** mean AI-generated.
3. Origin evidence is less reliable under replay, platform compression, and unfamiliar real-world recording chains.
4. Partial evidence identifies candidate regions for review; it does not prove fabrication by itself.
5. User-facing Low / Medium / High bands are evidence bands fitted on leakage-safe dev, not calibrated legal probabilities.
6. The final matrix documents known failures: origin T1.2/T4.1/T4.5, replay T2.2/T3.2/T3.3/T3.4/T4.1, mixer T2.2/T2.4/T3.4.

## Final Decision

Package the final release as:

**Origin Phase 2 + replay/mixer existing axes + Phase 5 partial + Phase 6 evidence-band UI.**

Do **not** ship Phase 4 unified manipulation v3. Document replay/mixer external limitations honestly and keep manual review required for all elevated or mixed indicators.
