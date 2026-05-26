# Phase 7E0 — AASIST Label Strategy

**Status:** Locked for Phase 7E training adapters (7E2+)  
**Task type:** Binary **forensic-risk / spoof evidence** — not full forensic taxonomy

---

## 1. Principle

AASIST’s initial head predicts **low risk (0)** vs **suspicious / spoof-risk (1)**. This is **evidence for the decision layer**, not a final statement of:

- “AI-generated speech” vs “human speech” (origin), or  
- “authentic recording” vs “tampered evidence” (integrity).

Human replay and human mixer are **human-origin** but **forensic-risk positive** for training and thresholding.

---

## 1.1 Critical warning — `risk_target=1` is not “AI-generated”

| Field | Meaning |
|-------|---------|
| `risk_target` (or `label`) **1** | **Forensic-risk positive** — suspicious for spoof/manipulation/replay/channel/partial evidence |
| `risk_target` **0** | Low-risk clean / bonafide for this evidence head |

**`risk_target=1` does NOT mean the clip is AI-generated.** It means the model should treat the sample as **forensic-risk positive** for this binary evidence branch.

### Examples (training label vs report wording)

| Category | `risk_target` | Origin wording (decision/report) | Manipulation / other wording |
|----------|---------------|----------------------------------|------------------------------|
| **human_replay** | **1** | `human_likely` | replay / re-recording evidence — **not** “AI-generated” |
| **human_mixer** | **1** | `human_likely` | `channel_processed` — **not** “deepfake” |
| **direct_ai** | **1** | `ai_suspicious` / `likely_ai` (evidence only) | synthesis / spoof-like evidence |
| **partial_fabrication** (suspicious region) | **1** for region/window | `mixed_or_partial_ai` or `uncertain` | edited / spliced / partial-fab risk |

### Do not repeat the Phase 7C3-v1 mistake

Phase 7C3-v1 trained the binary head as if it were **complete origin truth**. That improved clean-human behavior but **destroyed** replay/mixer/partial detection.

**For AASIST:** the binary head is **forensic-risk / spoof evidence** only. **Origin** and **manipulation** labels are assigned in the **decision layer** and report layer using category metadata and fusion — not by equating `risk_target=1` with “fake human speech.”

---

## 2. Binary target

| Label | Meaning |
|-------|---------|
| **0** | Low-risk clean / bonafide speech |
| **1** | Synthetic, spoof, replay, mixer, partial suspicious, or other forensic-risk-positive speech |

---

## 3. Mapping — old balanced / ASVspoof-derived data

| Source label / attack | Training label | Notes |
|----------------------|----------------|-------|
| Bonafide | **0** | |
| Synthesis | **1** | |
| Voice conversion | **1** | |
| Replay | **1** | Replay is risk-positive for evidence head |

---

## 4. Mapping — Phase 7C1 local forensic dataset

| 7C1 category | Training label | Forensic wording (reports / decision layer) |
|--------------|----------------|-----------------------------------------------|
| Human clean | **0** | Low risk; may still be borderline at inference |
| Direct AI | **1** | Synthetic / direct-AI evidence |
| Human replay | **1** | **Not** “AI-generated” — map to replay / re-recording evidence |
| AI replay | **1** | AI-origin + replay chain evidence |
| Human mixer | **1** | **Not** “AI-generated” — map to channel / processing evidence |
| AI mixer | **1** | AI-origin + channel processing evidence |
| Partial fabrication (suspicious region) | **1** | Partial insertion / splice-risk evidence; use region metadata in adapter |

---

## 5. What labels are excluded from AASIST training

| Data | Rule |
|------|------|
| Phase 7A T1–T5 holdout | **Never** in train/val — eval only |
| Phase 7C4-v2 `final_status` / decisions | **Not** training labels — comparison only |
| Multiclass origin-only head (7C3 mistake) | **Do not** train AASIST as pure origin classifier |

---

## 6. Adapter requirements (7E2 preview)

The dataset adapter must emit at minimum:

- `audio_path` (resolved)
- `label` ∈ {0, 1}
- `source_dataset` ∈ {old, phase7c1}
- `forensic_category` (original 7C1 category for analysis joins)
- `split` ∈ {train, val, test}
- `use_for_training` (boolean; false for holdout rows)

For partial fabrication:

- `suspicious_start_time`, `suspicious_end_time` when present
- Training windows centered on suspicious region (mirror 7C3-R2 policy)

---

## 7. Decision-layer mapping (post-inference, not training labels)

When AASIST score is high on human replay or human mixer:

| Evidence | `origin_hint` (example) | `manipulation_hint` (example) |
|----------|-------------------------|-------------------------------|
| Human replay | human_likely | replayed_or_re_recorded |
| Human mixer | human_likely | channel_processed |
| Direct AI | ai_likely | synthesis / spoof-like |
| Partial fab | mixed_or_partial_ai or uncertain | edited_or_spliced |

Exact report fields remain Phase 7D spec; **7D implementation is postponed** until evidence improves.

---

## 8. Common mistakes to avoid

| Mistake | Correct approach |
|---------|------------------|
| Label human replay as 0 because “human” | Label **1** for risk head; separate origin in fusion |
| Describe human mixer detections as “deepfake” | Channel / manipulation risk language |
| Train on 7A to improve holdout numbers | Invalid run |
| Use 7C4-v2 accept/borderline as softmax targets | Use only for benchmark comparison |
| Treat high `risk_target` as “AI-generated” in UI/reports | Use category + fusion for origin; risk score is evidence only |
| Repeat 7C3-v1 “binary = origin” training | Risk head only; origin from metadata + 7E5 rules |

---

## 9. Related

- [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md)  
- [phase7c1_labeling_guide.md](../phase7c1_collection/phase7c1_labeling_guide.md)  
- [PHASE7_LABEL_SCHEMA.md](../PHASE7_LABEL_SCHEMA.md)
