# Phase 7D — Report Wording Guide

**Purpose:** Mandatory language rules for all user-facing forensic narrative in JSON and Markdown reports.  
**Audience:** Report builder (`build_phase7d_forensic_report.py`), reviewers, thesis/demo readers.

---

## 1. Core principle

FASSD is a **forensic decision-support prototype**. Reports **indicate** and **suggest**; they do **not** prove authenticity or deception.

Every report must include the standard disclaimer from [PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md](PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md).

---

## 2. Approved phrasing patterns

Use these constructions (adapt with specific evidence):

| Pattern | Example |
|---------|---------|
| Evidence consistency | “The audio shows evidence **consistent with** replay or re-recording indicators under the current analysis settings.” |
| System detection | “The system **detected indicators of** channel processing or mixer-like artifacts.” |
| Suggestion | “This result **suggests** synthetic or AI-generated speech content may be present; manual review is recommended.” |
| Segment evidence | “**Segment-level evidence indicates** elevated spoof-like scores between {start}s and {end}s.” |
| Suspicious treatment | “The file should be **treated as suspicious** pending expert review.” |
| Manual review | “**Manual review is recommended** because model outputs conflict or scores are near decision thresholds.” |
| Origin vs manipulation | “Speech content appears **human-origin**, while the **recording chain** shows manipulation-like indicators (replay/channel), not necessarily AI synthesis.” |
| Partial fabrication | “Most of the file appears human-like overall, but **one or more segments** show indicators that may be consistent with partial insertion or editing.” |
| False-alarm awareness | “This category has **known false-alarm risk** on clean human speech; expert listening is required before any accusatory conclusion.” |
| Limitation | “Results were produced on **controlled evaluation data**; performance on unseen channels and languages is not guaranteed.” |

---

## 3. Forbidden phrasing

**Never** use in `executive_summary`, `technical_summary`, `evidence_summary`, `recommended_action`, or UI headlines:

| Forbidden | Why |
|-----------|-----|
| “definitely fake” / “proven fake” | Over-claims |
| “100% real” / “100% fake” | Over-claims |
| “This proves the speaker is AI” | Conflates detector with identity |
| “Court-ready conclusion” | Legal over-reach |
| “Guaranteed detection” | False certainty |
| “Authentic” / “genuine recording” (as verdict) | Implies chain-of-custody proof |
| “Deepfake confirmed” | Media/legal loaded term without review |
| “The speaker is lying” | Out of scope |

**Automated lint (7D1):** reject report build if narrative contains (case-insensitive):  
`definitely fake`, `proven`, `court-ready`, `guaranteed`, `100%`, `confirms that the`, `legal proof`.

---

## 4. Terminology

| Prefer | Avoid |
|--------|-------|
| synthetic / AI-generated speech indicators | deepfake (unless quoting user) |
| replay or re-recording indicators | “fake recording” without context |
| channel processing / mixer artifacts | “tampered” (vague) |
| partial fabrication **indicators** | “spliced fake audio” (absolute) |
| manual review | automatic rejection |
| decision-layer prototype | final forensic model |
| segment-level evidence | whole-file proof |

---

## 5. Section-specific tone

### Executive summary

- 2–4 sentences.  
- Lead with **risk level** and **review need**.  
- No raw score dumps.  

### Technical summary

- May cite thresholds, chunk counts, model names.  
- Still avoid absolute verdict language.  

### Evidence summary

- Tie claims to **which model** and **which segment**.  
- Mention disagreement when baseline and R2 diverge.  

### Recommended action

- Actionable: “Expert listen to segments X–Y”, “Obtain original device recording”, “Do not use as sole disciplinary evidence”.  

---

## 6. Status-specific headline templates

Templates are expanded in [PHASE7D_DECISION_TO_REPORT_MAPPING.md](PHASE7D_DECISION_TO_REPORT_MAPPING.md). Examples:

**clean_human_accepted**  
> No strong synthetic or manipulation evidence was detected under the current analysis settings. Routine review may still apply per organizational policy.

**clean_human_borderline**  
> The file contains conflicting evidence. Some outputs suggest low risk, while segment-level indicators require manual review. The file should not be labeled as synthetic without expert review.

**direct_ai_detected**  
> The system detected indicators consistent with AI-generated or synthetic speech at the file level under current settings. Manual review is required.

**human_replay_manipulation_detected**  
> Speech content is assessed as likely human-origin, with indicators consistent with replay or re-recording. This does not by itself indicate AI synthesis.

**partial_fabrication_detected**  
> Segment-level evidence suggests possible partial fabrication or inserted synthetic content within an otherwise human-like recording. Manual review of flagged times is required.

---

## 7. Confidence language

`confidence_level` describes **analytic evidence strength**, not legal confidence.

| Level | Wording hint |
|-------|----------------|
| `low` | Near thresholds, heavy VAD drop, or model disagreement |
| `medium` | Clear category signal but known false-alarm or segment-only evidence |
| `high` | Strong consistent file-level + segment evidence (still not “proof”) |

Example `confidence_explanation`:  
> “Confidence reflects internal score separation and model agreement on this controlled test profile; it is not a measure of legal certainty.”

---

## 8. Bilingual / Urdu notes (future)

Phase 7D1 reports are **English** only. Urdu narrative templates are Phase 8+; wording rules above still apply to translations.

---

## 9. Review checklist (human)

Before external demo, confirm each sample report:

- [ ] Disclaimer present  
- [ ] No forbidden phrases  
- [ ] Origin and manipulation separated where applicable  
- [ ] Borderline ≠ “fake”  
- [ ] Partial cases reference times  
- [ ] Limitations mention prototype + 7C1/7A scope  
