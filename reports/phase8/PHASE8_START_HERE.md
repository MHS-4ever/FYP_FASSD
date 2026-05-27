# Phase 8 — Start Here

**Title:** Multi-Axis Forensic Audio Intelligence Architecture  
**Status:** Phase 8A-C1 hardened — **no code, no training** · Phase 8B **NOT STARTED**  
**Schema version:** `phase8a_v1_1`

---

## Read order (authoritative — Phase 8A freeze)

1. [architecture/phase8a_architecture_freeze.md](architecture/phase8a_architecture_freeze.md)  
2. [label_schema/phase8a_multi_axis_label_schema.md](label_schema/phase8a_multi_axis_label_schema.md)  
3. [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md)  
4. [fusion/phase8a_fusion_and_abstention_rules.md](fusion/phase8a_fusion_and_abstention_rules.md)  
5. [validation/phase8a_success_and_rejection_criteria.md](validation/phase8a_success_and_rejection_criteria.md)  
6. [roadmap/phase8a_to_phase8b_readiness_review.md](roadmap/phase8a_to_phase8b_readiness_review.md)  

Phase 7 handoff: [../phase7/PHASE7_TO_PHASE8_TRANSITION.md](../phase7/PHASE7_TO_PHASE8_TRANSITION.md)

**Historical drafts** (superseded — do not implement from these):  
[PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md](PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md), [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md)

---

## Why Phase 8 starts now

Phase 7 proved:

- HybridResNet is valuable **manipulation evidence** (replay, mixer, partial) — not final origin truth.
- Single binary spoof/fake models **fail** the forensic product goal.
- AASIST is **not sufficient** as the current standalone solution.
- **7C4-v2** is a **decision-layer prototype only**.

---

## Phase 8 goal

Build a **multi-axis forensic audio intelligence system** that produces:

- Parallel **origin** evidence: four scores → `human` / `ai_synthetic` / `mixed` / `unknown`
- Parallel **manipulation** evidence (multi-label)
- **Segment** evidence with explicit `segment_origin_*` scores
- **Fusion** → `final_forensic_status`, `forensic_risk_level`, `manual_review_required`, `fusion_trace`

**Forbidden:** one `evidence_origin_score` column or fake/real collapse.

---

## What Phase 8 is NOT

- ❌ One fake/real classifier as final truth  
- ❌ Hard AI/human routing gate  
- ❌ `manipulation_direct_synthetic` as a manipulation label  
- ❌ Treating `clean` manipulation as “human-safe”  

---

## Current next action

**Human review** of Phase 8A documents (8A-C1 cleanup complete).

Do **not** start Phase 8B evidence table builder until sign-off on [roadmap/phase8a_to_phase8b_readiness_review.md](roadmap/phase8a_to_phase8b_readiness_review.md).
