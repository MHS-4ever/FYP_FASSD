# FASSD Forensic Analysis Report

**Report ID:** `{{report_id}}`  
**Report version:** `{{report_version}}`  
**Analysis time:** `{{analysis_timestamp}}`  
**Decision layer:** `{{decision_layer_version}}`

---

## 1. Report Header

| Field | Value |
|-------|-------|
| Project | {{project_name}} |
| Audio file | `{{audio_filename}}` |
| Path | `{{input_audio_path}}` |
| Duration | {{audio_duration_s}} s |
| Sample rate | {{sample_rate_hz}} Hz |
| Channels | {{channels}} |
| Analysis profile | {{analysis_profile}} |

---

## 2. Audio Metadata

{{audio_metadata_notes}}

---

## 3. Executive Summary

{{executive_summary}}

---

## 4. Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | **{{overall_risk_level}}** |
| Overall status | `{{overall_status}}` |
| Manual review required | **{{manual_review_required}}** |
| Confidence | {{confidence_level}} — {{confidence_explanation}} |

---

## 5. Origin and Manipulation Hints

| Hint | Value |
|------|-------|
| Origin hint | {{origin_hint}} |
| Manipulation hint | {{manipulation_hint}} |
| Attack hint (auxiliary) | {{attack_hint}} |

**Interpretation:** Origin and manipulation are reported separately. A human-origin assessment does not imply an unmodified original recording.

---

## 6. Evidence Table

### File-level

{{file_level_evidence_summary}}

| Metric | Baseline | R2 product | R2 loss |
|--------|----------|------------|---------|
| Decision score | {{baseline_decision_score}} | {{r2_product_decision_score}} | {{r2_loss_decision_score}} |
| Status | {{baseline_status}} | {{r2_product_status}} | {{r2_loss_status}} |
| Phase 7C4-v2 status | **{{phase7c4_status}}** | | |
| Selected evidence | {{selected_model_evidence}} | | |

### Chunk-level

| Metric | Value |
|--------|-------|
| Chunks used / total | {{n_chunks_used}} / {{n_chunks_total}} |
| Suspicious chunk ratio | {{suspicious_chunk_ratio}} |
| Max chunk spoof (baseline) | {{baseline_max_chunk_spoof}} |
| Max chunk spoof (R2 product) | {{r2_product_max_chunk_spoof}} |
| Max chunk spoof (R2 loss) | {{r2_loss_max_chunk_spoof}} |

### Segment-level (partial fabrication)

| Field | Value |
|-------|-------|
| Labeled region | {{labeled_suspicious_start_s}} – {{labeled_suspicious_end_s}} s |
| Inside-region max spoof | {{partial_inside_max_spoof}} |
| Outside-region max spoof | {{partial_outside_max_spoof}} |
| Region delta | {{partial_region_delta}} |
| Partial region detected | {{partial_region_detected}} |

---

## 7. Suspicious Segment Analysis

{{#if suspicious_segments}}
| Start (s) | End (s) | Type | Score | Source | Priority | Explanation |
|-----------|---------|------|-------|--------|----------|-------------|
{{#each suspicious_segments}}
| {{start_time}} | {{end_time}} | {{segment_type}} | {{evidence_score}} | {{evidence_source}} | {{review_priority}} | {{explanation}} |
{{/each}}
{{else}}
No suspicious segments were listed above the reporting threshold for this file. Manual review may still be required based on file-level status.
{{/if}}

---

## 8. Model Agreement / Disagreement

{{model_agreement_summary}}

**Disagreement flags:** {{disagreement_flags}}

---

## 9. Recommended Human Review Actions

{{recommended_action}}

---

## 10. Limitations

{{#each limitations}}
- {{this}}
{{/each}}

---

## 11. Disclaimer

{{disclaimer}}

---

## Appendix — Technical Traceability

| Field | Value |
|-------|-------|
| manipulation_type | {{manipulation_type}} |
| source_origin | {{source_origin}} |
| is_error_case | {{is_error_case}} |

*Internal traceability for audit; not a user verdict.*
