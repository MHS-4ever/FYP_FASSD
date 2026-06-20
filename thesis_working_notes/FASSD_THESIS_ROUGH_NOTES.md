# FASSD Thesis Rough Notes

**Purpose:** Per-heading rough notes for thesis writing — one block per heading in `FASSD_Thesis_Structure.md`.  
**Detailed section notes file:** `thesis_working_notes/FASSD_THESIS_SECTION_NOTES.md` (use this for ChatGPT section-by-section prompts)  
**Primary software deliverable (user-facing):** Live web platform at https://www.deepfakedetection.dev/ (**separate hosting repository** — not in `E:\FYP` git).  
**ML/research repo:** `E:\FYP` — training, evaluation, `release/` inference backend source.  
**Generated:** 2026-06-13

---

## 1. Project Identity

- **Full project name:** Forensic Acoustics for Synthetic Speech Detection (FASSD)
- **Product/demo names:**
  - **Public web platform (primary):** https://www.deepfakedetection.dev/ — voice integrity console (separate hosting repo)
  - FYP backend package label: Deepfake Audio Detector — Local Demo (`phase9g_...` — ML source in `E:\FYP\release/`)
- **Students:** Rana M. Areeb, M. Hasnain — source: proposal form, `code/features/feature_extraction.py` header
- **Supervisor:** Sir Faran Mehmood — source: proposal form
- **Program:** BS CS, Computing, Institute of Space Technology (IST)
- **Duration:** 12 Oct 2025 – 12 Jun 2026 — source: proposal form
- **Registration numbers:** MISSING / NEEDS CONFIRMATION (not found in repo)
- **Final project status:**
  - Official approved scope: software ML deepfake detection system — implemented (LCNN/LFCC/log-mel, augmentation, EER/AUC)
  - Extended scope: multi-axis forensic evidence prototype — implemented in `release/` + release audit
  - Phase 9G: **PASS** (local demo/handoff)
  - Release audit Phase 7 matrix: documented with known failures
  - **Live web platform: deployed** at https://www.deepfakedetection.dev/ + API api.deepfakedetection.dev
- **What the system is:**
  - Experimental forensic audio **decision-support prototype**
  - Multi-axis evidence indicators: origin, replay, mixer/channel, partial fabrication
  - Software tool for analyzing uploaded audio and producing structured evidence reports
  - Multi-axis evidence indicators exposed through **deployed web application**
  - Phase 9 inference API (production: api.deepfakedetection.dev)
- **What the system is NOT:**
  - Court-ready or legal proof
  - Conclusive authenticity/fake verdict engine
  - Operational forensic certification system
  - Universal deepfake detector for all real-world cases
- **Safe wording to use:**
  - "experimental forensic decision-support prototype"
  - "evidence indicator / evidence axis"
  - "manual review recommended"
  - "partial-fabrication candidate region"
  - "software-based deepfake speech detection system" (for official scope)
  - "extended multi-axis forensic architecture" (for post-proposal work)
- **Forbidden wording to avoid:**
  - proves fake / proves authentic / court-ready / legal evidence
  - detects all deepfakes / 100% reliable
  - replay means AI-generated / mixer means AI-generated
  - no partial evidence means authentic
  - final fake/real decision / fake_score / real_score

---

## 2. One-Paragraph Project Summary

Rough bullets only:

- Started as ASVspoof LFCC/log-mel CNN/LCNN anti-spoofing with augmentation (approved proposal scope)
- Strong ResNet EER on ASVspoof but failed on real broadcast — exposed domain mismatch
- Expanded to real-world data, environmental features, unified dataset (~1.89M samples), HybridResNetEnvironmental
- Hybrid improved research pipeline but remained binary; Phase 7 controlled forensic testing + AASIST/HybridResNet fine-tune both rejected as final judges
- Final architecture: separate origin (SSL), replay (acoustic), mixer/channel (acoustic), partial fabrication (segment) axes + fusion + evidence-band reports
- Phase 9G backend packaging **PASS**; release audit completed
- **Live web platform deployed** at deepfakedetection.dev (separate repo)
- Limitations: experimental prototype, small accepted Phase 8/9 training sets for active models, replay/mixer generalization, platform-compressed AI, manual review required

---

## 3. Problem Statement Notes

- **Problem addressed:** AI-generated/manipulated speech threatens identity verification, digital trust, misinformation; forensic reviewers need more than a single fake/real score
- **Why binary fake/real was not enough:**
  - ASVspoof benchmark success ≠ real broadcast/YouTube/phone/mixer cases
  - Forensic users ask: human vs AI origin? replayed? mixer/channel processed? partially replaced?
  - Single anti-spoof model collapses distinct manipulation types (Phase 7C3, 7E evidence)
- **Why origin, replay, mixer/channel, segment evidence:**
  - Proposal objectives 3–4 explicitly mention embedded deepfake voice and replayed AI speech
  - Environmental/acoustic cues (noise, reverb, channel) are core project idea (`README.md`, proposal)
  - Partial fabrication needs segment-level analysis when only part of file is synthetic
- **Limitations to mention:**
  - Each axis is experimental; thresholds tuned on small dev splits
  - Replay/mixer evidence ≠ AI origin
  - Partial axis = manual-review candidate only
  - Platform compression (e.g. WhatsApp) weakens origin on documented failures (T4.5 in matrix)

---

## 4. Objectives Notes

### Official approved objectives (proposal form)

1. Bonafide vs spoof/AI classification — **achieved** (LCNN/CNN pipeline, EER/AUC evaluation)
2. Forensic acoustic cues (noise, reverb, channel) — **achieved/extended** (environmental features, multi-axis acoustic models)
3. AI voice embedded in real recordings — **partially achieved / manual-review** (partial fabrication segment model experimental)
4. Replay of AI through device re-recording — **achieved as evidence axis** (replay model; not conclusive proof)
5. Robust evaluation with augmentation/real-world — **achieved/extended** (unified dataset, controlled Phase 7, release audit matrix)
6. Complete software system — **achieved** (deployed web platform + Phase 9 API backend)

### Extended objectives

- Multi-axis evidence architecture — **achieved**
- Fusion + abstention + safe wording — **achieved** (`release/src/fusion_rules.py`, Phase 6 calibration)
- JSON/Markdown/PDF reports — **achieved** in release pipeline
- **Deployed web application** — **achieved** (deepfakedetection.dev; separate hosting repo)

