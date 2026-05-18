# Why Phase 7 Is Needed — Thesis Rationale

**Project:** FASSD — Forensic Voice Authenticity Analyzer  
**Status:** Phase 7A, 7B, 7C0 signed off — Phase 7C1 active  
**Canonical Phase 7 docs:** [phase7/README.md](phase7/README.md)

---

## 1. Background

FASSD began as a **synthetic and deepfake speech detection** project. Earlier phases established a complete pipeline: unified dataset construction, log-mel and environmental feature extraction, training, formal evaluation, and raw-audio inference.

The working model is **HybridResNetEnvironmental** (`code/phase3/hybrid_resnet_environmental.py`). It combines:

- **Log-mel spectrogram** analysis (4 s chunks, ResNet branch) for synthetic-speech artifacts  
- **Twelve environmental acoustic features** (noise, reverb, SNR, stability, etc.) for recording-context cues  

Phase 6 inference (`code/phase6/explain_prediction.py`) produces **REAL/FAKE** predictions with chunk pooling, VAD, and an auxiliary **attack-type** head (bonafide, synthesis, conversion, replay).

This stack is a strong **baseline detector**, but **forensic audio analysis** requires more than a single binary label.

---

## 2. Why Binary REAL/FAKE Is Not Enough

| Label | What it actually means | What it does **not** mean |
|-------|------------------------|---------------------------|
| **REAL** | Speech content is **human-like** under the model | Original, unedited, court-ready, or free of replay/compression |
| **FAKE** | **Spoof/synthetic-like** evidence in the model | Legally proven malicious fabrication or identity fraud |

Real evidence may be **replayed** through a speaker, **re-recorded** on a phone, **compressed** on WhatsApp, **edited** or spliced, or **partially fabricated** (mostly real with a short AI insert). AI-generated speech may also be replayed or shared through platforms, mixing synthesis and channel artifacts.

The product must assess **authenticity and manipulation risk**, not only **speech origin**.

---

## 3. Market / Practical Need

Users of a forensic voice product need a **report**, not only a button:

- **Investigators** need to know *what* is suspicious and *where* in the timeline.  
- **Journalists and reviewers** need safe language that does not over-claim proof.  
- **Organizations** need separation of **origin** (human vs AI-like) from **integrity** (clean vs replayed/processed/edited).  

Audio can be manipulated **without** being AI-generated (replay, splice, mixer). AI-generated audio can be **replayed or platform-compressed**, changing acoustic evidence. The system must assess **both origin and manipulation risk**.

---

## 4. What Phase 7 Adds

Phase 7 upgrades FASSD from a classifier to a **forensic authenticity analyzer**:

| Component | Phase |
|-----------|--------|
| Controlled forensic test suite (T1–T5) | 7A |
| Local/domain-specific test cases | 7A |
| Partial fabrication / segment timeline analysis | 7A, 7D |
| Forensic label schema | 7B, [PHASE7_LABEL_SCHEMA.md](phase7/PHASE7_LABEL_SCHEMA.md) |
| Forensic report layer (safe wording, JSON) | 7D |
| Hybrid model fine-tuning on measured gaps | 7C |
| Optional AASIST / WavLM / wav2vec experiments | 7E |
| Late fusion / ensemble decision logic | 7F |

**Fixed order:** 7A → 7B → 7C → 7D → 7E → 7F → Phase 8 (product/API).

---

## 5. Research Gap Addressed

Many published detectors focus on **AI-vs-human classification** on benchmark corpora (e.g. ASVspoof). Real forensic audio also requires:

- **Environmental consistency** across segments  
- **Replay** and re-recording detection  
- **Compression and platform** awareness  
- **Partial manipulation** (inserted synthetic segments inside long real recordings)  

FASSD is positioned as a **forensic authenticity analyzer**—combining origin detection, environmental profiling, and structured reporting—rather than a simple binary classifier.

---

## 6. Why Environmental Features Still Matter

Environmental cues help detect:

- **Replay** and double-hop recording  
- **Room or background changes** across chunks  
- **Channel effects** (mixer, PA, device coloration)  
- **Unnatural cleanliness** or inconsistency  

They support **explainable reports** (“why this file looks suspicious”) even if later phases add transformer or attention-based models. Environmental features remain part of the hybrid baseline and can inform the report layer and ensemble.

---

## 7. Why Controlled Test Cases Are Needed Before Fine-Tuning

| Risk without 7A | Mitigation |
|-----------------|------------|
| Unknown failure modes (Urdu FPs, human-replay REAL calls) | Measure per condition first |
| Fine-tuning that helps one domain, hurts another | Targeted 7C only after 7A gaps |
| Wrong labels or thresholds | Evidence from `forensic_test_results.csv` |

Controlled tests reveal whether the issue is **AI detection**, **replay**, **compression**, **language**, **phone recording**, **mixer processing**, or **partial fabrication**. **Phase 7A must complete before training** (7C) or transformer work (7E).

---

## 8. Expected Thesis Contribution

1. A **hybrid forensic pipeline** combining speech-origin detection (log-mel ResNet) and **environmental acoustic profiling**.  
2. A **layered forensic label system** (`origin_label`, `manipulation_label`, `attack_hint`, `risk_level`) instead of a single binary output.  
3. A **controlled forensic test suite** covering clean, replayed, processed, compressed, and partially fabricated audio (T1–T5).  
4. A **report-generation layer** that maps model scores to safe forensic wording and segment timelines.  
5. A **future-ready architecture** that can compare the hybrid baseline with transformer/attention models (7E) and late fusion (7F).

---

## 9. Current Phase 7 Decision

**Completed (signed off):** Phase **7A** (controlled forensic testing), Phase **7B** (forensic label schema on T1–T5 holdout), Phase **7C0** (legacy training dataset audit).

**Immediate next step:** **Phase 7C1** — new forensic data collection plan and recording.

**Do not start until 7C1 data is collected and validated:**

- Model fine-tuning (7C)  
- Transformer experiments (7E)  
- Ensemble / late fusion (7F)  

### Thesis-style summary (post–7A/7B/7C0)

After controlled testing and the legacy dataset audit, the project found that the current **HybridResNetEnvironmental** model is **technically functional** but **product-mismatched**: it is sensitive to **manipulation artifacts** (replay, channel processing) yet tends to **confuse processed human audio with AI-origin spoofing** when interpreted through binary REAL/FAKE alone. Segment-level evidence and separate **origin** vs **manipulation** handling are required, together with **local forensic data** (Urdu/Pakistani, phone, WhatsApp, partial insertion) before fine-tuning. This justifies **Phase 7C1** as a necessary step before model improvement — not fine-tuning directly on the existing ~1.89M-row studio/replay-heavy corpus.

See [phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md) and [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md).
