# FASSD — Project Scope

**Document type:** Canonical project scope (FYP)  
**Last updated:** May 2026 (Phase 8 scope revision)  
**Status:** Active — supersedes the original three-item scope list

> **Scope document locations (duplicates — do not delete):**
>
> | Path | Role |
> |------|------|
> | **`FASSD - Scope.md`** (this file) | **Canonical** project-resource scope — updated in this revision |
> | `reports/UPDATED_PROJECT_SCOPE.md` | Expanded six-scope reference; retained for backward compatibility |
> | `reports/phase8/architecture/fassd_scope_update_draft.md` | Phase 8A draft; does not replace this file |

---

## 1. Project Title

| Type | Title |
|------|--------|
| **Academic title** | Forensic Acoustics for Synthetic Speech Detection |
| **Product-facing title** | Forensic Deepfake Audio Detector |
| **Short name** | FASSD |

---

## 2. Project Vision

FASSD aims to develop a **forensic audio decision-support prototype** that accepts an audio file and produces a **structured forensic analysis** — not a single guaranteed fake/real verdict.

The system should help a reviewer identify:

- indicators consistent with **synthetic / AI-generated speech**
- indicators consistent with **replay / rerecording**
- indicators consistent with **mixer / channel / device processing**
- indicators consistent with **partial fabrication / splicing**
- **suspicious segments** and timestamps where evidence is localized
- an overall **confidence / risk level**
- whether **manual review** is required

**Important limits:** The system is **not** intended to be a legal-proof engine, court-ready certification, or substitute for expert judgment. It is a **forensic analysis and triage support tool** that presents **multi-axis evidence** with explicit limitations.

FASSD is **not** simply a binary real/fake detector. It is a forensic audio decision-support prototype that analyzes audio evidence related to synthetic speech, replay, mixer/channel processing, partial fabrication, and suspicious segments.

---

## 3. Problem Statement

Modern AI voice generation, voice conversion, replay attacks, compression, editing, and partial fabrication make audio authenticity analysis difficult for investigators, journalists, and reviewers.

A simple real/fake classifier is **insufficient** because:

- human speech can be **replayed** or **mixer/channel processed** without being AI-generated
- AI speech can be **directly generated** or **replayed** through a device
- some files contain **only partial fake insertion** inside otherwise human content
- channel artifacts can look suspicious **without** indicating synthetic origin
- forensic reporting needs **evidence and explainability**, not only a label

The project therefore evolved toward **parallel origin, manipulation, and segment evidence** with calibrated fusion and forensic-safe reporting.

---

## 4. Original Scope

The original FASSD scope (early FYP definition) focused on:

1. **AI vs human voice detection** — whether a recording is natural human speech or AI-generated synthetic speech.
2. **Detection of AI-replaced voices in real recordings** — environmental/acoustic inconsistency suggesting voice swap or replacement within a genuine recording.
3. **Replay detection of AI voices** — playback through a device and rerecording, with replay artifacts.

Broader original project intent also included:

- detect synthetic / deepfake speech
- train and evaluate audio classification models
- use public datasets such as **ASVspoof-derived** data
- use **local / collected** audio where needed
- produce a detection result for uploaded audio
- eventually deliver a **usable product / demo**

The initial technical approach was **model-centric** and **binary-classifier oriented** (spoof vs bonafide / fake vs real).

---

## 5. Updated Scope After Experimental Findings

After controlled evaluation (Phase 7A), local forensic dataset work (Phase 7C1), fine-tuning attempts (Phase 7C3), decision-layer prototypes (Phase 7C4), and AASIST experiments (Phase 7E), the scope evolved from a **single fake/real classifier** to a **multi-axis forensic evidence system**.

| Area | Original scope | Updated scope |
|------|----------------|---------------|
| Main output | fake/real decision | forensic evidence summary |
| Model goal | binary classification | origin + manipulation + segment evidence |
| Audio cases | clean vs fake | clean, AI, replay, mixer, partial, edited, compressed |
| Report | simple result | forensic-safe report with limitations |
| Product | local detector | website-based forensic analysis prototype |
| Final decision | model prediction | calibrated fusion + manual review |

