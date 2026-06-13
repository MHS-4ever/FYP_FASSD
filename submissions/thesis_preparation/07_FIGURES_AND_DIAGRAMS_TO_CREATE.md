# Figures and Diagrams for Thesis

| Fig. No. (suggested) | Figure title | Existing source | Need to create | What it should show | Chapter |
|---------------------|--------------|-----------------|----------------|---------------------|---------|
| 1.1 | FASSD high-level processing pipeline | Text flow in `README.md` | **Yes** | Input audio → preprocessing → features → multi-axis inference → report/UI | Ch. 1 |
| 1.2 | Project evolution timeline | `PROJECT_STORY_FROM_DAY_ONE.md` phase list | **Yes** | Horizontal timeline: Phases 0–9 + release audit with scope pivots | Ch. 1 |
| 2.1 | Taxonomy of audio authenticity threats | None | **Yes** | Origin vs manipulation vs partial vs channel; human replay vs AI direct | Ch. 2 |
| 3.1 | Final multi-axis system architecture | ASCII in `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md` | **Yes** (polish) | Parallel origin/replay/mixer/partial → fusion → forensic-safe report | Ch. 3 |
| 3.2 | Dataset composition by source | `data/statistics/unified_dataset_stats.json` | **Yes** | Bar/pie: PA, DF, LA, RealWorld sample counts | Ch. 3 |
| 3.3 | Domain distribution (studio vs RealWorld) | Same JSON | **Yes** | Domain crosstab visualization | Ch. 3 |
| 3.4 | Preprocessing and segmentation pipeline | `release/src/segmentation.py`, Phase 6 docs | **Yes** | Resample, normalize, windowing, overlap, VAD | Ch. 3 |
| 3.5 | Feature extraction pipeline | `reports/FULL_PROJECT_DOCUMENTATION.md` | **Yes** | LFCC/log-mel, 12 env features, SSL, acoustic branch | Ch. 3 |
| 3.6 | HybridResNetEnvironmental architecture | `code/phase3/hybrid_resnet_environmental.py` (cite only) | **Yes** | Dual branch ResNet + env MLP fusion | Ch. 3 |
| 3.7 | Phase 7C1 forensic condition matrix | `reports/phase7/phase7_dataset/` | **Optional** | 8 conditions × role definitions | Ch. 3 |
| 3.8 | Partial fabrication segmentation method | `reports/release_audit/phase5_partial_redesign_2026-06-13/` | **Yes** | Window scores, oracle top-k, F9 removal, gating | Ch. 3 |
| 3.9 | Multi-axis fusion and abstention flow | `release/src/fusion_rules.py`, Phase 8F docs | **Yes** | Conflict handling, manual review paths | Ch. 3 |
| 4.1 | Baseline vs ResNet EER comparison | `06_RESULTS_TABLES_TO_USE.md` Tables 4.1–4.3 | **Yes** | Bar chart EER by model/feature | Ch. 4 |
| 4.2 | HybridResNet ROC curve (overall test) | `reports/evaluation/figures/roc_overall.png` | **No** | ROC for 254k test samples | Ch. 4 |
| 4.3 | HybridResNet binary confusion matrix | `reports/evaluation/confusion_matrices/overall_binary_cm.png` | **No** | Binary bonafide vs spoof CM | Ch. 4 |
| 4.4 | HybridResNet multiclass confusion matrix | `reports/evaluation/confusion_matrices/overall_multiclass_cm.png` | **No** | Attack-type CM | Ch. 4 |
| 4.5 | ROC by domain (ASVspoof vs RealWorld) | `roc_asvspoof.png`, `roc_realworld.png` | **No** | Domain comparison | Ch. 4 |
| 4.6 | Phase 7C1 clean-human false alarm comparison | Phase 7 summary tables | **Yes** | Hybrid vs 7C4-v2 vs AASIST clean-human FP counts | Ch. 4 |
| 4.7 | Phase 8E origin SSL probability histogram | `reports/phase8/models/phase8e1a/figures/origin_file_model__ssl__prob_hist.png` | **No** | Origin score distribution | Ch. 4 |
| 4.8 | Replay/mixer threshold tradeoff curves | `phase8e1a/figures/*_threshold_tradeoff.png` | **No** | Threshold selection evidence | Ch. 4 |
| 4.9 | Partial fabrication timeline example (AI) | `phase8e2/figures/*ai*fabricated*timeline.png` | **No** | Segment suspicion over time | Ch. 4 |
| 4.10 | Partial fabrication timeline example (human) | `phase8e2/figures/*human*fabricated*timeline.png` | **No** | Compare human partial case | Ch. 4 |
| 4.11 | T4.3 partial localization (release audit) | Narrative in Phase 5 decision | **Yes** | Waveform with 35–58 s label vs 46–50 s detection | Ch. 4 |
| 4.12 | Final testing_audios axis performance | Table 4.16 | **Yes** | Grouped bar: bal-acc/recall/spec per axis | Ch. 4 |
| 4.13 | Release audit before/after partial T4.3 | `phase7_final_release_report.md` | **Yes** | Broad activation vs localized Phase 5 fix | Ch. 4 |
| 4.14 | Evidence band UI card example | Phase 6 consistency report | **Yes** | Screenshot: Low/Medium/High not raw 0.999 | Ch. 4 |
| 4.15 | Gradio demo screenshot | `release/app_gradio.py` runtime | **Yes** | Upload UI + evidence cards (run locally) | Ch. 4 / Appx |
| 4.16 | Waveform with highlighted suspicious segment | `reports/phase9/app/phase9e_p3_8variant_eval/**/waveform_*.png` | **No** | Pick 1 human_fabricated + 1 ai_fabricated | Ch. 4 |
| 4.17 | Partial diagnostic by case group | `phase9d_p5f_p2_diagnostics/plots/high_segment_fraction_by_case_group.png` | **No** | Partial metric distribution | Ch. 4 |
| 4.18 | Model comparison diagram (active vs rejected) | `release/MODEL_REGISTRY.md` | **Yes** | Active 4 axes vs reference AASIST/Hybrid vs stopped Phase 4 v3 | Ch. 4 |
| 5.1 | Contribution summary diagram | Synthesis from closure reports | **Yes** | Multi-axis schema, audit cycle, demo packaging | Ch. 5 |
| A.1 | Sample PDF report excerpt | `release/src/pdf_report_generator.py` output | **Yes** | Redacted appendix screenshot | Appendix |
| A.2 | API response JSON structure | `phase9f_api_contract.md` | **Optional** | Schema diagram | Appendix |

