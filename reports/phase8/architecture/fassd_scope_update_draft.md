# FASSD Scope Update — Draft (Phase 8 Forensic Product)

**Status:** DRAFT for supervisor review — **does not replace** [../../../FASSD - Scope.md](../../../FASSD%20-%20Scope.md)  
**Version:** 8A draft 1  
**Date:** 2026-05-28  

---

## 1. Document purpose

This draft expands the original three-item FASSD scope into a **multi-axis forensic audio decision-support** product scope aligned with Phase 8 architecture. It uses careful wording appropriate for a university prototype and public website — **not** court-ready proof or absolute fake/real judgment.

---

## 2. Product positioning (unchanged intent, clarified limits)

| Aspect | Statement |
|--------|-----------|
| Product type | **Forensic audio decision-support prototype** |
| Outputs | **Evidence indicators**, suspicious segments, fused status, manual-review flags |
| Not provided | Court-ready proof, legal verdict, absolute “fake” or “real” label |
| User action | Human expert may use outputs to prioritize review — system recommends, does not prove |

---

## 3. Expanded functional scope

### 3.1 AI vs human voice evidence (origin axis)

**Draft scope item:** The system shall produce **origin evidence indicators** estimating whether dominant speech content is consistent with **human-produced**, **AI-synthetic**, **mixed**, or **unknown** origin.

- Reports shall state evidence strength, not certainty.  
- Origin shall **not** be inferred from replay or mixer evidence alone.

*Maps to original scope §1 — reframed as evidence, not a single detector verdict.*

---

### 3.2 AI voice replacement / partial fabrication

**Draft scope item:** The system shall detect **localized suspicious regions** consistent with **partial fabrication** or voice replacement within longer recordings, including **segment-level timestamps** and inside/outside region comparisons where annotations exist.

- File-level averaging alone is insufficient for this capability.  
- Output: **suspicious segments** with time ranges and reasons — manual review recommended when borderline.

*Maps to original scope §2 — expanded with segment axis.*

---

### 3.3 Replay / rerecording detection

**Draft scope item:** The system shall produce **manipulation evidence** for **replay and rerecording** patterns (e.g. playback through a device and recapture), separate from origin.

- **Human-origin replay** must be reportable without claiming AI generation.  
- **AI-origin replay** must report both origin and manipulation evidence explicitly.

*Maps to original scope §3 — semantic separation enforced.*

---

### 3.4 Mixer / channel / device processing evidence

**Draft scope item:** The system shall indicate when audio is consistent with **mixer, broadcast, or channel/device processing**, as manipulation evidence — **not** as automatic proof of synthetic speech.

- Human speech through mixer/phone chain remains **human origin** unless other origin evidence exists.

*New explicit scope item — required by Phase 7C1 roles.*

---

### 3.5 Additional manipulation evidence (Phase 8)

**Draft scope items:**

- **Edited / spliced** content indicators  
- **Compression / low-quality** stress indicators with abstention when reliability is limited  

---

### 3.6 Segment-level suspicious timestamp detection

**Draft scope item:** For each analyzed file, the system shall expose **window-level scores** and flag **suspicious segments** with start/end times and short **segment reasons** for UI and report embedding.

---

### 3.7 Fusion, risk, and manual review

**Draft scope item:** The system shall **fuse** parallel evidence axes into a controlled **final forensic status** (e.g. accept human clean, suspicious manipulation, suspicious mixed, inconclusive manual review) and set **manual review recommended** when evidence is insufficient or conflicting.

- **`risk_positive`** legacy signals may inform review priority but **must not** be displayed as “fake.”

---

### 3.8 Forensic-safe report generation

**Draft scope item:** The system shall generate **forensic-safe summaries** that:

- Cite which evidence axes contributed  
- Distinguish AI-generation claims from manipulation/channel claims  
- Include timestamps for suspicious segments when present  
- State limitations (quality, domain, prototype status)  

**Prohibited wording in default templates:** “proven fake,” “definitely AI,” “court-ready,” “100% synthetic.”

**Preferred wording:** “evidence consistent with,” “suspicious segment,” “manual review recommended,” “decision-support indicator.”

---

### 3.9 Website-based decision-support interface

**Draft scope item:** A **web-based interface** shall allow upload or selection of audio, display evidence indicators per axis, show segment timeline visualizations, present the forensic summary, and export a review-oriented report (PDF/HTML — implementation in Phase 8G).

- UI presents **indicators and recommendations**, not legal conclusions.  
- Clear disclaimer: prototype for research and assisted review.

---

## 4. Technical scope (high level)

| Layer | In scope |
|-------|----------|
| Evidence table (file + segment) | Yes — Phase 8B |
| Reuse Phase 7 Hybrid / 7C4-v2 outputs | Yes — as evidence |
| Lightweight axis models | Yes — Phase 8E after schema freeze |
| Large SSL fine-tuning | Deferred — frozen embeddings first |
| AASIST as product classifier | **Out of scope** (rejected Phase 7) |

---

## 5. Validation scope (draft)

- Primary: Phase 7C1 controlled roles (metrics in [../validation/phase8a_success_and_rejection_criteria.md](../validation/phase8a_success_and_rejection_criteria.md))  
- Secondary: Phase 7A holdout sanity — no product threshold tuning  

---

## 6. Comparison to original scope file

| Original ([FASSD - Scope.md](../../../FASSD%20-%20Scope.md)) | This draft |
|----------------------------------|------------|
| Three bullet capabilities | Nine detailed capability areas |
| Implied single detection | Multi-axis evidence + fusion |
| No mention of manual review | Inconclusive / manual review required |
| No segment timestamps | Segment axis explicit |
| No mixer/channel item | Mixer/channel manipulation axis |
| No reporting/UI detail | Report + website decision-support |

**Action after approval:** Supervisor may merge this draft into official scope or thesis chapter — **do not auto-overwrite** original file without approval.

---

## 7. Out of scope (explicit)

- Real-time telephony fraud prevention at scale  
- Speaker identification / diarization as primary product  
- Court admissibility certification  
- Training new large foundation models on limited deadline  
- Binary fake/real API as only output  

---

## 8. Approval

| Role | Status |
|------|--------|
| Phase 8A draft complete | ✅ |
| Supervisor approval | ☐ Pending |
| Merge to official scope | ☐ Not done |

**Phase 8B:** NOT STARTED