Phase 7 did **not** invalidate the project; it produced the findings required to define this updated architecture (see Phase 8).

---

## 6. Core Objectives

Final project objectives:

1. Build an audio analysis pipeline for forensic deepfake / synthetic speech and related manipulation analysis.
2. **Separate origin evidence from manipulation evidence** (parallel axes).
3. Detect or flag direct synthetic speech, replay, mixer/channel processing, and partial fabrication where evidence supports it.
4. Provide **segment-level suspicious evidence** where possible (windows, timestamps, inside/outside region comparisons).
5. Produce **forensic-safe** JSON / Markdown / PDF-ready reports.
6. Provide a **website / demo interface** for uploading audio and viewing structured results.
7. Retain **manual-review logic** when evidence is uncertain, conflicting, or below reliability thresholds.

---

## 7. In-Scope Items

- audio upload and preprocessing
- waveform / spectrogram / audio feature extraction
- **forensic evidence table** (per file and segment where applicable)
- **origin evidence** estimation (human / AI / mixed / unknown)
- **manipulation evidence** estimation (clean, replay, mixer, partial, edit, compression, …)
- replay / rerecording evidence
- mixer / channel processing evidence
- partial fabrication evidence
- suspicious segment / timestamp evidence
- **HybridResNet** evidence branch (baseline manipulation/replay/partial sensitivity)
- **Phase 7C4-v2** decision-layer prototype as **historical / feature reference** (not final product logic)
- possible **frozen SSL embeddings** (e.g. WavLM / wav2vec2) **only after Phase 8A approval**
- acoustic / channel features for replay and mixer evidence
- **calibrated fusion** with abstention and manual-review rules
- forensic-safe report generation
- website / demo UI **after** evidence fusion rules are defined
- final evaluation and FYP defense documentation

---

## 8. Out-of-Scope Items

- legal proof or **court-ready** certification
- speaker **identity verification**
- speaker **diarization** as a core objective
- speech-to-text **transcription** as a main objective
- language **translation**
- **emotion** detection
- **intent** detection
- **lie** detection
- source device identification as a **guaranteed** output
- full end-to-end training of large transformers on limited GPU **unless specifically approved**
- another **binary fake/real model** without multi-axis schema approval
- **hard AI/human first-stage routing** as final product logic
- using **rejected checkpoints** in product decisions (per checkpoint registry policy)

---

## 9. Dataset Scope

### 9.1 Public anti-spoofing / deepfake datasets

- ASVspoof-derived and related project dataset assets
- logical access / deepfake / physical access style data where applicable

### 9.2 Local controlled forensic dataset

- **Phase 7C1** controlled set with roles including:
  - clean human
  - human replay
  - human mixer / channel processed
  - human partial fabrication
  - direct AI
  - AI replay
  - AI mixer / channel processed
  - AI partial fabrication

### 9.3 Controlled holdout

- **Phase 7A** forensic test set
- must remain **holdout**
- must **not** be used for training or threshold tuning presented as unbiased product performance

### 9.4 Collected / curated audio

- broadcast and public-source material where licensed/collected
- YouTube and similar curated samples where applicable
- local recordings
- augmentation data where applicable

**Leakage control:** Dataset use must avoid leakage across **speakers**, **base audio**, and **paired variants** (e.g. clean vs replay of the same base).

---

## 10. Model and Evidence Scope

Models and features are **evidence sources**, not final truth engines. Product decisions must follow the checkpoint registry (`models_saved/registry/`).

| Component | Status | Role |
|-----------|--------|------|
| HybridResNet baseline | usable evidence model | replay / mixer / partial sensitivity; over-flags some clean human |
| Phase 7C4-v2 | accepted **prototype only** | decision-layer / fusion reference |
| Phase 7C3-v1 | rejected | manipulation sensitivity collapsed |
| Phase 7C3-R2 | rejected as standalone | prototype evidence only |
| AASIST pretrained | rejected as current solution | archived experiment |
| AASIST fine-tuned | rejected | archived experiment |
| WavLM / wav2vec2 | candidate feature source | only after Phase 8A approval |
| Acoustic / channel features | planned | channel / mixer / replay evidence |
| Multi-axis fusion | planned | final Phase 8 decision layer |

