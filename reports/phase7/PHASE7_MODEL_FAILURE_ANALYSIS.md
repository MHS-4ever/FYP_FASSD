# Phase 7 Model Failure Analysis

**Purpose:** Explain *why* Phase 7 model strategies failed — not to dismiss the work, but to inform Phase 8 design.

---

## 1. Failure Pattern Across Models

Repeated pattern on Phase 7C1:

| Symptom | Hybrid baseline | Fine-tunes | AASIST |
|---------|-----------------|------------|--------|
| Replay/mixer/partial sensitivity | High | Variable | High |
| Clean-human false alarms | High | Improved sometimes | Very high (pretrained) |
| Direct-AI file-level detection | Low | Mixed | Moderate |
| Direct-AI segment rescue | Strong | Mixed | Moderate |

**Root cause class:** treating forensic audio as **one binary score** (fake/real, spoof/bonafide, or coarse risk) instead of **parallel evidence axes**.

---

## 2. HybridResNet Failure Mode

**What worked:** chunk-level scores flag replay, mixer, and partial regions reliably.

**What failed:** file-level aggregation and thresholding treat many clean-human clips as risk-positive.

**Why:**

- Environmental / channel features correlate with “suspicious” in training distribution.
- No separate **origin** vs **manipulation** head — one score must explain all roles.
- Clean human is not the same distribution as “bonafide” in anti-spoof training corpora.

---

## 3. Fine-Tuning Failure Mode

### 7C3-v1 (origin-style binary)

Training collapsed toward origin discrimination; **manipulation-positive human-origin cases** (replay, mixer) were harmed.

### 7C3-R2 (risk-tuned)

Improved some trade-offs but **did not** qualify as standalone checkpoint — still entangled origin and manipulation in one target.

**Lesson:** fine-tuning the same binary head cannot fix label semantics; it only shifts the operating point.

---

## 4. AASIST Failure Mode

AASIST is an **anti-spoofing** model (ASVspoof-style bonafide vs spoof), not a full forensic multi-axis system.

**Pretrained:** extreme clean-human false alarms (22/23) in local Phase 7C1 setup.

**Fine-tuned (best_product / best_loss):** did not achieve acceptable clean-human behavior on Phase 7C1 re-eval; rejected as current solution.

**Why:** domain mismatch + single-axis output cannot express “human replay is not AI-generated but is manipulation-positive.”

---

## 5. Why Binary Labels Collapse Forensic Meaning

| Case | Origin | Manipulation | Binary risk=1 means… |
|------|--------|--------------|----------------------|
| Human replay | Human | Replay | “Fake” ❌ misleading |
| AI replay | AI | Replay | Risk-positive ✓ but conflates origin |
| Human mixer | Human | Channel/mixer | Often flagged as “AI-like” |
| AI mixer | AI | Channel | Conflates processing with generation |
| Partial fabrication | Mixed over time | Partial insert | Needs segment axis |

**Therefore:** `risk_positive` **cannot** mean AI-generated.

Phase 8 must encode **origin_human / origin_ai / origin_mixed / origin_unknown** separately from manipulation types.

---

## 6. Why Hard AI/Human First-Stage Routing Is Risky

A pipeline like:

```text
if AI_origin: use anti-spoof model
else: use bonafide path
```

causes **cascade errors**:

- Human replay misrouted as “bonafide path” → missed manipulation.
- AI mixer misrouted as “deepfake path” → wrong explanation in report.
- Partial clips with mixed segments cannot be decided at file level.

**Phase 8 principle:** origin and manipulation are inferred **in parallel**, then fused with confidence and manual-review flags.

---

## 7. What Phase 8 Must Avoid

1. Another monolithic fake/real classifier as the “final model.”
2. Hard AI/human router before manipulation analysis.
3. Threshold tuning on holdout to claim product readiness.
4. Report language that equates risk-positive with “AI-generated.”
5. File-level averaging that hides partial-fabrication regions.
6. Discarding Hybrid/AASIST scores entirely — use as **evidence features**, not sole judges.

See [../phase8/PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md](../phase8/PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md).
