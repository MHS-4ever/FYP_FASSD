# FASSD Thesis Skeleton (No Full Text)

Headings follow `05_PROPOSED_THESIS_STRUCTURE.md`. Under each heading: bullet notes only — **what to write**, **sources**, **tables/figures**, **missing info**. Do not expand into paragraphs here.

---

## Front Matter

### Title Page
- **Write later:** Official title, Rana M. Areeb & M. Hasnain, Computing/BS CS, Sir Faran Mehmood, IST, dates
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §1; `10_MISSING_INFORMATION_QUESTIONNAIRE.md`
- **Missing:** Registration numbers; supervisor official designation spelling

### Certificate / Declaration
- **Write later:** Paste exact text from `thesis_layout.pdf`
- **Missing:** PDF not in repo

### Dedication
- **Write later:** Personal dedication or omit
- **Missing:** Student input

### Acknowledgement
- **Write later:** Thank supervisor, team, dataset providers
- **Missing:** Names TBD

### Abstract
- **Write later:** 250–350 words (verify limit); problem, method, key results, limitations, keywords
- **Sources:** `02_PROJECT_FACTS_MASTER.md`, `06_RESULTS_TABLES_TO_USE.md` Table 4.16, `11_CLAIMS_AND_WORDING_RULES.md`
- **Missing:** Word limit from PDF

### Lists (TOC, tables, figures, abbreviations)
- **Write later:** Auto-generate at end; abbreviations from `08_ABBREVIATIONS_GLOSSARY.md`

---

## Chapter 1: Introduction

### 1.1 Motivation
- **Write later:** AI voice cloning risk; inadequacy of single fake scores for investigators/journalists
- **Sources:** `FASSD - Scope.md` §3, `reports/PHASE7_THESIS_RATIONALE.md` §3
- **Missing:** Local/regional context examples if supervisor wants (TBD)

### 1.2 Background
- **Write later:** Anti-spoofing vs forensic acoustics; FASSD as FYP evolution
- **Sources:** `README.md`, `PROJECT_STORY_FROM_DAY_ONE.md` §1–2
- **Figures:** Fig 1.1 pipeline (create)

### 1.3 Problem Statement
- **Write later:** Synthetic speech risk (proposal); extended need for multi-axis evidence
- **Sources:** Proposal form; `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`
- **Warning:** Decision-support not legal proof

### 1.4 Approved Scope and Extended Development Boundary
- **Write later:** Official LCNN/ASVspoof scope FIRST; Phase 7–9 extensions SECOND — do not imply proposal promised every Phase 9 feature
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §6–8
- **Warning:** Do not say scope was “replaced”

### 1.5 Objectives

#### 1.5.1 Official approved objectives
- **Write later:** Six proposal objectives (bonafide/spoof, forensic cues, embedded deepfake, replay, robust eval, software system)
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §3

#### 1.5.2 Extended implementation objectives
- **Write later:** Multi-axis evidence, reports, manual review, demo tooling, Next.js frontend
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §5
- **Warning:** Frame as supervisor/external-consultation-driven extensions — not NCCIA formal deliverables

