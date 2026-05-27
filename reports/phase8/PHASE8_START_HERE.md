# Phase 8 — Start Here

**Title:** Multi-Axis Forensic Audio Intelligence Architecture  
**Status:** Planning initialized — **no code, no training**

---

## Why Phase 8 starts now

Phase 7 closed as **Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings**.

It proved:

- HybridResNet is valuable **evidence** for replay, mixer, and partial fabrication.
- Single binary spoof/fake or origin-first models **fail** the forensic product goal (clean-human false alarms, wrong semantics).
- AASIST anti-spoof models are **not sufficient** as the current solution in this local setup.
- **7C4-v2** remains an accepted **decision-layer prototype only** — not a final model.

Phase 8 exists because **architecture must change**, not because Phase 7 “failed.”

---

## Phase 8 goal

Build a **multi-axis forensic audio intelligence system** that produces:

- Parallel **origin** evidence (human / AI / mixed / unknown)
- Parallel **manipulation** evidence (clean, replay, mixer, partial, edit, compression, …)
- **Segment** evidence (windows, timestamps, region deltas)
- **Fusion** into forensic status, risk level, manual-review flags, and report-ready summaries

---

## What Phase 8 is NOT

- ❌ One fake/real classifier marketed as final truth  
- ❌ Hard AI/human routing gate before analysis  
- ❌ Another binary spoof model without multi-axis approval  
- ❌ Immediate WavLM / large-transformer training  

---

## What Phase 8 IS

- ✅ Evidence table per file/segment  
- ✅ Reuse Hybrid chunk timelines and 7C4-v2 outputs as features  
- ✅ Lightweight axis models after schema freeze  
- ✅ Calibrated fusion with abstention  
- ✅ Forensic-safe report wording (decision-support prototype)  

---

## Read order

1. [PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md](PHASE8_RESEARCH_AND_ARCHITECTURE_PLAN.md)  
2. [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md)  
3. [PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md](PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md)  
4. [PHASE8_IMPLEMENTATION_ROADMAP.md](PHASE8_IMPLEMENTATION_ROADMAP.md)  
5. [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md)  

Phase 7 handoff: [../phase7/PHASE7_TO_PHASE8_TRANSITION.md](../phase7/PHASE7_TO_PHASE8_TRANSITION.md)

---

## Current next action

**Phase 8A — Research-backed architecture freeze** (documentation review only).

Do **not** train models until 8A is signed off.
