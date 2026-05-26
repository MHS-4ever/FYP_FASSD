# Phase 7D — Report Output Schema

**Version:** `report_version` = `7d.1.0` (planning)  
**Consumer:** JSON API, Markdown renderer, future PDF/UI  
**Producer (planned):** `code/phase7/build_phase7d_forensic_report.py`

All string enums are lowercase snake_case unless noted. Times are seconds (float) from start of file.

---

## 1. Top-level metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_id` | string | yes | UUID or `{sample_id}_{analysis_timestamp}` |
| `report_version` | string | yes | Schema version, e.g. `7d.1.0` |
| `project_name` | string | yes | `FASSD` |
| `analysis_timestamp` | string | yes | ISO 8601 UTC |
| `input_audio_path` | string | yes | Path or URI analyzed |
| `audio_filename` | string | yes | Basename |
| `audio_duration_s` | number | yes | Duration in seconds |
| `sample_rate_hz` | integer | no | From metadata or decode |
| `channels` | integer | no | 1 = mono |
| `analysis_profile` | string | yes | e.g. `pct_vote_0.65_0.70_vad40` |
| `decision_layer_version` | string | yes | `phase7c4_v2` |

---

## 2. Main interpretation

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overall_risk_level` | enum | yes | `low` \| `medium` \| `high` \| `inconclusive` |
| `overall_status` | enum | yes | Machine status code (see mapping doc) |
| `origin_hint` | enum | yes | `likely_human` \| `likely_ai_generated` \| `ai_suspicious` \| `mixed_or_uncertain` \| `likely_human_or_uncertain` \| `uncertain` |
| `manipulation_hint` | enum | yes | See §2.1 |
| `attack_hint` | enum | no | `bonafide` \| `synthesis` \| `voice_conversion` \| `replay` \| `unknown` |
| `manual_review_required` | boolean | yes | Reviewer must inspect |
| `confidence_level` | enum | yes | `low` \| `medium` \| `high` — reflects **evidence strength**, not legal certainty |
| `confidence_explanation` | string | yes | Why confidence is limited |

### 2.1 `manipulation_hint` values

| Value | Meaning |
|-------|---------|
| `no_strong_manipulation_evidence` | No strong replay/channel/edit signals under current settings |
| `synthetic_generation_indicators` | Indicators consistent with synthetic speech |
| `synthetic_segment_indicators` | Segment-level synthetic suspicion |
| `replayed_or_rerecorded` | Replay / second-hop recording indicators |
| `channel_processed` | Mixer / EQ / chain processing indicators |
| `edited_or_partially_synthetic` | Partial fabrication / splice indicators |
| `uncertain` | Conflicting or weak manipulation evidence |

---

## 3. Evidence blocks

### 3.1 `file_level_evidence` (object)

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | One paragraph, cautious wording |
| `baseline_prediction` | string | `REAL` / `FAKE` |
| `baseline_decision_score` | number | Pooled vote / score |
| `r2_product_decision_score` | number | nullable |
| `r2_loss_decision_score` | number | nullable |
| `selected_evidence_source` | string | From v2 `selected_model_evidence` |
| `calibrated_status` | string | Raw 7C4-v2 status (traceability) |

### 3.2 `chunk_level_evidence` (object)

| Field | Type | Description |
|-------|------|-------------|
| `n_chunks_used` | integer | After VAD |
| `n_chunks_total` | integer | Before VAD |
| `suspicious_chunk_ratio` | number | Fraction above chunk threshold |
| `max_chunk_spoof_baseline` | number | |
| `max_chunk_spoof_r2_product` | number | nullable |
| `max_chunk_spoof_r2_loss` | number | nullable |
| `high_spoof_chunk_count` | integer | Optional |

### 3.3 `segment_level_evidence` (object)

| Field | Type | Description |
|-------|------|-------------|
| `labeled_suspicious_start_s` | number | nullable — from manifest |
| `labeled_suspicious_end_s` | number | nullable |
| `partial_inside_max_spoof` | number | nullable |
| `partial_outside_max_spoof` | number | nullable |
| `partial_region_delta` | number | nullable |
| `partial_region_detected` | boolean | nullable |

### 3.4 `model_agreement` / `model_disagreement` (objects)

| Field | Type | Description |
|-------|------|-------------|
| `agreement_summary` | string | Plain language |
| `baseline_status` | string | From baseline CSV |
| `r2_product_status` | string | nullable |
| `r2_loss_status` | string | nullable |
| `disagreement_flags` | string[] | e.g. `baseline_high_r2_low_clean_human` |

### 3.5 `selected_model_evidence` (string)

Copy of v2 field explaining which checkpoint drove the decision branch.

---

## 4. `suspicious_segments` (array)

Each element:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_time` | number | yes | Seconds |
| `end_time` | number | yes | Seconds |
| `segment_type` | enum | yes | `high_spoof_chunk` \| `labeled_partial_region` \| `attack_hint_spike` \| `env_anomaly` |
| `evidence_score` | number | yes | e.g. max spoof prob in window |
| `evidence_source` | string | yes | `baseline` \| `r2_product` \| `r2_loss` \| `fused` |
| `explanation` | string | yes | Cautious one-liner |
| `review_priority` | enum | yes | `low` \| `medium` \| `high` |

