# Phase 8 Failure Mode and Loophole Analysis

> **Historical draft** — failure modes remain valid; **label names updated** to Phase 8A frozen vocabulary below.  
> **Mitigations in implementation:** use [fusion/phase8a_fusion_and_abstention_rules.md](fusion/phase8a_fusion_and_abstention_rules.md) and [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md).

**Phase 8B:** NOT STARTED

---

## Label vocabulary used in mitigations (frozen)

| Old reference in sections below | Frozen term |
|---------------------------------|-------------|
| `origin_human` evidence | `evidence_origin_human_score` / `human` |
| `origin_ai` | `evidence_origin_ai_score` / `ai_synthetic` |
| `manipulation_replay` | `replay_rerecorded` |
| `manipulation_mixer_channel` | `mixer_channel_processed` |
| `manipulation_direct_synthetic` | **Not manipulation** — `ai_synthetic` origin only |
| Single origin/spoof score | **Forbidden** — four origin scores |

---

## 1. Binary label collapse

| | |
|---|---|
| **Failure** | Single label or single `evidence_origin_score` mixes origin + manipulation. |
| **Example** | Human replay flagged → report implies AI generation. |
| **Mitigation** | Four-tuple origin scores + separate manipulation scores; fusion forbids origin inference from manipulation alone. |

---

## 2. Hard-routing cascade error

| | |
|---|---|
| **Failure** | AI/human gate sends clip to wrong downstream model. |
| **Mitigation** | Parallel axis inference; no mandatory first-stage origin gate. |

---

## 3. Clean-human false alarms

| | |
|---|---|
| **Failure** | Clean local speech scored as spoof/risk (Hybrid 17/23, AASIST 22/23). |
| **Mitigation** | `clean` manipulation + `evidence_origin_human_score` Moderate+; fusion clean-human protection; abstain with `manual_review_reason`. |

---

## 4. Partial fabrication hidden by file-level averaging

| | |
|---|---|
| **Failure** | Short synthetic region diluted by long bonafide context. |
| **Mitigation** | `segment_origin_*` + `partial_fabrication_score`; `region_delta`; segment_reason `origin_ai_local`. |

---

## 5. Replay confused with synthetic generation

| | |
|---|---|
| **Failure** | Replay described as “deepfake” without origin evidence. |
| **Example** | Human mic replay → “AI-generated audio.” |
| **Mitigation** | `replay_rerecorded` separate from `ai_synthetic`; never use `manipulation_direct_synthetic`. |

---

## 6. Mixer/channel processing confused with AI generation

| | |
|---|---|
| **Failure** | Broadcast/mixer artifacts trigger anti-spoof scores. |
| **Mitigation** | `mixer_channel_processed` + `evidence_mixer_channel_score`; do not set `evidence_origin_ai_score` from mixer alone. |

---

## 7. Dataset leakage through paired variants

| | |
|---|---|
| **Mitigation** | `split_group_id` discipline (7C2); evidence table `split` column. |

---

## 8. Threshold overfitting

| | |
|---|---|
| **Mitigation** | Locked 7C1 for development; 7A sanity only. |

---

## 9. Report overclaiming

| | |
|---|---|
| **Mitigation** | `manual_review_required`, `forensic_summary`, decision-support language; `fusion_trace` for audit. |

---

## 10. Domain mismatch

| | |
|---|---|
| **Mitigation** | `manual_review_reason` = `unknown_domain`; abstention. |

---

## 11. Single origin score loophole (8A-C1 addition)

| | |
|---|---|
| **Failure** | Implementer adds `evidence_origin_score` ≈ “fake probability.” |
| **Mitigation** | Schema validation rejects single origin column; require four-tuple per [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md). |

---

## Cross-reference

- Phase 7: [../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md](../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md)  
- Acceptance: [validation/phase8a_success_and_rejection_criteria.md](validation/phase8a_success_and_rejection_criteria.md)
