# FASSD Project Facts Master Sheet

**Scope authority:** Official approved scope = `(IST-Dean-F-18)_S_Project Proposal Form-1.docx`. Extended work framing = `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`.  
**Last verified against repo:** 2026-06-13 (proposal-form correction pass)

---

## 1. Project Identity

| Item | Value | Source |
|------|-------|--------|
| Short name | FASSD | Proposal form; project convention |
| **Official thesis title** | **Forensic Acoustics for Synthetic Speech Detection** | Proposal form; `(IST-Dean-F-18)_S_Project Proposal Form-1.docx` |
| Degree program | BS CS | Proposal form |
| Department | Computing | Proposal form |
| **Official deliverable type** | Software system (deepfake speech detection) | Proposal form |
| Extended system status | Experimental forensic decision-support prototype; not court-ready proof | `release/MODEL_REGISTRY.md`, `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` |
| **Primary user-facing software deliverable** | Deployed Next.js web app at **https://www.deepfakedetection.dev/** (separate hosting repository) | `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md` |
| FYP backend package label | Deepfake Audio Detector — Local Demo (Phase 9G) | `reports/phase9/final_release/phase9g_final_release_report.md` — **inference backend source** in `E:\FYP\release/` |
| Production inference API | https://api.deepfakedetection.dev/ | `FRONTEND_AND_DEPLOYMENT_STORY.md` |

**Scope document hierarchy:** Proposal form (official) → `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` → `PROJECT_STORY_FROM_DAY_ONE.md` → `FASSD - Scope.md` (extended Phase 8 reference, **not** sole official scope).

**Naming caution:** Present **deepfakedetection.dev** as the primary user-facing software deliverable. The FYP `release/` folder is the Phase 9 inference **backend source**, not the main UI story for thesis/defense.

---

## 2. Team and Administration

| Item | Value | Source |
|------|-------|--------|
| Student name(s) | Rana M. Areeb; M. Hasnain | Proposal form; `code/features/feature_extraction.py` |
| Registration number(s) | TBD | Not in repository |
| Supervisor | Sir Faran Mehmood | Proposal form |
| Co-supervisor | TBD | Not in proposal extract |
| Degree program | BS CS | Proposal form |
| Department | Computing | Proposal form |
| Institute / university | Institute of Space Technology | Proposal form; title defence PPTX |
| Project start date | 12 October 2025 | Proposal form |
| Project finish date | 12 June 2026 | Proposal form |
| External consultation | Historical external consultation during project (including early NCCIA-related discussions per title defence) | Title defence PPTX — **not a continuing formal partner unless confirmed** |
| Supervisor designation spelling | “Sir Faran Mehmood” in proposal — confirm official title (Mr./Dr./Sir) | **TBD** — questionnaire |
| Early title-defence framing | Binary “Authentic / AI-Generated” output; NCCIA named as collaborator | Title defence PPTX — **soften in thesis**; see `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` |

---

## 3. Motivation and Problem

| Statement | Source |
|-----------|--------|
| Modern AI voice generation, replay, compression, editing, and partial fabrication make audio authenticity analysis difficult | `FASSD - Scope.md` |
| A simple real/fake classifier is insufficient because human speech can be replayed without being AI-generated; AI speech can be replayed; partial fake insertion exists; channel artifacts can look suspicious without synthetic origin | `FASSD - Scope.md`, `reports/PHASE7_THESIS_RATIONALE.md` |
| Low EER on ASVspoof does not mean real-world forensic success — broadcast Trump test: 6 real + 2 fake, all 8 predicted fake (100% FP on real in that small test) | `PROJECT_STORY_FROM_DAY_ONE.md`, `reports/PREVIOUS_PIPELINE_WORK.md` |
| Stakeholders need structured forensic reports, not a single REAL/FAKE button | `reports/FORENSIC_PRODUCT_ROADMAP.md`, `reports/PHASE7_THESIS_RATIONALE.md` |

---

## 4. Scope

### 4A. Official approved scope (proposal form)

