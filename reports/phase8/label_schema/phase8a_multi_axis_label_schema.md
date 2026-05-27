# Phase 8A — Multi-Axis Label Schema (Frozen)

**Status:** FROZEN for Phase 8A  
**Version:** 8A.1  
**Supersedes for implementation:** Use this document over draft [../PHASE8_MULTI_AXIS_LABEL_SCHEMA.md](../PHASE8_MULTI_AXIS_LABEL_SCHEMA.md) where they differ.

---

## 1. Design principles

1. Labels are **evidence axes**, not a single court verdict.  
2. **Origin** and **manipulation** are independent axes; both may be active.  
3. **`risk_positive`** (Phase 7 legacy) = elevated forensic concern — **≠** `ai_synthetic`, **≠** “fake”.  
4. Multiple manipulation labels may apply to one file (multi-label manipulation).  
5. Exactly **one** primary origin label per file/segment after calibration (or `unknown`).  
6. Decision labels are **fusion outputs**, not training targets alone.

---

## 2. Origin axis (required)

| Label | Code | Meaning |
|-------|------|---------|
| Human | `human` | Evidence supports naturally produced human speech as dominant origin |
| AI synthetic | `ai_synthetic` | Evidence supports AI/TTS/neural synthetic speech as dominant origin |
| Mixed | `mixed` | Materially different origin evidence across file or segments (e.g. partial fabrication) |
| Unknown | `unknown` | Insufficient or conflicting origin evidence — do not force AI or human |

**Scores (implementation):** Continuous scores `origin_human_score`, `origin_ai_score`, `origin_mixed_score`, `origin_unknown_score` in [0, 1] may coexist before argmax calibration; calibrated field is single-valued `calibrated_origin_label`.

---

## 3. Manipulation axis (required, multi-label allowed)

| Label | Code | Meaning |
|-------|------|---------|
| Clean | `clean` | No meaningful manipulation beyond benign capture |
| Replay / rerecorded | `replay_rerecorded` | Playback and re-capture pattern (human or AI content replayed) |
| Mixer / channel processed | `mixer_channel_processed` | Mixer, broadcast chain, or device/channel coloration |
| Partial fabrication | `partial_fabrication` | Localized synthetic insert, voice replacement, or inconsistent region |
| Edited / spliced | `edited_spliced` | Cuts, splices, or editorial discontinuities |
| Compressed / low quality | `compressed_low_quality` | Heavy compression or quality loss dominating cues |
| Unknown manipulation | `unknown_manipulation` | Manipulation suspected but not classifiable |

**Multi-label rule:** `clean` is **mutually exclusive** with all other manipulation labels. Non-clean labels may co-occur (e.g. `replay_rerecorded` + `mixer_channel_processed`).

**Storage:** `known_manipulation_labels` / `calibrated_manipulation_labels` as semicolon-separated ordered list in CSV, or JSON array in JSON.

---

## 4. Decision / fusion labels (required)

| Label | Code | Typical trigger (fusion — see fusion doc) |
|-------|------|---------------------------------------------|
| Accept human clean | `accept_human_clean` | Strong human origin + clean manipulation + low segment suspicion |
| Suspicious origin | `suspicious_origin` | AI or mixed origin evidence without mandatory manipulation alarm |
| Suspicious manipulation | `suspicious_manipulation` | Replay/mixer/partial/edit evidence; origin may be human |
| Suspicious mixed | `suspicious_mixed` | Mixed origin and/or partial fabrication with segment support |
| Inconclusive manual review | `inconclusive_manual_review` | Weak/conflicting evidence, quality-limited, or axis conflict |

**`manual_review_required`:** Boolean; must be `true` when `final_forensic_status` = `inconclusive_manual_review` or when fusion rules flag borderline cases.

---

## 5. Allowed multi-label combinations (examples)

These are **valid** forensic states — reports must support them explicitly.

