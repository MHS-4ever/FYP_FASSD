# Phase 8 — Multi-Axis Forensic Audio Intelligence (Reports)

**Status:** Phase 8A-C1 hardened — **no implementation** · Phase 8B **NOT STARTED**  
**Schema version:** `phase8a_v1_1`  
**Code hub:** [code/phase8/README.md](../../code/phase8/README.md)

---

## Authoritative Phase 8A documents (use these for implementation)

| Area | Document |
|------|----------|
| Architecture | [architecture/phase8a_architecture_freeze.md](architecture/phase8a_architecture_freeze.md) |
| Labels | [label_schema/phase8a_multi_axis_label_schema.md](label_schema/phase8a_multi_axis_label_schema.md) |
| Evidence table | [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md) |
| Fusion | [fusion/phase8a_fusion_and_abstention_rules.md](fusion/phase8a_fusion_and_abstention_rules.md) |
| Validation | [validation/phase8a_success_and_rejection_criteria.md](validation/phase8a_success_and_rejection_criteria.md) |
| 8B readiness | [roadmap/phase8a_to_phase8b_readiness_review.md](roadmap/phase8a_to_phase8b_readiness_review.md) |
| Research alignment | [research/phase8a_research_alignment_matrix.md](research/phase8a_research_alignment_matrix.md) |
| Scope draft | [architecture/fassd_scope_update_draft.md](architecture/fassd_scope_update_draft.md) |

**Entry point:** [PHASE8_START_HERE.md](PHASE8_START_HERE.md)

---

## Historical drafts (root — superseded)

These root-level files are **historical drafts**. Do not use outdated field names (`origin_ai`, `manipulation_replay`, `evidence_origin_score`, etc.) for Phase 8B.

| File | Status |
|------|--------|
| [PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md](PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md) | Superseded by `architecture/phase8a_architecture_freeze.md` |
| [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) | Superseded by `label_schema/phase8a_multi_axis_label_schema.md` |
| [PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md](PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md) | Superseded for labels — mitigations unchanged in spirit |
| [PHASE8_IMPLEMENTATION_ROADMAP.md](PHASE8_IMPLEMENTATION_ROADMAP.md) | Superseded for schema detail — use 8A readiness review |
| [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md) | Still useful summary — see also `validation/phase8a_success_and_rejection_criteria.md` |

---

## Deprecated label mapping (do not use in 8B)

| Old (deprecated) | Frozen Phase 8A |
|------------------|-----------------|
| `origin_ai` | `ai_synthetic` / `evidence_origin_ai_score` |
| `origin_human` | `human` / `evidence_origin_human_score` |
| `origin_mixed` | `mixed` / `evidence_origin_mixed_score` |
| `origin_unknown` | `unknown` / `evidence_origin_unknown_score` |
| `manipulation_replay` | `replay_rerecorded` |
| `manipulation_mixer_channel` | `mixer_channel_processed` |
| `manipulation_direct_synthetic` | **Not a manipulation label** — use `ai_synthetic` origin evidence |
| `manipulation_partial_fabrication` | `partial_fabrication` |
| `manipulation_edited_spliced` | `edited_spliced` |
| `manipulation_compressed_low_quality` | `compressed_low_quality` |
| `evidence_origin_score` | **Forbidden** — use four-tuple origin scores |

---

## Why Phase 8 exists

Phase 7 closed as **Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings**. It showed that HybridResNet remains useful **manipulation evidence**, and that parallel **origin** and **manipulation** axes are required — not one fake/real score.

---

## Subfolders

| Folder | Purpose |
|--------|---------|
| `research/` | Phase 8A research alignment |
| `architecture/` | Architecture freeze + scope draft |
| `label_schema/` | **Authoritative** label definitions |
| `evidence_table/` | **Authoritative** evidence CSV schema |
| `fusion/` | Fusion / abstention rules |
| `validation/` | Success and rejection criteria |
| `roadmap/` | 8A → 8B readiness |

---

## Phase 7 closure (read-only reference)

- [../phase7/PHASE7_FINAL_CLOSURE_REPORT.md](../phase7/PHASE7_FINAL_CLOSURE_REPORT.md)
- [../phase7/PHASE7_TO_PHASE8_TRANSITION.md](../phase7/PHASE7_TO_PHASE8_TRANSITION.md)

---

## Current status

- Phase **7** is **closed**.
- Phase **8A-C1** complete — **human sign-off pending** before 8B.
- Phase **8B** — **NOT STARTED**.
- **Checkpoint registry:** verify `models_saved/registry/CHECKPOINT_REGISTRY.md` exists before 8B.

**Do not:** train models, run inference, or implement evidence table builder until 8A is signed off.
