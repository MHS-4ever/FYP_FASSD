# Phase 7D — Decision-to-Report Mapping

Maps Phase 7C4-v2 `calibrated_status` (and fallbacks) to report fields.  
**Source of truth for status strings:** `code/phase7/apply_phase7c4_v2_decision_layer.py`

If `calibrated_risk_level` is present on the CSV row, use it as a hint but **override** with this table when they conflict.

---

## Legend

| Column | Meaning |
|--------|---------|
| `overall_risk_level` | `low` \| `medium` \| `high` \| `inconclusive` |
| `manual_review_required` | Boolean |
| `confidence_level` | Default; may downgrade on disagreement |

---

## Clean human family

### `clean_human_accepted`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `low` |
| `overall_status` | `no_strong_synthetic_or_manipulation_evidence` |
| `origin_hint` | `likely_human` |
| `manipulation_hint` | `no_strong_manipulation_evidence` |
| `manual_review_required` | `false` (org policy may still require review) |
| `confidence_level` | `medium` |
| **Executive wording** | No strong synthetic or manipulation evidence was detected under the current analysis settings. |

### `clean_human_borderline`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `inconclusive_manual_review_recommended` |
| `origin_hint` | `likely_human_or_uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |
| **Executive wording** | The file contains conflicting evidence. Some model outputs suggest low risk, while segment-level indicators require manual review. |

### `clean_human_false_alarm`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `suspicious_but_possible_clean_human_false_alarm` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |
| **Executive wording** | The system flagged suspicious evidence, but this category has known false-alarm risk on clean human speech. Manual review is required. |

---

## Direct AI family

### `direct_ai_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `ai_synthetic_speech_indicators_detected` |
| `origin_hint` | `likely_ai_generated` |
| `manipulation_hint` | `synthetic_generation_indicators` |
| `manual_review_required` | `true` |
| `confidence_level` | `high` |
| **Executive wording** | The system detected indicators consistent with AI-generated or synthetic speech at the file level. Manual review is required. |

### `direct_ai_file_level_missed_but_segment_suspicious`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `segment_level_ai_suspicion` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `synthetic_segment_indicators` |
| `manual_review_required` | `true` |
| `confidence_level` | `medium` |
| **Executive wording** | File-level pooled scores did not reach the detection threshold, but segment-level evidence indicates possible synthetic speech in one or more regions. |

### `direct_ai_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `evaluation_mismatch_or_weak_ai_evidence` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |
| **Executive wording** | Under current settings, strong AI indicators were not assigned; internal evaluation flags a possible miss. Expert review recommended if ground context expects synthetic speech. |
| **Note** | Internal/QA emphasis; do not tell end user “ground truth says AI”. |

---

## Human replay family

### `human_replay_manipulation_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` (use `high` if `suspicious_chunk_ratio` ≥ 0.5) |
| `overall_status` | `replay_or_rerecording_indicators_detected` |
| `origin_hint` | `likely_human` |
| `manipulation_hint` | `replayed_or_rerecorded` |
| `manual_review_required` | `true` |
| `confidence_level` | `medium` |
| **Executive wording** | Speech content appears consistent with human origin, with indicators of replay or re-recording. This does not by itself indicate AI synthesis. |

### `human_replay_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `replay_evidence_weak_or_missed` |
| `origin_hint` | `likely_human_or_uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |

---

## AI replay family

### `ai_replay_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `ai_replay_or_processed_speech_indicators_detected` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `replayed_or_rerecorded` |
| `manual_review_required` | `true` |
| `confidence_level` | `high` |
| **Executive wording** | Indicators suggest AI-related speech content combined with replay or re-recording / channel effects. Manual review is required. |

### `ai_replay_file_level_missed_but_segment_suspicious`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `segment_level_ai_replay_suspicion` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `replayed_or_rerecorded` |
| `manual_review_required` | `true` |
| `confidence_level` | `medium` |

