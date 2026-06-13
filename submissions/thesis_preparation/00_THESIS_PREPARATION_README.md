# FASSD Thesis Preparation Folder

**Project:** FASSD — Forensic Acoustics for Synthetic Speech Detection  
**Purpose:** Gather, verify, organize, and structure thesis-writing inputs before drafting full chapters.  
**Created:** 2026-06-13  
**Rule:** Documentation preparation only — no training code, release code, models, datasets, or evaluation outputs were modified.

---

## Purpose of This Folder

This folder is the **single working area** for thesis preparation. It contains:

- Extracted template requirements (where source PDF is available)
- A verified master fact sheet with source paths
- A source inventory for citation and chapter mapping
- Chapter-to-evidence maps, proposed structure, results tables, figure plans
- Abbreviations, reference gap analysis, missing-information questionnaire
- Claims/wording rules and a staged writing plan
- A thesis skeleton (headings + bullet notes only — **no full prose**)

All thesis claims must trace back to repository evidence or be marked **TBD**.

---

## What Was Scanned

### Primary narrative and scope

| Path | Status |
|------|--------|
| `PROJECT_STORY_FROM_DAY_ONE.md` | Found — primary evolution narrative |
| `FASSD - Scope.md` | Found — canonical scope |
| `README.md` | Found — project overview |
| `reports/COMPLETE_PROJECT_STORY.md` | Found |
| `reports/FULL_PROJECT_DOCUMENTATION.md` | Found |
| `reports/PREVIOUS_PIPELINE_WORK.md` | Found |
| `reports/FORENSIC_PRODUCT_ROADMAP.md` | Found |
| `reports/PHASE7_THESIS_RATIONALE.md` | Found |

### Phase closure and architecture

| Path | Status |
|------|--------|
| `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md` | Found |
| `reports/phase7/PHASE7_FINAL_STATUS_FREEZE.md` | Found |
| `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` | Found |
| `reports/phase8/PHASE8_START_HERE.md` | Found |
| `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md` | Found |
| `reports/phase8/freeze/phase8g_limitations_and_claims.md` | Found |
| `reports/phase8/freeze/phase8g_phase9_handoff_plan.md` | Found |

### Release, validation, and audit

| Path | Status |
|------|--------|
| `release/README_RELEASE.md` | Found |
| `release/MODEL_REGISTRY.md` | Found |
| `release/config/evidence_calibration.json` | Found |
| `reports/phase9/final_release/phase9g_final_release_report.md` | Found |
| `reports/phase9/integration_docs/phase9f_known_limitations.md` | Found |
| `reports/phase9/integration_docs/phase9f_release_file_map.md` | Found |
| `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md` | Found |
| `reports/release_audit/phase2_origin_release_2026-06-13/` | Found |
| `reports/release_audit/phase3_controlled_experiments_2026-06-13/` | Found |
| `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/` | Found |
| `reports/release_audit/phase5_partial_redesign_2026-06-13/` | Found |
| `reports/release_audit/phase6_calibration_2026-06-13/` | Found |
| `reports/release_audit/phase7_final_release_2026-06-13/` | Found |

### Results and data statistics

| Path | Status |
|------|--------|
| `reports/evaluation/comprehensive_evaluation_report.md` | Found |
| `data/statistics/unified_dataset_stats.json` | Found |
| Model cards under `release/models/` | Found |
| `release/models/partial_fabrication_experimental_p5b/partial_report_contract.json` | Found |

### Figures and images

| Path | Status |
|------|--------|
| `images/` (root) | **Not found in repository** (referenced in `README.md`) |
| `reports/figures/` | **Not found as top-level folder** |
| `reports/evaluation/figures/` and `reports/phase8/models/**/figures/` | Found — hundreds of PNG plots |
| `reports/phase9/app/phase9e_p3_8variant_eval/**/waveform_*.png` | Found — demo waveform screenshots |

### University template and external materials

| Path | Status |
|------|--------|
| `thesis_layout.pdf` | **Not found in repository** (still TBD) |
| `submissions/title defence/Forensic_Acoustics_for_Synthetic_Speech_Detection_Title_Defence.pptx` | **Found** — 18 slides; IST + NCCIA collaboration stated |
| `research_article/1.pdf` … `research_article/9.pdf` | **Found** — 9 literature PDFs (titles extracted; see `09_REFERENCES_RESEARCH_GAP_PLAN.md`) |