### Limited / manual-review only

- Partial fabrication as legal proof — **not achieved by design**
- Unified manipulation classifier (Phase 4 v3) — **rejected** (20% manipulated recall on testing_audios)
- AASIST/HybridResNet as active decision models — **rejected** (reference only)
- Conclusive authenticity decision — **explicitly disabled**

---

## 5. Scope Notes

### In-scope (documented)

- ASVspoof 2021 LA, DF, PA + RealWorld custom data
- LFCC, log-mel, environmental/acoustic, SSL (WavLM-style) features
- CNN/LCNN, ResNet, HybridResNetEnvironmental, AASIST experiments
- Multi-axis release models + fusion + reports
- Deployed web app + Phase 9 API backend source in FYP repo
- Evaluation: EER, AUC, accuracy, balanced accuracy, controlled forensic matrix

### Out-of-scope claims (do not claim)

- Court admissibility / legal certification
- Real-time streaming at scale (not documented as production feature)
- Full speaker identification / ASV
- Guaranteed detection of all synthesis engines/platforms
- NCCIA as continuing official partner — use neutral "supervision/external consultation" unless supervisor confirms

### Final release scope

- Active models: origin, replay, mixer, partial_segment (`.joblib` in `release/models/`)
- Inactive reference: AASIST, HybridResNet
- Evidence bands Low/Medium/High (`release/config/evidence_calibration.json`)
- Production API serves active models at api.deepfakedetection.dev
- FYP `release/` = backend **source** vendored into website hosting repo for Docker deploy

### Web platform limitations (experimental)

- Not court-ready / not legal proof — disclaimer in UI
- Model weights (`.joblib`) uploaded manually to Droplet, not in git
- Firestore history stores simplified fields, not full Phase 9 JSON
- No server-side audio retention after analysis
- Separate hosting repo from FYP ML git

---

## 6. Dataset Notes

| Dataset/source | Purpose | Approx size | Domain/type | How used | Limitations |
|----------------|---------|-------------|-------------|----------|-------------|
| **ASVspoof 2021 LA** | Official scope baseline | 181,566 files (`PROJECT_STORY` §4; unified stats) | LA, studio | LFCC/log-mel CNN training | Not broadcast/replay-real-world alone |
| **ASVspoof 2021 DF** | DeepFake track | 611,829 files | DF, studio | Training/eval | Synthesis-focused |
| **ASVspoof 2021 PA** | Replay/physical access | 943,110 in unified stats | PA, replay | Added for replay coverage | Still studio-dominated overall |
| **Augmented ASVspoof** | Robustness | +611,829 samples (`PROJECT_STORY` §5) | MUSAN/RIR/codec/gain/clipping | Train robust models | Does not replace real-world domain |
| **RealWorld (custom)** | Broadcast/podcast/social | 157,414 samples | broadcast, podcast, social, read_speech, synthetic | HybridResNet, domain eval | Smaller than ASVspoof; domain shift remains |
| **Unified dataset** | Combined manifests | **1,893,919** samples, 73,421 speakers | Mixed — see `data/statistics/unified_dataset_stats.json` | Hybrid training, statistics | 96%+ studio domain in unified stats |
| **Phase 7 controlled forensic set** | Product-style testing | 23–46 cases per metric in summaries | clean human, direct AI, replay, mixer, partial | Phase 7C1/C4, release audit | Small, controlled — not population representative |
| **testing_audios** | Release validation matrix | 18 origin / 25 replay-mixer-partial cases | T1–T5 folders | `reports/release_audit/phase7_final_release_2026-06-13/` | Documented failures (T1.2, T4.1, T4.5, T2.2, etc.) |
| **Phase 8/9 axis training sets** | Active release models | MISSING exact counts in rough pass — see model cards | Leakage-safe splits | Origin retrain, 8E-1 replay/mixer, Phase 5 partial | Model cards mark "small accepted datasets" |

**Unified stats highlights** (`data/statistics/unified_dataset_stats.json`):
- bonafide: 320,611; spoof: 1,573,308
- attack types: replay 816,480; conversion 589,212; synthesis 167,616
- domains: studio 1,819,660; broadcast 17,994; podcast 17,512; social 5,712; synthetic 4,502

---

## 7. Methodology Notes

### Audio input
- User uploads `.wav`/`.mp3`/etc. via Gradio, FastAPI, or Next.js dashboard
- Case ID optional; no permanent server storage on web platform (frontend doc §18)

### Preprocessing
- Loading, resampling, normalization — see `release/src/` pipeline, `PROJECT_STORY` phase docs
- Release audit tested resampling/window hypotheses (Phase 3) — details in audit reports

### Segmentation
- `release/src/segmentation.py` — segment-level evidence for partial fabrication
- Top suspicious segments returned in API (`return_top_segments`)

### Feature extraction
- **LFCC:** 20-dim — early baseline (`PROJECT_STORY` §4)
- **Log-mel:** 64 bins — ResNet/Hybrid path
- **Environmental/acoustic:** 12 features — HybridResNetEnvironmental (`comprehensive_evaluation_report.md`)
- **SSL embeddings:** WavLM-style for origin axis (`release/MODEL_REGISTRY.md`, `ssl_embeddings.py`)

### Model axes
- File-level: origin (SSL), replay (acoustic), mixer (acoustic)
- Segment-level: partial fabrication (combined_no_f9)

### Fusion logic
- `release/src/fusion_rules.py` / Phase 8F rules
- Combines axis evidence; abstention/inconclusive states; no forced verdict
- `phase8f_fusion_rules.py` required for production (frontend deployment issue)

### Report generation
- JSON analysis + Markdown report + optional PDF + waveform visual
- Phase 6 evidence bands (Low/Medium/High) — not raw scores in user-facing cards
- Safety wording contract — `release/` docs, Phase 9F limitations

### UI/API output
- Local: Gradio cards, FastAPI JSON
- Web: four check cards, waveform highlights, Firebase history (simplified fields)

---

## 8. Model and Architecture Notes

