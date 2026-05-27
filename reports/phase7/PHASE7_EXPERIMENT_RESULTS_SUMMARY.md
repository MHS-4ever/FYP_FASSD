# Phase 7 Experiment Results Summary

**Status:** Phase 7 closed (read-only reference)  
**Detailed closure:** [PHASE7_FINAL_CLOSURE_REPORT.md](PHASE7_FINAL_CLOSURE_REPORT.md)

---

## Master results table

| Phase | Artifact | Result | Final Decision |
|-------|----------|--------|----------------|
| 7A | Controlled forensic testing | Completed | Signed off |
| 7B | Forensic label preparation | Completed | Signed off |
| 7C0 | Current dataset audit | Completed | Signed off |
| 7C1 | Local forensic dataset + baseline | Completed | Signed off |
| 7C2 | Training manifest preparation | Completed | Signed off |
| 7C3-v1 | HybridResNet fine-tune v1 | Collapsed manipulation detection | **Rejected** |
| 7C3-R2 best_product | Risk-tuned checkpoint | Not standalone | **Rejected** as standalone |
| 7C3-R2 best_loss | Risk-tuned checkpoint | Not standalone | **Rejected** as standalone |
| 7C4-v1 | Decision layer v1 | Too many clean-human false alarms | **Rejected** |
| 7C4-v2 | Decision layer v2 | Passed controlled prototype gates | **Accepted** as prototype only |
| 7D | Report layer planning | Planned only | Implementation **postponed** |
| 7E | AASIST experiment | Did not solve clean-human / product goal | **Rejected** as current solution |

---

## Phase 7C1 — HybridResNet baseline (controlled)

Source: `reports/phase7/phase7c1_baseline/results/`

| Metric | Count |
|--------|------:|
| clean_human_accepted | 4/23 |
| clean_human_false_alarm | 17/23 |
| direct_ai_detected (file-level) | 0/23 |
| direct_ai_file_missed_but_segment_suspicious | 19/23 |
| human_replay_detected | 23/23 |
| ai_replay_detected_or_segment_suspicious | 23/23 |
| human_mixer_detected | 23/23 |
| ai_mixer_detected | 23/23 |
| partial_fabrication_detected | 43/46 |

**Interpretation:** Strong manipulation/replay/mixer/partial sensitivity; poor clean-human specificity at file level; direct-AI often recovered via segment evidence.

---

## Phase 7C4-v2 — Decision layer prototype (controlled)

Source: `reports/phase7/phase7c4_calibration_v2/`

| Metric | Count |
|--------|------:|
| clean_human_false_alarm | 7/23 |
| clean_human_accepted | 1/23 |
| clean_human_borderline | 15/23 |
| clean_human accepted + borderline | 16/23 |
| direct_ai_detected_or_segment_suspicious | 19/23 |
| human_replay_detected | 23/23 |
| ai_replay_detected_or_segment_suspicious | 23/23 |
| human_mixer_detected | 23/23 |
| ai_mixer_detected | 23/23 |
| partial_fabrication_detected | 44/46 |

**Decision:** Accepted as **decision-layer prototype only** — not a final forensic model.

---

## Phase 7E — AASIST-L pretrained (Phase 7C1)

Source: `reports/phase7/phase7e_aasist_experiment/phase7e3a_pretrained_eval/phase7c1/`

| Metric | Count |
|--------|------:|
| clean_human_false_alarm | 22/23 |
| clean_human_accepted | 1/23 |
| direct_ai_detected_or_segment_suspicious | 18/23 |
| replay/mixer | Largely detected (similar to Hybrid sensitivity) |
| partial_fabrication_detected | 45/46 |

**Decision:** **Rejected** as standalone and as branch-only **current** solution (domain mismatch on clean human).

---

## Phase 7E — AASIST-L fine-tuned (Phase 7C1)

Source: `reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/` (post-training eval)

| Checkpoint | Phase 7C1 outcome |
|------------|-------------------|
| best_product | **Rejected** — clean-human false alarms remained unacceptable |
| best_loss | **Rejected** — did not meet product goal |

**Decision:** Fine-tuned AASIST-L is **rejected as current solution**. Outputs may be archived as experimental evidence only.

---

## What Phase 7 did not achieve

- A single model that simultaneously meets clean-human specificity and full manipulation-axis coverage.
- An anti-spoof-only branch that replaces Hybrid without harming clean-human behavior.
- Production-ready report automation (7D postponed).

---

## Next

[PHASE7_TO_PHASE8_TRANSITION.md](PHASE7_TO_PHASE8_TRANSITION.md) · [../phase8/PHASE8_START_HERE.md](../phase8/PHASE8_START_HERE.md)