### `ai_replay_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `ai_replay_evidence_weak_or_missed` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |

---

## Mixer family

### `human_mixer_manipulation_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` (→ `high` if extreme channel scores) |
| `overall_status` | `channel_processing_or_mixer_artifacts_detected` |
| `origin_hint` | `likely_human` |
| `manipulation_hint` | `channel_processed` |
| `manual_review_required` | `true` |
| `confidence_level` | `medium` |

### `human_mixer_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `mixer_evidence_weak_or_missed` |
| `origin_hint` | `likely_human_or_uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |

### `ai_mixer_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `ai_speech_with_channel_processing_indicators` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `channel_processed` |
| `manual_review_required` | `true` |
| `confidence_level` | `high` |

### `ai_mixer_file_level_missed_but_segment_suspicious`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `segment_level_ai_mixer_suspicion` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `channel_processed` |
| `manual_review_required` | `true` |
| `confidence_level` | `medium` |

### `ai_mixer_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `ai_mixer_evidence_weak_or_missed` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |

---

## Partial fabrication family

### `partial_fabrication_detected`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `high` |
| `overall_status` | `partial_fabrication_or_splice_indicators_detected` |
| `origin_hint` | `mixed_or_uncertain` |
| `manipulation_hint` | `edited_or_partially_synthetic` |
| `manual_review_required` | `true` |
| `confidence_level` | `high` |
| **Executive wording** | Segment-level evidence suggests possible partial fabrication or inserted content. Review flagged time ranges. |
| **Segments** | Must include labeled window + high inside-region chunks when data available. |

### `partial_fabrication_missed`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `medium` |
| `overall_status` | `no_strong_partial_fabrication_evidence_but_limitations_apply` |
| `origin_hint` | `mixed_or_uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |
| **Executive wording** | Strong partial-fabrication indicators were not detected under current settings; limitations apply if editing is suspected from external context. |

### `partial_fabrication_not_evaluable`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `inconclusive` |
| `overall_status` | `partial_fabrication_not_evaluable_missing_timestamps` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |
| **Executive wording** | Partial-fabrication region evaluation requires valid suspicious start/end times; manual review is required. |

---

## Fallback statuses

### `borderline_needs_review` / `unknown_review_required`

| Field | Value |
|-------|-------|
| `overall_risk_level` | `inconclusive` |
| `overall_status` | `inconclusive_manual_review_recommended` |
| `origin_hint` | `uncertain` |
| `manipulation_hint` | `uncertain` |
| `manual_review_required` | `true` |
| `confidence_level` | `low` |

---

## `attack_hint` derivation (auxiliary)

Derive from baseline multiclass when available:

| Condition | `attack_hint` |
|-----------|---------------|
| Top class bonafide + low spoof | `bonafide` |
| Top synthesis | `synthesis` |
| Top conversion | `voice_conversion` |
| Top replay | `replay` |
| Else | `unknown` |

Never present `attack_hint` as the sole forensic conclusion.

---

## `recommended_action` defaults

| `overall_risk_level` | Default action |
|----------------------|----------------|
| `low` | Optional routine review per policy; retain original file and metadata. |
| `medium` | Manual listen; compare segment timeline; do not use as sole accusatory evidence. |
| `high` | Priority manual review; document chain of custody; consider independent expert. |
| `inconclusive` | Do not automate decision; obtain missing metadata or re-analyze with valid partial timestamps. |

---

## Origin hint refinement by `source_origin`

When `manipulation_type` implies AI origin but status is replay/mixer:

- Keep `origin_hint` from table; add sentence in `technical_summary` if `source_origin=ai` vs `human` differs from acoustic hint.

---

## Error-case overlay

If `sample_id` ∈ `phase7c4_v2_error_cases.csv`:

- Set `is_error_case=true`  
- Append limitation: “This file was flagged in the Phase 7C4-v2 internal error-case set; treat conclusions with extra caution.”  
- Do **not** change `calibrated_status` in the report.  
