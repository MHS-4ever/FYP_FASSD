# FASSD Thesis Section Notes

**Purpose:** Per-heading rough notes for thesis writing — one block per heading in `FASSD_Thesis_Structure.md`.  
**Primary software deliverable (user-facing):** Live web platform at https://www.deepfakedetection.dev/ (separate hosting repo — **not** in `E:\FYP` git).  
**ML/research repo:** `E:\FYP` — training, evaluation, `release/` inference backend source.  
**Website/deployment story:** `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`  
**Rule:** Experimental forensic decision-support prototype — not court-ready proof.  
**Citation placeholders:** use `[cite: R1]` during drafting.


---

## Writing Length Control Guide

Use the targets below to prevent overwriting or making any thesis heading too long. The word counts are approximate and apply to the final paragraph text only. Tables, figures, captions, equations, references, and appendix extracts are not counted in the word limit.

**General rules:**
- Small front-matter sections should stay short and template-based.
- Chapter 1 sections should usually be 2–3 paragraphs.
- Chapter 2 literature sections may be longer because they need citations and comparison.
- Chapter 3 methodology sections should explain what was built without becoming a code manual.
- Chapter 4 result sections should combine numbers with interpretation, not repeat every log.
- Chapter 5 should be concise and honest.
- If a required table or figure is present, reduce paragraph length by 15–25%.
- Do not expand a heading only to fill space. If the documented material is limited, write less and add a note for missing information.

---

## Front Matter

### Title Page

**Length target:** Template page only; no thesis paragraph. Use confirmed names, registration numbers, supervisor, department, institute, and date.

**Write:**
- Project title: **Forensic Acoustics for Synthetic Speech Detection (FASSD)**
- Students: Rana M. Areeb, M. Hasnain
- Registration numbers: **MISSING / NEEDS CONFIRMATION**
- Supervisor: Sir Faran Mehmood
- Department: Computing; Institute: Institute of Space Technology (IST)
- Submission: June 2026

**Sources:** `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.docx`, title defence materials in `submissions/title defence/`

**Do not invent:** registration numbers, co-supervisor unless confirmed

---

### Approval by Board of Examiners

**Length target:** Template page only; no thesis paragraph. Follow the official IST format.

**Write:** IST official approval page with signature blocks for supervisor, examiners.

**Sources:** University thesis template — **MISSING in repo** (`thesis_layout.pdf` TBD)

---

### Authors' Declaration

**Length target:** 120–180 words, usually 1 paragraph, unless the university template provides fixed wording.

**Write:** Standard IST originality declaration; work completed under supervision; sources acknowledged.

**Note:** Mention that extended multi-axis work exceeds original proposal but is documented as extension, not replacement.

---

### Certificate

**Length target:** Template/certificate wording only, usually 80–150 words or as provided by IST.

**Write:** Supervisor certificate page per IST format.

---

### Copyright Page

**Length target:** Template page only; use official wording if provided.

**Write:** University template copyright wording.

---

### Dedication

**Length target:** 30–80 words, 1 short paragraph. Keep personal and simple.

**Write:** Personal — no repo source.

---

### Acknowledgement

**Length target:** 250–350 words, 3 paragraphs. Keep it sincere, not exaggerated.

**Write:**
- Supervisor Sir Faran Mehmood
- IST Computing department
- Teammate collaboration (Rana M. Areeb & M. Hasnain)
- External consultation: neutral wording only — **NCCIA only if supervisor approves** (`16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`)

**Avoid:** NCCIA as continuing official partner without confirmation

---

### Abstract

**Length target:** 200–250 words, preferably 1 paragraph unless the template allows 2 short paragraphs. Do not cite unless the university specifically requires citations in the abstract.

**Write (200–250 words):**
- **Problem:** AI synthetic speech threatens identity verification and digital trust; forensic review needs structured evidence, not one binary score
- **Method:** Approved ASVspoof LCNN/LFCC/log-mel pipeline → extended multi-axis forensic architecture (origin, replay, mixer/channel, partial fabrication) with fusion and evidence-band reporting
- **Implementation:** ML pipeline in FYP repo; **deployed web application** at deepfakedetection.dev (Next.js/Vercel + Phase 9 API on DigitalOcean + Firebase) — **separate hosting repo**
- **Results:** Key EER milestones (LCNN 15.71% aug; ResNet 2.61% aug; Hybrid 16.21% test EER); final testing_audios matrix (origin BA 0.825, etc.)
- **Contribution:** Documented path from benchmark anti-spoofing to experimental forensic decision-support prototype
- **Limitation:** Not court-ready; manual review required

**Sources:** §13 metrics in `FASSD_THESIS_ROUGH_NOTES.md`, release audit matrix

**Forbidden in abstract:** proves fake, court-ready, detects all deepfakes

---

### Table of Contents

**Length target:** Auto-generated; no manual paragraph.

**Write:** Auto-generate after final Word/LaTeX formatting.

---

### List of Tables

**Length target:** Auto-generated; no manual paragraph.

**Write:** Auto-generate. Expected tables: Official vs Extended Scope, Dataset Summary, ASVspoof Tracks, Research Gaps, Feature Sets, Final Axis Results, Objectives vs Achieved, Limitations.

---

### List of Figures