### 1.6 Scope
- **Write later:** Official vs extended vs out-of-scope (legal proof, NCCIA endorsement)
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`; `FASSD - Scope.md` (extended reference only)

### 1.7 Environment and Sustainability
- **Write later:** Large-scale training compute; responsible AI triage
- **Sources:** TBD — supervisor guidance
- **Missing:** Required SDG/sustainability paragraph content

### 1.8 Relevance to SDGs
- **Write later:** SDG 9 innovation, SDG 16 institutions — careful wording
- **Missing:** Supervisor approval for SDG claims

### 1.9 Thesis Outline
- **Write later:** One paragraph per chapter
- **Figures:** Fig 1.2 project timeline (create)

---

## Chapter 2: Literature Survey

### 2.1 Introduction
- **Write later:** Survey scope and organization

### 2.2 Deepfake Audio and Synthetic Speech
- **Write later:** TTS, VC, generative voice
- **Sources:** `09_REFERENCES_RESEARCH_GAP_PLAN.md`
- **Missing:** Survey PDFs TBD

### 2.3 Audio Anti-Spoofing and Presentation Attacks
- **Write later:** LA, DF, PA attack types
- **Sources:** ASVspoof papers TBD; `data/statistics/unified_dataset_stats.json`

### 2.4 ASVspoof Datasets and Evaluation Protocols
- **Write later:** Challenge history, EER metric culture
- **Tables:** Dataset scale from Table 4.5

### 2.5 Spectral and Cepstral Features
- **Write later:** LFCC, MFCC, log-mel role in CM
- **Sources:** `PROJECT_STORY_FROM_DAY_ONE.md` §4–7

### 2.6 Convolutional and Residual Network Approaches
- **Write later:** LCNN, ResNet spectrogram detectors
- **Sources:** `reports/PREVIOUS_PIPELINE_WORK.md`

### 2.7 Graph Attention and AASIST-Class Models
- **Write later:** AASIST architecture; why tested in FASSD
- **Sources:** `PHASE7E0_AASIST_EXPERIMENT_PLAN.md`
- **Missing:** AASIST paper citation TBD

### 2.8 Self-Supervised Speech Embeddings
- **Write later:** wav2vec2/WavLM for origin axis
- **Sources:** `release/MODEL_REGISTRY.md`
- **Missing:** SSL paper citations TBD

### 2.9 Replay, Channel, and Environmental Artifacts
- **Write later:** Replay vs synthesis; environmental forensics
- **Sources:** `reports/PHASE7_THESIS_RATIONALE.md`, `FORENSIC_PRODUCT_ROADMAP.md`

### 2.10 Partial Fabrication and Segment-Level Localization
- **Write later:** Splicing, partial AI insertion gap
- **Sources:** `phase8e0_partial_fabrication_policy.md`

### 2.11 Research Gaps
- **Write later:** Benchmark vs forensic product gap
- **Sources:** `09_REFERENCES_RESEARCH_GAP_PLAN.md` §7

### 2.12 Problem Statement (Formal)
- **Write later:** Consolidated FASSD problem for multi-axis prototype
- **Sources:** `FASSD - Scope.md` §3

### 2.13 Chapter Summary
- **Write later:** Bridge to methodology

---

## Chapter 3: Methodology

### 3.1 Research Design Overview
- **Write later:** Approved LCNN plan → experimental evolution → extended multi-axis system
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`; `PROJECT_STORY_FROM_DAY_ONE.md`
- **Figures:** Fig 1.2 timeline

### 3.2 System Architecture Overview
- **Write later:** Official baseline path vs extended multi-axis path
- **Sources:** `PHASE8A_ARCHITECTURE_FREEZE.md`
- **Figures:** Fig 3.1 architecture (create)

### 3.2A Deployment Architecture
- **Write later:** Backend | Gradio/FastAPI demo/testing | Next.js intended final frontend
- **Sources:** `reports/website/PARTNER_INTEGRATION_GUIDE.md`; `release/`
- **Warning:** Gradio is NOT final submission application
- **Missing:** Next.js completion status (Q21)

### 3.3 Dataset Collection and Preparation
- **Write later:** ASVspoof, RealWorld, augmentation, 7C1, testing_audios
- **Sources:** `data/statistics/unified_dataset_stats.json`, `FASSD - Scope.md` §9
- **Tables:** Table 4.5
- **Figures:** Fig 3.2, 3.3 dataset charts
- **Missing:** Dataset permission citations

### 3.4 Audio Preprocessing and Segmentation
- **Write later:** Resample, chunks, VAD, 4 s windows
- **Sources:** `FULL_PROJECT_DOCUMENTATION.md`, `release/src/segmentation.py`
- **Figures:** Fig 3.4

### 3.5 Feature Extraction
- **Write later:** LFCC, log-mel, 12 env, SSL, acoustic, partial features
- **Sources:** Same + `PROJECT_STORY_FROM_DAY_ONE.md`
- **Figures:** Fig 3.5

### 3.6 Baseline CNN Experiments (Phase 3)
- **Write later:** LCNN LFCC setup
- **Sources:** `PROJECT_STORY_FROM_DAY_ONE.md` §6
- **Tables:** Table 4.1