**Note:** Root-level paths `Title Defence/` and `Research Article/` referenced in `README.md` are **not** present; the active copies live under `submissions/title defence/` and `research_article/`.

---

## What Was Created

| File | Description |
|------|-------------|
| `00_THESIS_PREPARATION_README.md` | This file |
| `01_TEMPLATE_REQUIREMENTS_EXTRACTED.md` | Template structure + checklist |
| `02_PROJECT_FACTS_MASTER.md` | Verified fact sheet with sources |
| `03_SOURCE_INVENTORY.csv` | Scanned source inventory |
| `04_THESIS_CHAPTER_SOURCE_MAP.md` | Chapter-to-evidence map |
| `05_PROPOSED_THESIS_STRUCTURE.md` | FASSD-adapted thesis outline |
| `06_RESULTS_TABLES_TO_USE.md` | Thesis-ready result tables |
| `07_FIGURES_AND_DIAGRAMS_TO_CREATE.md` | Figure plan |
| `08_ABBREVIATIONS_GLOSSARY.md` | Abbreviations and glossary |
| `09_REFERENCES_RESEARCH_GAP_PLAN.md` | Literature plan (no invented refs) |
| `10_MISSING_INFORMATION_QUESTIONNAIRE.md` | Items for student/supervisor to fill |
| `11_CLAIMS_AND_WORDING_RULES.md` | Allowed/forbidden thesis wording |
| `12_FIRST_DRAFT_WRITING_PLAN.md` | Staged writing plan |
| `13_THESIS_SKELETON_NO_FULL_TEXT.md` | Headings + bullet notes only |

---

## What Is Still Missing

1. **`thesis_layout.pdf`** — required to confirm exact university formatting, page order, reference style, and department boilerplate.
2. **Student/administrative details** — names, registration numbers, supervisor names, department, month/year, dedication, acknowledgements.
3. **`research_article/*.pdf`** — 9 papers found; full bibliographic cleanup and in-text mapping still needed in `09_REFERENCES_RESEARCH_GAP_PLAN.md`.
4. **`submissions/title defence/*.pptx`** — found; contains early binary-output and NCCIA collaboration wording that must be reconciled with final experimental scope (see `11_CLAIMS_AND_WORDING_RULES.md`).
5. **Root `images/` folder** — not in repo; use `reports/` figure paths instead or recreate diagrams.
6. **Dataset permission/citation strings** — ASVspoof, LibriSpeech, VCTK, YouTube/broadcast collection permissions (TBD).
7. **NCCIA / external collaboration wording** — whether and how to mention (TBD).
8. **Final thesis title sign-off** — options exist; one official title must be chosen.
9. **Which numeric results are “final” for defense** — internal leakage-safe vs external `testing_audios` must be stated explicitly in front matter.

---

## Strict Warning: Honest, Evidence-Based Claims

The FASSD project **deliberately** documents failures, rejected models, and external-test limitations. The thesis must **not** overclaim.

**Always state:**

- The final system is an **experimental forensic audio decision-support prototype**, not legal proof.
- **Multi-axis evidence indicators** (origin, replay, mixer/channel, partial fabrication) require **manual review**.
- **Replay** and **mixer/channel** evidence do **not** mean AI-generated speech.
- **No partial evidence** does **not** mean authentic.
- Report **both** leakage-safe internal metrics **and** external `testing_audios` failures.

**Never claim:**

- Proves audio is fake / court-ready / detects all deepfakes / production-ready forensic system.

See `11_CLAIMS_AND_WORDING_RULES.md` for replacement phrases.

---

## Recommended Next Step

1. Fill `10_MISSING_INFORMATION_QUESTIONNAIRE.md` (especially admin details and final title).
2. Obtain or add `thesis_layout.pdf` to the repo or shared folder; update `01_TEMPLATE_REQUIREMENTS_EXTRACTED.md` if the PDF differs from the assumed structure.
3. Collect `Research Article/` PDFs or EndNote library; update `09_REFERENCES_RESEARCH_GAP_PLAN.md`.
4. Review `05_PROPOSED_THESIS_STRUCTURE.md` and `13_THESIS_SKELETON_NO_FULL_TEXT.md` with supervisor.
5. Begin **Stage 1** in `12_FIRST_DRAFT_WRITING_PLAN.md` — finalize structure, then write Chapter 1.