**Length target:** Auto-generated; no manual paragraph.

**Write:** Auto-generate. Expected: workflow, multi-axis architecture, deployment architecture, phase evolution, ROC/confusion (appendix), **website screenshots** (landing, dashboard, results, waveform).

---

### List of Abbreviations

**Length target:** Table/list only; no paragraph required unless the template asks for a short note.

**Include:** FASSD, AI, ASVspoof, LA, DF, PA, LFCC, MFCC, LCNN, CNN, ResNet, AASIST, SSL, EER, AUC, VAD, API, UI, JSON, PDF, SNR, RT60, SDG, BA (balanced accuracy), WavLM (if cited)

**Source:** `submissions/thesis_preparation/08_ABBREVIATIONS.md` if present

---

## Chapter 1: Introduction

### 1.1 Motivation

**Length target:** 300–450 words, 2–3 paragraphs. Keep broad motivation first, then connect directly to FASSD.

**Write:**
- AI voice cloning → fraud, impersonation, misinformation
- Binary “fake detector” insufficient for forensic triage
- Need for software tools that support **human review** with structured acoustic evidence
- FYP framed as cybersecurity / digital trust software project

**Citations:** RA1, RA2 (`research_article/`, `09_REFERENCES_RESEARCH_GAP_PLAN.md`)

**Figures/tables:** None required

---

### 1.2 Background

**Length target:** 350–500 words, 2–3 paragraphs. Keep high-level; leave detailed literature for Chapter 2.

**Write:**
- Synthetic speech (TTS, VC, deepfake audio)
- Spoofing vs bonafide; replay attacks; partial edits
- ML/audio anti-spoofing as standard approach
- High-level only — detail in Ch 2

**Citations:** Surveys RA1–RA3

---

### 1.3 Problem Statement

**Length target:** 300–450 words, 2–3 paragraphs. End with the exact FASSD problem focus.

**Write:**
- Official problem (proposal): classify bonafide vs spoof/AI using spectral + forensic acoustic cues; detect embedded AI voice; detect replayed AI speech
- Extended problem discovered in implementation: real-world domain mismatch; need separate evidence for origin, replay, channel, partial fabrication
- Thesis problem = approved scope **plus** documented extensions

**Sources:** Proposal form, `README.md`, `FASSD - Scope.md`

---

### 1.4 Approved Scope and Extended Development Boundary

**Length target:** 450–650 words, 3–4 paragraphs plus one table. Explain official scope first, then extended work.

**Write:**
- **First:** official IST proposal scope (LCNN, LFCC, log-mel, ASVspoof DF+LA, augmentation, EER/AUC, software tool)
- **Then:** extended work (multi-axis models, fusion, reports, **deployed web platform**)
- Do **not** say official scope was replaced

**Required table:** Official Scope vs Extended Development Work

**Sources:** `submissions/thesis_preparation/16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`

**Table rows (minimum):**
| Area | Official | Extended |
|------|----------|----------|
| Classifier | LCNN binary | Multi-axis evidence models |
| Features | LFCC, log-mel | + environmental, SSL |
| Interface | Software tool for external audio | **Web app deepfakedetection.dev** (separate repo) |
| Evaluation | EER, AUC | + controlled forensic matrix, release audit |

---

### 1.5 Project Objectives

**Length target:** 350–500 words, 2–3 paragraphs plus objective bullets/table if needed.

#### 1.5.1 Official Approved Objectives

**Length target:** 200–300 words or a compact table. Keep objective status factual.

**Write (from proposal):**
1. Bonafide vs spoof/AI classification — **achieved** (LCNN/CNN pipeline)
2. Forensic acoustic cues — **achieved/extended**
3. AI voice embedded in real recordings — **partial / manual-review** (partial fabrication axis)
4. Replay of AI through device — **achieved as evidence axis** (not legal proof)
5. Robust augmented + real-world evaluation — **achieved/extended**
6. Complete software system — **achieved via deployed web platform** + ML backend

