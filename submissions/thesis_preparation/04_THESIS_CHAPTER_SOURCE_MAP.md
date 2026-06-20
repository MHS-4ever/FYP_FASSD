# Thesis Chapter Source Map

Maps each thesis section to repository evidence, figures, missing information, and claim warnings.

---

## Front Matter

### What this section should say

- Title page with official project and degree details
- Approval, declaration, dedication, acknowledgement (per template)
- Lists of tables, figures, abbreviations

### Files that support it

| File | Use |
|------|-----|
| `(IST-Dean-F-18)_S_Project Proposal Form-1.docx` | **Official title, team, dates, approved scope** |
| `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` | Scope boundary and wording |
| `submissions/title defence/*.pptx` | Historical motivation only — not scope authority |
| `reports/phase9/final_release/phase9g_final_release_report.md` | Demo package name (testing interface) |
| `08_ABBREVIATIONS_GLOSSARY.md` | Abbreviations page |
| `thesis_layout.pdf` | **TBD — not in repo** |

### Figures/tables

- None in front matter except lists auto-generated from thesis body

### Missing information

- All student/supervisor/department/date fields
- Exact template page order from PDF

### Warning notes

- Do not use "Forensic Deepfake Audio Detector" as thesis title unless supervisor overrides Phase 9 naming check (`reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`)

---

## Abstract

### What this section should say

- Problem: synthetic speech and audio manipulation threaten evidence integrity
- Approach: **official software ML deliverable achieved**; **extended** multi-axis prototype documented separately
- Methods: proposal plan (LCNN, ASVspoof, LFCC/log-mel) + extensions; Gradio demo testing; Next.js intended frontend
- Results: strong internal controlled metrics; external `testing_audios` shows origin/replay/mixer limitations; partial improved after Phase 5
- Conclusion: experimental decision-support with manual review — not legal proof

### Files that support it

| File | Use |
|------|-----|
| `02_PROJECT_FACTS_MASTER.md` | Verified numbers |
| `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` | Final matrix summary |
| `reports/phase8/freeze/phase8g_limitations_and_claims.md` | Claim limits |

### Figures/tables

- None in abstract (optional: no figure)

### Missing information

- Word limit from `thesis_layout.pdf`
- Final keyword list approval

### Warning notes

- Lead with **decision-support** framing
- Include one explicit limitation sentence (external generalization)

---

## Chapter 1 — Introduction

### What this section should say

- **Motivation:** AI synthetic speech risks (proposal form summary)
- **Background:** anti-spoofing baseline vs extended forensic analysis
- **Approved scope and extended boundary:** official LCNN/ASVspoof plan first; Phase 7–9 extensions second
- **Objectives:** six official objectives; then extended objectives (multi-axis, reports, deployment)
- **Scope:** software deliverable achieved; extensions documented separately
- **Deployment:** **deepfakedetection.dev** = primary UI; FYP `release/` = backend source; `FRONTEND_AND_DEPLOYMENT_STORY.md` authoritative
- **Environment / SDGs:** TBD supervisor approval
- **Thesis outline:** chapter roadmap

### Files that support it

| File | Use |
|------|-----|
| `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` | Official vs extended scope, deployment framing |
| `submissions/title defence/*.pptx` | Motivation only — NCCIA historical, not continuing partner |
| `reports/PHASE7_THESIS_RATIONALE.md` | Extended forensic rationale |
| `PROJECT_STORY_FROM_DAY_ONE.md` | Narrative arc |
| `README.md` | Core idea diagram text |
| `reports/FORENSIC_PRODUCT_ROADMAP.md` | Product questions |

### Figures/tables

| Figure | Source |
|--------|--------|
| High-level pipeline (proposed) | Adapt from `README.md` text flow; create new — see `07_FIGURES_AND_DIAGRAMS_TO_CREATE.md` |
| Project evolution timeline | Create from `PROJECT_STORY_FROM_DAY_ONE.md` phases |

### Missing information

