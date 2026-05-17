# FASSD Updated Project Scope — Forensic Voice Authenticity Analyzer

**Effective:** May 2026  
**Supersedes:** “Simple AI-vs-human deepfake detector” as the sole product definition  
**Baseline model:** `HybridResNetEnvironmental` (unchanged until Phase 7C review)

---

## Overview

FASSD (**Forensic Voice Authenticity Analyzer**) analyzes a given audio file and produces a **forensic authenticity report**. The system still performs AI-vs-human discrimination, but that is **Scope 1** only. Scopes 2–6 cover manipulation, partial fabrication, replay chains, environmental profiling, and safe report generation.

**Official product goal:** Analyze audio and produce a forensic-style report — not only a REAL/FAKE label.

---

## Scope 1 — AI vs Human Voice Origin Detection

Detect whether the **speech source** is human-likely or AI-likely.

| Output | Meaning |
|--------|---------|
| `human_likely` | Speech content consistent with human origin |
| `ai_likely` | Speech content consistent with synthetic/spoof origin |
| `uncertain` | Borderline or insufficient evidence |

**Purpose:** Core baseline task; maps from current binary head + pooling (Phase 6).

---

## Scope 2 — Manipulation and Processing Risk Detection

Detect whether the audio is **clean/original** or affected by replay, mixer/equalizer, codec compression, channel alteration, noise reduction, or re-recording.

| Output | Meaning |
|--------|---------|
| `clean_original` | No strong manipulation signals (rare in field audio) |
| `replayed_or_re_recorded` | Second-hop or speaker→device recording likely |
| `channel_processed` | Mixer, EQ, PA, or chain processing likely |
| `platform_compressed` | WhatsApp/social/codec compression risk |
| `noisy_low_quality` | Quality too poor for confident assessment |
| `uncertain` | Insufficient evidence |

**Purpose:** A **human** voice can still be **manipulated**. **`REAL` ≠ original recording.**

---

## Scope 3 — Partial Fabrication / Inserted Fake Segment Detection

Detect cases where a **mostly real** recording contains a small AI-generated, converted, cloned, or spliced section.

**Example:** 120 s human audio + 10 s AI/cloned inserted segment.

| Output | Meaning |
|--------|---------|
| `partial_fabrication_detected` | `true` / `false` |
| `suspicious_start_time` | Start of flagged region (seconds) |
| `suspicious_end_time` | End of flagged region (seconds) |
| `suspicious_segment_reason` | Why the segment was flagged |

**Purpose:** Whole-file REAL/FAKE is insufficient; small fake regions can hide inside long real recordings. Requires **chunk-level** analysis (Phase 7A tests this on current pipeline).

---

## Scope 4 — Replay Detection of AI and Human Audio

Detect whether audio was **played through a speaker/device and recorded again**.

| Distinction | Report meaning |
|-------------|----------------|
| **Human replay** | Human-origin; **not** clean/original |
| **AI replay** | AI-origin **plus** replay/channel artifacts |

| Output | Meaning |
|--------|---------|
| `human_origin_replay_risk` | low / medium / high |
| `ai_origin_replay_risk` | low / medium / high |
| `replay_uncertain` | Cannot separate replay from other effects |

---

## Scope 5 — Environmental Acoustic Profiling

Analyze acoustic environment cues to support interpretation:

- Background noise level and consistency  
- Reverberation (RT60)  
- SNR  
- Channel / spectral artifacts  
- Background consistency across chunks  
- Environment stability  

**Purpose:** Supports forensic narrative; current model uses **12 environmental features** per chunk (Phase 2/6).

---

## Scope 6 — Forensic Report Generation

Convert model scores into **safe forensic wording** for reviewers, UI, and API.

Report must include:

| Section | Content |
|---------|---------|
| Report header | File metadata, model id, analysis time |
| Main verdict | Layered origin + manipulation + risk |
| Origin assessment | `origin_label` |
| Manipulation risk | `manipulation_label` |
| Model scores | Binary, decision_score, attack probs |
| Attack probabilities | Auxiliary multiclass hints |
| Suspicious segment timeline | Chunk-level flags |
| Environmental findings | Aggregated env features + reasons |
| Forensic interpretation | Case-based narrative |
| Limitations | Probabilistic nature, quality, domain gaps |
| Recommended next step | e.g. manual review, longer sample |

**Specification:** [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md)  
**Implementation plan:** [pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md](pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md)

---

## Updated Product Goal

| Old goal | New goal |
|----------|----------|
| Detect fake audio | **Analyze authenticity** of a given recording |
| Single REAL/FAKE | **Layered report**: origin + manipulation + segments + reliability + limitations |
| Attack type as verdict | **Attack hint** only (auxiliary) |

---

## Relationship to current implementation

| Scope | Current status |
|-------|----------------|
| 1 | ✅ Baseline via Phase 6 + hybrid model |
| 2 | ⚠️ Partial — rules + attack hints; not trained labels |
| 3 | ❌ Not implemented — **test in Phase 7A** |
| 4 | ⚠️ Inferred from manipulation_type in tests, not dedicated head |
| 5 | ✅ Features extracted; report layer pending (7D) |
| 6 | 📋 Specified; **mandatory Phase 7D** |

---

## Related documents

| Document | Role |
|----------|------|
| [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) | Roadmap and rules |
| [pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md](pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md) | Phase 7A–7F plan |
| [pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) | Controlled testing |
| [NEXT_ACTIONS.md](NEXT_ACTIONS.md) | Immediate checklist |
