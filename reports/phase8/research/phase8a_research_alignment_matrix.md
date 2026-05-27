# Phase 8A — Research Alignment Matrix

**Status:** Frozen for Phase 8A architecture review  
**Purpose:** Map FASSD forensic product requirements to research areas that must be confirmed before implementation — **not** a bibliography of completed literature review.  
**Rule:** Source placeholders mark gaps to fill during research; do not treat placeholders as citations.

---

## How to use this matrix

| Column | Meaning |
|--------|---------|
| **Project requirement** | FASSD / Phase 8 forensic capability |
| **Relevant research area** | Topic to investigate |
| **Why it matters for FASSD** | Product justification |
| **Architecture implication** | What Phase 8 must build |
| **Risk if ignored** | Failure mode (often seen in Phase 7) |
| **Source placeholder** | Where to anchor protocol or paper — **to be filled** |

---

## Matrix

| Project requirement | Relevant research area | Why it matters for FASSD | Architecture implication | Risk if ignored | Source placeholder |
|---------------------|------------------------|--------------------------|---------------------------|-----------------|-------------------|
| Separate human vs AI voice **origin** | Speaker / synthetic speech detection, generative TTS vs human vocoder cues | Product scope item 1 — users ask “is this AI-generated?” | Dedicated **origin evidence axis** (`human`, `ai_synthetic`, `mixed`, `unknown`); never infer from manipulation alone | Replay/mixer flagged as “fake”; clean human over-alarmed | [ASVspoof official protocol/paper needed] |
| Detect **replay / rerecording** without claiming AI | Replay attack detection, physical playback + re-capture | Scope item 3; Phase 7 Hybrid strong on replay | **Manipulation axis** `replay_rerecorded` parallel to origin; fusion forbids replay → `ai_synthetic` | Human mic replay reported as deepfake | [channel/replay detection reference needed] |
| **Mixer / channel / device** processing evidence | Channel mismatch, broadcast chain, device transfer functions | Local 7C1 human/AI mixer roles; anti-spoof confuses channel with spoof | Axis `mixer_channel_processed`; channel features in 8C | Mixer artifacts → “AI-generated” in report | [channel/replay detection reference needed] |
| **Partial fabrication** / voice replacement in real recordings | Audio deepfake localization, splice detection, inconsistent segment origin | Scope item 2; file-level mean fails | **Segment axis** + `partial_fabrication` + inside/outside region delta | Short synthetic insert missed | [deepfake audio localization paper needed] |
| **Edited / spliced** content | Audio forensics cut detection, discontinuity cues | Distinct from full-file synthetic or replay | Manipulation label `edited_spliced`; segment timestamps | Edits collapsed into generic “fake” | [audio splice forensics reference needed] |
| **Compression / low quality** handling | Codec artifacts, bandwidth reduction vs spoof cues | Noisy local recordings; must not equal “fake” | `compressed_low_quality` manipulation; abstention path | Low quality → false AI claim | [compression artifact vs spoof reference needed] |
| **Multi-label** forensic roles | Multi-task learning, hierarchical labels | Human replay ≠ AI replay; AI mixer ≠ human clean | Allowed combinations in label schema; parallel inference | Binary label collapse | [anti-spoofing survey needed] |
| **Segment-level** suspicious regions | Weakly supervised localization, sliding-window detection | 19/23 direct-AI rescued at segment level in Phase 7 | Per-window evidence table rows; aggregation rules in fusion | Partial fabrication hidden by averaging | [deepfake audio localization paper needed] |
| **Calibration & abstention** | Reject option, selective prediction, forensic uncertainty | Witness-grade recordings need manual review path | `inconclusive_manual_review`, `manual_review_required` | Forced binary verdict; overclaiming | [selective prediction / abstention in audio reference needed] |
| **Fusion** of heterogeneous scores | Score fusion, Dempster–Shafer / rule-based fusion (words only in 8A) | 7C4-v2 prototype; multiple evidence streams | Phase 8F fusion layer; clean-human protection rules | Single threshold on Hybrid score | [score fusion for anti-spoof reference needed] |
| **Anti-spoof benchmarks** (context only) | ASVspoof, ADD Challenge metrics | Informs feature ideas — **not** product definition | AASIST archived as optional feature column only | Leaderboard chasing; domain mismatch (22/23 clean FA) | [ADD Challenge protocol/paper needed] |
| **SSL embeddings** for origin (later) | WavLM, wav2vec2, self-supervised speech | Rich origin cues without immediate large fine-tune | Phase 8D frozen embeddings as features | Premature training; deadline slip | [SSL speech model reference needed] |
| **Forensic reporting** standards | Decision-support, human-in-the-loop AI in law enforcement | Thesis / product must not claim court-ready proof | Phase 8G templates: evidence indicators, manual review | “Proven fake” from score > 0.5 | [forensic AI decision-support reporting reference needed] |
| **Dataset leakage** control | Speaker-disjoint splits, variant grouping | 7C2 `split_group_id` discipline | Evidence table carries `split`, `source_dataset`; validation asserts no leakage | Inflated replay/partial metrics | [ASVspoof official protocol/paper needed] |
| **Urdu / local device domain** | Cross-lingual / cross-device robustness | FASSD local recordings ≠ ASVspoof English | Domain tags; abstention; no global threshold claim | AASIST-style clean-human false alarms | [domain robustness audio forensics reference needed] |
| **Risk vs origin semantics** | Forensic risk scoring vs content authenticity | Phase 7 `risk_target` ≠ AI-generated | `risk_positive` in features only; fusion uses axis labels | risk_positive = fake in UI | [anti-spoofing survey needed] |

---

## Phase 7 findings preserved in research priorities

| Phase 7 finding | Research alignment action |
|-----------------|----------------------------|
| HybridResNet useful for manipulation, not origin truth | Research confirms replay/mixer/partial detectors ≠ origin classifiers |
| Binary fine-tune rejected | No single-label training objective without multi-axis approval |
| 7C4-v2 decision layer only | Fusion literature + abstention — not new monolithic classifier |
| AASIST rejected standalone | Anti-spoof papers inform features, not product architecture |

---

## Research confirmation checklist (before Phase 8E training)

- [ ] Origin vs manipulation definitions aligned with at least one public protocol (ASVspoof / ADD) **without** adopting binary product semantics  
- [ ] Replay detection literature distinguishes physical replay from synthetic generation  
- [ ] Partial-fabrication localization approach chosen (window size, aggregation)  
- [ ] Reporting language reviewed against decision-support (not court-proof) standards  
- [ ] Placeholders above replaced with real citations in thesis bibliography — **not required for 8A sign-off**

---

## Related Phase 8A documents

- [../architecture/phase8a_architecture_freeze.md](../architecture/phase8a_architecture_freeze.md)  
- [../label_schema/phase8a_multi_axis_label_schema.md](../label_schema/phase8a_multi_axis_label_schema.md)  
- [../validation/phase8a_success_and_rejection_criteria.md](../validation/phase8a_success_and_rejection_criteria.md)

**Phase 8B status:** NOT STARTED
