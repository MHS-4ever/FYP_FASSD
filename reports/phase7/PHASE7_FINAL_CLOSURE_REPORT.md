# Phase 7 Final Closure Report

**Project:** FASSD — Forensic Voice Authenticity Analyzer  
**Phase 7 title (closed):** Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings  
**Status:** Closed — transition to Phase 8

---

## 1. Executive Summary

Phase 7 executed a controlled forensic evaluation program on local Phase 7C1 audio and Phase 7A holdout tests. It established HybridResNet as a **useful evidence source** for replay, mixer/channel processing, and partial fabrication sensitivity, while repeatedly showing **unacceptable clean-human false alarms** when used as a single binary scorer.

Fine-tuning experiments (7C3-v1, 7C3-R2) and anti-spoof model experiments (AASIST pretrained and fine-tuned) did **not** produce an acceptable standalone forensic product model. The **only accepted prototype** from Phase 7 is **Phase 7C4-v2** — a **decision-layer fusion** over multiple evidence streams, not a replacement backbone.

**Phase 7 is not a failed phase.** It is the experimental phase that proved the current single-model / binary-spoof approach is **insufficient** for the forensic product goal.

---

## 2. Why Phase 7 Is Being Closed

Phase 7 scope grew across 7A–7E (controlled tests, dataset prep, Hybrid fine-tunes, decision layers, AASIST branch). The program reached a stable architectural conclusion:

> A single binary real/fake, spoof/bonafide, or origin-first classifier cannot represent the forensic product goal.

Further Phase 7 model iterations would repeat the same failure mode without a new multi-axis design. Phase 7 is therefore **formally closed** and Phase 8 is opened for **multi-axis forensic audio intelligence**.

---

## 3. What Phase 7 Tested

| Track | What was tested |
|-------|-----------------|
| **7A** | Controlled forensic test suite (T1–T5) |
| **7B** | Forensic label preparation (holdout-aware) |
| **7C0** | Legacy training dataset audit |
| **7C1** | Local forensic dataset collection + Hybrid baseline |
| **7C2** | Signed-off train/val/test manifests |
| **7C3** | HybridResNet fine-tuning (v1 and R2 risk-tuned) |
| **7C4** | Threshold / decision-layer fusion (v1 rejected, v2 prototype) |
| **7D** | Report layer planning (implementation postponed) |
| **7E** | AASIST-L pretrained + fine-tune experiment |

---

## 4. Final Phase 7 Decisions

| Decision | Outcome |
|----------|---------|
| HybridResNet baseline | Retained as **evidence** (not sole judge) |
| 7C3-v1 | **Rejected** |
| 7C3-R2 standalone | **Rejected** |
| 7C4-v1 | **Rejected** |
| 7C4-v2 | **Accepted** as decision-layer **prototype only** |
| 7D implementation | **Postponed** |
| AASIST (pretrained + fine-tuned) | **Rejected** as current standalone/branch solution |
| Phase 7 reopen | **Frozen** unless new controlled plan approved |

---

## 5. Key Technical Findings

1. **HybridResNet** detects replay, mixer, and partial-region signals strongly on Phase 7C1 but **over-flags clean human** at file level.
2. **Segment-level evidence** (suspicious windows) rescues many direct-AI cases that file-level averaging misses.
3. **Binary origin-style training** (7C3-v1) collapsed manipulation sensitivity.
4. **Risk-tuned R2** improved balance metrics but did not qualify as a standalone checkpoint.
5. **7C4-v2 fusion** improved clean-human behavior vs raw Hybrid while preserving most manipulation detection on controlled 7C1 criteria.
6. **AASIST-L** (pretrained and fine-tuned) remained **anti-spoof biased** — high clean-human false alarms in this local setup.
7. **Label semantics matter:** `risk_target=1` is forensic-risk positive, **not** synonymous with AI-generated.

---

## 6. Why Binary Model Strategy Is Insufficient

Forensic cases require **parallel evidence**:

- **Origin:** human, AI, mixed, unknown (not a single gate)
- **Manipulation:** replay, mixer, partial fabrication, editing, compression artifacts
- **Segment:** where suspicion concentrates (timestamps, inside/outside region deltas)

A single spoof score cannot encode:

- Human-origin replay (manipulation-positive, not AI-generated)
- AI-origin mixer processing (AI-origin but not necessarily “deepfake speech”)
- Partial fabrication (mixed-origin over time)

Phase 7 repeatedly rediscovered this limitation across Hybrid fine-tunes and AASIST.

---

## 7. Accepted Artifacts

- `reports/phase7/phase7_forensic_tests/` — Phase 7A
- `reports/phase7/phase7_dataset/` — Phase 7B
- `reports/phase7/phase7c1_baseline/` — Phase 7C1 baseline
- `reports/phase7/phase7c2_training_prep/` — Phase 7C2 manifests
- `reports/phase7/phase7c4_calibration_v2/` — **7C4-v2 prototype** (decision layer)
- Phase 7E planning + eval archives (experimental evidence only)

---

## 8. Rejected Artifacts

- `reports/phase7/phase7c3_finetune/` — 7C3-v1
- 7C3-R2 checkpoints as **standalone** product scorers
- `reports/phase7/phase7c4_calibration/` — 7C4-v1
- AASIST pretrained / fine-tuned as **current** product path (`phase7e3a_pretrained_eval/`, `phase7e3c_finetune/`)

---

## 9. Lessons Learned

- Evaluate **per manipulation role**, not one aggregate accuracy.
- Always report **clean-human false alarms** alongside spoof detection.
- Use **segment timelines** for partial fabrication and borderline direct-AI cases.
- Separate **origin evidence** from **manipulation evidence** in design and reporting.
- Decision layers can help but cannot fix a fundamentally wrong single-axis model.

---

## 10. Transition to Phase 8

Phase 8: **Multi-Axis Forensic Audio Intelligence Architecture**

- Start with an **evidence table**, not a new monolithic classifier.
- Infer origin and manipulation **in parallel**, then fuse with abstention / manual review.

See [PHASE7_TO_PHASE8_TRANSITION.md](PHASE7_TO_PHASE8_TRANSITION.md) and [../phase8/PHASE8_START_HERE.md](../phase8/PHASE8_START_HERE.md).
