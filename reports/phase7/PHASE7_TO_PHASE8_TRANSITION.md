# Phase 7 → Phase 8 Transition

**Most important handoff document for the next development phase.**

---

## 1. Reason for Transition

Phase 7 ran controlled tests, dataset preparation, Hybrid fine-tuning, decision-layer prototypes, and an AASIST evidence branch. All tracks converged on the same architectural conclusion:

> **A single binary real/fake or spoof/bonafide model cannot represent the forensic product goal.**

Phase 7 is therefore closed. Phase 8 opens with an explicit **multi-axis** design.

---

## 2. What Phase 7 Proved

| Proved | Evidence |
|--------|----------|
| HybridResNet is useful **evidence** | Strong replay/mixer/partial on 7C1 |
| Hybrid over-flags clean human | 17/23 false alarms (baseline) |
| Segment evidence matters | 19/23 direct-AI rescued at segment level |
| Binary origin fine-tune fails | 7C3-v1 manipulation collapse |
| R2 not standalone | 7C3-R2 rejected as product checkpoint |
| Fusion can help | 7C4-v2 prototype passes controlled v2 criteria |
| Anti-spoof ≠ forensic product | AASIST 22/23 clean-human FA pretrained; fine-tune rejected |
| Report layer needs better evidence | 7D postponed |

**Phase 7 is not a failed phase.** It produced the findings required to justify Phase 8.

---

## 3. Why Phase 8 Is Needed

The product must support statements like:

- “Manipulation consistent with replay” **without** claiming “AI-generated” incorrectly.
- “Possible AI-synthetic segment” **with** timestamp evidence.
- “Clean human recording” **with** low false-alarm rate on local data.
- “Uncertain — manual review recommended” when axes disagree.

That requires **parallel axes** and calibrated fusion — not another threshold on one score.

---

## 4. Phase 8 Architectural Principle

> **Origin and manipulation must be inferred as parallel evidence axes, not as one binary fake/real label.**

Optional segment axis for time-localized suspicion.

---

## 5. Phase 8 Target Architecture

```text
Audio
  ↓
Evidence extraction (features + model scores + timelines)
  ↓
Origin axis:
  - human
  - AI
  - mixed
  - unknown

Manipulation axes:
  - clean
  - replay / rerecording
  - mixer / channel processed
  - partial fabrication
  - edited / spliced
  - compressed / low-quality

Segment axis:
  - suspicious windows
  - suspicious timestamps
  - inside/outside region deltas

Fusion:
  - final forensic status
  - risk level
  - manual review requirement
  - report-ready evidence summary
```

**Phase 8 does not start with training a large transformer.**  
**Phase 8 starts with building an evidence table.**

---

## 6. Phase 8 First Deliverables (8A–8B)

| Step | Deliverable |
|------|-------------|
| **8A** | Research-backed architecture freeze (docs reviewed) |
| **8B** | Multi-axis evidence table builder (schema + manifests) |
| **8C–8E** | Features + lightweight axis scorers (after freeze) |
| **8F** | Fusion + abstention |
| **8G** | Report layer + UI integration |
| **8H** | Final evaluation + thesis defense package |

See [../phase8/PHASE8_IMPLEMENTATION_ROADMAP.md](../phase8/PHASE8_IMPLEMENTATION_ROADMAP.md).

---

## 7. What Must Not Be Repeated

1. Training another binary fake/real model as the “final” solution.
2. Hard AI/human router before manipulation analysis.
3. Claiming 7C4-v2 or any single checkpoint is production-ready forensic proof.
4. More Phase 7 AASIST/Hybrid fine-tunes without multi-axis schema approval.
5. Threshold tuning on Phase 7A holdout for marketing claims.
6. Overwriting Phase 7 CSVs/checkpoints.

---

## Links

- [PHASE7_FINAL_CLOSURE_REPORT.md](PHASE7_FINAL_CLOSURE_REPORT.md)
- [PHASE7_FINAL_STATUS_FREEZE.md](PHASE7_FINAL_STATUS_FREEZE.md)
- [../phase8/PHASE8_START_HERE.md](../phase8/PHASE8_START_HERE.md)
