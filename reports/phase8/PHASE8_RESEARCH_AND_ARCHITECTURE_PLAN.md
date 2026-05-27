# Phase 8 Research and Architecture Plan

**Status:** Draft for Phase 8A review — no implementation

---

## 1. Goal

Deliver a **decision-support** forensic audio system that:

- Minimizes clean-human false alarms on Phase 7C1-style local data  
- Preserves manipulation detection (replay, mixer, partial, direct-AI segments)  
- Separates **origin evidence** from **manipulation evidence** in outputs  
- Supports **manual review** when uncertain  

---

## 2. Research Direction

Build on Phase 7 findings and anti-spoof / audio-deepfake literature, but **do not** copy ASVspoof leaderboard metrics as the product definition.

Focus areas:

- Multi-task / multi-head audio classification with abstention  
- Segment-level detection for partial fabrication  
- Channel-robust features (not only spectral spoof cues)  
- Calibration and fusion under class imbalance  
- Human-in-the-loop forensic reporting standards  

---

## 3. Why Binary Models Failed

See [../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md](../phase7/PHASE7_MODEL_FAILURE_ANALYSIS.md).

Summary: forensic roles (human replay, AI mixer, partial insert) are **not** collapsible to one label without semantic error.

---

## 4. Why Hard AI/Human First Is Risky

Cascade routing amplifies early mistakes and prevents “mixed origin” reasoning. Phase 8 infers axes **in parallel**, then fuses.

---

## 5. Multi-Axis Architecture

```text
Audio input
    → feature + model evidence extraction
    → origin axis scores (human / AI / mixed / unknown)
    → manipulation axis scores (clean / replay / mixer / partial / …)
    → segment axis (windows, timestamps, region deltas)
    → fusion + abstention
    → final_status, risk_level, manual_review_required, evidence_summary
```

---

## 6. Evidence Sources (Phase 8 inputs)

| Source | Role in Phase 8 |
|--------|------------------|
| HybridResNet baseline scores + chunk timelines | Core manipulation/replay evidence |
| Phase 7C4-v2 decision outputs | Prototype fusion baseline |
| Acoustic / channel features (8C) | Explain mixer/compression |
| Partial-region features (8C) | Partial fabrication axis |
| Frozen SSL embeddings WavLM/wav2vec2 (8D) | Later — not day-one training |
| AASIST archived scores (7E) | Optional feature column only — **not** trusted classifier |

---

## 7. Planned Models / Features

| Component | Phase | Notes |
|-----------|-------|-------|
| Evidence table builder | 8B | **First code priority** |
| Hand-crafted acoustic features | 8C | Lightweight |
| Frozen SSL embeddings | 8D | No large fine-tune at start |
| Per-axis lightweight classifiers | 8E | Small heads, calibrated |
| Fusion + abstention | 8F | Extends 7C4-v2 ideas |
| Report layer | 8G | Forensic-safe wording |

---

## 8. Validation Strategy

- **Primary:** Phase 7C1 locked file set (same IDs, same roles)  
- **Safety:** Phase 7A holdout — no threshold tuning for product claims  
- **Metrics:** per-axis counts + clean-human FA + partial region metrics  
- **Gates:** [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md)  

---

## 9. Deadline-Aware Implementation Strategy

1. **Week 1 (8A):** Freeze schema + architecture docs.  
2. **Week 2 (8B):** Evidence table from existing Phase 7 CSVs (no new training).  
3. **Week 3–4 (8C–8E):** Features + lightweight heads.  
4. **Week 5 (8F):** Fusion v3 with manual review.  
5. **Week 6+ (8G–8H):** Reports + thesis package.  

Skip large transformer training until evidence table + baselines prove value.

---

## No implementation before 8A review

Do not write Phase 8 training code until this plan and [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) are approved.