| Model/axis | Status | Features | Purpose | Threshold | Key results | Limitations | Safe thesis wording |
|------------|--------|----------|---------|-----------|-------------|-------------|---------------------|
| **Baseline CNN/LCNN** | Historical/official scope | LFCC | First working detector | 0.5 typical | Clean 9.68% EER; Aug 15.71% EER (`PROJECT_STORY` §6) | High EER vs ResNet | "approved-scope baseline" |
| **ResNet CNN** | Reference (`reject_for_now`) | Log-mel | Strong ASVspoof performance | — | Clean 0.57% EER; Aug 2.61% EER (`PROJECT_STORY` §8) | Failed broadcast real-world | "benchmark-strong but forensic-insufficient" |
| **HybridResNetEnvironmental** | Reference (`reject_for_now`) | Log-mel + 12 env | Unified binary+multiclass | 0.5 | Test EER 16.21%; AUC 0.9167; RW EER 16.14% (`comprehensive_evaluation_report.md`) | High bonafide FPR; 64.36% multiclass acc | "research milestone, not final forensic judge" |
| **AASIST** | Reference/shadow | SSL/spectrogram (AASIST arch) | Advanced anti-spoof experiment | — | Phase 7E: 22/23 clean-human false alarms | Rejected — domain mismatch on clean human | "experimental reference, inactive in release" |
| **Origin model** | **Active** | SSL | Human vs AI-origin evidence | **0.92** | Leakage-safe BA 0.95; testing_audios origin acc 0.8333, BA 0.825 (`MODEL_REGISTRY`, matrix) | Fails: T1.2 human→AI, T4.1 human→AI, T4.5 AI→human (WhatsApp) | "origin evidence indicator (experimental)" |
| **Replay model** | **Active** | Acoustic | Replay/rerecording evidence | **0.65** | Matrix: acc 0.80, BA 0.7738; NOT AI proof | Fails on mixer-human T2.2, missed AI replays T3.2–T3.4 | "replay evidence ≠ AI-generated" |
| **Mixer/channel model** | **Active** | Acoustic | Mixer/channel processing evidence | **0.75** | Matrix: acc 0.88 but recall 0.0 (no TP) | Does not detect positive mixer cases in matrix | "channel evidence indicator only" |
| **Partial fabrication model** | **Active (experimental)** | combined_no_f9 | Segment candidate localization | **0.95** | Matrix: acc 1.0 on 25 files; Phase 5 oracle 10/10 | Manual-review only; F9 features removed | "partial-fabrication candidate, not proof" |
| **Fusion rules** | Active | N/A | Combine axes + wording | Phase 8F | Phase 9C report structure | Can return processing errors if modules missing | "decision-support fusion, not verdict" |
| **Report layer** | Active | N/A | JSON/MD/PDF + evidence bands | Phase 6 calibration | `evidence_calibration.json` | Uncalibrated probs in technical details only | "structured forensic-style report" |

**Evidence calibration** (`release/config/evidence_calibration.json`):
- origin: threshold 0.92, low_max 0.0444, medium_max 0.0986
- replay: 0.65 / 0.5338 / 0.9891
- mixer: 0.75 / 0.2201 / 0.9663
- partial_segment: 0.95 / 0.2638 / 0.8139

---

## 9. Phase-Wise Project Evolution

| Phase | Done | Why | Key result | Problem remained | Next influence |
|-------|------|-----|------------|------------------|----------------|
| **Early ASVspoof/LFCC/CNN** | Feature pipeline + LCNN | Approved proposal | LFCC aug EER 15.71% | Too weak vs deeper models | Log-mel comparison |
| **Log-mel/ResNet** | Deeper CNN | Improve EER | Aug EER 2.61% | Broadcast failure | Real-world data push |
| **Real-world broadcast failure** | Test on broadcast | Validate product | ~24.5% env anomaly acc; ResNet failed real cases | Domain mismatch | Environmental features |
| **Environmental feature phase** | Supervised env classifier | Forensic cues | 81.69% on ASVspoof-style | Still not broadcast-ready | Hybrid model |
| **Unified dataset phase** | Merge ASVspoof+RealWorld+PA | Scale + diversity | 1.89M samples | Still studio-heavy | HybridResNet training |
| **HybridResNet phase** | Spectrogram+env fusion | Single strong model | EER 16.21%, RW 16.14% | Binary collapse; high bonafide FPR | Forensic product pivot |
| **Raw audio explanation** | Phase 6 explainability | User trust | Evidence bands concept | Still single-score mindset | Phase 7 controlled testing |
| **Controlled forensic Phase 7** | 7A–7E experiments | Product validation | HybridResNet/AASIST rejected; 7C4-v2 prototype only | Clean-human false alarms | Multi-axis architecture |
| **AASIST/HybridResNet rejection** | 7C3, 7E | False simplification | 22/23 clean-human FA (AASIST) | No standalone judge | Phase 8 freeze |
| **Phase 8 multi-axis** | Separate axis models + fusion | Forensic semantics | Origin/replay/mixer/partial modules | Small training sets | Phase 9 packaging |
| **Phase 9 local demo/handoff** | Gradio/FastAPI + zip | Teammate handoff | Phase 9G **PASS** | Weak testing_audios cases | Release audit |
| **Release audit + final fixes** | Phases 0–7 audit | Repair shipped weaknesses | Origin retrain; partial redesign; Phase 7 matrix | T4.5, T1.2, mixer recall | Web platform integration |
| **Web platform (post-Phase 9)** | Next.js + DO + Firebase | Public product layer | **Live** deepfakedetection.dev | Vercel upload limit; simplified history | Thesis deployment chapter |

---

## 10. Implementation Notes

