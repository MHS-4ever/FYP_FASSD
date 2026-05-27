# Phase 8A — Architecture Freeze

**Status:** CANDIDATE FROZEN — pending human sign-off before Phase 8B  
**Schema version:** `phase8a_v1_1`  
**Version:** 8A.1.1  
**Date freeze:** 2026-05-28 (updated 8A-C1)  

---

## 1. Executive summary

Phase 8 delivers a **forensic audio decision-support system**, not a single fake/real classifier. The frozen pipeline ingests audio, extracts parallel evidence on **origin**, **manipulation**, and **segments**, fuses with abstention, and emits **forensic-safe** reports suitable for a website-based decision-support interface.

This document is the authoritative architecture freeze for implementation phases 8B onward.

---

## 2. Frozen pipeline

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AUDIO INPUT (file / upload)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              PREPROCESSING & SEGMENTATION                                      │
│  • Resample / normalize (document sample_rate)                               │
│  • Fixed-duration windows + overlap (segment axis)                           │
│  • Optional known partial-region annotations (eval / training metadata)      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              EVIDENCE EXTRACTION (no single routing gate)                    │
│  • HybridResNet chunk scores + timelines (manipulation evidence)             │
│  • Phase 7C4-v2 prototype outputs (fusion baseline features)                   │
│  • Hand-crafted acoustic / channel features (8C)                             │
│  • Optional archived AASIST scores (feature only — not trusted judge)          │
│  • Later: frozen SSL embeddings (8D) — not day-one blocker                     │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
        ┌───────────┘                    │                    └───────────┐
        ▼                                ▼                                ▼
┌──────────────────┐          ┌──────────────────────┐          ┌──────────────────┐
│ ORIGIN EVIDENCE  │          │ MANIPULATION EVIDENCE │          │ SEGMENT EVIDENCE │
│ AXIS (parallel)  │          │ AXES (parallel)       │          │ AXIS (parallel)  │
│                  │          │                       │          │                  │
│ human            │          │ clean                 │          │ per-window scores│
│ ai_synthetic     │          │ replay_rerecorded     │          │ suspicious flags │
│ mixed            │          │ mixer_channel_proc.   │          │ timestamps       │
│ unknown          │          │ partial_fabrication   │          │ region_delta     │
│                  │          │ edited_spliced        │          │                  │
│                  │          │ compressed_low_qual.  │          │                  │
│                  │          │ unknown_manipulation  │          │                  │
└──────────────────┘          └──────────────────────┘          └──────────────────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              FUSION & ABSTENTION (Phase 8F — rules frozen in 8A doc)           │
│  • Evidence strength levels                                                  │
│  • Conflict handling (origin vs manipulation disagreement)                   │
│  • clean-human protection                                                    │
│  • manual_review_required / inconclusive paths                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              FORENSIC-SAFE REPORT / UI (Phase 8G)                              │
│  • evidence indicators (not absolute verdicts)                               │
│  • suspicious segments with timestamps                                       │
│  • manual review recommended when appropriate                                │
│  • explicit: decision-support prototype — not court-ready proof              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Non-negotiable architectural rules

### 3.1 No hard AI/human first-stage routing

- There is **no** mandatory gate that sends audio to “bonafide path” vs “spoof path” before other evidence runs.
- All axis evidence is computed **in parallel** (or from a shared feature pass with **independent** axis heads/rules).
- **Rationale:** Phase 7 cascade/routing amplified early mistakes; mixed-origin cases cannot be represented.

### 3.2 Origin and manipulation are parallel evidence axes

- **Origin** answers: who/what likely produced the speech content (human, AI, mixed over time, unknown).
- **Manipulation** answers: what processing or attack pattern is present (replay, mixer, partial insert, edit, compression, clean).
- Fusion may combine them for **decision labels**; neither axis alone may silently redefine the other.

### 3.3 Semantic separation (mandatory)

| Statement | Allowed | Forbidden |
|-----------|---------|-----------|
| `risk_positive` | Elevated forensic concern for review | Equating to “AI-generated” or “fake” |
| Replay detected | `replay_rerecorded` manipulation evidence | Automatic `ai_synthetic` origin |
| Mixer/channel detected | `mixer_channel_processed` manipulation evidence | Automatic `ai_synthetic` origin |
| Low quality | `compressed_low_quality` + possible abstention | Automatic “fake” |
| High manipulation score | Suspicious manipulation decision | “Proven deepfake” without origin evidence |

### 3.4 Human replay ≠ AI-generated speech

- **Human replay:** `origin` → `human` (or `unknown` if origin weak) + `replay_rerecorded`.
- Report wording: manipulation consistent with replay — **not** “AI-generated audio” unless `ai_synthetic` origin evidence exists.

### 3.5 Mixer/channel processing ≠ proof of AI

