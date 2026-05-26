# Phase 7E — AASIST Evidence Branch Experiment

**Status:** Phase **7E0** active (planning + locked benchmark — **no training**)  
**Canonical planning folder:** `reports/phase7/phase7e_aasist_experiment/`  
**Future code location:** `code/phase7/aasist/` (not created in 7E0)

---

## Purpose

Add **AASIST** as a **candidate evidence branch** — not as a assumed final forensic product model. Evaluate against locked benchmarks on Phase 7C1 and Phase 7A holdout before any fusion or report-layer claims.

---

## Phase 7E0 documents (review these first)

| Document | Role |
|----------|------|
| [PHASE7E0_AASIST_EXPERIMENT_PLAN.md](PHASE7E0_AASIST_EXPERIMENT_PLAN.md) | Why AASIST, scope, architecture role, datasets |
| [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) | **Locked** evaluation protocol (do not change without new phase gate) |
| [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md) | Binary forensic-risk labels and wording rules |
| [PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md](PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md) | GPU/RAM policy, batch sizes, what to avoid |
| [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md) | Standalone vs branch-only acceptance |
| [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md) | 7E0 → 7E5 phased path |
| [PHASE7E0_DO_NOT_DO.md](PHASE7E0_DO_NOT_DO.md) | Hard stops for this experiment track |

---

## Parent index

- [PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md) — summary + links  
- [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](../PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) — broader transformer track (WavLM later)  
- [../README.md](../README.md) — Phase 7 hub  
- [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md) — project checklist

---

## Current model context (frozen)

| Component | Status |
|-----------|--------|
| HybridResNet baseline | Evidence source — replay/mixer/partial |
| 7C3-v1 / standalone R2 | Rejected |
| 7C4-v2 | Decision-layer **prototype** only |
| 7D report implementation | **Postponed** until evidence layer improves |

---

## Sub-phases (planned)

| Phase | Name | Training? |
|-------|------|-----------|
| **7E0** | Planning + locked benchmark | **No** |
| **7E1** | Code integration smoke test | **No** |
| **7E2** | Dataset adapter | **No** |
| **7E3** | Baseline / fine-tune run | Yes (after 7E1–7E2 review) |
| **7E4** | Evaluation vs baselines | Inference only |
| **7E5** | Fusion decision layer v3 | Calibration only (after 7E4) |

Do **not** train until **7E1** and **7E2** are reviewed.