**Source:** `(IST-Dean-F-18)_S_Project Proposal Form-1.docx`; summary in `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §2–4

- ML system for detecting AI-generated or manipulated speech using spectral and forensic acoustic cues  
- Bonafide/human vs spoof/AI-generated classification  
- Deepfake voice embedded in real recordings  
- Replayed synthetic speech (device rerecording)  
- ASVspoof 2021 DF + LA, augmentation (MUSAN, RIR, codec), LFCC + Log-Mel, **LCNN binary classifier**  
- Evaluation: EER, ROC-AUC, accuracy, confusion matrices  
- Deliverable: **software system** for external test audio  

### 4B. Extended development (beyond proposal — not replacement)

**Source:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §5; `FASSD - Scope.md`; Phase 7/8/9 docs

- ResNet, HybridResNetEnvironmental, unified real-world dataset, Phase 6 explanation  
- Controlled forensic testing, AASIST experiment (rejected as final model)  
- Multi-axis origin / replay / mixer / partial evidence architecture  
- Fusion, abstention, evidence-band reports, release audit  
- **Deployed web platform:** https://www.deepfakedetection.dev/ — separate hosting repo (`thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`)  
- **Phase 9 inference backend source:** `release/` in FYP ML repo — powers production API on DigitalOcean  
- Motivation for extensions: limitations discovered in implementation + additional forensic-review requirements suggested during **supervision and external consultation**  

### 4C. Out of scope (both official and thesis)

- Legal proof / court-ready certification  
- Speaker identity verification, diarization, transcription as core goals  
- Claiming NCCIA endorsement or continuing partnership without confirmation  

**Secondary reference (extended only):** `FASSD - Scope.md` — Phase 8 six-area scope; do not cite as official approved baseline alone.

---

## 5. Datasets

| Dataset / corpus | Scale / role | Source |
|------------------|--------------|--------|
| ASVspoof 2021 LA | 181,566 files | `PROJECT_STORY_FROM_DAY_ONE.md`, `data/statistics/unified_dataset_stats.json` |
| ASVspoof 2021 DF | 611,829 files | Same |
| ASVspoof PA | 943,110 files (unified stats) | `data/statistics/unified_dataset_stats.json` |
| RealWorld collected | 157,414 samples | `data/statistics/unified_dataset_stats.json` |
| **Unified total** | **1,893,919 samples**, 73,421 speakers | `data/statistics/unified_dataset_stats.json` |
| Label split | spoof 1,573,308; bonafide 320,611 | `data/statistics/unified_dataset_stats.json` |
| Attack types | replay 816,480; conversion 589,212; synthesis 167,616; bonafide 320,611 | Same |
| Augmentation (Phase 2) | 611,829 additional augmented samples | `PROJECT_STORY_FROM_DAY_ONE.md` |
| Phase 7C1 local forensic set | 184 files, 8 conditions × 23 files | `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` |
| Phase 7A holdout / testing_audios | External heterogeneous test set (25 files in final matrix) | `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` |
| LibriSpeech, VCTK, YouTube broadcast/podcast/social | Mentioned in unified pipeline | `PROJECT_STORY_FROM_DAY_ONE.md` |

**Speaker-independent test overlap:** 0 speakers between train and test in Phase 5 eval — `reports/evaluation/comprehensive_evaluation_report.md`

---

## 6. Features

| Feature set | Details | Source |
|-------------|---------|--------|
| LFCC | 20 coefficients | `PROJECT_STORY_FROM_DAY_ONE.md`, `reports/PREVIOUS_PIPELINE_WORK.md` |
| Log-mel / MFCC-style | 64 frequency bins | Same |
| Environmental (12 features) | RT60, SNR, spectral tilt, flatness, rolloff, background noise, etc. | `PROJECT_STORY_FROM_DAY_ONE.md`, `reports/FULL_PROJECT_DOCUMENTATION.md` |
| SSL embeddings | WavLM/wav2vec-style frozen embeddings for origin axis (release) | `release/MODEL_REGISTRY.md`, `release/models/origin/origin_file_model__ssl__model_card.md` |
| Acoustic/channel features | Replay and mixer axes (59 input, 50 selected) | `release/models/replay/replay_file_model__acoustic__model_card.md` |
| Partial segment features | combined_no_f9 (F9 within-file percentile features removed in Phase 5) | `release/MODEL_REGISTRY.md`, `reports/release_audit/phase5_partial_redesign_2026-06-13/phase5_partial_redesign_decision.md` |

---

## 7. Models Tried

| Model / experiment | Role | Outcome | Source |
|--------------------|------|---------|--------|
| LCNN baseline (LFCC) | Early baseline | 9.68% EER clean; 15.71% augmented | `PROJECT_STORY_FROM_DAY_ONE.md` |
| Log-mel CNN (ResNet-style) | ASVspoof detector | 0.57% clean; 2.61% augmented EER | Same |
| Environmental Isolation Forest | Anomaly detector | ~24.5% accuracy — rejected | `PROJECT_STORY_FROM_DAY_ONE.md` |
| Environmental supervised classifier | RF-style | 81.69% on ASVspoof — insufficient alone | Same |
| HybridResNetEnvironmental | Log-mel + 12 env features, ~2.9M params | 16.21% test EER; strong manipulation evidence but poor clean-human specificity in Phase 7 | `reports/evaluation/comprehensive_evaluation_report.md`, `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` |
| HybridResNet fine-tune 7C3-v1 | Origin-style fine-tune | **Rejected** — manipulation sensitivity collapsed | `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md` |
| HybridResNet 7C3-R2 | Risk-tuned | **Rejected** as standalone | Same |
| Phase 7C4-v1 decision layer | Fusion | **Rejected** — too many clean-human false alarms | Same |
| Phase 7C4-v2 decision layer | Fusion prototype | **Accepted as prototype only** | Same |
| AASIST-L pretrained + fine-tuned | Anti-spoof branch | **Rejected** — 22/23 clean-human false alarms (pretrained) | `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` |
| Phase 8E-1 axis models (LR on features) | Origin/replay/mixer file models | Experimental CV metrics; small dataset | `reports/phase8/models/phase8e1/phase8e1_training_report.md` |
| Phase 2 origin SSL retrain | Release origin axis | Leakage-safe test bal-acc 0.95; testing_audios 0.8731 | `reports/release_audit/phase2_origin_release_2026-06-13/phase2_origin_release_report.md` |
| Phase 4 two-stage manipulation v3 | Unified manipulation | **STOP** — 20% Stage-1 recall on testing_audios | `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/phase4_two_stage_manipulation_v3_decision.md` |
| Phase 5 partial no-F9 localizer | Partial segment | **PASS** oracle stop rule; promoted | `reports/release_audit/phase5_partial_redesign_2026-06-13/phase5_partial_redesign_decision.md` |

---

## 8. Final Active Release Models (2026-06-13 audit)

| Axis | Artifact | Threshold | Feature | Source |
|------|----------|-----------|---------|--------|
| Origin | `release/models/origin/origin_file_model__ssl__experimental.joblib` | 0.92 | SSL | `release/MODEL_REGISTRY.md` |
| Replay | `release/models/replay/replay_file_model__acoustic__experimental.joblib` | 0.65 | acoustic | Same |
| Mixer/channel | `release/models/mixer/mixer_file_model__acoustic__experimental.joblib` | 0.75 | acoustic | Same |
| Partial segment | `release/models/partial_segment/partial_segment_model__combined__experimental.joblib` | 0.95 | combined_no_f9 | Same |
| UI calibration | `release/config/evidence_calibration.json` | Low/Medium/High bands | Phase 6 | Same |

**Inactive reference only:** AASIST, HybridResNet — `release/MODEL_REGISTRY.md`, `reports/phase9/integration_docs/phase9f_known_limitations.md`

---

## 9. Rejected / Inactive Models

| Model | Status | Source |
|-------|--------|--------|
| 7C3-v1 Hybrid fine-tune | Rejected | `reports/phase7/PHASE7_FINAL_STATUS_FREEZE.md` |
| 7C3-R2 standalone | Rejected | Same |
| 7C4-v1 fusion | Rejected | Same |
| AASIST pretrained/fine-tuned | Rejected (`reject_for_now`) | Same; `reports/phase9/final_release/phase9g_final_release_report.md` |
| HybridResNet in release inference | Rejected (`reject_for_now`) | Same |
| Phase 4 manipulation v3 | Not shipped | `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/phase4_two_stage_manipulation_v3_decision.md` |
| Environmental Isolation Forest | Rejected early | `PROJECT_STORY_FROM_DAY_ONE.md` |

---

## 10. System Architecture and Deployment

### Extended backend (experimental prototype)

```text
Audio input → preprocessing/segmentation → parallel feature extraction
  → origin (SSL) + replay (acoustic) + mixer (acoustic) + partial (segment)
  → fusion + abstention → evidence-band report (JSON/MD/PDF)
