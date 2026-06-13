# Official Scope vs Extended Development Work

**Purpose:** Define the **approved baseline FYP scope** (IST proposal form) versus **extended implementation work** completed later. This document is the primary scope authority for thesis writing.

**Official scope source:** `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.docx`  
**PDF copy:** `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.pdf`  
**Note:** `FASSD - Scope.md` and Phase 8/9 documents describe **evolved project direction** and must not be treated as the sole official approved scope.

**Supporting internal docs (extended work only):** `FASSD - Scope.md`, `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md`, `release/MODEL_REGISTRY.md`, `PROJECT_STORY_FROM_DAY_ONE.md`

---

## 1. Official approved project identity

Extracted from the IST project proposal form:

| Field | Value | Source |
|-------|-------|--------|
| Project title | Forensic Acoustics for Synthetic Speech Detection | Proposal form |
| Short name | FASSD | Proposal form / project convention |
| Degree program | BS CS | Proposal form |
| Department | Computing | Proposal form |
| Institute | Institute of Space Technology | Proposal form; title defence PPTX |
| Project start date | 12th October, 2025 | Proposal form |
| Project finish date | 12th June, 2026 | Proposal form |
| Supervisor | Sir Faran Mehmood | Proposal form |
| Students | Rana M. Areeb and M. Hasnain | Proposal form; `code/features/feature_extraction.py` header |
| Final deliverable type | Software system | Proposal form |

---

## 2. Official approved project summary

The approved proposal describes the following problem and aim:

- AI-generated synthetic speech creates risks for **digital security**, **identity verification**, and **information trustworthiness**.
- The project aims to develop a **robust machine-learning system** for detecting AI-generated or manipulated speech.
- The system analyzes **acoustic and environmental cues**, including spectral features, replay signatures, background noise artifacts, and device-induced distortions.
- The **original planned technical approach** used ASVspoof 2021, augmented data, LFCC, Log-Mel spectrograms, and an **LCNN classifier**.
- The **approved final deliverable** was a **functional software system** for evaluating speech authenticity and detecting deepfake audio.

**Source:** `(IST-Dean-F-18)_S_Project Proposal Form-1.docx`

---

## 3. Official approved objectives

From the proposal form:

1. Develop a machine learning model that classifies speech as **bonafide/human** or **spoof/AI-generated**.
2. Use **forensic audio cues** such as noise patterns, reverberation, and channel artifacts.
3. **Identify deepfake voice embedded** into real audio recordings.
4. **Detect replayed synthetic speech** where AI-generated audio is played through a device and re-recorded.
5. Build a **robust evaluation pipeline** using augmented and real-world testing scenarios.
6. Deliver a **complete software-based system** for deepfake speech detection.

**Source:** Proposal form

---

## 4. Official approved implementation method

From the proposal form:

| Step | Approved plan |
|------|----------------|
| Dataset | ASVspoof 2021 **DeepFake** and **Logical Access** tracks |
| Augmentation | MUSAN noise, RIR reverberation, codec distortions |
| Features | **LFCC** (20-dimensional), **Log-Mel** (64-dimensional) |
| Classifier | **LCNN-based binary classification** |
| Robustness | Noise, replay simulation, compression |
| Evaluation | **EER**, **ROC-AUC**, accuracy, confusion matrices |
| Deployment | **Software tool** for external test audio files |

**Source:** Proposal form

**Evidence that approved baseline was implemented (repository):** LCNN/LFCC baseline (`PROJECT_STORY_FROM_DAY_ONE.md` §6), augmentation (`§5`), LFCC vs log-mel comparison (`§7`), EER/ROC evaluation (`reports/evaluation/comprehensive_evaluation_report.md` for later hybrid eval).

---

## 5. Extended development work completed later

The following work **exceeds the original LCNN/binary proposal** but is supported by repository evidence. Frame as **extensions** motivated by limitations discovered during implementation and additional forensic-review requirements suggested during **supervision and external consultation** (not as originally promised deliverables).

| Extension | Evidence | Notes |
|-----------|----------|-------|
| Baseline CNN/LCNN experiments | `PROJECT_STORY_FROM_DAY_ONE.md` | Aligns with approved plan |
| LFCC vs Log-Mel comparison | Same §7 | Within approved feature scope |
| Deep ResNet CNN | Same §8 | Beyond LCNN plan |
| Environmental feature classifier | Same §10 | Forensic acoustic extension |
| Unified ASVspoof + real-world dataset | `data/statistics/unified_dataset_stats.json` | Beyond DF+LA-only proposal |
| HybridResNetEnvironmental | `reports/evaluation/comprehensive_evaluation_report.md` | Major architecture extension |
| Raw-audio explanation pipeline | Phase 6 docs, `FULL_PROJECT_DOCUMENTATION.md` | Explainability extension |
| Controlled forensic testing (Phase 7) | `PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` | Extended evaluation |
| AASIST experiment + rejection | Phase 7E reports | Experimental branch, not shipped |
| Multi-axis forensic architecture | `PHASE8A_ARCHITECTURE_FREEZE.md` | Major scope extension |
| Separate origin / replay / mixer / partial models | `release/MODEL_REGISTRY.md` | Extended evidence system |
| Fusion, abstention, manual-review wording | Phase 8F, Phase 9F docs | Extended reporting |
| **Gradio/FastAPI local demo** | `release/app_gradio.py`, `release/app_fastapi.py` | **Experimental testing/demo interface only** |
| **Next.js web application frontend** | `reports/website/PARTNER_INTEGRATION_GUIDE.md` | **Intended final user-facing deployment** (under development / separate repo path noted as `D:\FASSD`) |
| JSON / Markdown / PDF report outputs | `release/sample_outputs/`, Phase 9 docs | Extended reporting |
| Release audit + evidence-band UI | `reports/release_audit/phase7_final_release_2026-06-13/` | Post-Phase-9 repair cycle |