**Source:** Proposal form via `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §3

#### 1.5.2 Extended Implementation Objectives

**Length target:** 200–300 words or a compact table. Separate extended work from approved proposal.

**Write:**
- Multi-axis evidence (origin, replay, mixer/channel, partial fabrication)
- Fusion + abstention + safe wording
- Structured JSON/report outputs with evidence bands
- **Deployed web-based frontend** integrated with Phase 9 inference API — **complete** at deepfakedetection.dev
- Separate **website hosting repository** (not merged into FYP ML git)

**Do not write:** “local testing interface” as primary deliverable — web platform is the user-facing software representation for thesis/defense

**Source:** `FRONTEND_AND_DEPLOYMENT_STORY.md`

---

### 1.6 Scope of the Study

**Length target:** 300–450 words, 2–3 paragraphs. Clearly separate in-scope and out-of-scope.

**Write — in scope:**
- Dataset preparation (ASVspoof, augmentation, RealWorld, unified stats)
- Feature extraction (LFCC, log-mel, environmental, SSL)
- Model training experiments (CNN, ResNet, Hybrid, AASIST, multi-axis)
- Evaluation (EER, controlled forensic, release audit matrix)
- Final evidence system + report layer
- **Web software interface** (primary) — upload, four evidence cards, waveform, auth/history

**Out of scope:**
- Court/legal certification
- Universal deepfake detection guarantee
- Speaker identification ASV product

---

### 1.7 Development Model

**Length target:** 300–450 words, 2–3 paragraphs plus one phase-flow figure if available.

**Write:**
- Hybrid **iterative-incremental** with phase-gated accept/reject decisions
- Each phase: train → evaluate → discover failure → pivot (documented in `PROJECT_STORY_FROM_DAY_ONE.md`)
- Prototyping: binary CNN → ResNet → Hybrid → multi-axis → release audit → **web deployment**

**Required figure:** FASSD Iterative-Incremental Development Flow (phases 1–9 + web platform)

**Key pivots to show:** broadcast failure, Phase 7 rejections, release audit origin/partial repair, Phase 9 → production web

---

### 1.8 Environment and Sustainability

**Length target:** 180–280 words, 1–2 paragraphs. Keep concise and realistic.

**Write:**
- Software-only deliverable (no hardware product waste)
- GPU training energy — mention responsible use briefly
- Cloud hosting (Vercel hobby, DO droplet with student credit) vs on-premise alternative

**Keep concise**

---

### 1.9 Relevance to Sustainable Development Goals

**Length target:** 180–280 words, 1–2 paragraphs. Do not overclaim impact.

**Write (brief):**
- SDG 9: innovation, digital infrastructure (web-based detection tool)
- SDG 16: institutions, trust, reduced misinformation risk (decision-support only)

**Do not overclaim global impact**

---

### 1.10 Thesis Outline

**Length target:** 180–250 words, 1 paragraph. Briefly preview chapters only.

**Write:** One paragraph: Ch2 literature → Ch3 methodology & system design (incl. **web deployment**) → Ch4 results → Ch5 conclusion → appendices (proposal, API, screenshots, configs)

---

## Chapter 2: Literature Survey

### 2.1 Historical Background

**Length target:** 400–600 words, 3–4 paragraphs. Use citations for field history and prior work.

**Write:** Speech synthesis evolution → neural TTS → voice conversion → spoofing countermeasures → audio deepfakes

**Citations:** RA1, RA2, RA3

---

### 2.2 Synthetic Speech and Audio Deepfakes

**Length target:** 450–650 words, 3–4 paragraphs. Explain TTS/VC/deepfake audio at a high level.

**Write:** How AI speech is generated (high level); cloning; detection difficulty under compression/replay/partial edit

**Citations:** RA2, RA4

---

### 2.3 Audio Anti-Spoofing

**Length target:** 400–600 words, 3–4 paragraphs. Define bonafide/spoof, CM, score, and EER.

**Write:** Bonafide/spoof formulation; score thresholds; EER; CM pipeline

**Citations:** RA1 — link to FASSD official scope

---

### 2.4 ASVspoof Dataset and Evaluation Tracks

**Length target:** 450–650 words, 3–4 paragraphs plus one table. Cite official ASVspoof sources.

**Write:**
- LA (logical access), DF (deepfake), PA (physical access/replay)
- Why FASSD used all three in unified dataset

**Required table:** ASVspoof Tracks and Relevance to FASSD

| Track | FASSD use | Samples (unified) |
|-------|-----------|-------------------|
| LA | Baseline training | 181,566 |
| DF | Deepfake synthesis | 611,829 |
| PA | Replay coverage | 943,110 |
| RealWorld | Domain extension | 157,414 |

**Source:** `data/statistics/unified_dataset_stats.json`

**Citation needed:** Official ASVspoof 2021 paper — **TBD / NEEDS VERIFICATION**

---

### 2.5 Audio Features for Deepfake Detection

**Length target:** 500–700 words, 4–5 paragraphs. Cover LFCC, MFCC/log-mel, and acoustic cues.

**Write:** LFCC, MFCC, log-mel; environmental/acoustic cues; why FASSD compared LFCC vs log-mel

**Citations:** RA1, RA7

---

### 2.6 Deep Learning Models for Audio Detection

**Length target:** 450–650 words, 3–4 paragraphs. Cover CNN/LCNN/ResNet/hybrid ideas.

**Write:** CNN/LCNN, ResNet-style, hybrid fusion — maps to FASSD experiments

**Citations:** RA7, ASVspoof baselines TBD

---

### 2.7 Data Augmentation and Real-World Robustness

**Length target:** 400–600 words, 3–4 paragraphs. Include augmentation limits.

**Write:** MUSAN noise, RIR reverb, codec, gain — FASSD used +611,829 augmented samples; limits of augmentation-only robustness (project lesson)

**Citations:** MUSAN/RIR papers — **TBD**

---

### 2.8 Advanced Anti-Spoofing and SSL-Based Methods

**Length target:** 450–650 words, 3–4 paragraphs. Cover AASIST and SSL embeddings without overclaiming.

**Write:** AASIST; WavLM/wav2vec2/Whisper embeddings; FASSD origin axis uses SSL (WavLM-style)

**Citations:** AASIST TBD, RA9, WavLM TBD

**Note:** AASIST tested but **rejected** as active model in FASSD

---

### 2.9 Forensic Audio Cues and Manipulation Evidence

**Length target:** 450–650 words, 3–4 paragraphs. Keep replay/channel separate from AI origin.

**Write:** Replay signatures, noise/reverb mismatch, device/channel effects; why separated from synthesis detection

**Citations:** RA1, RA2; forensic audio lit TBD

**Critical thesis rule:** Replay/mixer evidence ≠ AI-generated

---

### 2.10 Partial Fabrication and Segment-Level Analysis

**Length target:** 400–550 words, 3 paragraphs. Explain why segment analysis is needed.

**Write:** File-level scores miss localized synthetic inserts; segment oracle evaluation

**Citations:** RA6 (arXiv:2505.13847 — verified in prep doc)

**FASSD:** partial axis = experimental manual-review candidate only

---

### 2.11 Research Gaps

**Length target:** 500–700 words, 3–4 paragraphs plus one gap table. Connect each gap to FASSD response.

**Write gaps:**
1. Binary benchmark focus vs forensic product needs
2. Benchmark EER ≠ real broadcast/platform success
3. Need multi-axis evidence for origin/replay/channel/partial

**Required table:** Research Gaps and FASSD Response

| Gap | FASSD response |
|-----|----------------|
| Single fake/real score | Four evidence axes + fusion |
| ASVspoof-only domain | RealWorld + controlled forensic testing |
| No user-facing forensic report | Evidence-band reports + web UI |

**Source:** Phase 7/8 docs, RA5

---

### 2.12 Summary of Literature Survey

**Length target:** 250–350 words, 2 paragraphs. Summarize and transition to methodology.

**Write:** Literature supports official LCNN scope AND motivates extended multi-axis + web-based software deliverable; transition to Ch3

---

## Chapter 3: Methodology And System Design

### 3.1 Overview of Methodology

**Length target:** 300–450 words, 2–3 paragraphs plus one workflow figure.

**Write:** End-to-end: datasets → features → models → multi-axis inference → fusion → reports → **web/API output**

**Required figure:** Overall FASSD Workflow (include browser upload → API → four axes → UI cards)

**Sources:** `PHASE8A_ARCHITECTURE_FREEZE.md`, `FRONTEND_AND_DEPLOYMENT_STORY.md` §8

---

### 3.2 Research Design

**Length target:** 300–450 words, 2–3 paragraphs. Explain experimental and iterative design.

**Write:** Experimental ML; hypothesis-test-pivot; documented accept/reject per phase (`PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`)

---

### 3.3 Official Approved Methodology

**Length target:** 350–500 words, 2–3 paragraphs. Keep it tied to proposal scope.

**Write (from proposal):**
- ASVspoof 2021 DF + LA
- LFCC (20-D), Log-Mel (64-D)
- LCNN classifier
- Augmentation: MUSAN, RIR, codec
- Metrics: EER, ROC-AUC, accuracy, confusion matrices
- Software tool for external test audio

**Source:** Proposal form — `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §4