```

**Source:** `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md`, `release/MODEL_REGISTRY.md`

### Deployment layers (thesis must distinguish)

| Layer | Role | Thesis framing |
|-------|------|----------------|
| Backend inference + reporting | Phase 9 `release/` pipeline → production API on DigitalOcean | Extended implementation core |
| **Deployed web platform** | https://www.deepfakedetection.dev/ — **primary user-facing deliverable** | Separate hosting repo; `FRONTEND_AND_DEPLOYMENT_STORY.md` |
| **FYP `release/` folder** | Phase 9 inference backend **source** | Vendored into website repo for Docker deploy |
| Official proposal deliverable | Software tool for evaluating external test audio | Achieved via baseline + extended software stack |

**Source:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §10; `reports/website/PARTNER_INTEGRATION_GUIDE.md`; `release/README_RELEASE.md`

---

## 11. Phase-by-Phase Timeline (Summary)

| Phase | Focus | Key outcome | Source |
|-------|-------|-------------|--------|
| 0–1 | ASVspoof setup, LFCC/log-mel features | Feature pipeline working | `PROJECT_STORY_FROM_DAY_ONE.md` |
| 2 | Augmentation | 611,829 aug samples | Same |
| 3 | Baseline CNN | 15.71% EER augmented | Same |
| 4.1 | LFCC vs log-mel | Log-mel robust 15.25% vs LFCC 15.71% | Same |
| 4.2 | Deep ResNet | 2.61% EER augmented | Same |
| 4.3 | Environmental classifier | 81.69%; broadcast failure | Same |
| 0–6 rebuild | Unified dataset + HybridResNet | 1.89M samples; 16.21% test EER | `data/statistics/unified_dataset_stats.json`, `reports/evaluation/comprehensive_evaluation_report.md` |
| 7 | Controlled forensic eval, fine-tunes, AASIST | Binary strategy insufficient; 7C4-v2 prototype | `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md` |
| 8 | Multi-axis architecture + axis models | 8A freeze; 8E models | `reports/phase8/PHASE8_START_HERE.md` |
| 9 | Local demo packaging | Phase 9G PASS | `reports/phase9/final_release/phase9g_final_release_report.md` |
| Release audit 0–7 | Origin repair, partial redesign, calibration | Final testing_audios matrix | `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` |

---

## 12. Final Validation Results (Selected)

### Phase 7C1 Hybrid baseline (controlled, 23 per category)

- clean_human_false_alarm: 17/23; partial_fabrication_detected: 43/46  
**Source:** `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`

### Phase 7C4-v2 prototype

- clean_human_false_alarm: 7/23; partial_fabrication_detected: 44/46  
**Source:** Same

### Phase 9 demo freeze (184 files)

- 184/184 evaluated; human_clean_false_suspicious_rate = 0.0  
**Source:** `reports/phase9/integration_docs/phase9f_known_limitations.md`

### Release audit final testing_audios matrix (25 files)

| Axis | Balanced accuracy | Recall | Specificity |
|------|------------------:|-------:|------------:|
| Origin (n=18) | 0.8250 | 0.9000 | 0.7500 |
| Replay | 0.7738 | 0.7143 | 0.8333 |
| Mixer | 0.4783 | 0.0000 | 0.9565 |
| Partial | 1.0000 | 1.0000 | 1.0000 |

**Source:** `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_matrix.md`

*Note: Partial binary matrix uses gated detection; interpret with Phase 5 limitation notes.*

### Leakage-safe internal (stronger than external)

- Origin test bal-acc: 0.9500 (`phase2_origin_release_report.md`)  
- Partial oracle top-5: 10/10 (`phase5_partial_redesign_decision.md`)

---

## 13. Limitations

| Limitation | Source |
|------------|--------|
| Small Phase 7C1 / Phase 8E controlled corpus (46–184 files) | `release/models/origin/origin_file_model__ssl__model_card.md`, `reports/phase8/models/phase8e1/phase8e1_training_report.md` |
| External replay/mixer generalization weak | `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` |
| Origin false positives on clean human (T1.2, T4.1); WhatsApp AI miss (T4.5) | Same |
| Partial: experimental manual-review only; single-window spikes possible | `reports/release_audit/phase5_partial_redesign_2026-06-13/phase5_partial_redesign_decision.md` |
| Phase 4 unified manipulation not shipped (20% recall) | `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/phase4_two_stage_manipulation_v3_decision.md` |
| Evidence bands fitted on leakage-safe dev — not legal probabilities | `release/config/evidence_calibration.json`, `release/MODEL_REGISTRY.md` |
| Conclusive authenticity decision: no | `reports/phase9/integration_docs/phase9f_known_limitations.md` |

---

## 14. Allowed Claims

**Source:** `reports/phase8/freeze/phase8g_limitations_and_claims.md`, `release/MODEL_REGISTRY.md`, `reports/phase9/integration_docs/phase9f_known_limitations.md`

- Experimental forensic audio **decision-support prototype**
- **Multi-axis evidence indicators** (origin, replay, mixer, partial)
- **Voice origin evidence** (not conclusive)
- **Replay/rerecording evidence** (does not mean AI-generated)
- **Mixer/channel evidence** (does not mean AI-generated)
- **Partial fabrication candidate regions** for manual review
- **Manual review recommended** when indicators conflict or are elevated
- System **avoids binary fake/real collapse** in final architecture
- Phase 5 demonstrates F9 feature removal fixed broad partial activation

---

## 15. Forbidden Claims

**Source:** Same as above + `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`

- Proves audio is fake / authentic with legal certainty
- Court-ready proof or operational deployment readiness
- Detects all deepfakes or all manipulations
- Replay means AI-generated
- Mixer/channel means AI-generated
- No partial evidence means authentic
- "Forensic Deepfake Audio Detector" as final product title (unless supervisor explicitly overrides Phase 9 naming rule)
- Presenting leakage-safe metrics alone without external failure disclosure

---

## 16. Ethical and Forensic-Safety Wording

| Principle | Wording guidance | Source |
|-----------|------------------|--------|
| Decision support only | "Experimental evidence indicator" not "verdict" | `release/MODEL_REGISTRY.md` |
| Manual review | Required for elevated/mixed indicators | `FASSD - Scope.md` |
| Origin under replay/mixer | "Inconclusive under replay/channel processing" | `reports/phase9/integration_docs/phase9f_known_limitations.md` |
| Partial detection | "Candidate region for manual forensic review" | `release/models/partial_fabrication_experimental_p5b/partial_report_contract.json` |
| No detection | "Does not prove authentic; subtle manipulations may be missed" | Same |
| Dataset ethics | Holdout integrity; no leakage across speakers/pairs | `FASSD - Scope.md` |
| Public audio collection | Broadcast/YouTube — permissions TBD | TBD |
| External consultation | Use neutral wording; do not imply NCCIA continuing partnership | `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §7 |

