# Phase 7 AASIST Negative Finding

**Experiment track:** Phase 7E (AASIST-L evidence branch)  
**Status:** Closed — negative but **useful** finding for architecture direction

---

## 1. Why AASIST Was Tested

Phase 7C showed HybridResNet is strong on manipulation-like cases but weak on clean-human specificity. AASIST-L is a published **anti-spoofing** backbone with strong performance on spoof detection benchmarks. The hypothesis was:

> A dedicated anti-spoof model might improve direct-AI / spoof sensitivity without relying only on Hybrid environmental features.

Phase 7E followed a locked benchmark protocol (7C1 + 7A holdout) before any product claims.

---

## 2. Pretrained AASIST-L Result (Phase 7C1)

| Metric | Result |
|--------|--------|
| clean_human_false_alarm | **22/23** |
| clean_human_accepted | 1/23 |
| direct_ai_detected_or_segment_suspicious | 18/23 |
| replay/mixer | Largely detected |
| partial_fabrication_detected | 45/46 |

**Finding:** High spoof sensitivity did **not** translate into acceptable forensic product behavior — clean-human clips were overwhelmingly flagged.

---

## 3. Fine-Tuned AASIST-L Result

Fine-tuning was executed with controlled manifests (7E3B) and training scripts (7E3C), using balanced sampling + sample weights (class-balanced loss optional, not default).

| Checkpoint | Phase 7C1 re-eval |
|------------|-------------------|
| **best_product** | **Rejected** — clean-human false alarms remained unacceptable |
| **best_loss** | **Rejected** — insufficient improvement for product goal |

Artifacts preserved under `phase7e3c_finetune/` — do not overwrite.

---

## 4. Why AASIST Did Not Solve the Product Goal

AASIST optimizes **bonafide vs spoof** in anti-spoof benchmarks. The forensic product requires:

- Low false alarms on **clean human** local recordings
- Explicit handling of **human-origin manipulation** (replay, mixer)
- **Segment-level** partial fabrication reasoning
- Language that separates **AI generation evidence** from **channel/manipulation evidence**

A single AASIST spoof score cannot represent these axes. Fine-tuning reduced some errors but not to Phase 8 acceptance targets.

**Careful wording:** AASIST is not “bad.” It is an anti-spoofing model that was **not sufficient** for the broader forensic multi-axis goal in this local controlled setup.

---

## 5. What We Learned

1. Anti-spoof pretraining **transfers suspicion** to out-of-domain clean speech.
2. Balanced fine-tune sampling alone does not fix axis collapse.
3. AASIST scores may still be useful as **one feature column** in a future evidence table — not as the final classifier.
4. Phase 8 must not repeat “replace Hybrid with another binary spoof model.”

---

## 6. Final Decision

| Item | Decision |
|------|----------|
| Pretrained AASIST-L | **Rejected** as standalone |
| Pretrained AASIST-L | **Rejected** as branch-only **current** solution |
| Fine-tuned best_product | **Rejected** |
| Fine-tuned best_loss | **Rejected** |
| Phase 7 product path | AASIST **not** used in final Phase 7 product path |
| Archives | May be kept as **experimental evidence only** |

Do not delete `phase7e3a_pretrained_eval/` or `phase7e3c_finetune/` — they document this negative finding.

---

## References

- [phase7e_aasist_experiment/README.md](phase7e_aasist_experiment/README.md)
- [PHASE7_EXPERIMENT_RESULTS_SUMMARY.md](PHASE7_EXPERIMENT_RESULTS_SUMMARY.md)
- [PHASE7_TO_PHASE8_TRANSITION.md](PHASE7_TO_PHASE8_TRANSITION.md)