---

## 11. Final Architecture Scope

Target processing flow:

```text
Audio
  ↓
Preprocessing
  ↓
Evidence extraction
  ↓
Origin axis          Manipulation axes        Segment axis
  ↓                  ↓                        ↓
Fusion layer
  ↓
Forensic report / UI
```

### Origin axis (parallel)

- `human`
- `ai_synthetic` (or equivalent AI indicator)
- `mixed`
- `unknown`

### Manipulation axes (parallel)

- `clean`
- `replay_rerecorded`
- `mixer_channel_processed`
- `partial_fabrication`
- `edited_spliced`
- `compressed_low_quality`
- (additional labels per Phase 8 schema as approved)

### Segment axis

- suspicious windows and timestamps
- inside vs outside region score differences for partial-fabrication roles

### Fusion output

- final forensic status (forensic-safe wording)
- risk level
- evidence summary
- manual review requirement
- report-ready explanation

**Architecture rule:** Origin and manipulation must be inferred **in parallel**. Do **not** use hard AI/human first-stage routing as final logic.

---

## 12. Product Scope

The forensic decision-support prototype should include:

- audio upload
- backend analysis pipeline
- structured forensic decision output
- JSON analysis output
- Markdown / PDF-ready forensic report
- suspicious segment timeline where available
- evidence explanation per axis
- limitations and disclaimer
- website / demo interface

The product must **not** claim legal certainty, guaranteed detection, or final forensic proof.

---

## 13. Reporting Scope

Reports should include:

- audio metadata
- executive summary
- final risk assessment (decision-support wording)
- origin evidence
- manipulation evidence
- suspicious segment evidence
- model / evidence **agreement or disagreement**
- manual review recommendation
- limitations
- disclaimer
- technical traceability (models, versions, run identifiers where applicable)

Report wording must be **forensic-safe** (e.g. “evidence suggests”, “indicators of”, “suspicious”, “manual review required”) — not absolute claims.

---

## 14. Phase-Wise Scope Summary

| Phase | Scope | Status |
|-------|--------|--------|
| Phase 0 | Real-world data collection | Completed |
| Phase 1 | Unified dataset preparation | Completed |
| Phase 2 | Feature extraction pipeline | Completed |
| Phase 3 | HybridResNet architecture | Completed |
| Phase 4 | Model training | Completed |
| Phase 5 | Comprehensive evaluation | Completed |
| Phase 6 | Raw-audio testing & explanation runs | Completed |
| Phase 7A | Controlled forensic testing (holdout) | Signed off |
| Phase 7B | Forensic label preparation | Signed off |
| Phase 7C0 | Dataset audit | Signed off |
| Phase 7C1 | Local forensic dataset and baseline | Signed off |
| Phase 7C2 | Training manifest preparation | Signed off |
| Phase 7C3 | Fine-tuning attempts (v1, R2) | Rejected as final solution |
| Phase 7C4-v1 | Decision layer v1 | Rejected |
| Phase 7C4-v2 | Prototype decision layer | Accepted as **prototype only** |
| Phase 7D | Report layer planning | Postponed → Phase 8G |
| Phase 7E | AASIST experiment | Rejected as current solution |
| Phase 8 | Multi-axis forensic architecture | Initialized (8A freeze in progress) |

Detailed phase history: `reports/FULL_PROJECT_DOCUMENTATION.md`, `reports/phase7/`, `reports/phase8/`.

---

## 15. Phase 7 Final Findings

Phase 7 demonstrated that a **single binary spoof/fake model is insufficient** for the forensic product goal.

Key findings:

- **HybridResNet** is useful for **manipulation evidence** (replay, mixer, partial) but **over-flags clean human** on the controlled set.
- **HybridResNet fine-tuning** (7C3-v1) **collapsed** important forensic behavior.
- **AASIST** did not resolve the clean-human / product semantics problem in this local setup.
- **Phase 7C4-v2** is useful as a **prototype decision layer** but is **not** final product logic.
- Future work must **separate origin, manipulation, and segment evidence** with calibrated fusion.

Phase 7 is a **successful evaluation phase**, not a failed project phase.

---

