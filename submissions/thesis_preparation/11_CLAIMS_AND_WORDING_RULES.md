# Claims and Wording Rules for FASSD Thesis

Strict language rules derived from release documentation, Phase 8/9 validation, and forensic safety policy. **When in doubt, use the replacement phrase.**

**Primary sources:** `(IST-Dean-F-18)_S_Project Proposal Form-1.docx` (via `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md`), `release/MODEL_REGISTRY.md`, `reports/phase8/freeze/phase8g_limitations_and_claims.md`, `reports/phase9/integration_docs/phase9f_known_limitations.md`, `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md`

---

## 0. Scope and deployment rules (read first)

| Rule | Detail |
|------|--------|
| Official scope authority | IST proposal form — not `FASSD - Scope.md` alone |
| Extended work | Phase 7–9 multi-axis system = extensions, not scope replacement |
| NCCIA | Do **not** present as continuing official partner unless confirmed; use “supervision and external consultation” |
| Gradio/FastAPI | **Demo/testing interface only** — not final submission application |
| Next.js frontend | **Intended final user-facing deployment** — state if still in progress |
| Approved-scope claims | Allowed when backed by proposal + baseline results (LCNN, EER, software deliverable) |
| Extended claims | Must use experimental / prototype / decision-support wording |

---

## 1. System Identity — Allowed Wording

| Allowed phrase | When to use |
|----------------|-------------|
| experimental forensic audio **decision-support prototype** | Describing final system status |
| **multi-axis evidence indicators** | Describing outputs (origin, replay, mixer, partial) |
| **voice origin evidence** | SSL origin axis result |
| **replay / rerecording evidence** | Replay axis — always decouple from AI origin |
| **mixer / channel evidence** | Mixer axis — broadcast, phone, PA processing |
| **partial fabrication candidate regions** | Segment localizer output |
| **manual review recommended** | Elevated, mixed, or inconclusive cases |
| **evidence strength: Low / Medium / High** | User-facing bands (Phase 6) |
| **inconclusive under replay/channel processing** | Origin reliability caveat |
| **experimental_manual_review_only** | Partial module status |
| **software-based deepfake speech detection system** | Official proposal deliverable (baseline + extended software stack) |
| **local experimental demo and testing interface** | Gradio/FastAPI in `release/` |
| **intended final web-based frontend** | Next.js application (under development if incomplete) |
| **additional forensic-review requirements suggested during supervision and external consultation** | Explaining extensions without NCCIA endorsement |
| **Deepfake Audio Detector — Local Demo** | Phase 9 release folder name — demo tooling only |
| **FASSD — Forensic Acoustics for Synthetic Speech Detection** | Academic/thesis project name |
| **not a conclusive authenticity decision** | Required disclaimer |
| **leakage-safe internal evaluation** | Phase 7/8 controlled metrics |
| **external heterogeneous test set (`testing_audios`)** | Honest generalization reporting |

---

## 2. Forbidden Wording

| Forbidden phrase | Why forbidden | Source |
|------------------|---------------|--------|
| proves audio is fake / proves authentic | Legal/overclaim | phase8g_limitations |
| court-ready proof / courtroom evidence | Out of scope | phase9f_known_limitations |
| detects all deepfakes | Not supported | phase8g_limitations |
| final production-ready forensic system | Experimental status | phase7_final_release_report |
| operational deployment readiness | Local demo only | phase9g_final_release_report |
| replay means AI / replay proves synthetic origin | Semantic error | MODEL_REGISTRY, Phase 8A |
| mixer/channel means AI-generated | Semantic error | Same |
| no partial evidence means authentic | Absence ≠ proof | partial_report_contract.json |
| guaranteed detection of manipulation | Phase 4 failed; mixer weak externally | phase4 decision, final matrix |
| 100% accurate / perfect detector | Contradicted by failure tables | testing_audios matrix |
| **Forensic Deepfake Audio Detector** (as demo product name) | Phase 9 P4B naming check | phase9e_p4b validation |
| raw probability as "confidence" in user-facing text | Phase 6 policy | evidence_calibration.json |
| NCCIA endorsement / continuing partnership / deployment acceptance | No proof in repo; director change — use neutral consultation wording |
| NCCIA as official formal partner (unless supervisor confirms) | User instruction 2026-06-13 |
| Gradio/FastAPI described as final deployed application | User instruction; `16_OFFICIAL_SCOPE_VS_EXTENDED_WORK.md` |
| “The official proposal promised Phase 9 multi-axis release” | Misframes scope — extensions came later |
| Implies `FASSD - Scope.md` is the only official scope | Proposal form is authority |

---

## 3. Thesis-Safe Replacement Phrases

