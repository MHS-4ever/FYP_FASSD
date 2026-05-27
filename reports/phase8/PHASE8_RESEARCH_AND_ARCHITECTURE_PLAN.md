# Phase 8 Research and Architecture Plan

> **Historical draft — superseded** by [architecture/phase8a_architecture_freeze.md](architecture/phase8a_architecture_freeze.md) and [research/phase8a_research_alignment_matrix.md](research/phase8a_research_alignment_matrix.md).  
> **Do not implement** from this file. Use Phase 8A subdirectory docs only.

**Status:** Superseded · Phase 8B **NOT STARTED**

---

## 1. Goal (unchanged intent)

Deliver a **decision-support** forensic audio system that separates origin, manipulation, and segment evidence; supports manual review when uncertain.

---

## 2. Multi-Axis Architecture (updated vocabulary)

```text
Audio input
    → feature + model evidence extraction
    → origin evidence: evidence_origin_human_score, evidence_origin_ai_score,
                       evidence_origin_mixed_score, evidence_origin_unknown_score
    → manipulation evidence: replay, mixer, partial, splice, quality, …
    → segment evidence: segment_origin_* + manipulation per window
    → fusion + abstention → final_forensic_status, forensic_risk_level,
                            manual_review_required, fusion_trace
```

**Deprecated in this draft:** single “origin axis scores (human / AI …)” without four explicit columns; `final_status` alone without `final_forensic_status`.

---

## 3. Evidence Sources (Phase 8 inputs)

| Source | Role in Phase 8 |
|--------|------------------|
| HybridResNet baseline scores + chunk timelines | Manipulation/replay evidence — **not** `evidence_origin_ai_score` alone |
| Phase 7C4-v2 decision outputs | Fusion baseline features |
| Acoustic / channel features (8C) | `mixer_channel_processed`, `compressed_low_quality` |
| Frozen SSL embeddings (8D) | Later origin features |
| AASIST archived scores (7E) | Optional column — not trusted classifier |

---

## 4. Planned phases

See [PHASE8_IMPLEMENTATION_ROADMAP.md](PHASE8_IMPLEMENTATION_ROADMAP.md) (historical) and [roadmap/phase8a_to_phase8b_readiness_review.md](roadmap/phase8a_to_phase8b_readiness_review.md) (authoritative gates).

**No implementation before Phase 8A human sign-off.**

---

## Label vocabulary note

| Old term in this draft | Use instead |
|------------------------|-------------|
| `origin_ai` | `ai_synthetic` / `evidence_origin_ai_score` |
| `origin_human` | `human` / `evidence_origin_human_score` |
| `manipulation_replay` | `replay_rerecorded` |
| `manipulation_mixer_channel` | `mixer_channel_processed` |

Full list: [README.md](README.md#deprecated-label-mapping-do-not-use-in-8b)
