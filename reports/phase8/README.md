# Phase 8 — Multi-Axis Forensic Audio Intelligence (Reports)

**Status:** Planning initialized — **no implementation**  
**Code hub:** [code/phase8/README.md](../../code/phase8/README.md)

---

## Why Phase 8 exists

Phase 7 closed as **Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings**. It showed that:

- HybridResNet remains useful **evidence** for replay/mixer/partial sensitivity.
- Binary origin-style fine-tuning and anti-spoof-only models **do not** meet the full forensic product goal.
- A parallel **origin** axis and **manipulation** axes are required.

Phase 8 title: **Multi-Axis Forensic Audio Intelligence Architecture**.

---

## Start here

| Document | Role |
|----------|------|
| [PHASE8_START_HERE.md](PHASE8_START_HERE.md) | Entry point |
| [PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md](PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md) | Architecture + research direction |
| [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) | Label schema |
| [PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md](PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md) | Failure modes + mitigations |
| [PHASE8_IMPLEMENTATION_ROADMAP.md](PHASE8_IMPLEMENTATION_ROADMAP.md) | 8A–8H roadmap |
| [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md) | Phase 8 gates |

---

## Subfolders

| Folder | Purpose |
|--------|---------|
| `research/` | Literature and design notes |
| `architecture/` | Diagrams and architecture freeze |
| `label_schema/` | Extended label definitions |
| `evidence_table/` | Evidence table specs |
| `fusion/` | Fusion / abstention design |
| `validation/` | Benchmark protocol for Phase 8 |
| `roadmap/` | Milestone tracking |

---

## Phase 7 closure (read-only reference)

- [../phase7/PHASE7_FINAL_CLOSURE_REPORT.md](../phase7/PHASE7_FINAL_CLOSURE_REPORT.md)
- [../phase7/PHASE7_TO_PHASE8_TRANSITION.md](../phase7/PHASE7_TO_PHASE8_TRANSITION.md)
- [../phase7/PHASE7_FINAL_STATUS_FREEZE.md](../phase7/PHASE7_FINAL_STATUS_FREEZE.md)

---

## Current status

- Phase **7** is **closed** (see closure reports).
- Phase **8A** is next: **research-backed architecture freeze** (review only — no training).
- **Checkpoint registry:** run `organize_model_checkpoints.py` → `models_saved/registry/`

**Do not:** run more Phase 7 AASIST/Hybrid experiments; train WavLM or other large models until Phase 8A is approved.

### Checkpoint usage (after organization)

| Folder | Role |
|--------|------|
| `models_saved/active/` | Current evidence pipeline (Hybrid baseline) |
| `models_saved/prototype_evidence/` | 7C4-v2 reproduction only |
| `models_saved/pretrained_reference/` | AASIST official weights — reference only |
| `models_saved/rejected_archive/` | Rejected fine-tunes — **not** for product decisions |