| Component | Location / notes |
|-----------|------------------|
| **Main FYP repo** | `E:\FYP\` — Code/, release/, reports/, data/ |
| **Frontend repo** | `D:\FASSD\` (documented; not inside FYP git) |
| **Gradio UI** | `release/app_gradio.py` — local demo |
| **FastAPI API** | `release/app_fastapi.py`, `run_fastapi.bat` |
| **Inference pipeline** | `release/src/inference_pipeline.py` (Phase 9C) |
| **Model loader** | `release/src/model_loader.py` |
| **Feature extraction** | `release/src/feature_extraction.py`; legacy `Code/features/` |
| **SSL embeddings** | `release/src/ssl_embeddings.py` |
| **Segmentation** | `release/src/segmentation.py` |
| **Fusion rules** | `release/src/fusion_rules.py`, Phase 8F module |
| **Report generator** | Release sample outputs; Phase 9C report layer |
| **PDF/report** | API flags `generate_report`, `generate_visual` |
| **Visualization** | Waveform highlight images; web `audio-waveform-display.tsx` |
| **JSON/API outputs** | `release/sample_outputs/`; API `phase9c_report` payload |
| **Web mapper** | `D:\FASSD\lib\inference-response-mapper.ts` |
| **Deploy runbook** | `D:\FASSD\deploy/DEPLOY_DIGITALOCEAN.md` |

---

## 11. API Notes

**Local FastAPI** — `reports/phase9/integration_docs/phase9f_api_contract.md`

| Endpoint | Method | Input | Output | Purpose |
|----------|--------|-------|--------|---------|
| `/` | GET | — | App metadata, safety flags | Discovery |
| `/health` | GET | — | `models_loaded`, `manual_review_required` | Liveness |
| `/model-info` | GET | — | Inventory, partial module metadata | Debug/handoff |
| `/analyze-audio` | POST | multipart `audio_file`, optional `case_id`; query: `return_top_segments`, `save_report`, `generate_report`, `generate_visual` | Phase 9 multi-axis JSON | Primary analysis |
| `/analyze` | POST | Legacy alias | Same | Backward compatibility |

**Production API:** https://api.deepfakedetection.dev/ — same Phase 9 contract; CORS for www.deepfakedetection.dev

**Thesis notes:**
- Always state `manual_review_required: true`, `conclusive_authenticity_decision: false`
- No `fake_score`/`real_score` in contract
- Large files: direct to DO API, not Vercel proxy

---

## 12. UI and Report Notes

### Local Gradio (`release/app_gradio.py`)
- Upload audio → evidence axis cards with Low/Medium/High bands
- Safety disclaimer; manual-review wording
- Optional PDF/JSON download

### Live Next.js (`FRONTEND_AND_DEPLOYMENT_STORY.md`)
- **Landing:** Phase 9 multi-axis marketing, architecture bento, pipeline timeline
- **Dashboard:** upload → processing waveform → four cards (Voice source, Recording chain, Channel & mix, Edited segments)
- **Headlines:** "Sounds human-made" / "Worth a closer look" — not REAL/FAKE certificate
- **Waveform:** real file peaks + amber segment highlights
- **Profile/history:** Firestore `audioAnalyses` — simplified fields
- **Safety:** backend `safety.wording` in footer

### Report outputs
- JSON: full `phase9c_report`, `evidence_axis_cards`, `partial_fabrication.top_segments`
- Markdown/PDF: forensic-style with limitations section
- Evidence bands replace raw probability in user-facing cards

---

## 13. Results and Evaluation Notes

| Metric | Value | Source | Meaning | Safe interpretation | Limitation |
|--------|-------|--------|---------|---------------------|------------|
| LFCC CNN clean EER | 9.68% | `PROJECT_STORY` §6 | Baseline error rate | Official scope baseline works | Not final system |
| LFCC CNN aug EER | 15.71% | Same | Robustness drop | Augmentation hurts LFCC baseline | — |
| Log-mel aug EER | 15.25% | `PROJECT_STORY` §7 | Slightly better than LFCC | Motivated log-mel path | Still high |
| ResNet clean EER | 0.57% | `PROJECT_STORY` §8 | Strong ASVspoof | Benchmark success | Misleading for forensic product |
| ResNet aug EER | 2.61% | Same | Strong augmented ASVspoof | Historical best binary | Broadcast failure followed |
| Hybrid test EER | 16.21% | `comprehensive_evaluation_report.md` | Unified test split | Meets <20% RW target narrative | Above 10% product goal |
| Hybrid test AUC | 0.9167 | Same | Ranking quality | Good but not sufficient alone | — |
| Hybrid binary accuracy @0.5 | 89.78% | Same | Threshold accuracy | Bonafide FPR 41.28% at 0.5 | High false spoof rate |
| RealWorld test EER | 16.14% | Same | Domain subset | Better than ASVspoof-only path | Still experimental |
| Phase 7C1 clean-human accepted | 4/23 | `PHASE7_EXPERIMENT_RESULTS_SUMMARY.md` | File-level specificity | Poor — drove rejection | Controlled set only |
| Phase 7E AASIST clean-human FA | 22/23 | Same | False AI on human | AASIST rejected | — |
| Origin matrix accuracy | 0.8333 | `phase7_final_testing_audios_matrix.md` | 18-case release test | 2 FP, 1 FN | Small matrix |
| Origin matrix BA | 0.8250 | Same | Balanced | T1.2, T4.1, T4.5 failures | — |
| Replay matrix BA | 0.7738 | Same | 25 cases | Missed AI replays | Replay ≠ AI claim |
| Mixer matrix recall | 0.0000 | Same | No TP | Mixer axis weak on positives | — |
| Partial matrix acc | 1.0000 | Same | 25 cases gated | No FP in matrix | Oracle/candidate only |
| Origin leakage-safe BA | 0.9500 | `MODEL_REGISTRY.md` | Dev split | Better than matrix | Different split |
| Phase 9G status | PASS | `phase9g_final_release_report.md` | Handoff ready | Local demo approved | Not legal deployment |
| Phase 8E-3 partial BA | ~0.88 | `PROJECT_STORY` §23 | Segment model dev | ROC-AUC ~0.956 | Pre-redesign numbers — cross-check Phase 5 |

---

## 14. Limitations Notes

From Phase 9G, Phase 8G, MODEL_REGISTRY, release audit, frontend doc:

1. Experimental prototype — not court-ready / not legal proof
2. Real-world generalization gaps (broadcast, platform compression)
3. Replay/mixer axes: high sensitivity but semantic ambiguity; mixer recall 0 on final matrix
4. Partial fabrication: candidate regions only; full replacement not guaranteed
5. Platform-compressed AI (T4.5 WhatsApp) breaks origin
6. Language/domain: predominantly English ASVspoof + limited RealWorld domains
7. Small accepted Phase 8/9 training sets for shipped axis models
8. AASIST/HybridResNet inactive — not compared live in production without validation
9. Web: no audio retention; simplified history; manual model deploy to Droplet
10. Unified dataset studio-dominated despite RealWorld addition
11. Phase 4 unified manipulation v3 rejected (20% recall)
12. NCCIA partnership status — MISSING / NEEDS CONFIRMATION for thesis acknowledgement wording

---

## 15. Thesis Chapter Mapping (legacy section — see §21 for full heading notes)

| Chapter | Focus | Key repo files | External citations likely |
|---------|-------|----------------|---------------------------|
| Ch 1 Introduction | Problem, official vs extended scope, objectives | proposal form, `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` | Deepfake surveys RA1–RA3 |
| Ch 2 Literature | Anti-spoofing, ASVspoof, features, SSL, forensic cues | `research_article/`, `09_REFERENCES_RESEARCH_GAP_PLAN.md` | ASVspoof official paper TBD, AASIST TBD, WavLM TBD |
| Ch 3 Methodology | Datasets, features, models, multi-axis design, deployment | `PROJECT_STORY`, `PHASE8A_ARCHITECTURE_FREEZE.md`, `release/` | MUSAN/RIR augmentation papers TBD |
| Ch 4 Results | EER tables, Phase 7, matrix, UI screenshots | `comprehensive_evaluation_report.md`, release audit matrix | Compare to literature benchmarks cautiously |
| Ch 5 Conclusion | Achievements, limits, future work | Phase 9G, limitations docs | — |
| Appendices | Proposal, API, configs, screenshots | proposal PDF, `phase9f_api_contract.md`, `MODEL_REGISTRY.md` | — |

---

## 16. Figure and Table Suggestions

| Suggested title | Contents | Source files |
|-----------------|----------|--------------|
| FASSD Overall Workflow | Input → preprocess → features → 4 axes → fusion → report | `PHASE8A_ARCHITECTURE_FREEZE.md`, README diagram |
| Official vs Extended Scope | Two-column scope table | `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` |
| Dataset Summary | Counts by LA/DF/PA/RealWorld | `unified_dataset_stats.json` |
| Phase Evolution Timeline | Phases 1–9 + web | `PROJECT_STORY`, this doc §9 |
| Model Comparison | Active vs rejected, EER highlights | `MODEL_REGISTRY.md`, evaluation report |
| Feature Sets Table | LFCC, log-mel, env, SSL | `PROJECT_STORY`, model cards |
| Final Axis Results | Matrix metrics table | `phase7_final_testing_audios_matrix.md` |
| API Endpoints | Method, path, purpose | `phase9f_api_contract.md` |
| Deployment Architecture | Vercel + DO + Firebase | `FRONTEND_AND_DEPLOYMENT_STORY.md` |
| UI Screenshots | Landing, dashboard, results, waveform | deepfakedetection.dev captures — **MISSING in repo** (capture during thesis) |
| Limitations Table | Claim vs safe wording | `phase8g_limitations_and_claims.md`, §19–20 below |
| Confusion matrices | Hybrid multiclass | `reports/evaluation/confusion_matrices/` |

---

## 17. Citation Need Map

| Thesis section | Claim type | Citation? | Suggested source type | Notes |
|----------------|------------|-----------|----------------------|-------|
| AI speech security motivation | External field | Yes | RA1, RA2 surveys | Verified DOI for RA2 |
| ASVspoof 2021 LA/DF | Dataset | Yes | Official ASVspoof paper | **TBD — not in research_article/** |
| LFCC for spoof detection | Method | Yes | RA1, RA7 | — |
| LCNN baseline | Method | Yes | ASVspoof baseline lit | TBD |
| Log-mel/ResNet | Method | Yes | RA7 | — |
| AASIST | Method | Yes | AASIST paper | **TBD — not in folder** |
| WavLM/SSL origin | Method | Yes | WavLM paper | **TBD** |
| MUSAN/RIR augmentation | Method | Yes | Original corpus papers | **TBD** |
| Replay forensics | Concept | Yes | RA1, RA2 | — |
| Partial fabrication segments | Concept | Yes | RA6 arXiv | Verified arXiv ID |
| FASSD EER 2.61% ResNet | Project result | No external | Own Table | — |
| Phase 7 matrix BA 0.825 origin | Project result | No external | Own Table | — |
| Multi-axis architecture design | Project design | No external | Own methodology | — |
| Live deployment stack | Project impl | No external | Own §3.16 / frontend doc | Vercel/Firebase generic docs optional |
| "Court-ready" negation | Safety | No | Own limitations | — |

---

## 18. Reference Candidate Extraction

From `submissions/thesis_preparation/09_REFERENCES_RESEARCH_GAP_PLAN.md` — PDFs in `research_article/` (9 files; bibliographic details partially verified):

| ID | Title | Authors | Year | Venue | DOI/link | Path | Verification | Thesis use |
|----|-------|---------|------|-------|----------|------|--------------|------------|
| RA1 | Audio Deepfake Detection: A Survey | Jiangyan Yi et al. | 2023 | IEEE-style | TBD | `research_article/1.pdf` | needs verification | Ch2.1–2.3 |
| RA2 | Audio Deepfake Detection: What Has Been Achieved… | Bowen Zhang et al. | 2025 | Sensors 25, 1989 | 10.3390/s25071989 | `research_article/2.pdf` | verified DOI | Ch2, gaps |
| RA3 | Multimedia-enabled deepfake detection survey | Abdullah Ayub Khan et al. | 2025 | Discover Computing 28:48 | 10.1007/s10791-025-09550-0 | `research_article/3.pdf` | verified DOI | Ch2 |
| RA4 | Where are We in Audio Deepfake Detection? | Xiang Li et al. | TBD | Fordham/IBM | TBD | `research_article/4.pdf` | needs verification | Ch2.11 |
| RA5 | Beyond Identity: Generalizable Deepfake Audio Detection | Yasaman Ahmadiadli et al. | TBD | Preprint | TBD | `research_article/5.pdf` | needs verification | Domain gap |
| RA6 | Forensic deepfake audio detection using segmental speech features | Tianle Yang et al. | 2025 | arXiv:2505.13847 | arXiv link | `research_article/6.pdf` | verified arXiv | Partial fab |
| RA7 | Deepfake audio detection with spectral features and ResNeXt | Gul Tahaoglu et al. | TBD | Knowledge-Based Systems | TBD | `research_article/7.pdf` | needs verification | ResNet section |
| RA8 | Deepfake Voice Detection Using Speech Pause Patterns | Nikhil Valsan Kulangareth et al. | TBD | Klick Labs/JMIR-style | TBD | `research_article/8.pdf` | needs verification | Optional |
| RA9 | Improved DeepFake Detection Using Whisper Features | Piotr Kawa et al. | TBD | INTERSPEECH submitted | TBD | `research_article/9.pdf` | needs verification | SSL comparison |

**Also cite from project (not external):** proposal form, ASVspoof dataset docs when verified, IST thesis template.

---

## 19. Final Safe Wording Bank

- "FASSD is an experimental forensic audio decision-support prototype developed as a BSCS FYP software system."
- "The system provides evidence indicators across multiple axes rather than a single legal verdict."
- "Origin evidence suggests whether voice-source patterns appear human-like or AI-like; this requires manual review."
- "Replay evidence indicates possible rerecording or playback chain effects; it does not prove AI generation."
- "Mixer/channel evidence indicates possible mixing or channel processing; it does not prove AI generation."
- "Partial-fabrication evidence highlights candidate segments for reviewer attention; it is not fabrication proof."
- "Low/Medium/High evidence bands summarize model support without implying certainty."
- "Results on ASVspoof and controlled testing_audios matrices are experimental and not population representative."
- "The deployed web platform at deepfakedetection.dev demonstrates the system; it remains a research prototype."
- "Gradio and FastAPI in the FYP repository serve local testing and handoff; the Next.js site is the public interface."

---

## 20. Forbidden Claims Bank

Do **not** write:

- "proves the audio is fake/authentic"
- "court-ready" / "admissible legal evidence" / "certified forensic tool"
- "detects all deepfakes" / "fully reliable in all real-world conditions"
- "replay detection confirms AI-generated speech"
- "mixer/channel detection confirms deepfake"
- "no partial-fabrication evidence means the recording is authentic"
- "HybridResNet/AASIST is the production decision model" (they are reference-only)
- "EER 2.61% means the final product is solved"
- "NCCIA officially partnered" (unless supervisor confirms)
- Present Gradio as the only/final user interface (live Next.js exists)

---

# 21. Thesis Structure Notes (All Headings)

> **Superseded for section-by-section work:** use **`FASSD_THESIS_SECTION_NOTES.md`** — one dedicated notes block per heading from `FASSD_Thesis_Structure.md`.  
> The summary below is retained for quick reference only.

---

## Front Matter

### Title Page
- Title: **Forensic Acoustics for Synthetic Speech Detection**
- Students: Rana M. Areeb, M. Hasnain; registration numbers — **MISSING / NEEDS CONFIRMATION**
- Supervisor: Sir Faran Mehmood; department Computing; IST
- Submission: June 2026
- Source: proposal form, title defence materials in `submissions/title defence/`

### Approval by Board of Examiners
- Use IST template page; signature blocks — **template file MISSING in repo** (`thesis_layout.pdf` TBD)

### Authors' Declaration
- Standard IST declaration; originality + supervisor oversight
- Acknowledge extended work beyond proposal where applicable

### Certificate
- Supervisor certificate page — IST format

### Copyright Page
- University template wording

### Dedication
- Personal — no repo source

### Acknowledgement
- Supervisor Sir Faran Mehmood; teammate collaboration; IST Computing
- NCCIA: mention only if supervisor approves (title defence referenced historically — **NEEDS CONFIRMATION**)
- External consultation neutral wording per `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`

### Abstract (200–250 words)
- Problem: synthetic speech + forensic review needs
- Method: ASVspoof ML baseline → extended multi-axis evidence (origin/replay/mixer/partial)
- Implementation: Python release + live Next.js web demo
- Results: key EER milestones + final testing_audios matrix highlights
- Contribution: experimental decision-support path with honest limitations
- Avoid "court-ready" / "proves fake"

### Table of Contents / List of Tables / List of Figures
- Generate after final formatting

### List of Abbreviations
- Include: FASSD, AI, ASVspoof, LA, DF, PA, LFCC, MFCC, LCNN, CNN, ResNet, AASIST, SSL, EER, AUC, VAD, API, UI, JSON, PDF, SNR, RT60, SDG
- Add: WavLM (if used in thesis text), EER, ROC, BA (balanced accuracy)
- Source: `submissions/thesis_preparation/08_ABBREVIATIONS.md` if present

---

## Chapter 1: Introduction

### 1.1 Motivation
- AI voice cloning → identity fraud, misinformation, trust erosion
- Forensic/academic need for structured evidence not just binary labels
- Connect to cybersecurity/digital trust FYP framing
- Citations: RA1, RA2

### 1.2 Background
- Synthetic speech, voice conversion, TTS, deepfake audio definitions
- Spoofing vs bonafide; replay attacks; partial edits
- ML for audio anti-spoofing overview
- Citations: surveys

### 1.3 Problem Statement
- Detect bonafide/spoof **and** interpret forensic cues (replay, channel, partial edit)
- Gap: benchmark detectors ≠ practical forensic review
- Source: proposal form, `README.md`, `FASSD - Scope.md`

### 1.4 Approved Scope and Extended Development Boundary
- **Required table:** Official vs Extended (`16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`)
- Proposal: LCNN, LFCC, log-mel, ASVspoof DF+LA, software deliverable
- Extended: multi-axis, reports, web platform, release audit
- Do not say official scope was "replaced"

### 1.5 Project Objectives

#### 1.5.1 Official Approved Objectives
- List all 6 from proposal (see §4 above)
- Map each to baseline implementation evidence

#### 1.5.2 Extended Implementation Objectives
- Multi-axis evidence, fusion, reports, local demo, **deployed Next.js frontend**
- Partial fabrication as experimental objective

### 1.6 Scope of the Study
- Covers: data, features, training experiments, final evidence system, evaluation, interfaces
- Excludes: legal certification, universal deepfake coverage

### 1.7 Development Model
- Iterative-incremental + prototyping (phase failures drove redesign)
- **Required figure:** phase flow diagram from ASVspoof → web platform
- Source: `PROJECT_STORY` §2, phase docs

### 1.8 Environment and Sustainability
- Software-based project; GPU training energy mention (responsible compute)
- No hardware manufacturing waste
- Keep concise; link SDG 9/16 lightly

### 1.9 Relevance to Sustainable Development Goals
- SDG 9 (innovation/infrastructure), SDG 16 (institutions/trust) — brief
- Do not overclaim global impact

### 1.10 Thesis Outline
- One paragraph roadmap Ch2–5 + appendices

---

## Chapter 2: Literature Survey

### 2.1 Historical Background
- Speech synthesis history → neural TTS → deepfakes
- Spoofing countermeasures evolution
- Citations: RA1–RA3

### 2.2 Synthetic Speech and Audio Deepfakes
- How AI speech is generated (high level)
- Detection difficulty: compression, replay, partial edits
- Citations: RA2, RA4

### 2.3 Audio Anti-Spoofing
- Bonafide vs spoof formulation
- CM systems, score thresholds, EER
- Citations: RA1

### 2.4 ASVspoof Dataset and Evaluation Tracks
- LA, DF, PA/replay concepts
- **Required table:** tracks vs FASSD usage
- Official ASVspoof citation — **TBD**
- Project counts from unified stats

### 2.5 Audio Features for Deepfake Detection
- LFCC, MFCC, log-mel spectrograms
- Environmental/acoustic cues
- Citations: RA1, RA7

### 2.6 Deep Learning Models for Audio Detection
- CNN/LCNN, ResNet-style, hybrid architectures
- Citations: RA7, ASVspoof baselines TBD

### 2.7 Data Augmentation and Real-World Robustness
- MUSAN, RIR, codec, gain — project used these
- Limits of augmentation-only robustness (project lesson)
- Citations: augmentation papers TBD

### 2.8 Advanced Anti-Spoofing and SSL-Based Methods
- AASIST; WavLM/wav2vec2/Whisper features
- Why SSL used for origin axis in FASSD
- Citations: AASIST TBD, RA9, WavLM TBD

### 2.9 Forensic Audio Cues and Manipulation Evidence
- Replay signatures, noise, reverb, device response
- Separating channel effects from synthesis
- Citations: RA1, forensic audio lit TBD

### 2.10 Partial Fabrication and Segment-Level Analysis
- File-level scores miss localized edits
- Segment classifiers, oracle evaluation
- Citations: RA6

### 2.11 Research Gaps
- Binary focus; benchmark vs forensic product gap; need multi-axis evidence
- **Required table:** gaps vs FASSD response
- Source: Phase 7/8 docs, RA5 domain generalization

### 2.12 Summary of Literature Survey
- Literature supports both official LCNN scope and extended architecture
- Transition sentence to methodology

---

## Chapter 3: Methodology And System Design

### 3.1 Overview of Methodology
- End-to-end workflow diagram
- **Required figure:** overall FASSD workflow
- Two-tier story: official baseline + extended final system

### 3.2 Research Design
- Experimental ML; hypothesis → train → evaluate → pivot
- Phase-gated decisions (reject/accept documented)

### 3.3 Official Approved Methodology
- ASVspoof DF+LA, LFCC+log-mel, LCNN, augmentation, EER/AUC, software tool
- Direct quote/bullet from proposal form

### 3.4 Extended Methodology
- ResNet, environmental, HybridResNet, AASIST trials, multi-axis freeze, web deployment
- Frame as extensions after limitation discovery

### 3.5 Dataset Preparation
- Manifests, labels, unified dataset stats
- **Required table:** dataset summary (§6)
- RealWorld collection — source docs in `PROJECT_STORY` / data manifests

### 3.6 Audio Preprocessing
- Load, resample, normalize, channel handling
- Release pipeline behavior; audit resampling experiments

### 3.7 Data Augmentation
- MUSAN, RIR, codec, gain, clipping — 611,829 augmented samples
- Train-only augmentation for origin retrain (release audit)

### 3.8 Feature Extraction

#### 3.8.1 LFCC Features
- 20 coefficients; baseline CNN input

#### 3.8.2 Log-Mel Spectrogram Features
- 64 bins; ResNet/Hybrid path

#### 3.8.3 Environmental and Acoustic Features
- 12 features for Hybrid; acoustic axes for replay/mixer

#### 3.8.4 SSL Embeddings
- WavLM-style for origin active model
- HF hub download on first boot (deployment note)

- **Required table:** feature sets by phase/model

### 3.9 Baseline CNN/LCNN Model
- ~5k params; official scope deliverable
- EER 9.68% / 15.71%

### 3.10 ResNet-Based Model
- Deeper spectral model; 0.57% / 2.61% EER
- Why tested; why not final judge

### 3.11 Environmental Feature Classifier
- Anomaly ~24.5% acc; supervised 81.69%
- Motivation from broadcast failure

### 3.12 HybridResNetEnvironmental Model
- Fusion of spectrogram + env branches
- 16.21% EER, multiclass 64.36%
- Reference-only in release

### 3.13 AASIST Experiment
- Phase 7E; 22/23 clean-human false alarms
- Kept as reference in `release/models/reference/aasist/`

### 3.14 Final Multi-Axis Forensic Architecture
- **Required figure:** four axes + fusion + report
- Source: `PHASE8A_ARCHITECTURE_FREEZE.md`, `MODEL_REGISTRY.md`

#### 3.14.1 Origin Evidence Axis
- SSL file model; threshold 0.92; processed-AI positives in retrain

#### 3.14.2 Replay/Rerecording Evidence Axis
- Acoustic file model; 0.65; explicit non-AI semantics

#### 3.14.3 Mixer/Channel Evidence Axis
- Acoustic; 0.75; separate from origin

#### 3.14.4 Partial Fabrication Evidence Axis
- Segment combined_no_f9; F9 features removed in audit; 0.95 threshold

#### 3.14.5 Fusion and Manual Review Logic
- Phase 8F rules; abstention; no conclusive authenticity

### 3.15 Report Generation
- JSON, MD, PDF; evidence bands; partial segment list; safety block

### 3.16 System Interface and Deployment Design
- **Required figure:** deployment architecture
- **Local:** Gradio/FastAPI in `E:\FYP\release\` — testing/handoff
- **Production:** Vercel frontend + DigitalOcean API + Firebase — **live**
- Source: `FRONTEND_AND_DEPLOYMENT_STORY.md`
- Direct upload pattern for large audio

### 3.17 API Design
- Endpoints table from §11
- Optional appendix if chapter too long

### 3.18 Storage and Output Structure
- `release/sample_outputs/`; Firestore history schema; no persistent audio on web
- Case ID optional

### 3.19 Hardware and Software Environment
- **Required table:** Python, PyTorch, librosa, FastAPI, Next.js 16, Docker, etc.
- Dev GPU — **MISSING exact GPU model in notes** — check local docs
- Conda env `fassd`

### 3.20 Ethical and Safety Considerations
- Misuse risk; privacy; no legal verdict; human-in-the-loop
- Source: `phase8g_limitations_and_claims.md`, Phase 9F

### 3.21 Methodology Limitations
- Dataset bias, compression, small axis training sets, experimental thresholds

---

## Chapter 4: Results And Discussion

### 4.1 Evaluation Overview
- Define EER, AUC, accuracy, BA, precision/recall, confusion matrix
- Controlled vs benchmark vs release matrix distinctions

### 4.2 Baseline CNN/LCNN Results
- Table: clean/aug EER
- Establishes official scope completion

### 4.3 LFCC and Log-Mel Feature Comparison
- 15.71% vs 15.25% aug EER
- Justify log-mel continuation

### 4.4 ResNet Results
- 0.57% / 2.61% — strong benchmark
- Discuss broadcast failure narrative

### 4.5 Environmental Classifier Results
- Anomaly vs supervised numbers

### 4.6 HybridResNetEnvironmental Results
- EER, AUC, multiclass report, bonafide FPR table
- Figures from `reports/evaluation/figures/`

### 4.7 Controlled Forensic Evaluation Results
- Phase 7C1, 7C4-v2 tables
- Clean-human false alarm story

### 4.8 AASIST and Historical Model Comparison
- Why rejected; comparison table active vs reference models

### 4.9 Final Multi-Axis Evidence Results
- Phase 8 axis metrics from PROJECT_STORY §23 (cross-check model cards)
- **Required table:** axis BA/recall

### 4.10 Release/Demo Validation Results
- Phase 9G PASS; inference smoke tests
- Phase 9E-P4B validation report

### 4.11 Release Audit Results
- Full `phase7_final_testing_audios_matrix.md`
- Failure table discussion (T1.2, T4.1, T4.5, T2.2…)
- **Required table:** consolidated key results

### 4.12 Interface and Report Output
- **Screenshots needed:** landing, dashboard, results, waveform — capture from deepfakedetection.dev
- Gradio screenshot optional for appendix (local demo)
- Describe four cards + disclaimer

### 4.13 Discussion Against Literature
- Benchmark vs forensic product gap — aligns with RA5, RA2
- Multi-axis as response to gap

### 4.14 Official Objective-Wise Discussion
- **Required table:** objective vs achievement status (§4)

### 4.15 Extended Contribution Discussion
- Multi-axis design, evidence bands, deployment, documentation trail

### 4.16 Failure Cases and Limitations
- Matrix failures; mixer recall 0; WhatsApp AI miss
- **Required table:** limitations

### 4.17 Summary of Results
- Bullet top 5 findings

---

## Chapter 5: Conclusion And Future Work

### 5.1 Conclusion
- Official software ML goal met; extended forensic prototype delivered; web demo live
- Experimental status restated

### 5.2 Objective-Wise Conclusion
- Short paragraph per official + key extended objective

### 5.3 Main Contributions
- Pipeline, datasets, model experiments, multi-axis architecture, reports, **web platform**

### 5.4 Limitations
- Honest restate §14 — strengthens credibility

### 5.5 Future Work
- More external validation; replay/mixer generalization; compression robustness
- Stronger partial localization; expand datasets; expert forensic review
- Tighten Next.js build (ESLint/TS); full Phase 9 JSON in history
- Note: future work ≠ current claims

### 5.6 Final Statement
- BSCS-level foundation for deepfake detection + forensic decision support
- Manual review essential

---

## References
- Numbered IST format — only cited sources
- Merge RA1–RA9 after verification + ASVspoof/AASIST/WavLM when added
- Do not invent IEEE entries

---

## Appendices

### Appendix A: Official Project Proposal Details
- Extract from `(IST-Dean-F-18)_S_Project Proposal Form-1.pdf`

### Appendix B: Dataset and Manifest Details
- Extended unified stats; manifest column definitions

### Appendix C: Feature Extraction Details
- LFCC/log-mel/env/SSL parameters from code headers and docs

### Appendix D: Model and Configuration Details
- `MODEL_REGISTRY.md`, `evidence_calibration.json`, thresholds

### Appendix E: API Documentation
- Full `phase9f_api_contract.md` + sample JSON from `release/sample_outputs/`

### Appendix F: UI and Report Screenshots
- Web UI captures; Gradio; PDF sample

### Appendix G: Additional Results
- Confusion matrices; Phase 7 full tables; checksum manifest

### Appendix H: Ethical and Safety Wording
- Forbidden claims §20; safe wording §19; partial_report_contract.json

### Appendix I: Repository/File Structure
- `E:\FYP\` tree + `D:\FASSD\` frontend tree summary
- Key paths for reproducibility

---

# Appendix: Files Analyzed for These Notes

- `README.md`, `FASSD - Scope.md`, `PROJECT_STORY_FROM_DAY_ONE.md` (updated with web platform §37)
- `submissions/proposal/(IST-Dean-F-18)_S_Project Proposal Form-1.docx` (via prep docs)
- `submissions/thesis_preparation/16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`, `09_REFERENCES_RESEARCH_GAP_PLAN.md`
- `thesis_working_notes/FASSD_Thesis_Structure.md`, `FRONTEND_AND_DEPLOYMENT_STORY.md`
- `release/README_RELEASE.md`, `release/MODEL_REGISTRY.md`, `release/config/evidence_calibration.json`
- `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`
- `reports/phase9/final_release/phase9g_final_release_report.md`
- `reports/phase9/integration_docs/phase9f_api_contract.md`
- `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_matrix.md`
- `reports/evaluation/comprehensive_evaluation_report.md`
- `data/statistics/unified_dataset_stats.json`
- `reports/website/PARTNER_INTEGRATION_GUIDE.md`
- `research_article/` (9 PDFs — bibliographic via prep doc 09)

---

# Missing Information / Needs Confirmation

- Student registration numbers
- Official thesis template path (`thesis_layout.pdf` not in repo)
- Reference style (IEEE/APA) — TBD
- ASVspoof 2021 official citation details
- AASIST, WavLM, MUSAN, RIR original paper citations
- Exact GPU/hardware specs for §3.19
- NCCIA acknowledgement approval
- UI screenshots in repo (capture from live site)
- Exact Phase 8/9 axis training set sample counts (check individual model cards)
- Frontend repo not in FYP git — thesis should state separation clearly

---

# Sections Needing External References Most Urgently

1. Ch 2.4 — ASVspoof dataset official paper  
2. Ch 2.8 — AASIST architecture paper  
3. Ch 2.8 — WavLM / SSL embeddings paper (origin model)  
4. Ch 3.7 — MUSAN and RIR augmentation citations  
5. Ch 2.1–2.3 — Core surveys (RA1–RA3 verified DOIs where available)  
6. Ch 2.10 — Partial fabrication (RA6 arXiv verified)