### 3.7 Log-Mel ResNet Experiments (Phase 4.2)
- **Write later:** ResNet architecture, training
- **Tables:** Tables 4.2, 4.3

### 3.8 Environmental Feature Experiments (Phase 4.3)
- **Write later:** Anomaly vs supervised; broadcast failure
- **Tables:** Table 4.4

### 3.9 HybridResNetEnvironmental Model
- **Write later:** Dual branch, multi-task, training config
- **Sources:** `FULL_PROJECT_DOCUMENTATION.md`
- **Figures:** Fig 3.6

### 3.10 Phase 6 Inference and Explanation Layer
- **Write later:** Chunk pooling, attack-type head
- **Sources:** `FULL_PROJECT_DOCUMENTATION.md`, Phase 6 docs

### 3.11 Phase 7 Controlled Forensic Evaluation
- **Write later:** 7A–7E tracks; accept/reject decisions
- **Sources:** `PHASE7_FINAL_CLOSURE_REPORT.md`, `PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`

### 3.12 Phase 8 Multi-Axis Evidence Models
- **Write later:** 8B–8G; 8E axis LR models
- **Sources:** `phase8e1_training_report.md`, Phase 8 docs

### 3.13 Partial Fabrication and Segmentation Method
- **Write later:** Oracle metrics, F9 removal, threshold 0.95
- **Sources:** `phase5_partial_redesign_decision.md`
- **Figures:** Fig 3.8

### 3.14 Release Audit Repairs (2026-06-13)
- **Write later:** Origin retrain, Phase 3–6 decisions, final packaging
- **Sources:** `reports/release_audit/phase2` through `phase7_final_release_report.md`

### 3.15 Phase 9 Local Demo and Testing Interface
- **Write later:** Gradio/FastAPI — experimental local demo/testing only
- **Sources:** `release/app_gradio.py`, Phase 9G report
- **Warning:** Not final user-facing deliverable

### 3.16 Next.js Web Frontend (Intended Final Deployment)
- **Write later:** Dashboard, API integration; state if in progress at submission
- **Sources:** `reports/website/PARTNER_INTEGRATION_GUIDE.md`

### 3.17 Fusion and Forensic Report Layer
- **Write later:** Fusion rules, evidence bands, wording templates
- **Sources:** `evidence_calibration.json`, `phase9f_report_wording_guide.md`
- **Figures:** Fig 3.9

### 3.17 Tools, Hardware, and Software Environment
- **Write later:** Python 3.10, conda fassd, PyTorch, RTX 3050 (where evidenced)
- **Sources:** `README.md`, `PREVIOUS_PIPELINE_WORK.md`

### 3.18 Ethical Considerations and Dataset Integrity
- **Write later:** Holdout policy, leakage control, non-legal-use
- **Sources:** `FASSD - Scope.md`, `11_CLAIMS_AND_WORDING_RULES.md`

### 3.19 Chapter Summary

---

## Chapter 4: Results and Discussion

### 4.1 Introduction
- **Write later:** Separate official-scope vs extended-system results sections

### 4.2 Baseline CNN / LCNN Results — **Official scope alignment**
- **Tables:** 4.1
- **Sources:** `PROJECT_STORY_FROM_DAY_ONE.md`

### 4.3 LFCC vs Log-Mel Comparison
- **Tables:** 4.2

### 4.4 Deep ResNet Results and Domain Mismatch Finding
- **Tables:** 4.3
- **Write later:** Trump/broadcast 8/8 fake failure narrative
- **Warning:** Not final product metric

### 4.5 Environmental Classifier Results
- **Tables:** 4.4

### 4.6 Unified Dataset Statistics and HybridResNetEnvironmental Evaluation
- **Tables:** 4.5, 4.6, 4.7
- **Figures:** 4.2–4.5 ROC/CM from evaluation folder

### 4.7 Phase 7 Controlled Forensic Results
- **Tables:** 4.8, 4.9
- **Figures:** 4.6 comparison chart (create)

### 4.8 AASIST Experiment Results and Rejection Rationale
- **Tables:** 4.10
- **Write later:** Why reject_for_now

### 4.9 Phase 8 Axis Model Results
- **Tables:** 4.11
- **Figures:** 4.7, 4.8