**Selection rules (7D1):**

1. Include labeled partial region if timestamps valid.  
2. Include top-N chunks by spoof score (default N=5) above chunk threshold.  
3. De-duplicate overlapping windows.  

---

## 5. Forensic narrative

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `executive_summary` | string | yes | 2–4 sentences, non-technical lead |
| `technical_summary` | string | yes | Model/evidence detail |
| `evidence_summary` | string | yes | From v2 or expanded |
| `recommended_action` | string | yes | e.g. manual review, re-record, expert listen |
| `limitations` | string[] | yes | Bullet list |
| `disclaimer` | string | yes | Full disclaimer paragraph |

---

## 6. Internal traceability (required for audit)

| Field | Type | Description |
|-------|------|-------------|
| `phase7c4_status` | string | Same as `calibrated_status` |
| `baseline_status` | string | Baseline CSV `baseline_status` |
| `r2_product_status` | string | nullable |
| `r2_loss_status` | string | nullable |
| `baseline_decision_score` | number | |
| `r2_product_decision_score` | number | nullable |
| `r2_loss_decision_score` | number | nullable |
| `baseline_max_chunk_spoof` | number | |
| `r2_product_max_chunk_spoof` | number | nullable |
| `r2_loss_max_chunk_spoof` | number | nullable |
| `suspicious_chunk_ratio` | number | |
| `partial_region_delta` | number | nullable |
| `partial_inside_max_spoof` | number | nullable |
| `is_error_case` | boolean | Present in v2 error CSV |
| `manipulation_type` | string | From manifest/CSV |
| `source_origin` | string | `human` / `ai` |

---

## 7. Optional extensions (7D2+)

| Field | Type | When |
|-------|------|------|
| `environmental_findings` | object | If env features exported per file |
| `phase7a_holdout_flag` | boolean | 7A evaluation runs |
| `report_locale` | string | Future i18n |

---

## 8. Compatibility with legacy spec

[FORENSIC_REPORT_OUTPUT_SPEC.md](../../FORENSIC_REPORT_OUTPUT_SPEC.md) uses `origin_label` / `manipulation_label`. Phase 7D uses `origin_hint` / `manipulation_hint` in JSON; 7D1 may emit **both** during transition:

| 7D field | Legacy alias |
|----------|--------------|
| `origin_hint` | `origin_label` (mapped) |
| `manipulation_hint` | `manipulation_label` (mapped) |
| `overall_risk_level` | `risk_level` |

Mapping table in builder config, not duplicated here.

---

## 9. Validation rules

1. `disclaimer` must contain “decision-support” and “not … sole basis” language.  
2. If `overall_risk_level` is `high`, `manual_review_required` must be `true`.  
3. If `calibrated_status` contains `segment_suspicious`, `suspicious_segments` must be non-empty OR `confidence_explanation` must state why empty.  
4. Forbidden substrings in narrative fields: see [PHASE7D_REPORT_WORDING_GUIDE.md](PHASE7D_REPORT_WORDING_GUIDE.md).  
