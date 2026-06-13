# Proposed FASSD Thesis Structure

Adapted from the university template for a **computer/audio forensics / machine learning FYP**, not mechanical engineering. Headings use FASSD terminology. Verify against `thesis_layout.pdf` when available.

---

## Front Matter

1. Title Page  
2. Certificate of Approval *(TBD wording)*  
3. Declaration of Originality *(TBD wording)*  
4. Dedication *(optional)*  
5. Acknowledgement  
6. Abstract  
7. Table of Contents  
8. List of Tables  
9. List of Figures  
10. List of Abbreviations  

---

## Abstract

- Context: synthetic speech and audio manipulation  
- Aim: forensic acoustics decision-support for synthetic speech and related manipulations  
- Method summary: datasets, features, model evolution, multi-axis fusion, demo  
- Key results: internal controlled + external test honesty  
- Limitation statement: experimental prototype, manual review required  
- Keywords *(5–7)*  

---

## Chapter 1: Introduction

### 1.1 Motivation
- Proliferation of AI-generated and manipulated audio in media, social platforms, and investigative contexts  
- Limitations of single-score “fake detectors” for real evidence workflows  

### 1.2 Background
- Speech synthesis, voice conversion, and replay attacks  
- Forensic audio analysis vs benchmark anti-spoofing  
- FASSD project origin as FYP  

### 1.3 Problem Statement
- Why binary classification alone is insufficient in practice (extended finding)  
- Align official proposal problem (synthetic speech risk) with extended forensic need  
- **Source:** Proposal form; `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`; Phase 7 rationale  

### 1.4 Approved Scope and Extended Development Boundary
- **Official scope:** proposal form summary (LCNN, ASVspoof, LFCC/log-mel, software deliverable)  
- **Extended scope:** multi-axis evidence, reports, demo tooling, Next.js intended frontend  
- **Boundary rule:** official scope achieved first; extensions documented separately  
- **Source:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`  

### 1.5 Objectives

#### 1.5.1 Official approved objectives (proposal form)
1. ML model: bonafide/human vs spoof/AI-generated  
2. Forensic audio cues (noise, reverberation, channel artifacts)  
3. Deepfake voice embedded in real recordings  
4. Replayed synthetic speech detection  
5. Robust evaluation pipeline (augmented + real-world tests)  
6. Complete software-based deepfake speech detection system  

#### 1.5.2 Extended implementation objectives
- Multi-axis evidence (origin, replay, mixer, partial)  
- Forensic-safe structured reports (JSON/MD/PDF)  
- Manual review and abstention logic  
- Local Gradio/FastAPI testing interface  
- Next.js web frontend as intended final deployment UI  
- Controlled forensic evaluation and release audit honesty  

### 1.6 Scope
- **Official in scope:** per proposal form §4 in `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`  
- **Extended in scope:** Phase 7–9 architecture, release audit, demo tooling  
- **Out of scope:** legal proof; NCCIA endorsement unless confirmed  

### 1.7 Environment and Sustainability
- Large-scale ASVspoof training energy/compute considerations  
- Responsible deployment: triage not automated verdict  
- *(Expand with supervisor guidance — TBD)*  

### 1.8 Relevance to Sustainable Development Goals (SDGs)
- SDG 9: innovation in trustworthy AI tools  
- SDG 16: supporting integrity of information/evidence chains  
- *(Wording must avoid overclaiming legal outcomes — TBD)*  

### 1.9 Thesis Outline
- Brief description of Chapters 2–5 and appendices  

---

## Chapter 2: Literature Survey

### 2.1 Introduction

### 2.2 Deepfake Audio and Synthetic Speech
- TTS, VC, neural vocoders, generative AI voice  

### 2.3 Audio Anti-Spoofing and Presentation Attacks
- Logical access, deepfake, physical access/replay  

### 2.4 ASVspoof Datasets and Evaluation Protocols
- LA, DF, PA; EER-centric evaluation culture  

### 2.5 Spectral and Cepstral Features
- LFCC, MFCC, log-mel spectrograms  

### 2.6 Convolutional and Residual Network Approaches
- LCNN, ResNet-style spectrogram classifiers  

### 2.7 Graph Attention and AASIST-Class Models
- Spectrogram-temporal modeling; vendor/pretrained use in FASSD Phase 7E  

### 2.8 Self-Supervised Speech Embeddings
- wav2vec2 / WavLM-style representations for origin evidence  

### 2.9 Replay, Channel, and Environmental Artifacts
- Double reverberation, codec, mixer, platform compression  

### 2.10 Partial Fabrication and Segment-Level Localization
- Splicing, partial AI insertion, inside/outside region analysis  

### 2.11 Research Gaps
- Benchmark vs forensic product gap (`reports/PHASE7_THESIS_RATIONALE.md`)  

### 2.12 Problem Statement (Formal)
- Consolidated statement for FASSD multi-axis forensic prototype  

### 2.13 Chapter Summary

---

## Chapter 3: Methodology

### 3.1 Research Design Overview
- Start from **approved LCNN/ASVspoof proposal plan**  
- Document experimental evolution to extended multi-axis system  
- **Source:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`; `PROJECT_STORY_FROM_DAY_ONE.md`  

### 3.2 System Architecture Overview
- **Official baseline path:** features → classifier → metrics  
- **Extended path:** multi-axis parallel evidence → fusion → reports  
- **Source:** Phase 8A freeze + proposal comparison  

### 3.2A Deployment Architecture
- **Backend:** inference + report pipeline (`release/`, FastAPI)  
- **Gradio/FastAPI (release/):** experimental local demo and **testing interface only**  
- **Next.js frontend:** intended final user-facing web application (`reports/website/PARTNER_INTEGRATION_GUIDE.md`)  
- **Thesis rule:** do not present Gradio as final submission application  