---

### 3.4 Extended Methodology

**Length target:** 400–600 words, 3–4 paragraphs. Explain extensions as evidence from project evolution.

**Write:** ResNet, environmental features, HybridResNetEnvironmental, AASIST trial, Phase 7 controlled forensic testing, multi-axis freeze, release audit, **production web deployment**

**Frame as:** extensions after limitations discovered — not replacement of approved plan

---

### 3.5 Dataset Preparation

**Length target:** 500–700 words, 3–4 paragraphs plus dataset table. Use exact documented counts.

**Write:** Manifests, label schema, unified dataset merge

**Required table:** Dataset Summary — see `FASSD_THESIS_ROUGH_NOTES.md` §6

**Key stat:** 1,893,919 total samples; studio-dominated domains

**Source:** `data/statistics/unified_dataset_stats.json`

---

### 3.6 Audio Preprocessing

**Length target:** 300–450 words, 2–3 paragraphs. Explain loading, resampling, normalization, segmentation.

**Write:** Load, resample (16 kHz mono in production API per frontend doc), normalize, segmentation for partial axis

**Sources:** `release/src/segmentation.py`, release audit Phase 3 resampling experiments

---

### 3.7 Data Augmentation

**Length target:** 300–450 words, 2–3 paragraphs. Include types and purpose.

**Write:** MUSAN, RIR, codec, gain, clipping — 611,829 additional samples; train-only augmentation for origin retrain (release audit Phase 2)

**Source:** `PROJECT_STORY` §5

---

### 3.8 Feature Extraction

**Length target:** 250–350 words as an overview only, then use the subheadings for details.

**Write:** Overview of feature sets by project phase

#### 3.8.1 LFCC Features

**Length target:** 200–300 words, 1–2 paragraphs.

**Write:** 20 coefficients; baseline CNN/LCNN input; clean EER 9.68%, aug 15.71%

**Source:** `PROJECT_STORY` §6

#### 3.8.2 Log-Mel Spectrogram Features

**Length target:** 200–300 words, 1–2 paragraphs.

**Write:** 64 bins; ResNet/Hybrid path; aug EER 15.25% vs LFCC 15.71%

**Source:** `PROJECT_STORY` §7

#### 3.8.3 Environmental and Acoustic Features

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** 12-D environmental vector; replay/mixer acoustic features in active release models

**Source:** `comprehensive_evaluation_report.md`, `MODEL_REGISTRY.md`

