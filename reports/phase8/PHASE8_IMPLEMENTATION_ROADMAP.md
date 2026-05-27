# Phase 8 Implementation Roadmap

> **Historical draft — superseded** for schema and gates by Phase 8A docs in `architecture/`, `evidence_table/`, `fusion/`, `roadmap/`.  
> **Authoritative 8B gate:** [roadmap/phase8a_to_phase8b_readiness_review.md](roadmap/phase8a_to_phase8b_readiness_review.md)

**Rule:** No Phase 8B code until Phase 8A human sign-off. **Phase 8B: NOT STARTED**

---

## Overview

| Sub-phase | Name | Training? |
|-----------|------|-----------|
| **8A** | Architecture freeze (+ 8A-C1 schema hardening) | No |
| **8B** | Evidence table builder | No (aggregation only) |
| **8C** | Acoustic / channel features | No heavy ML |
| **8D** | Frozen SSL embedding extraction | Inference only (later) |
| **8E** | Multi-axis lightweight classifiers | Light training |
| **8F** | Fusion + abstention | Calibration |
| **8G** | Report layer + website | No |
| **8H** | Final evaluation | Eval only |

---

## Phase 8A — Architecture freeze (complete pending sign-off)

**Authoritative deliverables:**

- [architecture/phase8a_architecture_freeze.md](architecture/phase8a_architecture_freeze.md)  
- [label_schema/phase8a_multi_axis_label_schema.md](label_schema/phase8a_multi_axis_label_schema.md)  
- [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md) — `phase8a_v1_1`  
- [fusion/phase8a_fusion_and_abstention_rules.md](fusion/phase8a_fusion_and_abstention_rules.md)  

**Exit gate:** Human sign-off on readiness review; no deprecated origin columns in 8B.

---

## Phase 8B — Evidence table builder (NOT STARTED)

**Deliverables:**

- Populate `evidence_files.csv` / `evidence_segments.csv` per [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md)  
- **Required:** four file-level + four segment-level origin score columns  
- **Forbidden:** `evidence_origin_score`, `origin_score`, `manipulation_direct_synthetic`  
- Populate `evidence_source_paths`, `schema_version`, trace fields (fusion may be stub)  

**No new model training.**

---

## Phases 8C–8H

Unchanged intent — see historical sections in prior revisions. Always use frozen label vocabulary from `label_schema/phase8a_multi_axis_label_schema.md`.

---

## Dependencies

```text
8A (+ 8A-C1) → [human sign-off] → 8B → (8C, 8D) → 8E → 8F → 8G → 8H
```

---

## What not to do

- Train WavLM end-to-end before evidence table exists  
- Map Hybrid spoof score → single origin column  
- Use root [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) for column names  
