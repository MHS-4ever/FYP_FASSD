# FASSD Forensic Voice Authenticity Analyzer — Master Product Plan

**Last updated:** May 2026  
**Thesis rationale:** [PHASE7_THESIS_RATIONALE.md](PHASE7_THESIS_RATIONALE.md)  
**Phase 7 canonical docs:** [phase7/README.md](phase7/README.md)  
**Six scope areas:** [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md)

---

## 1. Final Product Goal

The final product accepts an **audio file** and generates a **forensic authenticity report**.

It should answer:

| Question | Report layer |
|----------|----------------|
| Is the speech source **human-likely or AI-likely**? | `origin_label` |
| Is the recording **clean/original** or **manipulated**? | `manipulation_label` |
| Is there **replay / re-recording** evidence? | `manipulation_label`, environmental findings |
| Is there **mixer / channel / platform compression** evidence? | `manipulation_label` |
| Is there **partial AI insertion or splicing**? | `origin_label`, `suspicious_timeline` |
| **Which time segments** are suspicious? | `suspicious_timeline` |
| How **reliable** is the decision? | `risk_level`, `confidence_note`, `limitations` |
| What **limitations** apply? | `limitations` (always present) |

Binary **REAL/FAKE** from Phase 6 remains an **internal detector score**, not the final product verdict.

---

## 2. Final Output Layers

### `origin_label`

| Value | Meaning |
|-------|---------|
| `human_likely` | Speech content favors human origin |
| `ai_likely` | Speech content favors synthetic/spoof-like origin |
| `mixed_or_partial_ai` | Mixed file or partial AI insertion suspected |
| `uncertain` | Borderline or conflicting chunk evidence |

### `manipulation_label`

| Value | Meaning |
|-------|---------|
| `clean_original` | No strong replay/channel/edit/platform signals |
| `replayed_or_re_recorded` | Replay / second-hop recording likely |
| `channel_processed` | Mixer, EQ, PA, or chain processing likely |
| `platform_compressed` | Social/codec compression risk |
| `edited_or_spliced` | Editing or splice-like inconsistency |
| `environment_mismatch` | Environmental features inconsistent across chunks |
| `noisy_low_quality` | Too poor for confident analysis |
| `uncertain` | Insufficient evidence |

### `attack_hint` (auxiliary)

| Value | Meaning |
|-------|---------|
| `bonafide` | Model favors bonafide class |
| `synthesis` | Synthesis-like auxiliary signal |
| `voice_conversion` | Conversion-like auxiliary signal |
| `replay` | Replay-like auxiliary signal |
| `unknown` | Low confidence or conflicting |

### `risk_level`

| Value | Meaning |
|-------|---------|
| `low` | Clear origin; weak manipulation signals |
| `medium` | Borderline or moderate channel effects |
| `high` | Strong spoof-like or integrity concerns |
| `inconclusive` | Short audio, heavy VAD drop, or near threshold |

### `final_forensic_interpretation`

One or more **safe, human-readable paragraphs** for reviewers (see [phase7/PHASE7D_FORENSIC_REPORT_LAYER.md](phase7/PHASE7D_FORENSIC_REPORT_LAYER.md) and [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md)).

### Product rules (mandatory)

1. Never rely on **whole-file REAL/FAKE alone** — use segment-level analysis.  
2. **REAL + replay/channel artifacts** → human-origin with **manipulation risk**, not “authentic.”  
3. **Mostly real + suspicious region** → partial fabrication risk even if whole-file is REAL.  
4. **Attack hint is auxiliary** — not the sole verdict.  
5. **Layered labels are the product output.**

---

## 3. Current Baseline

| Item | Detail |
|------|--------|
| **Model** | `HybridResNetEnvironmental` |
| **Checkpoint** | `models_saved/hybrid_resnet_environmental_best.pth` |
| **Inputs** | Log-mel `[64, 400]` + 12 environmental features per 4 s chunk |
| **Outputs** | Binary real/fake + 4-class attack type |
| **Inference** | `code/phase6/explain_prediction.py` — 4 s chunks, 1 s overlap, VAD, pooling |
| **Recommended settings** | `pct_vote`, chunk 0.65, vote 0.70, VAD percentile 40, min speech 0.40 |

This baseline stays **active** until Phase 7A results show what must improve and Phase 7C fine-tuning is approved.

---

## 4. Development Strategy

| Phase | Name | Training? |
|-------|------|-----------|
| **7A** | Controlled forensic testing (T1–T5) | **No** |
| **7B** | Forensic dataset + labels | Prepare only |
| **7C** | Fine-tune hybrid model | **Yes** (after 7A) |
| **7D** | Forensic report layer | Rules/schema (mandatory) |
| **7E** | AASIST → WavLM → wav2vec2 (separate) | Yes (after 7C, 7D) |
| **7F** | Ensemble + final decision | After 7E |
| **8** | Product / API / PDF/HTML | Deploy |

**Order:** 7A → 7B → 7C → **7D** → 7E → 7F. Do not skip 7D.

Detail per phase: [phase7/PHASE7_MASTER_PLAN.md](phase7/PHASE7_MASTER_PLAN.md).

---

## 5. Model Strategy

1. **Do not replace** the hybrid model immediately.  
2. **Test it properly** (Phase 7A on T1–T5).  
3. **Fine-tune** on local forensic conditions (Phase 7C).  
4. **Separately evaluate** AASIST, WavLM-base, and wav2vec2-base (Phase 7E).  
5. **Keep models separate** at first; document standalone metrics on the same manifest.  
6. **Late fusion / ensemble** (Phase 7F) only if separate results justify it.

---

## 6. Hardware Note

A **12 GB VRAM** PC is available, so transformer and SSL experiments are **practical** in Phase 7E.

They are still **Phase 7E**, not Phase 7A. Delay is **project discipline** (measure gaps, fine-tune hybrid, define report layer first), not only hardware limits.

---

## 7. Immediate Next Action

1. Complete **T1–T5** controlled test cases (audio + manifest).  
2. Include **fabricated / partial AI insertion** audio (e.g. `T5_FAB_001`: 34 s, fake insert **14–21 s**).  
3. Run **Phase 7A** — Phase 6 inference per file; aggregate results; write analysis.  
4. **Do not** fine-tune, run transformers, or build ensemble until 7A is reviewed.

Operational templates: [phase7_forensic_tests/](phase7_forensic_tests/)  
Test guide: [phase7/PHASE7_TEST_CASE_GUIDE.md](phase7/PHASE7_TEST_CASE_GUIDE.md)