| Instead of… | Write… |
|-------------|--------|
| "The system proves the audio is fake." | "The system reports evidence indicators consistent with synthetic speech origin; manual forensic review is recommended." |
| "Replay detected → AI-generated." | "Replay/rerecording evidence was detected; this does not by itself indicate AI-generated speech." |
| "Mixer processing detected → deepfake." | "Mixer/channel processing evidence was detected; human-origin recordings may exhibit similar artifacts." |
| "No partial fabrication found → audio is real." | "No partial-fabrication candidate regions were flagged by the experimental module; this does not prove authenticity." |
| "Model confidence 0.99." | "Evidence strength: High (uncalibrated score in technical appendix)." |
| "State-of-the-art forensic system." | "Experimental prototype evaluated on controlled and external test subsets with documented limitations." |
| "Detects WhatsApp deepfakes reliably." | "Platform-compressed AI cases remain challenging (e.g. T4.5 false negative in external testing)." |
| "HybridResNet is the final model." | "HybridResNet is an inactive reference baseline; the release uses separate axis models." |
| "AASIST improves origin detection." | "AASIST was shadow-tested and rejected for active use due to elevated clean-human false-AI rates." |
| "Gradio is the final FYP application." | "A Gradio/FastAPI interface was developed for local experimentation, testing, and demonstration; the intended final user-facing deployment is a Next.js web application integrated with the backend inference pipeline." |
| "Developed in partnership with NCCIA." | "Some extended forensic-review requirements were influenced by supervisor feedback and external consultation during the project." |
| "The scope was changed to multi-axis only." | "The approved scope was extended after implementation revealed real-world forensic limitations." |
| presenting only leakage-safe metrics as final | Also cite external `testing_audios` failures when citing extended system |

---

## 4. Mandatory Disclaimers (use at least once)

Include in Abstract, Chapter 1, Chapter 4 discussion, and Chapter 5:

1. The FASSD release is an **experimental forensic evidence demo**, not a court-ready authenticity system.  
2. Each axis provides **independent evidence**; replay/mixer do **not** imply AI-generated speech.  
3. Origin evidence is **less reliable** under replay, platform compression, and unfamiliar recording chains.  
4. Partial evidence identifies **candidate regions** for review; it does not prove fabrication.  
5. Low/Medium/High bands are **evidence bands** fitted on leakage-safe dev, not legal probabilities.  
6. External testing documents known failures (cite Table 4.16 file IDs).  

**Source:** `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md` §Final Disclaimers

---

## 5. Results Reporting Rules

| Rule | Detail |
|------|--------|
| Pair internal + external | When citing origin bal-acc 0.95 leakage-safe, also cite testing_audios 0.8250 |
| Separate active vs rejected | Hybrid/AASIST/Phase 4 v3 in "experiments" not "final system" |
| Count-based metrics | Phase 7C1 uses n=23 — state small sample explicitly |
| Partial metrics | Explain gating when citing partial 1.0000 on testing_audios |
| Negative results | Phase 3 closures and Phase 4 STOP are contributions |
| Demo regression | 184/184 PASS validates formatting, not field generalization |

---

## 6. Chapter-Specific Guidance

| Chapter | Emphasis |
|---------|----------|
| Abstract | Official deliverable achieved + extended prototype limitation in final sentence |
| Introduction | **Official scope first (§1.4–1.5.1), extensions second (§1.5.2)** |
| Literature | Official ASVspoof/LCNN literature first; extended topics labeled |
| Methodology | LCNN proposal plan → evolution; **Gradio vs Next.js deployment split** |
| Results | **§4.2–4.3 official**; **§4.7+ extended**; failure table for extended |
| Conclusion | Official objectives met + extended objectives with limits |

---

## 7. Naming Rules Summary

| Context | Use |
|---------|-----|
| Thesis cover / academic | Forensic Acoustics for Synthetic Speech Detection |
| Short | FASSD |
| Software demo (Gradio) | Deepfake Audio Detector — Local Demo (testing only) |
| Final web UI (intended) | Next.js web application |
| Avoid as product title | Forensic Deepfake Audio Detector (unless supervisor overrides Phase 9 rule) |

---

## 8. Quick Self-Check Before Submitting Any Paragraph

- [ ] Does this sentence imply legal proof?  
- [ ] Does replay/mixer language imply AI?  
- [ ] Is a rejected model described as active?  
- [ ] Are external failures mentioned when citing strong internal metrics?  
- [ ] Is manual review mentioned for elevated indicators?  
- [ ] Does this imply NCCIA endorsement or continuing partnership?  
- [ ] Does this describe Gradio as the final application?  
- [ ] Does this treat `FASSD - Scope.md` as official approved scope without proposal form?  
- [ ] Are official-scope and extended-scope results clearly separated?  