#### 3.8.4 SSL Embeddings

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** WavLM-style SSL for **origin_file_model** (active); HF hub download on API boot

**Source:** `release/MODEL_REGISTRY.md`, `FRONTEND_AND_DEPLOYMENT_STORY.md` §11.2

**Required table:** Feature Sets Used in FASSD (phase × feature × model)

---

### 3.9 Baseline CNN/LCNN Model

**Length target:** 300–450 words, 2–3 paragraphs. Include purpose and key EER results.

**Write:** ~5k params; official scope deliverable; establishes training/eval pipeline

**Results:** LFCC clean 9.68% EER, aug 15.71% EER

---

### 3.10 ResNet-Based Model

**Length target:** 300–450 words, 2–3 paragraphs. Explain success and why it was not final.

**Write:** Deeper spectral CNN; excellent ASVspoof EER (clean 0.57%, aug 2.61%) but broadcast failure

**Thesis point:** benchmark success ≠ forensic product success

**Status in release:** reference only (`reject_for_now`)

---

### 3.11 Environmental Feature Classifier

**Length target:** 300–450 words, 2–3 paragraphs. Explain anomaly and supervised results briefly.

**Write:** Added after real-world failure; anomaly ~24.5% acc; supervised 81.69% on ASVspoof-style data

**Source:** `PROJECT_STORY` §10

---

### 3.12 HybridResNetEnvironmental Model

**Length target:** 400–550 words, 3 paragraphs. Include architecture, results, and limitation.

**Write:** Log-mel + 12 environmental features; test EER 16.21%, AUC 0.9167, RW EER 16.14%; multiclass acc 64.36%; high bonafide FPR

**Source:** `comprehensive_evaluation_report.md`

**Status:** reference only in final release

---

### 3.13 AASIST Experiment

**Length target:** 250–400 words, 2 paragraphs. Explain why tested and why rejected.

**Write:** Phase 7E; 22/23 clean-human false alarms; rejected as standalone judge

**Source:** `PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`

**Release:** `release/models/reference/aasist/` — inactive

---

### 3.14 Final Multi-Axis Forensic Architecture

**Length target:** 500–750 words, 4–5 paragraphs plus architecture figure. This is a core thesis section.

**Write:** Four active axes + fusion + report layer; evidence bands not raw verdict scores

**Required figure:** Final Multi-Axis FASSD Architecture

**Source:** `PHASE8A_ARCHITECTURE_FREEZE.md`, `MODEL_REGISTRY.md`

#### 3.14.1 Origin Evidence Axis

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** SSL file model; threshold 0.92; processed-AI positives in release-audit retrain

**Results:** leakage-safe BA 0.95; matrix acc 0.8333, BA 0.825

**Failures:** T1.2, T4.1 (human→AI), T4.5 WhatsApp AI→human

#### 3.14.2 Replay/Rerecording Evidence Axis

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** Acoustic file model; threshold 0.65

**Critical:** replay evidence ≠ AI-generated

**Matrix:** acc 0.80, BA 0.7738; failures T2.2, T3.2–T3.4

#### 3.14.3 Mixer/Channel Evidence Axis

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** Acoustic; threshold 0.75; separate semantic from origin

**Matrix weakness:** recall 0.0 (no TP on 25-case matrix)

#### 3.14.4 Partial Fabrication Evidence Axis

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** Segment model `combined_no_f9`; threshold 0.95; F9 within-file features removed in audit

**Status:** experimental manual-review only

**Matrix:** acc 1.0 on 25 files (gated); Phase 5 oracle 10/10

#### 3.14.5 Fusion and Manual Review Logic

**Length target:** 220–320 words, 1–2 paragraphs.

**Write:** Phase 8F fusion rules; abstention; `manual_review_required: true`; no conclusive authenticity

**Source:** `release/src/fusion_rules.py`, Phase 9F API contract

---

### 3.15 Report Generation

**Length target:** 300–450 words, 2–3 paragraphs. Explain JSON/evidence bands/report safety.

**Write:**
- JSON analysis payload (`phase9c_report`, `evidence_axis_cards`)
- Evidence bands Low/Medium/High (`release/config/evidence_calibration.json`)
- Partial segment timestamps for waveform highlights
- Safety/limitation blocks in API response
- Optional PDF/Markdown in backend (web UI focuses on on-screen cards + disclaimer)

**Source:** Phase 9 docs, `FRONTEND_AND_DEPLOYMENT_STORY.md` §14

---

### 3.16 System Interface and Deployment Design

**Length target:** 500–750 words, 4–5 paragraphs plus deployment figure. This is a core implementation section.

