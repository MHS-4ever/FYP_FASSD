# Phase 7D — Forensic Report Layer

**Status:** 📋 **SPECIFIED** (implementation after Phase 7A review)  
**Priority:** 🔴 **MANDATORY** (not optional)  
**Dependencies:** Phase 6 inference outputs; Phase 7A failure patterns; optional Phase 7C fine-tuned checkpoint  
**Training:** None (rule + mapping layer; may add ML later)

---

## 1. Goal

The **report layer** converts raw model scores (Phase 6 / future ensemble) into **safe, understandable forensic conclusions** suitable for UI, API, PDF/HTML export, and human review.

It does **not** replace the detector; it **interprets** it.

---

## 2. Inputs

From Phase 6 / Phase 7A JSON (and future Phase 7F ensemble):

| Input | Description |
|-------|-------------|
| `prediction` | `REAL` or `FAKE` (whole-file, pooled) |
| `confidence` | Distance to threshold |
| `decision_score` | Pooled spoof vote or equivalent |
| `effective_threshold` | Operating threshold used |
| `attack_type` | Top multiclass class name |
| `attack_probs` | `[bonafide, synthesis, conversion, replay]` |
| `chunk_scores` | Per-chunk spoof probabilities (from JSON debug or future export) |
| `n_chunks_used` | Chunks after VAD |
| `n_chunks_total` | Chunks before VAD |
| `env_features` | Aggregated environmental dict |
| `env_reasons` | Heuristic env strings |
| `spec_reasons` | Pooling / VAD / consistency strings |
| `suspicious_regions` | List of `{start_time, end_time, ...}` (built in 7D) |
| VAD information | `vad_mode`, chunks dropped, speech ratios |

**Future inputs (Phase 7F):** AASIST score, WavLM score, environmental inconsistency score.

---

## 3. Report Output Schema

Top-level forensic report object:

| Field | Type | Description |
|-------|------|-------------|
| `file_name` | string | Original filename |
| `duration` | float | Duration in seconds |
| `sample_rate` | int | Hz |
| `file_hash` | string | Optional SHA-256 |
| `model_checkpoint` | string | e.g. `hybrid_resnet_environmental_best.pth` |
| `origin_label` | enum | `human_likely`, `ai_likely`, `mixed_or_partial_ai`, `uncertain` |
| `manipulation_label` | enum | See roadmap |
| `attack_hint` | enum | `bonafide`, `synthesis`, `voice_conversion`, `replay`, `unknown` |
| `risk_level` | enum | `low`, `medium`, `high`, `inconclusive` |
| `final_verdict` | string | Short headline (UI) |
| `confidence_note` | string | Reliability explanation |
| `model_scores` | object | Raw/detector scores |
| `suspicious_timeline` | array | Segment entries (see §6) |
| `environmental_findings` | object | Features + interpretations |
| `forensic_interpretation` | string | Main narrative paragraph(s) |
| `limitations` | array of strings | Always present |
| `recommended_next_step` | string | e.g. manual review |

Nested `model_scores` should include: `prediction`, `decision_score`, `effective_threshold`, `confidence`, `attack_type`, `attack_probs`, `pooling`, `n_chunks_used`, `n_chunks_total`.

---

## 4. Wording Rules

### Use

- likely  
- suggests  
- indicates  
- shows signs of  
- consistent with  
- may indicate  
- requires review  

### Avoid

- proved  
- confirmed  
- 100% real / 100% fake  
- guaranteed  
- definitely authentic  
- court-proof  
- malicious deepfake (unless user context supplies it)  

---

## 5. Case-Based Wording Templates

Select template by mapped case (rules in report mapper). Replace bracketed values at runtime.

### Case A — Clean human

> The audio is assessed as **human-likely** with **low manipulation risk**. No strong AI-generation, replay, or processing indicators were detected.

### Case B — Direct AI

> The audio is assessed as **AI-likely**. The model detected synthetic speech patterns consistent with generated or text-to-speech audio.

### Case C — Voice conversion / cloned voice