### 3.3 Dataset Collection and Preparation
- ASVspoof LA/DF/PA integration  
- RealWorld broadcast/podcast/social/read speech  
- Augmentation (MUSAN, RIR, codec, gain, clipping)  
- Unified dataset statistics and speaker-independent splits  
- Phase 7C1 controlled forensic corpus (8 conditions)  
- Phase 7A holdout / `testing_audios`  

### 3.4 Audio Preprocessing and Segmentation
- Resampling, normalization, chunking, VAD  

### 3.5 Feature Extraction
- LFCC and log-mel extraction and HDF5 packing  
- Twelve environmental acoustic features  
- Frozen SSL embeddings  
- Acoustic/channel features for replay and mixer  
- Segment features for partial fabrication (combined_no_f9)  

### 3.6 Baseline CNN / LCNN Experiments (Phase 3) — **Official scope alignment**

### 3.7 Log-Mel ResNet Experiments (Phase 4.2) — **Extension beyond LCNN plan**

### 3.8 Environmental Feature Experiments (Phase 4.3)
- Anomaly vs supervised environmental classifiers  

### 3.9 HybridResNetEnvironmental Model (Phases 3–5)
- Architecture, training, multi-task heads  

### 3.10 Phase 6 Inference and Explanation Layer
- Chunk pooling, attack-type head, raw-audio CLI  

### 3.11 Phase 7 Controlled Forensic Evaluation
- 7A tests, 7C1 baseline, 7C3 fine-tunes, 7C4 fusion, 7E AASIST  

### 3.12 Phase 8 Multi-Axis Evidence Models
- 8B evidence table, 8C acoustic features, 8D SSL, 8E axis LR models, 8F fusion, 8G reporting  

### 3.13 Partial Fabrication and Segmentation Method
- Window scoring, oracle metrics, F9 removal (Phase 5 audit)  

### 3.14 Release Audit Repairs (2026-06-13)
- Phase 2 origin retrain, Phase 3 ablations, Phase 4 stop, Phase 5 partial, Phase 6 calibration  

### 3.15 Phase 9 Local Demo and Testing Interface
- Gradio/FastAPI in `release/` — **not final frontend deliverable**  

### 3.16 Next.js Web Frontend (Intended Final Deployment)
- Dashboard upload UI, API integration, optional Firebase — **ongoing if incomplete at submission**  

### 3.17 Fusion and Forensic Report Layer
- Evidence bands, manual review rules, wording templates  

### 3.18 Tools, Hardware, and Software Environment

### 3.19 Ethical Considerations and Dataset Integrity
- Holdout policy, leakage control, non-legal-use disclaimer  

### 3.20 Chapter Summary

---

## Chapter 4: Results and Discussion

### 4.1 Introduction
- Separate **official-scope results** and **extended-system results**

### 4.2 Baseline CNN / LCNN Results — **Official scope**

### 4.3 LFCC vs Log-Mel Comparison

### 4.4 Deep ResNet Results and Domain Mismatch Finding

### 4.5 Environmental Classifier Results

### 4.6 Unified Dataset Statistics and HybridResNetEnvironmental Evaluation

### 4.7 Phase 7 Controlled Forensic Results
- Hybrid baseline, 7C4-v2 prototype, clean-human false alarms  

### 4.8 AASIST Experiment Results and Rejection Rationale

### 4.9 Phase 8 Axis Model Results (Origin, Replay, Mixer)

### 4.10 Release Audit Results
- Origin Phase 2, Phase 3 ablation closures, Phase 4 failure, Phase 5 partial success  

### 4.11 Final Release Matrix on External testing_audios

### 4.12 Phase 9 Demo Freeze Validation Results

### 4.13 Limitations and Failure Case Analysis

### 4.14 Discussion Against Literature
- *(Requires references — TBD)*  

### 4.15 Chapter Summary

---

## Chapter 5: Conclusion and Future Work

### 5.1 Introduction

### 5.2 Objective-Wise Conclusions
- **Official objectives (proposal):** software ML system, bonafide/spoof classification, forensic cues, replay/embedded deepfake scenarios, EER/AUC evaluation  
- **Extended objectives:** multi-axis evidence prototype, structured reports, demo testing interface, intended Next.js deployment  

### 5.3 Major Contributions

### 5.4 Limitations

### 5.5 Future Work
- Complete and validate Next.js final frontend integration  
- Broader validation of extended forensic modules (mixer/replay generalization)  
- Dataset expansion; operational validation beyond demo interfaces  

### 5.6 Closing Remarks

---

## References

- Numbered list per university style (**TBD**)

---

## Appendices

### Appendix A: Sample Forensic Report Outputs (JSON / Markdown / PDF excerpt)

### Appendix B: Phase 7C1 Forensic Condition Definitions

### Appendix C: Full testing_audios Evaluation Matrix

### Appendix D: API Contract Summary

### Appendix E: Additional Figures and Confusion Matrices

### Appendix F: Model Registry and Threshold Summary *(optional)*

---

## Structural Notes

| Template expectation | FASSD adaptation |
|---------------------|------------------|
| Mechanical engineering methods | Audio ML + forensic evidence engineering |
| Single system prototype | Official LCNN software deliverable + extended multi-axis prototype |
| Problem in Ch. 2 only | Official problem in Ch. 1; extended gap in Ch. 2 |
| Results as metrics only | Official-scope EER tables + extended failure tables |
| One UI deliverable | Gradio = demo/testing; Next.js = intended final frontend |
