# Literature Review Rebuild Strategy

**Purpose:** Rebuild Chapter 2 around **official approved scope first**, then **extended implementation scope**, using `research_article/` PDFs as **legacy seed material** only—not as the sole literature base.

**Scope authority:** `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`  
**Reference catalog:** `09_REFERENCES_RESEARCH_GAP_PLAN.md`, `15_REFERENCE_SELECTION_MATRIX.csv`

---

## 1. Two-layer literature structure

### Layer A — Official approved scope literature

Support the proposal form topics:

| Topic | What to cite | FASSD evidence to connect |
|-------|--------------|---------------------------|
| ASVspoof 2021 LA/DF | Official challenge papers **TBD** | `data/statistics/unified_dataset_stats.json` |
| Anti-spoofing / bonafide vs spoof | RA1, RA2 survey sections | Phase 3 LCNN baseline |
| LFCC / log-mel features | RA1, RA7 | `PROJECT_STORY_FROM_DAY_ONE.md` §4–7 |
| LCNN / lightweight CNN | RA1; ASVspoof baseline papers **TBD** | Baseline 15.71% EER augmented |
| Data augmentation (MUSAN, RIR, codec) | ASVspoof augmentation literature **TBD** | Phase 2 augmentation |
| Replay simulation / PA attacks | RA1, RA2 | Proposal objective 4 |
| EER, ROC-AUC, confusion matrices | RA1, RA2 | `comprehensive_evaluation_report.md` |
| Deepfake in real recordings | RA4, RA6 (partial) | Proposal objective 3 |
| Software-based detection systems | RA2 | Official deliverable type |

### Layer B — Extended scope literature

Support work beyond the LCNN proposal:

| Topic | What to cite | FASSD evidence |
|-------|--------------|----------------|
| Deep ResNet / spectrogram CNNs | RA7 | 2.61% EER ASVspoof |
| Environmental / forensic acoustics | RA6, RA8 | 12 env features, Phase 4.3 |
| Domain mismatch / generalization | RA5 | Broadcast failure, testing_audios |
| AASIST / graph attention | **TBD** (not in research_article/) | Phase 7E rejection |
| SSL / Whisper embeddings | RA9 | Origin SSL release model |
| Multi-axis / explainable forensic reporting | RA6; gap from RA2 | Phase 8 architecture |
| Segment-level / partial fabrication | RA6 | Phase 5 partial redesign |
| Decision-support vs legal proof | RA2 limitations | `11_CLAIMS_AND_WORDING_RULES.md` |
| Web UI for forensic/ML tools | General HCI/ML deployment lit **TBD** | Next.js intended frontend |

---

## 2. Role of `research_article/` PDFs

| Status | Rule |
|--------|------|
| RA1–RA9 | **Seed/survey material** — use for Chapter 2 themes, not as proof FASSD invented methods |
| Priority for official scope | RA1, RA2, RA7 (spectral/CNN), plus ASVspoof papers to be added |
| Priority for extended scope | RA5, RA6, RA9 |
| RA3 | Optional multimedia survey — use sparingly (broader than audio-only thesis) |
| RA8 | Optional pause-pattern cue — secondary to core pipeline |

Do **not** imply every RA paper was used to implement the final release. Map papers to **topics**, not unchecked implementation claims.

---

## 3. Chapter 2 writing order (recommended)

1. **2.1–2.2** Threat model and synthetic speech (RA4, RA2) — motivates proposal  
2. **2.3–2.4** Anti-spoofing and ASVspoof (RA1, RA2 + official ASVspoof **TBD**) — official dataset basis  
3. **2.5–2.6** LFCC, log-mel, LCNN/CNN (RA1, RA7) — **official method alignment**  
4. **2.7** Augmentation and replay (RA1, RA2) — official robustness plan  
5. **2.8** Evaluation metrics EER/AUC (RA1, RA2) — official evaluation  
6. **2.9–2.10** Extended topics: ResNet, environmental cues, SSL, partial segments (RA5–RA7, RA9) — label as **extensions**  
7. **2.11** Research gaps → motivates multi-axis extension without claiming it was in proposal  
8. **2.12** Formal problem statement — bridge official + extended  

---

## 4. Literature ↔ results alignment (Chapter 4)

| Results subsection | Official scope results | Extended scope results |
|--------------------|------------------------|------------------------|
| Baseline LCNN/LFCC | Table 4.1 | — |
| LFCC vs log-mel | Table 4.2 | — |
| ResNet | Table 4.3 | Extension |
| Hybrid / unified dataset | Table 4.5–4.7 | Extension |
| Phase 7 forensic | — | Tables 4.8–4.10 |
| Release audit matrix | — | Table 4.16 |

When discussing literature in Ch. 4, cite **RA7** near ResNet/Hybrid spectral results; cite **RA5** near domain-mismatch discussion.

---

## 5. Gaps to fill manually (high priority)

1. ASVspoof 2021 official publication  
2. AASIST (Jung et al.) — Phase 7E  
3. LCNN / Light CNN anti-spoof baseline paper cited in ASVspoof community  
4. MUSAN and RIR augmentation dataset citations (if augmentation section is detailed)  
5. wav2vec2 / WavLM if origin SSL axis discussed beyond RA9 Whisper paper  

---

## 6. Title defence vs proposal vs thesis

| Source | Use in literature review |
|--------|--------------------------|
| Proposal form | Defines **minimum** literature coverage (ASVspoof, LCNN, features, metrics) |
| Title defence PPTX | Motivation only; **do not** treat binary pipeline slide as final architecture |
| Phase 8/9 docs | Cite as **project reports** when describing extended system—not as external literature |

---

## 7. Quality checks before Chapter 2 draft is complete

- [ ] First half of Ch. 2 supports **proposal form** method (LCNN, LFCC, log-mel, ASVspoof, EER)  
- [ ] Extended topics clearly labeled as post-proposal development  
- [ ] RA papers cited for **concepts**, not false implementation claims  
- [ ] ASVspoof official citation added (not only surveys)  
- [ ] No NCCIA endorsement implied in literature chapter  
- [ ] Deployment literature (if any) distinguishes demo UI vs production web frontend  
