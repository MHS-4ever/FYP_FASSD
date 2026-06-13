# First Draft Writing Plan

Staged plan to write the thesis chapter by chapter **after** this preparation folder is approved. Do **not** skip limitation/disclaimer steps.

---

## Stage 1 — Finalize Structure

| Item | Detail |
|------|--------|
| **Inputs** | `05_PROPOSED_THESIS_STRUCTURE.md`, `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`, `01_TEMPLATE_REQUIREMENTS_EXTRACTED.md`, completed `10_MISSING_INFORMATION_QUESTIONNAIRE.md`, supervisor feedback |
| **Outputs** | Approved heading hierarchy; official vs extended boundary; Gradio vs Next.js deployment distinction |
| **Quality checks** | Proposal form scope reflected in Ch. 1; extended work not presented as original promise |

---

## Stage 2 — Write Chapter 1 (Introduction)

| Item | Detail |
|------|--------|
| **Inputs** | `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`, `02_PROJECT_FACTS_MASTER.md`, proposal form summary, `reports/PHASE7_THESIS_RATIONALE.md`, `11_CLAIMS_AND_WORDING_RULES.md` |
| **Outputs** | Draft Ch. 1 with **official scope/objectives first**, extended boundary second, deployment distinction |
| **Quality checks** | No NCCIA partnership overclaim; Gradio not called final app; disclaimers seeded |

---

## Stage 3 — Write Chapter 2 (Literature Survey)

| Item | Detail |
|------|--------|
| **Inputs** | `14_LITERATURE_REVIEW_REBUILD_STRATEGY.md`, `15_REFERENCE_SELECTION_MATRIX.csv`, `09_REFERENCES_RESEARCH_GAP_PLAN.md`, `research_article/*.pdf` |
| **Outputs** | Ch. 2 with **official-scope literature first** (ASVspoof, LFCC, LCNN, EER), extended topics second |
| **Quality checks** | RA PDFs as seed only; ASVspoof official paper added; extensions labeled in text |

---

## Stage 4 — Write Chapter 3 (Methodology)

| Item | Detail |
|------|--------|
| **Inputs** | `PROJECT_STORY_FROM_DAY_ONE.md`, `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`, `reports/website/PARTNER_INTEGRATION_GUIDE.md`, `release/` docs |
| **Outputs** | Ch. 3 with LCNN plan → evolution; **§3.2A deployment** (backend / Gradio demo / Next.js intended frontend) |
| **Quality checks** | Gradio ≠ final UI; proposal method traced; rejected models labeled |

---

## Stage 5 — Write Chapter 4 (Results and Discussion)

| Item | Detail |
|------|--------|
| **Inputs** | `06_RESULTS_TABLES_TO_USE.md`, all Phase 7/8/9/release audit reports, evaluation figures |
| **Outputs** | Draft Ch. 4 with **official results subsection** + **extended results subsection** + failure analysis |
| **Quality checks** | Tables 4.1–4.3 for official scope; Table 4.16 for extended; Gradio results framed as demo testing only |

---

## Stage 6 — Write Chapter 5 (Conclusion and Future Work)

| Item | Detail |
|------|--------|
| **Inputs** | `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md`, `phase7_final_release_report.md`, `phase8g_limitations_and_claims.md`, Ch. 4 draft |
| **Outputs** | Objective-wise conclusions, contributions, limitations, future work |
| **Quality checks** | **Official proposal objectives** addressed first; extended objectives with limits; Next.js future work if incomplete |

---

## Stage 7 — Abstract, Front Matter, References, Appendices

| Item | Detail |
|------|--------|
| **Inputs** | Completed Ch. 1–5, questionnaire answers, EndNote library, sample outputs in `release/sample_outputs/` |
| **Outputs** | Abstract, title page, approval pages, dedication, acknowledgement, references, appendices A–F |
| **Quality checks** | Abstract within word limit; keywords approved; all `[n]` citations resolve; appendices referenced in text; abbreviations list complete |

---

## Stage 8 — Formatting and Plagiarism-Safe Review

| Item | Detail |
|------|--------|
| **Inputs** | `thesis_layout.pdf` formatting rules, final Word/LaTeX draft, similarity report |
| **Outputs** | Submission-ready PDF |
| **Quality checks** | Template margins/fonts; LOF/LOT complete; figure/table numbering continuous; `11_CLAIMS_AND_WORDING_RULES.md` self-check passed; supervisor sign-off; plagiarism threshold met |

---

## Suggested Timeline (adjust to deadline)

| Week | Stage |
|------|-------|
| 1 | Stage 1 + questionnaire + obtain PDF/papers |
| 2 | Stage 2 (Ch. 1) |
| 3 | Stage 3 (Ch. 2) — literature heavy |
| 4–5 | Stage 4 (Ch. 3) |
| 6–7 | Stage 5 (Ch. 4) |
| 8 | Stage 6 (Ch. 5) |
| 9 | Stage 7 (front matter, abstract, refs, appendices) |
| 10 | Stage 8 (formatting, review, submission) |

---

## Parallel Tasks (any stage)

- Create priority figures from `07_FIGURES_AND_DIAGRAMS_TO_CREATE.md`  
- Build EndNote library from `09_REFERENCES_RESEARCH_GAP_PLAN.md`  
- Run Gradio locally for **demo/testing** screenshot only (label as experimental interface)  
- Capture Next.js UI screenshots if available for **intended final frontend** section  
- Supervisor review after Stage 1 and after Stage 5 (results chapter critical)

---

## Stop Conditions — Do Not Proceed If

- `testing_audios` failure table omitted from Ch. 4  
- Active/inactive models conflated  
- Abstract claims "proves fake" or omits experimental status  
- Gradio described as final submission application  
- NCCIA presented as continuing official partner without confirmation  
- Official scope conflated with Phase 9-only features  
