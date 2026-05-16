# FASSD Forensic Report Output Specification

**Purpose:** Define what the **Forensic Voice Authenticity Analyzer** report should show to users, reviewers, and API consumers.  
**Status:** Specification only (UI/API implementation in Phase 7D / Phase 8)  
**Baseline model:** `HybridResNetEnvironmental` + Phase 6 chunk inference (interim scorer)

---

## 1. Report Header

| Field | Description | Example |
|-------|-------------|---------|
| `file_name` | Original upload name | `evidence_001.wav` |
| `duration_s` | Total duration | `127.4` |
| `sample_rate_hz` | Detected or decoded rate | `16000` |
| `channels` | Mono/stereo | `1` |
| `file_format` | Container/codec | `wav`, `mp3` |
| `analysis_timestamp` | ISO 8601 UTC/local | `2026-05-16T14:30:00` |
| `model_id` | Checkpoint / TorchScript id | `hybrid_resnet_environmental_best` |
| `model_version` | Date or git hash | `epoch_17_val_eer_20.17` |
| `inference_profile` | Pooling + thresholds used | `pct_vote_0.65_0.70_vad40` |
| `file_hash_sha256` | Optional integrity | `abc123...` |

---

## 2. Main Verdict

Layered fields (see `reports/FORENSIC_PRODUCT_ROADMAP.md`):

| Field | Type | Description |
|-------|------|-------------|
| `origin_label` | enum | `human_likely` \| `ai_likely` \| `mixed_or_partial_ai` \| `uncertain` |
| `manipulation_label` | enum | `clean_original` \| `replayed_or_re_recorded` \| `channel_processed` \| `platform_compressed` \| `edited_or_spliced` \| `environment_mismatch` \| `noisy_low_quality` \| `uncertain` |
| `risk_level` | enum | `low` \| `medium` \| `high` \| `inconclusive` |
| `final_verdict` | string | Short headline for UI (not legal conclusion) |
| `confidence_note` | string | Explains reliability limits |

**Example `final_verdict` (not legal advice):**  
*“Speech appears human-origin with moderate channel/re-recording risk; not assessed as direct AI synthesis under current model settings.”*

---

## 3. Model Scores

Expose baseline detector outputs transparently:

| Field | Description |
|-------|-------------|
| `prediction` | `REAL` or `FAKE` (binary head + pooling) |
| `decision_score` | Score used vs threshold (e.g. pct_vote ratio) |
| `effective_threshold` | e.g. `0.70` |
| `confidence` | Distance to threshold (UI-defined) |
| `attack_type` | Top multiclass: bonafide, synthesis, conversion, replay |
| `attack_probs` | `[P_bonafide, P_synthesis, P_conversion, P_replay]` |
| `pooling` | `pct_vote`, `median`, etc. |
| `spoof_prob_mean` | Mean chunk spoof probability |
| `spoof_prob_median` | Median chunk spoof probability |
| `n_chunks_used` | Chunks after VAD |
| `n_chunks_total` | Chunks before VAD |
| `vad_summary` | Mode, percentile, chunks dropped |

---

## 4. Segment Timeline

For long files, list **suspicious or high-interest chunks** (not necessarily every chunk):

| Field | Description |
|-------|-------------|
| `chunk_index` | 0-based |
| `start_time_s` | Segment start |
| `end_time_s` | Segment end |
| `spoof_probability` | Per-chunk score |
| `attack_hint` | Argmax multiclass on chunk |
| `environmental_notes` | Brief (RT60, SNR flags) |
| `reason` | Why flagged (e.g. “above chunk_threshold 0.65”) |

**UI:** Timeline bar or table; click chunk for detail.

**Threshold for listing:** e.g. spoof_prob ≥ 0.65 or top 10% of chunks.

---

## 5. Environmental Findings

Aggregated (median over chunks) with plain-language interpretation:

| Feature | Report label |
|---------|----------------|
| `rt60` | Reverberation (RT60) |
| `snr` | Signal-to-noise ratio |
| `background_level` | Background noise level |
| `silence_ratio` | Silence / pause ratio |
| `spectral_flatness` | Spectral flatness |
| `spectral_rolloff` | Spectral rolloff |
| `spectral_tilt` | Spectral tilt |
| `cleanliness_score` | “Too clean” indicator |
| `background_consistency` | Background stability |
| `env_stability` | Environmental stability |
| `high_freq_content` | High-frequency content |

Include `env_reasons[]` strings from Phase 6 (heuristic, not attribution).

---

## 6. Forensic Interpretation Rules

Apply **after** model scores. Examples for `final_forensic_interpretation` text:

| Pattern | Suggested narrative |
|---------|---------------------|
| Human-likely + high **conversion** prob | Human-origin speech; possible channel/processing or conversion-like artifacts — not automatic deepfake proof. |
| AI-likely + high **replay** prob | AI-generated content likely replayed or re-recorded. |
| Human-likely + **replay** / high decision_score on replay chunks | Human-origin; recording may be second-hop (speaker/phone), not necessarily synthetic speech. |
| `decision_score` within ±0.05 of vote threshold | **Borderline / inconclusive** — request longer or less compressed sample. |
| Duration &lt; 8 s (below Phase 7A minimum) or `n_chunks_used` &lt; 3 | **Lower reliability** — 7A test clips should be **20–30 s** default. |
| High **platform_compressed** label (future) | Scores may reflect WhatsApp/social codec; origin assessment less certain. |
| Mixed chunk scores (high std) | File may contain mixed segments or unstable channel; highlight timeline. |

**Never equate:** `FAKE` → “proved malicious” or `REAL` → “proved authentic recording.”

---

## 7. Limitations Section

**Always include** in every report (static + dynamic):

- AI/synthetic detection is **probabilistic**, not deterministic proof.
- Results depend on **recording quality**, length, language, and domain match to training data.
- **Compression, noise, replay, mixer, and platform processing** can shift scores.
- **Binary REAL** does not prove an **original unedited** recording.
- **Binary FAKE** does not prove **malicious intent** or a specific tool.
- Output supports **forensic review**; it does **not** replace expert acoustic or legal judgment.
- Model trained primarily on **English studio/broadcast** + ASVspoof; **Urdu/phone/social** may be unreliable until Phase 7C.

Optional dynamic lines:

- “Only {n_chunks_used} chunks met VAD criteria.”
- “Decision score {x} near threshold {y}.”

---

## 8. UI Wording

### Recommended labels

| Concept | UI label |
|---------|----------|
| Overall headline | **Final Decision** (with subtitle: origin + manipulation) |
| Spoof vote / pct_vote | **Spoof / Manipulation Score** |
| Threshold | **Operating Threshold** |
| Confidence | **Reliability** or **Confidence Note** |
| Origin layer | **Origin Assessment** |
| Manipulation layer | **Manipulation Risk** |
| Multiclass | **Auxiliary Attack Hint** |
| Narrative | **Forensic Interpretation** |
| Chunk list | **Segment Timeline** |

### Avoid

| Avoid | Why |
|-------|-----|
| “100% fake” / “100% real” | Scores are not certainties |
| “Proved fake” / “Proved authentic” | Legal/overclaim risk |
| “AI detected” when only channel/replay artifacts | Misleading |
| Showing only `FAKE`/`REAL` without manipulation context | Product direction mismatch |

---

## JSON report shape (future)

Top-level keys for API Phase 8:

```json
{
  "header": { },
  "verdict": { "origin_label", "manipulation_label", "risk_level", "final_verdict", "confidence_note" },
  "model_scores": { },
  "segment_timeline": [ ],
  "environmental_findings": { },
  "interpretation": { "rules_applied": [], "final_forensic_interpretation": "" },
  "limitations": [ ]
}
```

Interim Phase 7A may map Phase 6 JSON + manifest into a subset of these fields manually or via `analyze_forensic_test_results.py` (planned).

---

## Related

- `reports/FORENSIC_PRODUCT_ROADMAP.md`
- `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md`
- `reports/AUDIO_TESTING_OUTPUT_GUIDE.md`