- NCCIA naming decision (questionnaire A3)
- Next.js completion status at submission
- Department exact wording (Computing vs Department of Computer Science)

### Warning notes

- Do not present NCCIA as continuing official partner without confirmation
- Do not describe Gradio as final submission application
- Do not imply proposal originally promised Phase 9 multi-axis release

---

## Chapter 2 — Literature Survey

### What this section should say

- Historical spoofing and anti-spoofing (LA, DF, PA)
- Deepfake audio: synthesis, conversion, replay
- Features: LFCC, MFCC, log-mel spectrograms
- CNN/ResNet and AASIST graph-attention approaches
- SSL embeddings (wav2vec2/WavLM-style) for speech representations
- Replay/channel artifacts and partial fabrication detection gaps
- **Research gaps:** binary benchmark focus vs forensic multi-axis need
- **Problem statement:** formal alignment with FASSD updated scope

### Files that support it

| File | Use |
|------|-----|
| `09_REFERENCES_RESEARCH_GAP_PLAN.md` | RA1–RA9 catalog with DOIs where found |
| `research_article/1.pdf`–`9.pdf` | Primary literature PDFs |
| `reports/PHASE7_THESIS_RATIONALE.md` | Research gap §5 |
| `FASSD - Scope.md` | Problem statement §3 |
| `reports/phase7/phase7e_aasist_experiment/PHASE7E0_AASIST_EXPERIMENT_PLAN.md` | AASIST context (paper not in folder) |
| `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md` | Multi-axis rationale |

### Figures/tables

| Table | Content |
|-------|---------|
| Comparison of prior work vs FASSD | Create from gap analysis — sources TBD |
| ASVspoof dataset summary | From `data/statistics/unified_dataset_stats.json` |

### Missing information

- ASVspoof 2021 official citation (not in `research_article/`)
- AASIST primary paper (not in folder)
- Final keyword list approval

### Warning notes

- Do not invent references — mark TBD
- When citing ASVspoof, use official challenge papers once obtained

---

## Chapter 3 — Methodology

### What this section should say

- Research design: phased experimental evolution (Phases 0–9 + release audit)
- Dataset collection: ASVspoof + RealWorld + Phase 7C1 controlled forensic set
- Preprocessing: resample, normalize, 4 s chunks, VAD
- Feature extraction pipelines
- Model experiments chronology: baseline → ResNet → environmental → Hybrid → Phase 7 → Phase 8 axes → release audit repairs
- Segmentation and partial fabrication method (F9 removal)
- Fusion and report layer (7C4-v2 historical; final multi-axis fusion)
- Tools: Python, PyTorch, scikit-learn, Gradio, FastAPI
- Ethical considerations: holdout integrity, honest failure reporting

### Files that support it

| File | Use |
|------|-----|
| `PROJECT_STORY_FROM_DAY_ONE.md` | Full methodology story |
| `reports/FULL_PROJECT_DOCUMENTATION.md` | Hybrid architecture, 12 features |
| `reports/PREVIOUS_PIPELINE_WORK.md` | Early phases |
| `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md` | Final architecture |
| `reports/phase8/label_schema/phase8a_multi_axis_label_schema.md` | Labels |
| `release/MODEL_REGISTRY.md` | Final active models |
| `reports/phase9/integration_docs/phase9f_release_file_map.md` | Implementation layout |
| `data/statistics/unified_dataset_stats.json` | Dataset stats |

### Figures/tables

| Item | Source |
|------|--------|
| Dataset composition chart | `06_RESULTS_TABLES_TO_USE.md` unified stats |
| Preprocessing/segmentation pipeline | Create — `07_FIGURES_AND_DIAGRAMS_TO_CREATE.md` |
| Multi-axis architecture diagram | Phase 8A ASCII in `PHASE8A_ARCHITECTURE_FREEZE.md` |
| Phase 7C1 role matrix | `reports/phase7/phase7_dataset/` |

### Missing information