---

## 6. Correct thesis framing

- The **proposal form** is the **official approved scope** for the FYP.
- The thesis must **first** show how the official scope was achieved (software ML system, spectral/forensic cues, bonafide/spoof classification, replay/deepfake-in-audio scenarios, robust evaluation).
- The **multi-axis system** must be presented as an **extension** motivated by real-world forensic limitations discovered during implementation—not as if it replaced or invalidated the approved scope.
- Do **not** write that the official scope was “replaced.”
- Do **not** present **NCCIA** as a continuing official partner unless explicitly confirmed later. Title defence mentioned NCCIA historically; use neutral wording about **supervisor feedback and external consultation**.
- Do **not** overclaim the final extended system as court-ready or production-ready.
- Use **“experimental forensic audio decision-support prototype”** for the **extended final system**.
- Use **“software-based deepfake speech detection system”** when referring to the **official deliverable** and baseline achievement.
- Describe **Gradio/FastAPI** as a **development, demonstration, and testing interface**—not the intended final submission-facing application.
- Describe the **Next.js application** as the **intended final web-based frontend** integrated with the backend inference/report pipeline; if incomplete at submission, state it as **ongoing deployment work**.

---

## 7. Recommended wording for thesis

### Approved scope wording

> “The approved project scope focused on developing a software-based machine learning system for detecting AI-generated or manipulated speech using spectral and forensic acoustic cues, augmented datasets, and a robust evaluation pipeline.”

### Extension wording

> “During implementation, additional forensic-review requirements were considered, which led to an extended multi-axis evidence architecture separating voice-origin evidence, replay/rerecording evidence, channel/mixer processing evidence, and partial-fabrication candidate regions.”

### Deployment wording

> “A lightweight Gradio/FastAPI interface was developed during implementation for local experimentation, testing, and demonstration purposes, while the intended final user-facing deployment architecture is being developed as a Next.js-based web application integrated with the backend inference pipeline.”

### NCCIA-safe wording

> “Some extended forensic-review requirements were influenced by supervisor feedback and external consultation during the project. These requirements were retained because they improved the practical relevance of the system, although the final thesis treats them as project extensions rather than formal external deliverables.”

### External consultation (if NCCIA not named)

> “Additional forensic-review requirements suggested during supervision and external consultation motivated extended reporting and multi-axis evidence design; these extensions are documented separately from the officially approved proposal scope.”

---

## 8. Thesis chapter placement

| Chapter / section | What to include |
|-------------------|-----------------|
| **Ch. 1 — Scope** | Official proposal scope first; boundary to extended development second |
| **Ch. 1 — Objectives** | Official objectives (§3) first; extended objectives (multi-axis, reports, manual review) second |
| **Ch. 3 — Methodology** | Evolution from proposed LCNN plan → experiments → extended multi-axis implementation |
| **Ch. 3 — System design / deployment** | Backend inference/report pipeline; Gradio/FastAPI as demo tooling; Next.js as intended final frontend |
| **Ch. 4 — Results** | Official-scope results (baseline LCNN, LFCC/log-mel, EER/AUC) **and** extended-system results (Phase 7–9, release audit) in separate subsections |
| **Ch. 5 — Future work** | Broader validation of extended forensic modules; completion/integration of Next.js deployment |

---

## 9. Document hierarchy (scope authority)

| Priority | Document | Role in thesis |
|----------|----------|----------------|
| 1 | `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.docx` | **Official approved scope** |
| 2 | `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` | Thesis framing guide (this file) |
| 3 | `PROJECT_STORY_FROM_DAY_ONE.md` | Implementation timeline evidence |
| 4 | `FASSD - Scope.md` | **Extended** scope reference (Phase 8 revision) — not sole official scope |
| 5 | Phase 7/8/9 / release audit docs | Extended system evidence and limitations |

---

## 10. Deployment architecture summary

```text
OFFICIAL PLAN (proposal):     Software tool → upload audio → ML classifier → authenticity result

IMPLEMENTED BASELINE:         Feature extraction → CNN/LCNN/ResNet/Hybrid → EER/AUC evaluation

EXTENDED BACKEND:             Multi-axis inference + fusion + JSON/MD/PDF reports (release/)

DEMO / TEST INTERFACE:        Gradio + FastAPI in release/ (local experimentation only)

INTENDED FINAL FRONTEND:      Next.js web app → backend API (reports/website/PARTNER_INTEGRATION_GUIDE.md)
```

**Thesis rule:** Never describe Gradio as the final deployed application for submission.
