# Phase 7 Final Status Freeze

**Effective:** Phase 7 closed — transition to Phase 8  
**Phase 7 title (closed):** Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings

---

## Phase 7 is closed

Do **not** reopen Phase 7 experiments unless a new controlled evaluation plan is approved.

---

## Accepted

| Item | Notes |
|------|--------|
| Phase **7A** | Controlled forensic testing |
| Phase **7B** | Forensic labels |
| Phase **7C0** | Dataset audit |
| Phase **7C1** | Local forensic dataset + baseline evaluation |
| Phase **7C2** | Training manifest preparation |
| Phase **7C4-v2** | Decision-layer **prototype only** (not final product model) |

---

## Rejected (as current product solution)

| Item | Notes |
|------|--------|
| Phase **7C3-v1** checkpoint | Manipulation sensitivity collapsed |
| Phase **7C3-R2** checkpoints | Rejected as **standalone** (evidence-only context) |
| Phase **7C4-v1** decision layer | Too many clean-human false alarms |
| AASIST pretrained | Rejected as standalone and branch-only **current** solution |
| AASIST fine-tuned **best_product** | Rejected on Phase 7C1 |
| AASIST fine-tuned **best_loss** | Rejected on Phase 7C1 |

---

## Postponed

| Item | Notes |
|------|--------|
| Phase **7D** | Report layer — planning complete; implementation postponed until evidence layer improves |

---

## Next

**Phase 8 — Multi-Axis Forensic Audio Intelligence Architecture**

- Next active work: **Phase 8A** — research-backed architecture freeze (review docs; no training).

---

## Archive policy

- Preserve all Phase 7 CSVs, checkpoints, and reports **as-is**.
- Do not overwrite `phase7e3a_pretrained_eval/` or official vendor weights.

## Organized checkpoint copies (Phase 8)

Usable and archived weights may be **copied** (not moved) into `models_saved/` via:

`python code/phase8/validation/organize_model_checkpoints.py --models_root models_saved`

| Location | Role |
|----------|------|
| `models_saved/active/` | HybridResNet baseline — **accepted evidence** |
| `models_saved/prototype_evidence/` | 7C3-R2 — prototype support only |
| `models_saved/pretrained_reference/` | Official AASIST — reference only |
| `models_saved/rejected_archive/` | Fine-tuned AASIST — **not** for product use |

Registry: `models_saved/registry/CHECKPOINT_REGISTRY.md`
