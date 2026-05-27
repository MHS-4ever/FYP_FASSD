# Phase 8 Failure Mode and Loophole Analysis

**Purpose:** Document known failure modes from Phase 7 and mitigations in Phase 8.

---

## 1. Binary label collapse

| | |
|---|---|
| **Failure** | Single label mixes origin + manipulation (e.g. human replay labeled as “fake”). |
| **Example** | Human replay flagged → report implies AI generation. |
| **Mitigation** | Separate origin and manipulation axes; fusion rules forbid origin inference from manipulation alone. |

---

## 2. Hard-routing cascade error

| | |
|---|---|
| **Failure** | AI/human gate sends clip to wrong downstream model. |
| **Example** | Human mixer routed to “bonafide” path → missed processing evidence. |
| **Mitigation** | Parallel axis inference; no mandatory first-stage origin gate. |

---

## 3. Clean-human false alarms

| | |
|---|---|
| **Failure** | Clean local speech scored as spoof/risk (Hybrid 17/23, AASIST 22/23). |
| **Example** | Real witness recording marked suspicious. |
| **Mitigation** | Explicit `manipulation_clean` + origin_human evidence; high penalty in fusion; abstain to manual review. |

---

## 4. Partial fabrication hidden by file-level averaging

| | |
|---|---|
| **Failure** | Short synthetic region diluted by long bonafide context. |
| **Example** | Partial insert missed at file mean; visible only in one window. |
| **Mitigation** | Segment axis + `region_delta`; require suspicious window in partial role. |

---

## 5. Replay confused with synthetic generation

| | |
|---|---|
| **Failure** | Replay attack described as “deepfake” without evidence. |
| **Example** | Human mic replay → “AI-generated audio.” |
| **Mitigation** | `manipulation_replay` separate from `manipulation_direct_synthetic`; report templates. |

---

## 6. Mixer/channel processing confused with AI generation

| | |
|---|---|
| **Failure** | Broadcast/mixer artifacts trigger anti-spoof scores. |
| **Example** | Human mixer variant → high spoof score. |
| **Mitigation** | Channel feature bucket + `manipulation_mixer_channel`; do not map to `origin_ai` automatically. |

---

## 7. Dataset leakage through paired variants

| | |
|---|---|
| **Failure** | Same speaker/clip variants across train and eval. |
| **Example** | Inflated replay detection via memorization. |
| **Mitigation** | `split_group_id` discipline (7C2); Phase 8 validation asserts no group leakage. |

---

## 8. Threshold overfitting

| | |
|---|---|
| **Failure** | Thresholds tuned on holdout then reported as general performance. |
| **Example** | 7A holdout used to claim “production ready.” |
| **Mitigation** | Locked 7C1 for development; 7A for final sanity only; document all threshold sources. |

---

## 9. Report overclaiming

| | |
|---|---|
| **Failure** | UI/report states certainty beyond evidence. |
| **Example** | “Proven fake” from score > 0.5. |
| **Mitigation** | Phase 8G forensic-safe templates; `manual_review_required`; decision-support language. |

---

## 10. Domain mismatch across language/device/channel

| | |
|---|---|
| **Failure** | Model trained on one domain fails on Urdu/local device recordings. |
| **Example** | AASIST pretrained on ASVspoof → 22/23 clean-human FA locally. |
| **Mitigation** | Local evidence table; domain tags; abstention; no single global threshold claim. |

---

## Cross-reference

- Phase 7: [../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md](../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md)  
- Acceptance: [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md)