---

## Priority Creation List (if time-limited)

1. **Fig 3.1** — Final architecture (essential)  
2. **Fig 4.12** — External testing_audios axis chart (essential honesty figure)  
3. **Fig 1.2** — Project timeline (examiner orientation)  
4. **Fig 4.15** — Gradio demo screenshot (product evidence)  
5. **Fig 4.11** — T4.3 partial localization (key forensic story)

---

## Existing Asset Directories

| Directory | Content |
|-----------|---------|
| `reports/evaluation/figures/` | Hybrid ROC curves |
| `reports/evaluation/confusion_matrices/` | Hybrid CMs |
| `reports/phase8/models/phase8e1a/figures/` | Axis probability/threshold plots |
| `reports/phase8/models/phase8e2/figures/` | Partial timeline PNGs |
| `reports/phase9/app/phase9e_p3_8variant_eval/` | 184 waveform highlight PNGs |
| `reports/phase9/partial_redesign/phase9d_p5f_p2_diagnostics/plots/` | Partial diagnostics |

**Note:** Root `images/` folder referenced in `README.md` is **not present** in repository.

---

## Figure Caption Rules

- State dataset/eval split in every results figure caption  
- Label external eval figures explicitly as `testing_audios` (heterogeneous, n=25)  
- For partial figures, include "candidate region for manual review — not proof of fabrication"
