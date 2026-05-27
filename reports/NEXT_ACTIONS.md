# FASSD Next Actions

**Product:** [Forensic Voice Authenticity Analyzer](UPDATED_PROJECT_SCOPE.md)  
**Phase 7:** [Closed](phase7/PHASE7_FINAL_STATUS_FREEZE.md) · **Phase 8:** [Start here](phase8/PHASE8_START_HERE.md)

---

## Current active phase

**Phase 8A — Multi-axis forensic architecture freeze** (documentation review only)

---

## Correct project state

| Point | Status |
|-------|--------|
| Phase **7** | **Closed** — [closure report](phase7/PHASE7_FINAL_CLOSURE_REPORT.md) |
| Phase **7C4-v2** | **Accepted** as decision-layer **prototype only** (frozen artifact) |
| Phase **7D** | Report layer — **postponed** (moves to Phase 8G) |
| Phase **7E / AASIST** | **Rejected** as current solution — [negative finding](phase7/PHASE7_AASIST_NEGATIVE_FINDING.md) |
| Phase **8** | **Initialized** — planning docs + folder scaffold |
| Training / inference | **Do not run** until Phase 8A architecture review |

---

## Immediate next actions

| Step | Action |
|------|--------|
| **1** | Read [PHASE7_TO_PHASE8_TRANSITION.md](phase7/PHASE7_TO_PHASE8_TRANSITION.md) |
| **2** | Review [PHASE8_START_HERE.md](phase8/PHASE8_START_HERE.md) + [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](phase8/PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) |
| **3** | Review [PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md](phase8/PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md) |
| **4** | Sign off **Phase 8A** architecture freeze |
| **5** | Then begin **Phase 8B** evidence table (no model training) |

### Organize model checkpoints (copy only)

```text
python code/phase8/validation/organize_model_checkpoints.py --models_root models_saved
```

| Registry | Path |
|----------|------|
| Summary | `models_saved/registry/CHECKPOINT_REGISTRY.md` |
| CSV | `models_saved/registry/CHECKPOINT_REGISTRY.csv` |

- **Active:** `models_saved/active/hybrid_resnet_environmental_best.pth` (evidence branch)
- **Prototype:** 7C3-R2 best_product / best_loss if present (7C4-v2 support only)
- **Rejected archive:** AASIST fine-tunes copied for documentation only — not for product use

Original paths under `reports/phase7/` remain unchanged.

---

## Do not do

- Do **not** run more Phase 7 AASIST or Hybrid fine-tune experiments  
- Do **not** train WavLM or any large model yet  
- Do **not** overwrite Phase 7 CSVs, checkpoints, or `phase7e3a_pretrained_eval/`  
- Do **not** implement Phase 8 model code before 8A review  

---

## Phase 7 closure documents

| Document | Purpose |
|----------|---------|
| [PHASE7_FINAL_CLOSURE_REPORT.md](phase7/PHASE7_FINAL_CLOSURE_REPORT.md) | Executive closure |
| [PHASE7_EXPERIMENT_RESULTS_SUMMARY.md](phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md) | Metrics table |
| [PHASE7_MODEL_FAILURE_ANALYSIS.md](phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md) | Why binaries failed |
| [PHASE7_AASIST_NEGATIVE_FINDING.md](phase7/PHASE7_AASIST_NEGATIVE_FINDING.md) | AASIST outcome |
| [PHASE7_FINAL_STATUS_FREEZE.md](phase7/PHASE7_FINAL_STATUS_FREEZE.md) | One-page freeze |

---

## Phase 8 hubs

- Reports: [phase8/README.md](phase8/README.md)  
- Code: [code/phase8/README.md](../code/phase8/README.md)  
- Roadmap: [phase8/PHASE8_IMPLEMENTATION_ROADMAP.md](phase8/PHASE8_IMPLEMENTATION_ROADMAP.md)

---

## Quick links

| Doc | Use |
|-----|-----|
| [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) | Product direction |
| [phase7/README.md](phase7/README.md) | Phase 7 archive hub |
| [PHASE8_ACCEPTANCE_CRITERIA.md](phase8/PHASE8_ACCEPTANCE_CRITERIA.md) | Phase 8 gates |