**Write — primary (thesis focus):**
- **Public web application:** https://www.deepfakedetection.dev/
- **Separate website hosting repository** (documented path `D:\FASSD\` — not in FYP ML git)
- **Frontend:** Next.js 16 on Vercel — landing, dashboard upload, results, profile/history
- **Backend API:** Phase 9 FastAPI on DigitalOcean Droplet, HTTPS via Caddy — https://api.deepfakedetection.dev/
- **Auth/data:** Firebase Auth + Firestore history
- **Upload architecture:** browser posts large audio **directly to API** (bypasses Vercel 4.5 MB serverless limit)
- **User experience:** four evidence check cards, real waveform, segment highlights, manual-review headlines ("Sounds human-made" / "Worth a closer look")

**Write — supporting (brief mention only if needed):**
- FYP repo `release/` folder = ML inference backend **source** used to build production API (Phase 9C pipeline)
- Do **not** center thesis on Gradio/local hosting — online web platform is the software representation for evaluation/defense

**Required figure:** System Deployment Architecture (Browser → Vercel → DO API → four models → JSON → UI)

**Sources:** `FRONTEND_AND_DEPLOYMENT_STORY.md` (authoritative for deployment), `reports/website/PARTNER_INTEGRATION_GUIDE.md` (**outdated** — legacy Hybrid ResNet; see notice in that file)

---

### 3.17 API Design

**Length target:** 300–450 words, 2 paragraphs plus endpoint table.

**Write:** Production endpoints on api.deepfakedetection.dev (same contract as Phase 9 FastAPI)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness, `ready_for_analyze`, model load |
| GET | `/model-info` | Inventory, partial module metadata |
| POST | `/analyze` or `/analyze-audio` | Multipart audio upload → multi-axis JSON |

**Query flags:** `return_top_segments`, `generate_report`, `generate_visual` (backend)

**Safety fields:** `manual_review_required: true`, `conclusive_authenticity_decision: false`

**Source:** `reports/phase9/integration_docs/phase9f_api_contract.md`, `FRONTEND_AND_DEPLOYMENT_STORY.md` §8

**Optional table:** move to Appendix E if chapter too long

---

### 3.18 Storage and Output Structure

**Length target:** 250–400 words, 2 paragraphs.

**Write:**
- **Web:** no persistent audio storage after analysis (in-memory processing)
- **Firestore:** simplified history fields (`audioAnalyses` collection) — not full Phase 9 JSON
- **Backend optional:** case_id, saved JSON under sample_outputs when `save_report=true`
- **Separate repos:** FYP ML artifacts vs website repo — state clearly for reproducibility

**Source:** `FRONTEND_AND_DEPLOYMENT_STORY.md` §10, §18

---

### 3.19 Hardware and Software Environment

**Length target:** 250–350 words, 1–2 paragraphs plus table.

**Write:**

| Layer | Technology |
|-------|------------|
| ML training | Python, PyTorch, librosa, conda env `fassd` |
| Inference API | FastAPI, Docker, WavLM, joblib models |
| Web frontend | Next.js 16, React 19, Tailwind 4, shadcn/ui |
| Hosting | Vercel (frontend), DigitalOcean 4GB Droplet (API), Firebase |
| HTTPS | Caddy reverse proxy |

**GPU for training:** **MISSING exact spec in repo** — confirm from local dev notes

**Required table:** Hardware and Software Environment

---

### 3.20 Ethical and Safety Considerations

**Length target:** 300–450 words, 2–3 paragraphs.

**Write:**
- Misuse risk (false accusation); privacy (uploaded audio not retained on web)
- No legal verdict; human-in-the-loop mandatory
- Experimental prototype disclaimer shown in UI footer (`safety.wording`)
- Over-trusting automation risk

**Sources:** `phase8g_limitations_and_claims.md`, Phase 9F known limitations

---

### 3.21 Methodology Limitations

**Length target:** 300–450 words, 2–3 paragraphs.

**Write:**
- Studio-heavy unified dataset
- Small axis training sets for shipped models
- Platform compression (WhatsApp) breaks origin on documented cases
- Mixer axis weak positive detection on release matrix
- Partial fabrication = candidate only
- Web history simplifies multi-axis nuance
- Separate repos complicate single-repo reproducibility — document both paths

---

## Chapter 4: Results And Discussion

### 4.1 Evaluation Overview

**Length target:** 300–450 words, 2–3 paragraphs. Define metrics and evaluation tiers.

**Write:** Define EER, AUC, accuracy, balanced accuracy, precision/recall, confusion matrix

**Distinguish three evaluation tiers:**
1. Benchmark (ASVspoof/unified test splits)
2. Controlled forensic (Phase 7 sets)
3. Release validation (`testing_audios` matrix)

---

### 4.2 Baseline CNN/LCNN Results

**Length target:** 250–400 words, 2 paragraphs plus metrics table.

**Write:** LFCC clean 9.68% EER; aug 15.71% EER — proves official pipeline works

**Table:** Baseline metrics

**Source:** `PROJECT_STORY` §6

---

### 4.3 LFCC and Log-Mel Feature Comparison

**Length target:** 250–400 words, 2 paragraphs plus small comparison table.

**Write:** Aug EER 15.71% (LFCC) vs 15.25% (log-mel) — motivated log-mel continuation

---

### 4.4 ResNet Results

**Length target:** 300–450 words, 2–3 paragraphs. Discuss both strong EER and limitation.

**Write:** Clean 0.57%, aug 2.61% EER — strong benchmark; discuss broadcast failure narrative

**Thesis lesson:** best EER phase ≠ final system choice

---

### 4.5 Environmental Classifier Results

**Length target:** 250–400 words, 2 paragraphs.

**Write:** Anomaly ~24.5%; supervised 81.69% — useful but insufficient alone

---

### 4.6 HybridResNetEnvironmental Results

**Length target:** 450–650 words, 3–4 paragraphs plus result table/figure.

**Write:** EER 16.21%, AUC 0.9167, binary acc 89.78%, bonafide FPR 41.28% @0.5, multiclass 64.36%

**Figures:** ROC/confusion from `reports/evaluation/figures/`

**Source:** `comprehensive_evaluation_report.md`

---

### 4.7 Controlled Forensic Evaluation Results

**Length target:** 450–650 words, 3–4 paragraphs plus table.

**Write:** Phase 7C1 vs 7C4-v2 tables — high manipulation sensitivity, poor clean-human specificity

**Source:** `PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`

---

### 4.8 AASIST and Historical Model Comparison

**Length target:** 350–500 words, 2–3 paragraphs plus comparison table.

**Write:** Comparison table — active vs reference models; why HybridResNet/AASIST rejected

| Model | Status | Key issue |
|-------|--------|-----------|
| Origin SSL | Active | Best origin axis |
| Replay/Mixer/Partial | Active | Experimental |
| HybridResNet | Reference | Binary collapse |
| AASIST | Reference | 22/23 clean-human FA |

---

### 4.9 Final Multi-Axis Evidence Results

**Length target:** 450–650 words, 3–4 paragraphs plus final axis table.

**Write:** Per-axis metrics from release audit matrix + model registry dev splits

**Required table:** Final Evidence-Axis Results

| Axis | n | Accuracy | BA | Recall | Source |
|------|---|----------|-----|--------|--------|
| origin | 18 | 0.8333 | 0.8250 | 0.9000 | phase7_final_testing_audios_matrix.md |
| replay | 25 | 0.8000 | 0.7738 | 0.7143 | same |
| mixer | 25 | 0.8800 | 0.4783 | 0.0000 | same |
| partial | 25 | 1.0000 | 1.0000 | 1.0000 | same |

---

### 4.10 Release/Demo Validation Results

**Length target:** 300–450 words, 2–3 paragraphs.

**Write:** Phase 9G **PASS** — backend packaging validated inference pipeline that powers production API

**Frame:** Phase 9G validates ML backend readiness; **user-facing validation** = live web platform end-to-end checklist (`FRONTEND_AND_DEPLOYMENT_STORY.md` §16)

**Do not overclaim:** Phase 9G ≠ legal deployment approval

---

### 4.11 Release Audit Results

**Length target:** 450–650 words, 3–4 paragraphs plus failure table.

**Write:** Full failure table — T1.2, T4.1, T4.5, T2.2, T3.x, mixer misses

**Required table:** Consolidated Key Results Summary

**Source:** `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_matrix.md`

---

### 4.12 Interface and Report Output

**Length target:** 400–600 words, 3–4 paragraphs plus screenshots.

**Write — primary screenshots (from live site):**
1. Landing page — multi-axis architecture/marketing
2. Dashboard upload
3. Results — four evidence cards + waveform + segment highlights
4. Safety disclaimer footer

**Capture from:** https://www.deepfakedetection.dev/ — **screenshots not yet in repo**

**Explain user receives:**
- Plain-language headline + four axis cards + "Moments to replay" timestamps
- Not a legal certificate

**Source:** `FRONTEND_AND_DEPLOYMENT_STORY.md` §6, §13

**Do not use:** outdated Hybrid ResNet REAL/FAKE UI as final interface evidence

---

### 4.13 Discussion Against Literature

**Length target:** 400–600 words, 3–4 paragraphs with citations.

**Write:** FASSD aligns with surveys on deepfake growth but diverges by refusing single-score forensic claims; multi-axis design addresses gap in RA5-style generalization discussion

---

### 4.14 Official Objective-Wise Discussion

**Length target:** 350–500 words, 2–3 paragraphs plus objective table.

**Required table:** Official Objectives vs Achieved Work — map each proposal objective to evidence (see §1.5.1 notes)

---

### 4.15 Extended Contribution Discussion

**Length target:** 350–500 words, 2–3 paragraphs.

**Write:**
- Multi-axis architecture as main research extension
- Evidence-band reporting
- **Deployed web platform** making forensic evidence readable to non-ML users
- Documented rejections (AASIST, Hybrid, unified manipulation v3)

---

### 4.16 Failure Cases and Limitations

**Length target:** 450–650 words, 3–4 paragraphs plus limitations table.

**Write:** Matrix failures; mixer recall 0; WhatsApp compression; partial = candidate only; web history simplification

**Required table:** Limitations and Failure Cases

---

### 4.17 Summary of Results

**Length target:** 200–300 words, 1–2 paragraphs or short bullets if allowed.

**Write (bullets):**
- Official LCNN scope met with documented EER
- ResNet/Hybrid strong on benchmarks, weak on forensic product goals
- Multi-axis release + audit improved origin/partial
- Live web platform delivers experimental decision-support UX
- Remaining gaps: mixer positives, platform compression, manual review essential

---

## Chapter 5: Conclusion And Future Work

### 5.1 Conclusion

**Length target:** 350–500 words, 2–3 paragraphs.

**Write:** FASSD achieved approved software ML scope and extended to experimental multi-axis forensic prototype with **deployed web application** at deepfakedetection.dev; not court-ready

---

### 5.2 Objective-Wise Conclusion

**Length target:** 350–500 words, 2–3 paragraphs or compact table.

**Write:** Short status per official + extended objective (see §1.5)

---

### 5.3 Main Contributions

**Length target:** 350–500 words, 2–3 paragraphs or numbered contribution list.

**Write:**
1. Dataset/feature/training pipeline (ASVspoof → unified)
2. Model experiment trail with documented rejections
3. Multi-axis forensic evidence design
4. Evidence-band report layer
5. **Production web software interface** (separate hosting repo) integrated with Phase 9 API

---

### 5.4 Limitations

**Length target:** 300–450 words, 2–3 paragraphs.

**Write:** Honest restatement — strengthens thesis credibility (see §3.21, §4.16)

---

### 5.5 Future Work

**Length target:** 400–600 words, 3–4 paragraphs.

**Write:**
- Broader external validation beyond testing_audios
- Improved replay/mixer generalization
- Better platform-compressed audio robustness
- Stronger partial localization; reduce clean-human partial spikes
- Expanded dataset diversity
- Expert forensic validation
- Web platform: store full Phase 9 JSON in history; tighten Next.js build quality (ESLint/TS); cost management after DO student credit expires (July 2026 per frontend doc)

**Remove/outdated:** "finalized Next.js integration" — integration is **done**; future work = enhancement not completion

---

### 5.6 Final Statement

**Length target:** 120–200 words, 1 paragraph.

**Write:** FASSD as BSCS foundation for deepfake audio detection research and experimental forensic decision-support via **public web demo**; manual review remains essential

---

## References

### References

**Length target:** Reference list only. No paragraph. Include only sources actually cited in the thesis.

**Write:** Numbered IST format; only sources actually cited

**Seed list:** RA1–RA9 from `research_article/` via `09_REFERENCES_RESEARCH_GAP_PLAN.md`

**Still needed:** ASVspoof 2021, AASIST, WavLM, MUSAN, RIR — **TBD**

**Do not invent IEEE entries**

---

## Appendices

### Appendix A: Official Project Proposal Details

**Length target:** Appendix material; 150–250 words introduction plus extracted material/table.

**Include:** Title, objectives, method, deliverable — extract from `(IST-Dean-F-18)_S_Project Proposal Form-1.pdf`

---

### Appendix B: Dataset and Manifest Details

**Length target:** Appendix material; 150–250 words introduction plus tables/details.

**Include:** Full unified stats crosstabs; manifest column definitions; RealWorld source description

**Source:** `data/statistics/unified_dataset_stats.json`, data manifest docs

---

### Appendix C: Feature Extraction Details

**Length target:** Appendix material; 150–250 words introduction plus parameters/tables.

**Include:** LFCC/log-mel parameters, 12 environmental feature names, SSL model id

**Source:** `Code/features/`, `release/src/feature_extraction.py`, model cards

---

### Appendix D: Model and Configuration Details

**Length target:** Appendix material; 150–250 words introduction plus model/config tables.

**Include:** `MODEL_REGISTRY.md` full text; `evidence_calibration.json`; active vs reference table

---

### Appendix E: API Documentation

**Length target:** Appendix material; 150–250 words introduction plus endpoint/sample JSON details.

**Include:** Full `phase9f_api_contract.md`; sample JSON from `release/sample_outputs/`; production base URL api.deepfakedetection.dev

---

### Appendix F: UI and Report Screenshots

**Length target:** Appendix material; 100–200 words introduction plus screenshots/captions.

**Include:** Extra web UI captures (profile, landing sections, mobile if relevant)

**Primary source:** live site captures — not Gradio

---

### Appendix G: Additional Results

**Length target:** Appendix material; 100–200 words introduction plus extra tables/figures.

**Include:** Confusion matrices, Phase 7 full tables, phase9g manifest, checksum summary

---

### Appendix H: Ethical and Safety Wording

**Length target:** Appendix material; 150–250 words introduction plus safe/forbidden wording tables.

**Include:** Safe wording bank + forbidden claims from `FASSD_THESIS_ROUGH_NOTES.md` §19–20; `partial_report_contract.json`

---

### Appendix I: Repository/File Structure

**Length target:** Appendix material; 150–250 words introduction plus repository tree/table.

**Include two-repo layout:**

**FYP ML repo (`E:\FYP`):**
- `Code/` — training
- `release/` — Phase 9 inference backend source
- `reports/`, `data/`, `submissions/`

**Website hosting repo (separate git — documented `D:\FASSD\`):**
- `app/` — Next.js pages
- `components/` — detection-results, upload-zone, waveform
- `lib/` — inference-client, response-mapper, firebase
- `new backend/release/` — vendored Phase 9 API for Docker deploy
- `deploy/` — DigitalOcean runbook

**Cross-reference:** `FRONTEND_AND_DEPLOYMENT_STORY.md` §5

---

## Quick Reference: Two-Repo Architecture

```
[FYP ML repo E:\FYP]          [Website repo - separate git]
  training / evaluation    →    new backend/release/ (vendored API)
  release/ (source)        →    Docker on DigitalOcean
                                ↑
  reports / thesis docs          Next.js on Vercel → user browser
```

**Thesis rule:** Present **deepfakedetection.dev** as the software system the user interacts with. Cite FYP repo for ML methodology and backend source.
