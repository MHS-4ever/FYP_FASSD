# University Thesis Template Requirements (Extracted)

**Source status:** `thesis_layout.pdf` was **not found** in the repository at `E:\FYP\thesis_layout.pdf`.  
**Method:** Structure below follows the user-provided university template outline and standard FYP thesis conventions. **All formatting details marked TBD must be verified against the official PDF once available.**

---

## Title Page Information Needed

| Field | Requirement | FASSD Content | Status |
|-------|-------------|---------------|--------|
| Thesis title | Official full title | *Forensic Acoustics for Synthetic Speech Detection* (recommended) | TBD — confirm with supervisor |
| Degree program | e.g. BSc / BE | TBD | Missing |
| Department | Template may say Mechanical Engineering | FASSD is audio/ML/forensics — **department correction likely required** | TBD |
| Institute / university name | As per template | TBD | Missing |
| Student name(s) | Full legal name | TBD | Missing |
| Registration number(s) | As per template | TBD | Missing |
| Supervisor | Name, designation | TBD | Missing |
| Co-supervisor | If applicable | TBD | Missing |
| Submission month and year | e.g. June 2026 | TBD | Missing |

---

## Front Matter Sections

### Approval / Declaration / Certificate

- Placeholder pages typically required before Chapter 1.
- Exact wording from `thesis_layout.pdf`: **TBD**.
- Likely includes: supervisor approval, student declaration of originality, plagiarism statement.

### Dedication

- Optional personal dedication page.
- Content: **TBD** (student to provide).

### Acknowledgement

- Acknowledge supervisor, co-supervisor, department, dataset providers, teammates, family.
- Names: **TBD**.

### Abstract

| Requirement (typical) | FASSD guidance |
|----------------------|----------------|
| Length | TBD from PDF (often 250–350 words) |
| Content | Problem, approach, key methods, main results, limitations, conclusion |
| Keywords | deepfake audio, synthetic speech detection, forensic acoustics, ASVspoof, multi-axis evidence |
| Tone | Must state experimental decision-support; not legal proof |

### Table of Contents

- Auto-generated from final Word/LaTeX document.
- Include list of tables and list of figures as separate lists if required by template.

### List of Tables

- All numbered tables in Chapters 3–4 plus appendices.

### List of Figures

- Architecture diagrams, pipeline figures, result plots, UI screenshots.

### Abbreviations / Nomenclature

- See `08_ABBREVIATIONS_GLOSSARY.md`.
- Template may require a dedicated abbreviations page after lists.

---

## Chapter 1 — Introduction

Required subsections (per template outline):

| Subsection | Purpose |
|------------|---------|
| Motivation | Why deepfake/synthetic speech threatens audio evidence integrity |
| Background | Anti-spoofing, forensic audio, AI voice generation context |
| Objectives | FASSD objectives (multi-axis evidence, demo prototype) |
| Scope | In-scope / out-of-scope from `FASSD - Scope.md` |
| Environment and Sustainability | Energy/compute, responsible AI, digital trust (adapt to project) |
| Relevance to SDGs | e.g. SDG 16 (peace, justice, strong institutions), SDG 9 (innovation) — **word carefully** |
| Thesis Outline | Roadmap of Chapters 2–5 |

**Note:** Problem Statement may appear in Chapter 1 or Chapter 2 depending on supervisor preference and PDF template.

---

## Chapter 2 — Literature Survey

| Subsection | Purpose |
|------------|---------|
| Historical Background | Evolution of spoofing attacks and detection |
| Deepfake audio / synthetic speech | TTS, VC, generational models |
| Audio anti-spoofing | CNN, ResNet, graph attention (AASIST) |
| Datasets | ASVspoof LA, DF, PA |
| Features | LFCC, MFCC, log-mel, SSL embeddings |
| Replay / channel / partial fabrication | Forensic gaps |
| Research Gaps | Why binary classifiers fail for forensic use |
| Problem Statement | Formal statement aligned with FASSD scope |

---

## Chapter 3 — Methodology

- Research design and phase-wise evolution
- Dataset collection and preparation
- Preprocessing, segmentation, feature extraction
- Model experiments (baseline CNN, ResNet, environmental, HybridResNet, AASIST, multi-axis release)
- Fusion and report layer
- Tools, hardware, software
- Ethical considerations

---

## Chapter 4 — Results and Discussion

- Baseline through final release results
- Controlled forensic evaluation (Phase 7, release audit)
- Limitations and failure cases
- Discussion vs literature

---

## Chapter 5 — Conclusion and Future Work

- Objective-wise conclusions
- Contributions
- Limitations (honest)
- Future improvements

---

## References

- Style per university template: **TBD** (likely numbered IEEE or similar).
- Do not invent entries — see `09_REFERENCES_RESEARCH_GAP_PLAN.md`.

---

## Appendices

Typical contents for FASSD:

- Sample JSON / Markdown forensic report
- Phase 7C1 category definitions
- Full `testing_audios` failure table
- API contract excerpt
- Additional plots not in main text

Exact appendix rules: **TBD** from PDF.

---

## Template Compliance Checklist

| Template Section | Required by Template | FASSD Content Needed | Current Status | Missing Info |
|------------------|---------------------|----------------------|----------------|--------------|
| Title page | Yes | Title, names, dept, supervisors, date | Partial | All admin fields TBD |
| Approval / certificate | Yes (assumed) | Signed forms | Not started | PDF wording TBD |
| Declaration | Yes (assumed) | Originality statement | Not started | PDF wording TBD |
| Dedication | Optional | Personal text | Not started | Student input |
| Acknowledgement | Yes | Names and thanks | Not started | Student input |
| Abstract | Yes | Evidence-based summary | Not started | Write after Ch. 4–5 |
| Table of contents | Yes | Auto-generated | Not started | — |
| List of tables | Yes | From Ch. 3–4 | Prepared in `06_RESULTS_TABLES_TO_USE.md` | Final numbering TBD |
| List of figures | Yes | From `07_FIGURES_AND_DIAGRAMS_TO_CREATE.md` | Partial | Several figures need creation |
| Abbreviations | Yes (assumed) | `08_ABBREVIATIONS_GLOSSARY.md` | Draft ready | Verify against PDF |
| Ch. 1 Introduction | Yes | Motivation, scope, objectives | Evidence ready | SDG/sustainability wording TBD |
| Ch. 2 Literature | Yes | Survey + gaps | Themes identified | PDFs missing from repo |
| Ch. 3 Methodology | Yes | Full pipeline | Strong repo evidence | — |
| Ch. 4 Results | Yes | All result tables | Strong repo evidence | Choose final metric set |
| Ch. 5 Conclusion | Yes | Contributions + limits | Evidence ready | — |
| References | Yes | Numbered bibliography | Not started | Papers not in repo |
| Appendices | Yes (assumed) | Reports, schemas | Partial | PDF appendix rules TBD |

---

## Action When PDF Is Available

1. Replace all **TBD** formatting notes with exact page order, margins, font, and heading styles.
2. Confirm whether **Problem Statement** belongs in Chapter 1 or 2.
3. Confirm reference style (IEEE, APA, Harvard, etc.) and citation placement.
4. Confirm department name and whether Mechanical Engineering template applies or must be adapted.
