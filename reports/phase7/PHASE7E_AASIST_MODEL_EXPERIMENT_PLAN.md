# Phase 7E — AASIST Model Experiment Plan (Summary)

**Status:** Phase **7E0** active — planning and locked benchmark only  
**Detail folder:** [phase7e_aasist_experiment/](phase7e_aasist_experiment/README.md)  
**Broader transformer track:** [PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md](PHASE7E_TRANSFORMER_MODEL_EXPERIMENTS.md) (WavLM / wav2vec2 later)

---

## One-line goal

Add **AASIST** as a **candidate evidence branch**, evaluate on locked Phase 7C1 + Phase 7A benchmarks against HybridResNet and 7C4-v2, then fuse only if acceptance criteria are met.

---

## Why now (after 7C freeze)

| Fact | Implication |
|------|-------------|
| 7C4-v2 is prototype decision layer only | Evidence layer still weak on direct AI and clean-human auto-accept |
| HybridResNet is not final classifier | Need complementary spoof/synthetic evidence |
| 7D report implementation postponed | Reports should not mask weak scores |
| AASIST before WavLM | Lighter, spoof-specific, fits 6GB/12GB resources |

AASIST is **not** assumed to be the final product model.

---

## Architecture (target)

```text
HybridResNet evidence  +  AASIST evidence  →  fusion (7E5)  →  report (7D later)  →  UI
```

---

## 7E0 deliverables (complete in subfolder)

| Document | Link |
|----------|------|
| Experiment plan | [PHASE7E0_AASIST_EXPERIMENT_PLAN.md](phase7e_aasist_experiment/PHASE7E0_AASIST_EXPERIMENT_PLAN.md) |
| Locked benchmark | [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](phase7e_aasist_experiment/PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) |
| Label strategy | [PHASE7E0_AASIST_LABEL_STRATEGY.md](phase7e_aasist_experiment/PHASE7E0_AASIST_LABEL_STRATEGY.md) |
| Resources | [PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md](phase7e_aasist_experiment/PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md) |
| Acceptance | [PHASE7E0_ACCEPTANCE_CRITERIA.md](phase7e_aasist_experiment/PHASE7E0_ACCEPTANCE_CRITERIA.md) |
| Roadmap 7E0–7E5 | [PHASE7E0_IMPLEMENTATION_ROADMAP.md](phase7e_aasist_experiment/PHASE7E0_IMPLEMENTATION_ROADMAP.md) |
| Do not do | [PHASE7E0_DO_NOT_DO.md](phase7e_aasist_experiment/PHASE7E0_DO_NOT_DO.md) |

---

## Sub-phases

| Phase | Training? |
|-------|-----------|
| 7E0 Planning | **No** |
| 7E1 Smoke test | **No** |
| 7E2 Adapter | **No** |
| 7E3 Fine-tune | Yes (after review) |
| 7E4 Eval | Inference |
| 7E5 Fusion v3 | Calibration only |

---

## Next action

Review 7E0 docs → proceed to **Phase 7E1** AASIST code integration smoke test. **Do not train** until 7E1 and 7E2 are reviewed.

See [../NEXT_ACTIONS.md](../NEXT_ACTIONS.md).