> The audio shows **conversion-like** characteristics. This may indicate voice cloning, voice conversion, heavy processing, or impersonation-style synthetic speech.

### Case D — Human replay

> The speech appears **human-origin**, but the recording shows **replay or re-recording risk**. It should **not** be treated as a clean original recording.

### Case E — Human mixer/equalizer processed

> The audio appears **human-origin**, but **processing-like artifacts** were detected. These may be caused by mixer/equalizer processing, channel alteration, noise reduction, or re-recording.

### Case F — AI replay

> The audio is assessed as **AI-likely** and also shows **replay/re-recording** indicators. This suggests the voice may have been generated synthetically and then played through a device before being recorded again.

### Case G — WhatsApp/social compression

> The audio contains **platform or codec-compression** characteristics. Compression may affect model confidence and acoustic features, so the result should be interpreted with caution.

### Case H — Partial fake inserted

> The recording is **mostly human-like** overall, but **one or more suspicious segments** were detected. These segments show AI/conversion-like or environment-mismatch characteristics and may indicate **partial fabrication**, inserted synthetic speech, or splicing.

### Case I — Edited/spliced human

> The speech appears **human-origin**, but **environmental inconsistency** was detected across the recording. This may indicate editing, splicing, inserted speech, or a change in recording environment.

### Case J — Borderline/inconclusive

> The result is **borderline**. The model does not have enough confidence to make a strong real/fake decision. **Manual review** or a cleaner/longer sample is recommended.

### Case K — Short/low-quality audio

> The **reliability** of this result is limited because the audio is short, noisy, or contains limited speech.

---

## 6. Suspicious Timeline Format

Each entry in `suspicious_timeline`:

| Field | Description |
|-------|-------------|
| `start_time` | Seconds (float) |
| `end_time` | Seconds (float) |
| `risk_level` | `low` \| `medium` \| `high` |
| `chunk_scores` | Spoof prob(s) in range |
| `attack_hint` | Dominant class in range |
| `environmental_reason` | Brief env note |
| `explanation` | One line for UI |

**Display example:**  
`00:48–01:01 | High Risk | AI/conversion-like segment detected`

**Builder logic (planned):** Flag chunks where `spoof_prob >= chunk_threshold` or local env mismatch vs file median; merge adjacent chunks; cap list length for UI.

---

## 7. Limitation Section

**Always include** (static + dynamic):

- Results are **probabilistic**, not proof.  
- **Audio quality**, length, and language affect reliability.  
- **Compression, replay, noise, and platform processing** can affect scores.  
- System **supports forensic review** but does **not** replace expert judgment.  
- **Borderline** results require manual review.  
- Training is dominated by **English studio/broadcast**; Urdu/phone/social may be less reliable until Phase 7C.

Dynamic additions when applicable:

- Only *N* chunks used after VAD.  
- Decision score near threshold.  
- `partial_fabrication_detected` with whole-file REAL.

---

## 8. Deliverables (Phase 7D)

| Deliverable | Description |
|-------------|-------------|
| Report JSON schema | Versioned `forensic_report_v1.json` |
| Risk mapping logic | Phase 6 → layered labels |
| Suspicious timeline builder | Chunk-level regions |
| Wording templates | Cases A–K |
| UI-ready fields | Match [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md) |
| Future PDF/HTML | Export from same schema (Phase 8) |

**Do not implement in this documentation task** — spec only.

---

## Related

- [UPDATED_PROJECT_SCOPE.md](../UPDATED_PROJECT_SCOPE.md) — Scope 6  
- [FORENSIC_PRODUCT_ROADMAP.md](../FORENSIC_PRODUCT_ROADMAP.md)  
- [PHASE7_DOMAIN_ADAPTATION.md](PHASE7_DOMAIN_ADAPTATION.md) — Phase 7 sequence  
- [PHASE7A_FORENSIC_TEST_SUITE.md](PHASE7A_FORENSIC_TEST_SUITE.md) — Tests partial fabrication detection capability  
