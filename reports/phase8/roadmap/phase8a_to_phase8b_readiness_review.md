# Phase 8A → Phase 8B Readiness Review

**Status:** Phase 8A-C1 hardened — **awaiting human review**  
**Schema version:** `phase8a_v1_1`  
**Date:** 2026-05-28 (updated 8A-C1)  

---

## 1. Purpose

Checklist to determine whether Phase 8B (evidence table builder) may start. Phase 8B must **not** begin until every mandatory item is checked and a human has reviewed Phase 8A documents.

---

## 2. Prerequisites verified (environment)

| Check | Status | Evidence |
|-------|--------|----------|
| Phase 7 closed | ✅ | [../../phase7/PHASE7_FINAL_CLOSURE_REPORT.md](../../phase7/PHASE7_FINAL_CLOSURE_REPORT.md) |
| Phase 8 folder structure exists | ✅ | `reports/phase8/{research,architecture,label_schema,evidence_table,fusion,validation,roadmap}/` |
| Checkpoint registry expected | ⚠️ verify before 8B | `models_saved/registry/CHECKPOINT_REGISTRY.md` — confirm file exists on disk before builder runs |
| No training/inference in 8A task | ✅ | Documentation only |
| Phase 7 outputs not overwritten | ✅ | No Phase 7 file modifications in 8A task |

---

## 3. Phase 8A deliverable checklist

| # | Deliverable | File | Frozen? |
|---|-------------|------|---------|
| 1 | Research alignment matrix | [../research/phase8a_research_alignment_matrix.md](../research/phase8a_research_alignment_matrix.md) | ✅ Draft frozen |
| 2 | Architecture freeze | [../architecture/phase8a_architecture_freeze.md](../architecture/phase8a_architecture_freeze.md) | ✅ |
| 3 | Multi-axis label schema | [../label_schema/phase8a_multi_axis_label_schema.md](../label_schema/phase8a_multi_axis_label_schema.md) | ✅ |
| 4 | Evidence table schema | [../evidence_table/phase8a_evidence_table_schema.md](../evidence_table/phase8a_evidence_table_schema.md) | ✅ |
| 5 | Fusion and abstention rules | [../fusion/phase8a_fusion_and_abstention_rules.md](../fusion/phase8a_fusion_and_abstention_rules.md) | ✅ |
| 6 | Success and rejection criteria | [../validation/phase8a_success_and_rejection_criteria.md](../validation/phase8a_success_and_rejection_criteria.md) | ✅ |
| 7 | Scope update draft | [../architecture/fassd_scope_update_draft.md](../architecture/fassd_scope_update_draft.md) | ✅ Draft only |
| 8 | This readiness review | `phase8a_to_phase8b_readiness_review.md` | ✅ |

---

## 4. Reviewer-required cleanup before 8B (8A-C1)

| Cleanup item | Status |
|--------------|--------|
| Explicit origin score fields added (file + segment four-tuples) | ✅ Done in `phase8a_evidence_table_schema.md` |
| Deprecated `evidence_origin_score` / `origin_score` forbidden in 8B | ✅ Documented |
| Old label vocabulary removed or deprecated in root docs | ✅ Root docs marked superseded + mapping table |
| Root docs point to frozen Phase 8A subdirectory docs | ✅ README + START_HERE updated |
| Fusion rules use explicit origin score field names | ✅ `phase8a_fusion_and_abstention_rules.md` |
| `clean` manipulation ≠ human-safe / direct AI may be `ai_synthetic` + `clean` | ✅ Fusion doc §2 rule 6 |
| Human sign-off still pending | ☐ Required before 8B |

---

## 5. Architecture freeze checklist (must all pass before 8B)

- [x] **Architecture candidate frozen** — pipeline and non-negotiable rules in `phase8a_architecture_freeze.md`  
- [x] **Label schema frozen** — [label_schema/phase8a_multi_axis_label_schema.md](../label_schema/phase8a_multi_axis_label_schema.md)  
- [x] **Evidence table schema frozen** — `phase8a_v1_1` with explicit origin columns  
- [x] **Fusion rules drafted** — strength levels, conflict, abstention, 8 examples  
- [x] **Validation targets written** — 7C1 metrics + rejection criteria  
- [x] **Scope update draft created** — does not overwrite `FASSD - Scope.md`  
- [x] **No unresolved binary-label assumptions** — invalid assumption table explicit  
- [x] **No implementation started early** — no 8B builder code, no training, no inference  

---

## 6. Human review gate (required)

| Review question | Reviewer sign-off |
|-----------------|-------------------|
| Origin vs manipulation separation acceptable? | ☐ Pending |
| Label vocabulary complete for thesis/product? | ☐ Pending |
| Evidence table columns sufficient for 7C1 population? | ☐ Pending |
| Fusion rules align with Phase 7 findings? | ☐ Pending |
| Acceptance targets realistic for deadline? | ☐ Pending |
| Scope draft wording acceptable for supervisor? | ☐ Pending |

**Approver:** _________________ **Date:** _________

---

## 7. What Phase 8B may do (after sign-off)

1. Implement evidence table builder under `code/phase8/` (when approved).  
2. Read existing Phase 7 CSVs, JSONL timelines, manifests — **no new model training** in first 8B pass.  
3. Emit `evidence_files.csv` and `evidence_segments.csv` per frozen schema.  
4. Optional fusion dry-run using 8A rules.  

---

## 8. What Phase 8B must not do (first pass)

- Emit deprecated columns `evidence_origin_score` or `origin_score`

- Train or fine-tune models  
- Run new inference that overwrites Phase 7 evaluation outputs  
- Modify checkpoints in `models_saved/`  
- Treat Hybrid or AASIST as sole origin truth  
- Skip segment rows for 7C1 partial-fabrication files  

---

## 9. Open items / assumptions (not blockers for 8A freeze)

| Item | Assumption |
|------|------------|
| Research placeholders | Citations to be added during thesis literature review |
| Origin four-tuple in 8B | May stub high `evidence_origin_unknown_score` until 8E — never single scalar |
| Segment window size | Match Phase 7 Hybrid chunking unless 8C changes — document in 8B README |
| Score fusion bands | Default 0.25/0.50/0.75 — calibrate in 8F on 7C1 only |

---

## 10. Final status

```
Phase 8B status: NOT STARTED

Required next action: Human review of Phase 8A documents
  - reports/phase8/research/phase8a_research_alignment_matrix.md
  - reports/phase8/architecture/phase8a_architecture_freeze.md
  - reports/phase8/label_schema/phase8a_multi_axis_label_schema.md
  - reports/phase8/evidence_table/phase8a_evidence_table_schema.md
  - reports/phase8/fusion/phase8a_fusion_and_abstention_rules.md
  - reports/phase8/validation/phase8a_success_and_rejection_criteria.md
  - reports/phase8/architecture/fassd_scope_update_draft.md
  - reports/phase8/roadmap/phase8a_to_phase8b_readiness_review.md (this file)
```

After human approval, update this section:

- Phase 8B status: ALLOWED TO START  
- Start date: __________  
- Owner: __________  

---

## Related

- [../PHASE8_START_HERE.md](../PHASE8_START_HERE.md)  
- [../PHASE8_IMPLEMENTATION_ROADMAP.md](../PHASE8_IMPLEMENTATION_ROADMAP.md)
