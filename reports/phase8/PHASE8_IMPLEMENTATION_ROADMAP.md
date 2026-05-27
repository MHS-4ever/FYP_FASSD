# Phase 8 Implementation Roadmap

**Rule:** No implementation before **Phase 8A** architecture freeze is reviewed and approved.

---

## Overview

| Sub-phase | Name | Training? |
|-----------|------|-----------|
| **8A** | Research-backed architecture freeze | No |
| **8B** | Multi-axis evidence table builder | No (aggregation) |
| **8C** | Acoustic / channel feature extraction | No heavy ML |
| **8D** | Frozen SSL embedding extraction | Inference only |
| **8E** | Multi-axis lightweight classifiers | Light training |
| **8F** | Fusion + abstention / manual review | Calibration |
| **8G** | Report layer + website integration | No |
| **8H** | Final evaluation + defense package | Eval only |

---

## Phase 8A — Architecture freeze

**Deliverables:**

- Approved [PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](PHASE8_MULTI_AXIS_LABEL_SCHEMA.md)  
- Evidence table column spec  
- Fusion rules sketch  
- Sign-off in `reports/phase8/architecture/`  

**Exit gate:** No code in `code/phase8/models/` until signed.

---

## Phase 8B — Evidence table builder

**Deliverables:**

- Script: aggregate Hybrid CSVs, 7C4-v2 decisions, optional AASIST archives  
- One row per `sample_id` (+ segment rows if needed)  
- Output: `reports/phase8/evidence_table/`  

**No new model training.**

---

## Phase 8C — Acoustic / channel features

- Hand-crafted features for mixer/compression/editing cues  
- Partial-region statistics from timelines  

---

## Phase 8D — Frozen SSL embeddings

- WavLM / wav2vec2 **inference-only** features added to evidence table  
- Deferred if deadline tight — table-first strategy  

---

## Phase 8E — Lightweight axis classifiers

- Small heads per axis (not one softmax fake/real)  
- Train only on 7C2 manifests with multi-axis labels  

---

## Phase 8F — Fusion v3

- Extends 7C4-v2 concepts with abstention  
- `manual_review_required` when axes conflict  

---

## Phase 8G — Report layer + UI

- Implement postponed 7D concepts on Phase 8 evidence  
- Website shows evidence summary, not raw “FAKE”  

---

## Phase 8H — Final evaluation

- Phase 7C1 + 7A holdout per [PHASE8_ACCEPTANCE_CRITERIA.md](PHASE8_ACCEPTANCE_CRITERIA.md)  
- Thesis / defense evidence package  

---

## Dependencies

```text
8A → 8B → (8C, 8D parallel) → 8E → 8F → 8G → 8H
```

---

## What not to do in Phase 8 opening weeks

- Train WavLM end-to-end  
- Run more Phase 7 AASIST/Hybrid fine-tunes  
- Overwrite Phase 7 artifacts  
