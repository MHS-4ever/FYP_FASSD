# FASSD Forensic Voice Authenticity Analyzer — Product Roadmap

> **Note:** Phase 7 planning has been reorganized. The canonical Phase 7 documentation now lives in `reports/phase7/`. This file is retained for reference/backward compatibility. See also [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md) and [PHASE7_THESIS_RATIONALE.md](PHASE7_THESIS_RATIONALE.md).

**Last updated:** May 2026  
**Status:** **Phase 7 closed** · **Phase 8 initialized** (multi-axis architecture — planning only)  
**Phase 7 closure:** [phase7/PHASE7_FINAL_CLOSURE_REPORT.md](phase7/PHASE7_FINAL_CLOSURE_REPORT.md)  
**Phase 8 start:** [phase8/PHASE8_START_HERE.md](phase8/PHASE8_START_HERE.md)

---

## Current state (Phase 7 closed → Phase 8)

| Point | Detail |
|-------|--------|
| **Phase 7** | **Closed** — Controlled Forensic Evaluation, Fine-Tuning Attempts, and Architecture Findings. |
| **Accepted prototype (frozen)** | Phase 7C4-v2 **decision-layer fusion** only — not a final product model. |
| **Baseline evidence** | HybridResNet remains useful for replay/mixer/partial — not sufficient alone. |
| **AASIST (7E)** | **Rejected** as current standalone/branch solution — [PHASE7_AASIST_NEGATIVE_FINDING.md](phase7/PHASE7_AASIST_NEGATIVE_FINDING.md). |
| **Architecture finding** | Single binary spoof/fake models are **insufficient** for the forensic product goal. |
| **Phase 8** | **Multi-Axis Forensic Audio Intelligence** — evidence table first; no training until 8A freeze. |
| **Report / web UI** | Phase 7D postponed → planned as **Phase 8G**. |
| **Do not** | Reopen Phase 7 training; train WavLM or new binary models without 8A approval. |

---

## 0. Official scope expansion

The project scope is **officially expanded** from simple AI-vs-human detection to **forensic voice authenticity analysis**.

Full scope definition (six areas): [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md)

| Scope | Topic |
|-------|--------|
| 1 | AI vs human **origin** |
| 2 | **Manipulation** / processing risk |
| 3 | **Partial fabrication** / inserted segments |
| 4 | **Replay** (human-origin vs AI-origin) |
| 5 | **Environmental** acoustic profiling |
| 6 | **Forensic report** generation |

---

## 1. Current Product Direction

FASSD is a **Forensic Voice Authenticity Analyzer** — not only a simple AI-vs-human voice detector.

The system should take an audio file and produce a **forensic-style report** that helps a reviewer understand:

- Whether the **speech origin** is likely human, AI-generated, mixed, or uncertain.
- Whether the **recording** appears clean/original or shows signs of replay, re-recording, editing, channel processing, or platform compression.
- **Which segments** of a long file contribute most to suspicion.
- What **language and limitations** apply so results are not over-claimed.

### Questions the final product should answer

| Question | Future report layer |
|----------|---------------------|
| Is the speech likely **human or AI**? | `origin_label` |
| Is the audio **clean/original** or **suspicious**? | `manipulation_label`, `risk_level` |
| Is there **replay / re-recording** evidence? | `manipulation_label` (e.g. replayed_or_re_recorded) |
| Is there **mixer / channel / codec / platform** processing? | `manipulation_label` (channel_processed, platform_compressed) |
| Is there **editing / splicing** or **partial AI insertion**? | `manipulation_label` (edited_or_spliced, mixed_or_partial_ai) |
| **Which chunks** are suspicious? | Segment timeline in report |
| What should appear in a **forensic-style narrative**? | `final_forensic_interpretation` |

The **current** `HybridResNetEnvironmental` checkpoint remains the **baseline evidence model**. It is **not** the final forensic product by itself. The **accepted prototype** for controlled Phase 7C1 evaluation is the **Phase 7C4-v2 decision layer**, which must be wrapped by **Phase 7D** report wording before any external demo.

---

## 2. Why This Change Is Needed

Real-world and legal/investigative use cases rarely reduce to a single **REAL** or **FAKE** button.

| Scenario | Why binary labels fail |
|----------|-------------------------|
| Market / user need | Stakeholders ask “is this evidence trustworthy?” not only “is this a deepfake?” |
| Human speech, **replayed** through speaker and re-recorded on mobile | Source is human; **recording chain** is not original |
| Human speech, **edited** or spliced | Origin may be human; **integrity** is compromised |
| **AI** speech played through speaker and recorded on phone | Origin is AI; **artifacts** mix synthesis + replay + channel |
| **WhatsApp / YouTube / social** compression | Scores shift; need **platform risk** separate from origin |
| **Mixer / EQ / PA** processing | Human-origin audio can look “synthetic” to artifact detectors |
| **Urdu / Pakistani** and phone domains | Current model underperforms; need measured gaps before training |