## 16. Phase 8 Updated Scope

**Phase 8 title:** Multi-Axis Forensic Audio Intelligence Architecture

Phase 8 will define and implement (after **Phase 8A** architecture review):

- evidence table schema and builder
- multi-axis label schema
- acoustic / channel features
- possible frozen SSL embedding features (if approved)
- lightweight multi-axis classifiers
- fusion and abstention / manual-review logic
- report and website integration (including postponed 7D work as Phase 8G)

**Gate:** No model implementation or training should begin before **Phase 8A** architecture is reviewed and signed off.

Canonical Phase 8 entry: `reports/phase8/PHASE8_START_HERE.md`

---

## 17. Evaluation Scope

Final evaluation should measure, at minimum:

- clean-human accepted rate
- clean-human false alarms
- direct AI detected or marked suspicious
- human replay detected
- AI replay detected or suspicious
- human mixer detected
- AI mixer detected
- partial fabrication detected (segment-supported where applicable)
- suspicious segment quality
- Phase 7A holdout behavior (sanity / qualitative — not for product threshold tuning)
- report wording safety

### Controlled Phase 8 targets (Phase 7C1 locked inventory)

| Metric | Target |
|--------|--------|
| `clean_human_accepted` | ≥ 15 / 23 |
| `clean_human_false_alarm` | ≤ 5 / 23 |
| `direct_ai_detected_or_suspicious` | ≥ 18 / 23 |
| `human_replay_detected` | ≥ 20 / 23 |
| `ai_replay_detected_or_suspicious` | ≥ 20 / 23 |
| `human_mixer_detected` | ≥ 20 / 23 |
| `ai_mixer_detected` | ≥ 20 / 23 |
| `partial_fabrication_detected` | ≥ 40 / 46 |

Full criteria: `reports/phase8/validation/phase8a_success_and_rejection_criteria.md`

---

## 18. Hardware and Feasibility Scope

- development on local **Windows / miniconda** environment
- GPU constraints, including **RTX 3050 6GB** laptop GPU
- optional higher-VRAM machine if available for approved experiments
- avoid full fine-tuning of large SSL models unless justified and approved
- prefer **cached embeddings** and **lightweight classifiers** for Phase 8 where possible

---

## 19. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| binary label collapse | multi-axis labels and parallel axes |
| clean-human false alarms | explicit clean-human acceptance metric and fusion rules |
| replay confused with AI | separate replay / channel manipulation axis |
| partial fabrication hidden by file-level averaging | segment / window evidence |
| dataset leakage | base-audio / speaker split protection |
| threshold overfitting | holdout validation policy; no holdout tuning for product claims |
| report overclaiming | forensic-safe wording and disclaimers |
| limited GPU | frozen embeddings + lightweight heads |

---

## 20. Final Deliverables

- trained / accepted **evidence models** or feature pipelines (per registry)
- multi-axis **evidence table**
- **calibrated fusion** logic with abstention
- forensic **JSON** output
- forensic **Markdown / PDF-ready** report
- **website / demo** interface
- final **evaluation report**
- FYP **poster / presentation**
- project **documentation and defense package**

---

## 21. Change Log

| Date / stage | Change |
|--------------|--------|
| Initial scope | Synthetic speech / deepfake detection (three-item list) |
| Phases 0–6 | Dataset, HybridResNet pipeline, training, evaluation, raw-audio testing |
| Dataset expansion | Public, local, and controlled forensic datasets |
| Phase 7 closure | Binary model strategy rejected as **final** architecture |
| Phase 8 initialization | Multi-axis forensic evidence architecture added |
| Current update | Complete project scope revised to match final product direction |

---

## Related documentation

| Document | Purpose |
|----------|---------|
| `reports/FULL_PROJECT_DOCUMENTATION.md` | Full technical project history |
| `reports/NEXT_ACTIONS.md` | Current next steps |
| `reports/FORENSIC_PRODUCT_ROADMAP.md` | Product roadmap |
| `reports/phase7/PHASE7_FINAL_STATUS_FREEZE.md` | Phase 7 closure freeze |
| `reports/phase8/PHASE8_START_HERE.md` | Phase 8 entry point |
