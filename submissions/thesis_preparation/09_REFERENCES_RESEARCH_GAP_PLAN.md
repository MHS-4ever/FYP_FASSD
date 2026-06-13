# References and Research Gap Plan

**Updated:** 2026-06-13 — proposal-form scope correction + literature rebuild.  
**Scope authority:** `(IST-Dean-F-18)_S_Project Proposal Form-1.docx` via `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`  
**Literature strategy:** `14_LITERATURE_REVIEW_REBUILD_STRATEGY.md`, `15_REFERENCE_SELECTION_MATRIX.csv`  
**Rule:** Bibliographic fields extracted from PDF first pages where possible. Do not invent missing fields.

---

## 1. Reference Style Required by Template

| Item | Status |
|------|--------|
| Official style (IEEE, APA, Harvard, etc.) | **TBD** — `thesis_layout.pdf` not found in repository |
| In-text format | Likely numbered [1], [2], … if engineering template |
| EndNote / reference manager | Import from table in §3 below |

---

## 2. Available Research Papers in Repository

**Location:** `e:\FYP\research_article\` (9 PDFs)

| ID | File | Title (verified from PDF) | Authors (first page / metadata) | Year | Venue / notes | DOI or ID |
|----|------|---------------------------|--------------------------------|------|---------------|-----------|
| RA1 | `1.pdf` | Audio Deepfake Detection: A Survey | Jiangyan Yi, Chenglong Wang, Jianhua Tao, Xiaohui Zhang, Chu Yuan Zhang, Yan Zhao | 2023 | IEEE journal format (JLCL template header) | TBD — verify IEEE publication |
| RA2 | `2.pdf` | Audio Deepfake Detection: What Has Been Achieved and What Lies Ahead | Bowen Zhang, Hui Cui, Van Nguyen, Monica Whitty | 2025 | *Sensors*, 25, 1989 | [10.3390/s25071989](https://doi.org/10.3390/s25071989) |
| RA3 | `3.pdf` | A survey on multimedia-enabled deepfake detection: state-of-the-art tools and techniques… | Abdullah Ayub Khan et al. | 2025 | *Discover Computing*, 28:48 | [10.1007/s10791-025-09550-0](https://doi.org/10.1007/s10791-025-09550-0) |
| RA4 | `4.pdf` | Where are We in Audio Deepfake Detection? A Systematic Analysis over Generative and Detection Models | Xiang Li, Pin-Yu Chen, Wenqi Wei | TBD | Fordham / IBM — verify venue from PDF | TBD |
| RA5 | `5.pdf` | Beyond Identity: Generalizable Deepfake Audio Detection | Yasaman Ahmadiadli, Xiao-Ping Zhang, Naimul Khan | TBD | Preprint-style (Toronto Metropolitan Univ.) | TBD |
| RA6 | `6.pdf` | Forensic deepfake audio detection using segmental speech features | Tianle Yang, Chengzhe Sun, Siwei Lyu, Phil Rose | 2025 | arXiv:2505.13847v2 | [arXiv:2505.13847](https://arxiv.org/abs/2505.13847) |
| RA7 | `7.pdf` | Deepfake audio detection with spectral features and ResNeXt-based architecture | Gul Tahaoglu, Daniele Baracchi, Dasara Shullani, Massimo Iuliani, Alessandro Piva | TBD | *Knowledge-Based Systems*, Elsevier | TBD — verify volume/pages |
| RA8 | `8.pdf` | Investigation of Deepfake Voice Detection Using Speech Pause Patterns: Algorithm Development and Validation | Nikhil Valsan Kulangareth, Jaycee Kaufman, Jessica Oreskovic, Yan Fossat | TBD | Klick Labs — JMIR-style original paper | TBD |
| RA9 | `9.pdf` | Improved DeepFake Detection Using Whisper Features | Piotr Kawa, Marcin Plata, Michał Czuba, Piotr Szymański, Piotr Syga | TBD | Submitted to INTERSPEECH (per PDF header) | TBD — verify if published |

**Legacy README path:** `Research Article/` — **not present**. Use `research_article/` as seed PDF folder only (see §2A/2B below).

---

## 2A. Literature for official approved scope (proposal form)

| Topic | Papers / sources | Thesis section |
|-------|------------------|----------------|
| ASVspoof 2021 LA/DF | **TBD** official paper + RA1, RA2 surveys | Ch. 2.4, 3.3 |
| Bonafide vs spoof classification | RA1, RA2 | Ch. 2.3, 4.2 |
| LFCC / log-mel features | RA1, RA7 | Ch. 2.5, 3.5 |
| LCNN / lightweight CNN | RA1; ASVspoof baseline **TBD** | Ch. 2.6, 3.6 |
| Augmentation (MUSAN, RIR, codec) | **TBD** | Ch. 3.3 |
| Replay simulation | RA1, RA2 | Ch. 2.3, proposal obj. 4 |
| EER, ROC-AUC, confusion matrices | RA1, RA2 | Ch. 2.4, 4.2–4.3 |
| Software-based detection tool | RA2; proposal form | Ch. 1, 3 deployment |

## 2B. Literature for extended scope (post-proposal)

| Topic | Papers / sources | Thesis section |
|-------|------------------|----------------|
| ResNet / deep spectral CNN | RA7 | Ch. 2.6, 4.4 |
| Domain mismatch / generalization | RA5 | Ch. 2.11, 4.13 |
| AASIST | **TBD** (not in research_article/) | Ch. 2.7, 4.8 |
| SSL / Whisper embeddings | RA9; WavLM **TBD** | Ch. 2.8, 3.12 |
| Forensic segmental / partial cues | RA6 | Ch. 2.10, 3.13 |
| Multi-axis forensic reporting (gap) | RA2 limitations, RA6 | Ch. 2.11 |
| Web deployment / ML UI | **TBD** | Ch. 3.16 Next.js section |

**Seed PDFs (RA1–RA9):** legacy study material — see `14_LITERATURE_REVIEW_REBUILD_STRATEGY.md` §2.

---

## 3. Likely Literature Themes → FASSD Sections

| Theme | Supporting papers | FASSD thesis section |
|-------|-------------------|----------------------|
| Audio deepfake surveys & taxonomy | RA1, RA2, RA3 | Ch. 2.2, 2.11 |
| Generalization / identity leakage | RA5 | Ch. 2.11, 4.13 (domain mismatch) |
| TTS/VC threat model | RA4 | Ch. 2.2, 1.1 Motivation |
| Spectral features + deep CNN/ResNet | RA7 | Ch. 2.5, 2.6, 4.2–4.4 |
| SSL / Whisper front-ends | RA9 | Ch. 2.8, 3.5 (origin SSL axis) |
| Forensic / segmental acoustic features | RA6 | Ch. 2.10, 3.13 partial fabrication |
| Pause / prosodic cues | RA8 | Ch. 2.9 optional environmental cue discussion |
| ASVspoof / benchmark culture | RA1, RA2 (survey content) | Ch. 2.4 — **also cite official ASVspoof papers TBD** |

---

## 4. Which Paper Supports Which Section

| Thesis section | Primary papers | Secondary |
|----------------|----------------|-----------|
| Ch. 1 Motivation | RA2, RA4 | Title defence slide 5 (Pakistan manipulation context) |
| Ch. 2.2 Synthetic speech | RA4 | RA1 |
| Ch. 2.4 ASVspoof datasets | RA1, RA2 | Official ASVspoof 2021 paper **TBD** |
| Ch. 2.5 LFCC/MFCC/log-mel | RA1, RA7 | Project docs |
| Ch. 2.6 CNN/ResNet | RA7 | `PROJECT_STORY_FROM_DAY_ONE.md` |
| Ch. 2.7 AASIST | **TBD** — not in `research_article/` folder | `PHASE7E0_AASIST_EXPERIMENT_PLAN.md` |
| Ch. 2.8 SSL/Whisper | RA9 | `release/MODEL_REGISTRY.md` (WavLM-style origin) |
| Ch. 2.10 Partial / forensic segments | RA6 | Phase 5 partial redesign reports |
| Ch. 2.11 Research gaps | RA2, RA5, RA6 | `reports/PHASE7_THESIS_RATIONALE.md` |
| Ch. 4 Discussion | RA5 (generalization), RA7 (spectral baseline comparison) | RA2 limitations sections |

---

## 5. Title Defence Presentation (Historical Context Only)

**Path:** `submissions/title defence/Forensic_Acoustics_for_Synthetic_Speech_Detection_Title_Defence.pptx`

| Slide content | Thesis use | Warning |
|---------------|------------|---------|
| Title FASSD | Ch. 1 title | OK — matches proposal |
| IST | Title page | OK |
| NCCIA named | Historical only | **Not a continuing formal partner** unless confirmed — use neutral external-consultation wording |
| Binary pipeline / “Authentic vs AI-Generated” | Do not copy | Extended multi-axis system; see `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` |
| “Robust forensic solution” | Do not copy | Experimental decision-support only |
| Pakistan manipulation examples | Motivation optional | Cite responsibly |

**Literature and objectives authority:** proposal form, not title defence alone.

---

## 6. Missing Papers Still Needed (Beyond `research_article/`)

| Work | Why needed | Status |
|------|------------|--------|
| **ASVspoof 2021** evaluation plan / database paper | Dataset citation for LA/DF/PA | **TBD** — not in folder |
| **AASIST** (Jung et al.) | Phase 7E experiment | **TBD** — not in folder |
| **wav2vec 2.0** (Baevski et al.) | SSL origin axis | **TBD** |
| **WavLM** (Chen et al.) | Release origin embeddings | **TBD** |
| **LFCC anti-spoof baselines** (ASVspoof challenge papers) | Phase 3 baseline context | **TBD** |
| **AASIST-L / ASVspoof baseline LCNN** | Historical method comparison | **TBD** |

Search IEEE Xplore, arXiv, and ASVspoof challenge site for official BibTeX.

---

## 7. Research Gap Statement (Evidence + Literature)

1. **Official scope** (proposal): bonafide/spoof software detection on ASVspoof with LFCC/log-mel/LCNN and EER evaluation.  
2. Surveys (RA1–RA2) document benchmark-centric detection; **extended work** adds multi-axis forensic evidence (`16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`).  
3. Generalization failure (RA5) aligns with broadcast and `testing_audios` limits.  
4. Segmental forensic features (RA6) motivate extended partial axis — beyond LCNN proposal.  
5. Gap: few papers combine **origin, replay, mixer, partial** reporting — FASSD extended contribution.

---

## 8. EndNote Workflow

1. Create group **FASSD_thesis** with subfolders: **Official_Scope**, **Extended_Scope**, **Seed_PDFs**, **Datasets_TBD**.  
2. Import 9 PDFs from `research_article/` into **Seed_PDFs** only.  
3. Manually add ASVspoof 2021 + AASIST + WavLM/wav2vec papers.  
4. Use `15_REFERENCE_SELECTION_MATRIX.csv` when mapping citations to sections.  
5. Insert citations during Chapter 2 draft (Stage 3).  
6. Cross-check numbered list against SRC061–069 in `03_SOURCE_INVENTORY.csv`.

---

## 9. Citation Detail Status Log

| Work | BibTeX ready | Verified by student |
|------|--------------|---------------------|
| RA1–RA9 | Partial (first-page extract) | **TBD** |
| ASVspoof 2021 | No | **TBD** |
| AASIST | No | **TBD** |
| wav2vec2 / WavLM | No | **TBD** |

---

## 10. Internal Documents (Not Journal References)

Cite as project artifacts, not peer-reviewed papers:

- `PROJECT_STORY_FROM_DAY_ONE.md`
- `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md`

Use wording: *Internal FASSD project report (repository, 2026).*
