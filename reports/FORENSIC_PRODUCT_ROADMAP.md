# FASSD Forensic Voice Authenticity Analyzer — Product Roadmap

**Last updated:** May 2026  
**Status:** Direction document (baseline model exists; forensic product in progress)

---

## 1. Current Product Direction

FASSD is moving from a **simple AI-vs-human voice detector** toward a **Forensic Voice Authenticity Analyzer**.

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

The **current** `HybridResNetEnvironmental` model remains the **baseline detector** for Phase 7A testing. It is **not** the final forensic product by itself.

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
| **7A** | Controlled forensic test suite | **No** | Measure baseline failures by condition |
| **7B** | Controlled local dataset + manifest | Prepare only | Origin + manipulation labels |
| **7C** | Fine-tune current `HybridResNetEnvironmental` | **Yes** (after 7A review) | Domain adaptation on hybrid baseline |
| **7D** | Report generation + UI labels | Optional light | Layered forensic output, wording |
| **7E** | Compare SSL / transformer / AASIST-style + possible ensemble | **Yes** (after 7C) | Second model path vs hybrid; not a replacement without comparison |
| **8** | Product / API / report system | Deploy | End-to-end forensic workflow |

### Phase 7E — transformers / SSL (timing and hardware)

Phase **7E** is **not** deferred only because of GPU limits. It is deferred because the **hybrid baseline must be measured (7A), adapted (7C), and reported (7D)** before adding a second architecture.

**Hardware update:** A **12 GB VRAM** PC is available. After Phase 7A and 7C, the following are **practical** on that machine (with frozen backbone, LoRA/adapters, or small-batch experiments):

- WavLM-base  
- wav2vec2-base  
- AASIST-style or similar spoof-detection front-ends  
- Frozen SSL encoder + trainable head  
- Small SSL ablation runs before any full fine-tune  

**Do not start Phase 7E yet.** No WavLM/AASIST implementation, training, or ensemble until 7A results and 7C hybrid fine-tune are reviewed.

**7E deliverables (when started):** comparative metrics on the same forensic test manifest as 7A, document whether SSL beats hybrid on Urdu/replay/WhatsApp conditions, and only then consider ensemble or replacement.

**Specs:**

- Phase 7A: `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md`
- Phase 7 (legacy domain adaptation): `reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md` (updated structure)
- Report format: `reports/FORENSIC_REPORT_OUTPUT_SPEC.md`

---

## 8. Immediate Rule

> **No new model training, fine-tuning, or architecture replacement until Phase 7A test results are created and reviewed.**

Allowed before 7A review:

- Documentation and templates
- Running **existing** Phase 6 inference on new controlled test files
- Analysis markdown and CSV aggregation (when scripts exist)
- Threshold **experiments** documented as temporary (not permanent product defaults)

Not allowed before 7A review:

- Fine-tuning `hybrid_resnet_environmental_best.pth`
- Any Phase **7E** SSL/transformer/AASIST work (even on 12 GB VRAM)
- Replacing the hybrid with WavLM/AASIST without 7A/7C baseline comparison
- Permanent threshold changes without analysis
- Claiming forensic proof from binary score alone

Not allowed before **7C** review:

- Starting Phase **7E** (transformer/SSL comparison or ensemble)

---

## Related documents

| Document | Purpose |
|----------|---------|
| `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md` | Test plan and manifest |
| `reports/FORENSIC_REPORT_OUTPUT_SPEC.md` | Future report fields |
| `reports/NEXT_ACTIONS.md` | Immediate checklist |
| `reports/PROJECT_STATE_AUDIT.md` | Current repo/model state |
| `reports/FULL_PROJECT_DOCUMENTATION.md` | Technical baseline |