| Origin | Manipulation label(s) | Interpretation (forensic-safe) |
|--------|----------------------|--------------------------------|
| `human` | `clean` | Clean human recording |
| `human` | `replay_rerecorded` | Human speech replayed and rerecorded — **not AI-generated** |
| `ai_synthetic` | `replay_rerecorded` | AI speech replayed through device — suspicious replay + AI origin |
| `human` | `mixer_channel_processed` | Human speech via mixer/channel — **not AI proof** |
| `ai_synthetic` | `mixer_channel_processed` | AI speech with broadcast/mixer processing |
| `mixed` | `partial_fabrication` | Localized synthetic/replaced region in broader human context |
| `unknown` | `compressed_low_quality` | Quality too poor for origin; manipulation unclear |
| `human` | `replay_rerecorded`; `mixer_channel_processed` | Human content with replay and channel processing |
| `ai_synthetic` | `partial_fabrication` | Dominant synthetic with localized stronger anomaly |
| `mixed` | `edited_spliced` | Edits create mixed-origin timeline |
| `unknown` | `unknown_manipulation` | Abstain on both axes |

---

## 6. Invalid assumptions (explicitly forbidden)

The following mappings are **architecturally invalid** and must not appear in fusion, training targets, or UI copy:

| Invalid assumption | Correct handling |
|--------------------|------------------|
| Replay evidence alone ⇒ AI-generated | Set `replay_rerecorded`; origin from origin axis only |
| Mixer/channel evidence alone ⇒ AI-generated | Set `mixer_channel_processed`; do not set `ai_synthetic` without origin evidence |
| Low quality alone ⇒ fake | Set `compressed_low_quality`; prefer `unknown` origin + manual review |
| `risk_positive` ⇒ fake / AI | Map to manipulation/risk features; separate origin calibration |
| High Hybrid score ⇒ `ai_synthetic` | Hybrid = manipulation evidence in Phase 8; not origin ground truth |
| Single spoof score ⇒ `final_forensic_status` | Multi-axis fusion required |
| File mean only for partial role | Segment axis required for `partial_fabrication` |

---

## 7. Segment-level label usage

Per window/segment:

- Same origin/manipulation **vocabulary** applies to calibrated segment labels when computed.  
- `suspicious_segment_flag` (bool) — window-level suspicion for fusion aggregation.  
- `segment_reason` (string) — short code: e.g. `high_replay`, `region_delta`, `origin_ai_local`, `quality_limited`.

Partial fabrication acceptance requires at least one suspicious segment inside annotated region when ground truth available (validation).

---

## 8. Phase 7 field compatibility

| Phase 7 field | Phase 8 use |
|---------------|-------------|
| `risk_target` | Training/eval forensic-risk — **not** origin label |
| `expected_risk_binary` | Legacy feature only |
| `baseline_status` / Hybrid scores | Manipulation evidence input |
| `aasist_status` | Archived optional feature — not product judge |
| 7C4-v2 outputs | Fusion prototype features |

---

## 9. Calibration vocabulary mapping (informative)

| Evidence pattern | Typical `calibrated_origin_label` | Typical `calibrated_manipulation_labels` |
|------------------|-----------------------------------|------------------------------------------|
| Clean human witness clip | `human` | `clean` |
| Human mic replay | `human` | `replay_rerecorded` |
| Full-file AI TTS | `ai_synthetic` | `clean` or `compressed_low_quality` |
| AI + mixer variant | `ai_synthetic` | `mixer_channel_processed` |
| Inserted AI segment in human file | `mixed` | `partial_fabrication` |
| Noisy phone recording, weak scores | `unknown` | `compressed_low_quality` or `unknown_manipulation` |

---

## 10. Schema freeze checklist

- [x] Origin labels: `human`, `ai_synthetic`, `mixed`, `unknown`  
- [x] Manipulation labels: all seven required types  
- [x] Decision labels: all five required types  
- [x] Multi-label combinations documented  
- [x] Invalid assumptions listed  

**Phase 8B:** NOT STARTED — builder must implement columns per [../evidence_table/phase8a_evidence_table_schema.md](../evidence_table/phase8a_evidence_table_schema.md).