---

## 17. Hardware and Software (Evidence-Based)

| Item | Value | Source |
|------|-------|--------|
| Python environment | conda `fassd`, Python 3.10 recommended | `README.md` |
| GPU mentioned | RTX 3050 6GB (previous pipeline) | `reports/PREVIOUS_PIPELINE_WORK.md` |
| Frameworks | PyTorch, scikit-learn (release axes), Gradio, FastAPI | `release/README_RELEASE.md`, `reports/phase9/integration_docs/phase9f_release_file_map.md` |
| Mixed precision / TF32 | Used in ResNet training | `PROJECT_STORY_FROM_DAY_ONE.md` |

---

## 18. Open Items (TBD)

- Student registration numbers  
- Supervisor official designation spelling (Sir vs Mr. vs Dr.)  
- Department exact wording: Computing vs Department of Computer Science  
- Whether NCCIA may be named or only generic “external consultation”  
- Whether Next.js frontend will be complete before thesis submission  
- Confirm proposal form at `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.docx` is the final submitted version  
- Dataset citation strings; `thesis_layout.pdf` formatting rules  
- Complete BibTeX for RA1–RA9 and missing ASVspoof/AASIST/WavLM papers  

## 19. Official Approved Scope from Proposal Form

See **`16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §1–4** for full extract. Summary:

- **Identity:** FASSD, BS CS, Computing, IST, Oct 2025–Jun 2026, Sir Faran Mehmood, Rana M. Areeb & M. Hasnain, software deliverable  
- **Method:** ASVspoof 2021 DF+LA, augmentation, LFCC, Log-Mel, LCNN, EER/AUC evaluation  
- **Objectives:** bonafide/spoof classification, forensic cues, embedded deepfake, replay detection, robust pipeline, software system  

## 20. Extended Work Beyond Proposal

See **`16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` §5–10**. Includes ResNet/Hybrid, multi-axis models, fusion, release audit, **deployed web platform**, JSON/PDF reports. Framed as extensions from supervision/external consultation—not formal external deliverables unless confirmed.

## 21. Literature and Historical Materials

| Path | Contents |
|------|----------|
| `research_article/1.pdf`–`9.pdf` | Seed literature — see `09_REFERENCES_RESEARCH_GAP_PLAN.md` |
| `submissions/title defence/*.pptx` | Historical motivation; NCCIA mentioned — reconcile with §20 |
| `(IST-Dean-F-18)_S_Project Proposal Form-1.docx` | **Official scope authority** |