### 4.10 Release Audit Results
- **Tables:** 4.12, 4.13, 4.14, 4.15
- **Write later:** Phase 3 closures as negative results

### 4.11 Final Release Matrix on External testing_audios
- **Tables:** 4.16 — **critical honesty table**
- **Figures:** 4.12 bar chart, failure table from matrix MD
- **Warning:** Mixer recall 0%; origin FPs T1.2 T4.1

### 4.12 Phase 9 Demo Interface Validation
- **Write later:** 184-file regression — validates **demo/testing interface** wording, not field generalization
- **Warning:** Do not equate with official proposal EER evaluation alone

### 4.13 Limitations and Failure Case Analysis
- **Tables:** 4.17, 4.18
- **Figures:** 4.15 Gradio screenshot, 4.16 waveform PNGs

### 4.13 Limitations and Failure Case Analysis
- **Write later:** Per-axis failure modes; partial spikes T1.2/T1.3
- **Sources:** `phase7_final_release_report.md`, `phase5_partial_redesign_decision.md`
- **Figures:** 4.11 T4.3, 4.13 before/after partial

### 4.14 Discussion Against Literature
- **Write later:** Compare Hybrid EER to published baselines; forensic gap
- **Missing:** References TBD

### 4.15 Chapter Summary

---

## Chapter 5: Conclusion and Future Work

### 5.1 Introduction

### 5.2 Objective-Wise Conclusions
- **Write later:** Official six proposal objectives first; extended objectives second with limits
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §3, §5

### 5.3 Major Contributions
- **Write later:** Multi-axis architecture; release audit cycle; F9 diagnosis; evidence-band UI; demo package
- **Sources:** `phase7_final_release_report.md`, `PHASE7_FINAL_CLOSURE_REPORT.md`
- **Figures:** 5.1 contribution diagram (create)

### 5.4 Limitations
- **Write later:** External generalization, small forensic corpus, experimental status
- **Sources:** `phase8g_limitations_and_claims.md`, `phase9f_known_limitations.md`

### 5.5 Future Work
- **Write later:** Complete Next.js frontend; broader validation of extended modules
- **Sources:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §8; `reports/website/PARTNER_INTEGRATION_GUIDE.md`

### 5.6 Closing Remarks
- **Write later:** Manual review + non-legal-proof closing
- **Sources:** `11_CLAIMS_AND_WORDING_RULES.md` §4

---

## References
- **Write later:** Numbered bibliography from EndNote
- **Missing:** All entries TBD until PDFs added

---

## Appendices

### Appendix A: Sample Forensic Report Outputs
- **Sources:** `release/sample_outputs/`, `partial_report_contract.json`
- **Figures:** A.1 PDF excerpt

### Appendix B: Phase 7C1 Forensic Condition Definitions
- **Sources:** `reports/phase7/phase7_dataset/`

### Appendix C: Full testing_audios Evaluation Matrix
- **Sources:** `phase7_final_testing_audios_predictions.csv`, `phase7_final_testing_audios_matrix.md`

### Appendix D: API Contract Summary
- **Sources:** `phase9f_api_contract.md`

### Appendix E: Additional Figures and Confusion Matrices
- **Sources:** `reports/evaluation/figures/`, `phase8e2/figures/`

### Appendix F: Model Registry and Threshold Summary (optional)
- **Sources:** `release/MODEL_REGISTRY.md`, Table 4.19

---

## Skeleton Completion Checklist

- [ ] `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` reviewed with supervisor  
- [ ] Questionnaire `10_MISSING_INFORMATION_QUESTIONNAIRE.md` filled (NCCIA, Next.js, department wording)  
- [ ] `thesis_layout.pdf` obtained and `01_TEMPLATE_REQUIREMENTS_EXTRACTED.md` updated  
- [ ] Priority figures created (3.1, 4.12, 1.2, 4.15)  
- [ ] Literature PDFs added; `09_REFERENCES_RESEARCH_GAP_PLAN.md` updated  
- [ ] Supervisor approves structure in this skeleton  
- [ ] Begin Stage 2 in `12_FIRST_DRAFT_WRITING_PLAN.md`