- Exact hardware specs for all training runs (partial: RTX 3050 in PREVIOUS_PIPELINE)
- Dataset permission letters

### Warning notes

- Clearly separate **rejected** experiments (AASIST, 7C3, Phase 4 v3) from **active release** models
- State Phase 7C4-v2 is prototype reference not final product logic alone

---

## Chapter 4 — Results and Discussion

### What this section should say

- **Official-scope results:** Tables 4.1–4.3 (LCNN, LFCC/log-mel, EER)
- **Extended-system results:** Phase 7–9, release audit, Table 4.16
- **Demo interface results:** Phase 9 184-file regression — demo/testing only, not official proposal eval alone

### Files that support it

| File | Use |
|------|-----|
| `06_RESULTS_TABLES_TO_USE.md` | All thesis tables |
| `reports/evaluation/comprehensive_evaluation_report.md` | Hybrid eval |
| `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` | Phase 7 tables |
| `reports/release_audit/phase7_final_release_2026-06-13/` | Final matrix |
| `reports/release_audit/phase2_origin_release_2026-06-13/` | Origin metrics |
| `reports/release_audit/phase5_partial_redesign_2026-06-13/` | Partial fix |
| `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md` | Demo PASS |

### Figures/tables

| Item | Source |
|------|--------|
| All result tables | `06_RESULTS_TABLES_TO_USE.md` |
| ROC / confusion matrices | `reports/evaluation/figures/`, `confusion_matrices/` |
| Partial timelines | `reports/phase8/models/phase8e2/figures/` |
| Demo waveforms | `reports/phase9/app/phase9e_p3_8variant_eval/` |
| testing_audios failure table | `phase7_final_testing_audios_matrix.md` |

### Missing information

- Which result set supervisor wants emphasized for defense
- Statistical significance tests (mostly count-based in repo)

### Warning notes

- **Always pair** leakage-safe internal metrics with external failures
- Partial 1.0000 on testing_audios matrix is gated binary — explain gating
- Do not present ResNet 2.61% EER as final product performance
- Mixer recall 0% on external set must be stated clearly

---

## Chapter 5 — Conclusion and Future Work

### What this section should say

- Objective-wise conclusions (each original scope item → what was achieved experimentally)
- Contributions: multi-axis schema, release audit repair cycle, partial F9 diagnosis, evidence-band UI
- Limitations: external generalization, small forensic corpus, experimental status
- Future: larger forensic datasets, improved mixer/replay generalization, MP4 path, optional SSL improvements, operational validation

### Files that support it

| File | Use |
|------|-----|
| `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md` | Lessons learned |
| `reports/phase8/freeze/phase8g_limitations_and_claims.md` | Allowed/not allowed |
| `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` | Final disclaimers |
| `reports/phase9/final_release/phase9g_final_release_report.md` | Handoff status |
| `FASSD - Scope.md` | Objectives checklist |

### Figures/tables

- Optional summary table: objective vs outcome vs limitation

### Missing information

- Supervisor-required future work priorities

### Warning notes

- End with manual review and non-legal-proof disclaimer
- Do not promise court deployment

---

## References

### What this section should say

- Numbered bibliography per university style (**TBD**)

### Files that support it

| File | Use |
|------|-----|
| `09_REFERENCES_RESEARCH_GAP_PLAN.md` | Paper list and gaps |
| `Research Article/*.pdf` | **TBD** |

### Missing information

- Entire bibliography content

---

## Appendices

### What this section should say

- Sample forensic JSON/report output
- Phase 7C1 condition definitions
- Full testing_audios per-file table
- API contract excerpt
- Additional plots

### Files that support it

| File | Use |
|------|-----|
| `release/sample_outputs/` | Sample JSON/MD |
| `reports/phase9/integration_docs/phase9f_api_contract.md` | API |
| `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_predictions.csv` | Full matrix |
| `release/models/partial_fabrication_experimental_p5b/partial_report_contract.json` | Partial wording |

### Warning notes

- Redact any paths if thesis submission requires anonymization (TBD)