A **binary REAL/FAKE** label alone cannot express **origin vs manipulation vs platform effects**.

---

## 3. Current Model Baseline

| Item | Detail |
|------|--------|
| **Model** | `HybridResNetEnvironmental` |
| **Architecture** | `code/phase3/hybrid_resnet_environmental.py` |
| **Checkpoint** | `models_saved/hybrid_resnet_environmental_best.pth` |
| **Inputs** | Log-mel `[64, 400]` + **12** environmental features per 4 s chunk |
| **Binary head** | bonafide (real) vs spoof (fake) |
| **Multiclass head** | bonafide, synthesis, conversion, replay |
| **Inference** | `code/phase6/explain_prediction.py` — 4 s chunks, VAD, pooling |
| **Recommended settings** | `pct_vote`, chunk 0.65, vote 0.70, VAD percentile 40, min speech 0.40 |

Treat this stack as the **baseline detector** whose outputs will be **mapped** into forensic layers (Phase 7D+). Do not treat raw `prediction` as a court-ready verdict.

---

## 4. Known Weaknesses

Documented from Phase 5 evaluation, Phase 6 manual tests, and `reports/PROJECT_STATE_AUDIT.md`:

| Weakness | Impact |
|----------|--------|
| **Pakistani / Urdu** domain | Poor manual accuracy; not represented in training |
| **Phone** domain | ~0 samples in unified manifest domain counts |
| **WhatsApp / mixer / human replay** | No dedicated training labels for these chains |
| **Multiclass attack typing** | ~64% overall; replay/synthesis subclasses unreliable |
| **Processed real audio → FAKE** | High bonafide FPR at 0.5; broadcast/compression confusion |
| **Human replay → REAL** | Correct for *origin* but misleading if user wants “original recording” |
| **Binary-only UX** | Hides manipulation vs origin distinction |

**Conclusion:** Final output must separate **origin assessment** and **manipulation / channel risk**, not only binary prediction.

---

## 5. New Output Philosophy

Future product output uses **layered labels** derived from model scores, rules, and (later) fine-tuned heads.

### `origin_label`

| Value | Meaning |
|-------|---------|
| `human_likely` | Model and rules favor human-generated speech content |
| `ai_likely` | Model and rules favor synthetic/spoof-like speech content |
| `mixed_or_partial_ai` | Evidence of mixed segments or partial insertion (future) |
| `uncertain` | Scores near threshold or conflicting chunk evidence |

### `manipulation_label`

| Value | Meaning |
|-------|---------|
| `clean_original` | No strong replay/channel/edit/platform signals (rare in wild audio) |
| `replayed_or_re_recorded` | Replay / second-hop recording likely |
| `channel_processed` | Mixer, EQ, PA, or chain processing likely |
| `platform_compressed` | WhatsApp/social/codec compression risk |
| `edited_or_spliced` | Editing / splice-like inconsistency (future detection) |
| `environment_mismatch` | Env features inconsistent across chunks |
| `noisy_low_quality` | SNR/quality too poor for confident call |
| `uncertain` | Insufficient or borderline evidence |

### `attack_hint` (auxiliary)

| Value | Maps from model |
|-------|-----------------|
| `bonafide` | Multiclass bonafide |
| `synthesis` | LA-style |
| `voice_conversion` | DF-style conversion |
| `replay` | PA-style replay |
| `unknown` | Low confidence or conflicting |

### `risk_level`

| Value | Typical use |
|-------|-------------|
| `low` | Origin clear; manipulation signals weak |
| `medium` | Borderline scores or moderate channel effects |
| `high` | Strong spoof-like or integrity concerns |
| `inconclusive` | Short audio, VAD dropped most chunks, or near-threshold vote |

### `final_forensic_interpretation`

One or more paragraphs in plain language for the reviewer, following rules in Section 6 and `reports/FORENSIC_REPORT_OUTPUT_SPEC.md`.

### Product rules (mandatory)

1. **Never rely on whole-file REAL/FAKE alone.** Every file-level verdict must be supported by **segment-level** analysis (chunk scores, suspicious timeline) and **forensic interpretation** (Phase 7D).

2. **REAL + replay/conversion/channel artifacts:** Report **“human-origin with manipulation risk”** — not “authentic” or “clean original.”

3. **Mostly human-like + suspicious region(s):** Report **“partial fabrication risk detected”** (or `mixed_or_partial_ai` / `edited_or_spliced` as appropriate) even when pooled vote is REAL. Example: **34 s** file with AI insert **14–21 s** (`T5_FAB_001`) — whole-file may be REAL; chunk inside 14–21 s must show higher spoof/synthesis/conversion than outside (see `phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md`).

4. **Attack hint is auxiliary** — never the sole forensic verdict.

5. **Layered labels are the product output** — binary `prediction` is an internal detector score.

---

## 6. Important Interpretation Rules