- Broadcast, phone chain, or mixer artifacts map to `mixer_channel_processed`.
- AI-origin mixer cases are `ai_synthetic` + `mixer_channel_processed` — two explicit evidences, not one spoof score.

### 3.6 Partial fabrication and mixed origin over time

- Short synthetic or replaced regions require **segment axis** + `partial_fabrication` manipulation label.
- File-level origin may be `mixed` when segments disagree; do not average away suspicious windows.

---

## 4. Evidence axes (frozen list)

| Axis type | Outputs | Primary Phase 7 input |
|-----------|---------|------------------------|
| Origin | `human`, `ai_synthetic`, `mixed`, `unknown` | Lightweight origin head + SSL (later); not Hybrid alone |
| Manipulation | See label schema doc | Hybrid timelines, channel features, partial deltas |
| Segment | Window scores, flags, `region_delta` | Hybrid chunk JSONL, annotated partial regions |
| Decision (fused) | `accept_human_clean`, `suspicious_*`, `inconclusive_manual_review` | 8F fusion rules |

---

## 5. Component boundaries (implementation phases)

| Phase | Component | Frozen responsibility |
|-------|-----------|----------------------|
| 8A | Docs (this file) | Architecture + schema freeze |
| 8B | Evidence table builder | Populate file/segment rows from existing Phase 7 outputs — **no new training** |
| 8C | Acoustic / channel features | Explain mixer, compression |
| 8D | Frozen SSL embeddings | Optional origin features |
| 8E | Lightweight axis models | Calibrated scores per axis |
| 8F | Fusion v3 | Extends 7C4-v2 with multi-axis rules |
| 8G | Report / UI | Forensic-safe wording |
| 8H | Validation | 7C1 targets + rejection criteria |

---

## 6. Checkpoint and model usage (frozen policy)

Per `models_saved/registry/CHECKPOINT_REGISTRY.md`:

| Asset | Role in Phase 8 |
|-------|-----------------|
| `hybrid_resnet_environmental_best` (active) | Manipulation/replay/mixer/**risk** evidence — **not** final origin truth |
| Phase 7C4-v2 prototype | Fusion baseline features only |
| 7C3-R2 / AASIST rejected archives | Must not drive product decisions; optional audit columns |

**Prohibited in Phase 8A:** training, inference runs, checkpoint modification.

---

## 7. Outputs per audio file (summary)

**File-level store:** identity, audio metadata, known labels (eval), **four explicit origin evidence scores** (`evidence_origin_human_score`, `evidence_origin_ai_score`, `evidence_origin_mixed_score`, `evidence_origin_unknown_score`), manipulation evidence scores, calibrated labels, `final_forensic_status`, `manual_review_required`, `forensic_risk_level`, `manual_review_reason`, `fusion_trace`, `evidence_source_paths`, `forensic_summary`, `schema_version` = `phase8a_v1_1`.

**No single scalar origin score** — binary fake/real collapse is forbidden at the schema layer.

**Segment-level store:** one row per window with **four segment origin scores** (`segment_origin_*`), manipulation scores, `suspicious_segment_flag`, `segment_reason`, `segment_evidence_source`.

Full field list: [../evidence_table/phase8a_evidence_table_schema.md](../evidence_table/phase8a_evidence_table_schema.md).

---

## 8. Loopholes from Phase 7 explicitly prevented

| Loophole | Prevention |
|----------|------------|
| Binary fake/real collapse | Multi-axis schema + rejection criteria |
| Hard routing | Parallel extraction |
| Clean-human false alarms | Fusion clean-human protection + acceptance targets |
| File-mean hiding partial inserts | Segment axis required |
| Replay → AI narrative | Origin/manipulation separation + report templates |
| risk_positive = fake | Wording + invalid assumption list in label schema |
| Holdout threshold tuning | 7A sanity only; 7C1 primary |
| Report overclaiming | Decision-support language only |

Detail: [../PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md](../PHASE8_FAILURE_MODE_AND_LOOPHOLE_ANALYSIS.md).

---

## 9. What Phase 8A does not authorize

- Training or fine-tuning any model  
- Running inference to refresh scores (8B may **read** existing Phase 7 CSVs/JSONL only)  
- Modifying checkpoints or Phase 7 report artifacts  
- Implementing evidence table builder code (Phase 8B)  

---

## 10. Sign-off

| Role | Status |
|------|--------|
| Architecture freeze (8A doc) | **CANDIDATE FROZEN** — pending human review (8A-C1 hardened) |
| Phase 8B implementation | **NOT STARTED** |

**Related:** [phase8a_fusion_and_abstention_rules.md](../fusion/phase8a_fusion_and_abstention_rules.md) · [fassd_scope_update_draft.md](fassd_scope_update_draft.md)