1. **Binary REAL** = model judges speech **human-like**; it does **not** guarantee the file is an **original, unmodified** recording.
2. **Binary FAKE** = model sees **spoof/synthetic-like** evidence; it does **not** alone prove **malicious deepfake** or identity fraud.
3. **Attack type** is an **auxiliary hint**, not the final forensic verdict.
4. If binary says **REAL** but attack hint is **conversion** or **replay**, report: *“human-origin audio with manipulation-like or channel/replay artifacts”* — not simply “fake.”
5. **Human → laptop speaker → mobile recording** = **human-origin**, **replayed/processed** manipulation risk.
6. **AI → speaker → mobile recording** = **AI-origin** with **replay/channel** artifacts.
7. **Clean studio human** can look “too clean”; do not auto-label fake without other evidence.
8. **WhatsApp/YouTube compression** affects scores; report **compression/platform risk** separately from origin.

---

## 7. Development Strategy

**Order is fixed.** Do not skip ahead to transformers or ensemble work until earlier phases are reviewed.

| Phase | Name | Training? | Focus |
|-------|------|-----------|--------|
| **7A** | Controlled forensic test suite | **No** | Baseline failures; **partial-fabrication** segment probe |
| **7B** | Forensic dataset + labels | Prepare only | origin, manipulation, partial_fabrication, timeline fields |
| **7C** | Fine-tune `HybridResNetEnvironmental` | **Yes** (after 7A) | Urdu, phone, replay, mixer, WhatsApp, partial AI |
| **7D** | Forensic report layer | Rules/schema done; **implementation postponed** | Wording, timeline, JSON — [phase7d_report_layer/](phase7/phase7d_report_layer/README.md) |
| **7E** | AASIST evidence experiment | **Yes** (after 7E0–7E2 review) | **AASIST first** → WavLM/wav2vec2 later if needed |
| **7F** | Ensemble + final decision logic | After 7E | Late fusion (7E5 v3: HybridResNet + AASIST) |
| **8** | Product / API / report system | Deploy | PDF/HTML, full workflow — **after** stronger evidence |

**Order (updated May 2026):** 7A → 7B → 7C → **7E (evidence)** → 7D implementation → 7F → 8. Do not early-fuse all models. Do not treat 7C4-v2 as final production model.

### Phase 7E — transformers (separate evaluation first)

- **Not** blocked only by GPU — **12 GB VRAM** available.  
- **Blocked by process:** 7E0 planning must be reviewed; then 7E1 smoke + 7E2 adapter before training.  
- Evaluate **AASIST first**, then WavLM-base, then wav2vec2-base if AASIST is insufficient — each standalone vs hybrid on 7C1 + 7A.  
- **No early fusion** into one big model at first.  

### Phase 7F — ensemble

Combine hybrid + best 7E model(s) + chunk timeline + env inconsistency → final report. Only after 7E comparisons.

**Specs:**

- Scope: [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md)  
- Phase 7 master: [pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md](pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md)  
- Phase 7A: [pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md)  
- Phase 7D: [pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md](pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md)  
- Report format: [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md)

---

## 8. Immediate Rule

> **Phase 7C is frozen.** HybridResNet fine-tune experiments are complete; see [phase7/PHASE7C_FINAL_DECISION_RECORD.md](phase7/PHASE7C_FINAL_DECISION_RECORD.md).

> **Phase 7E0:** AASIST planning and locked benchmark — **no training** until 7E1/7E2 review.

**Active work:** Phase **7E0** — AASIST evidence branch planning. Hub: [phase7/phase7e_aasist_experiment/](phase7/phase7e_aasist_experiment/README.md).

**Postponed:** Phase **7D** report generator productization and **Phase 8** web UI until evidence layer improves.

Allowed now:

- Documentation and templates
- Running **existing** Phase 6 inference on new controlled test files
- Analysis markdown and CSV aggregation (when scripts exist)
- Threshold **experiments** documented as temporary (not permanent product defaults)

Not allowed now:

- Fine-tuning or new checkpoint training without updated evaluation plan
- Deploying **7C3-v1**, **standalone R2**, or **7C4-v1** as product scorers
- Claiming final forensic accuracy, court-ready proof, or market-ready automation from 7C4-v2
- Mass **7D** report/demo push before **7E** evidence evaluation improves scores
- AASIST **training** before **7E1** / **7E2** review
- Starting Phase **7F** (ensemble) before **7E** review
- Claiming forensic proof from binary score alone

---

## Related documents

| Document | Purpose |
|----------|---------|
| `reports/UPDATED_PROJECT_SCOPE.md` | Six scope areas (official) |
| `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md` | Test plan and manifest |
| `reports/pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md` | Mandatory report layer |
| `reports/FORENSIC_REPORT_OUTPUT_SPEC.md` | Report field spec |
| `reports/NEXT_ACTIONS.md` | Immediate checklist |
| `reports/PROJECT_STATE_AUDIT.md` | Current repo/model state |
| `reports/FULL_PROJECT_DOCUMENTATION.md` | Technical baseline |
