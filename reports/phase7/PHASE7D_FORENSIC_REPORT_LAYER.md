# Phase 7D — Forensic Report Layer (Legacy Overview)

> **Canonical Phase 7D planning (May 2026):** [phase7d_report_layer/README.md](phase7d_report_layer/README.md)  
> Master plan: [phase7d_report_layer/PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md](phase7d_report_layer/PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md)

**Status:** Planning complete — **7D1** implementation (`build_phase7d_forensic_report.py`) not started  
**Priority:** **Mandatory** (not optional)  
**Training:** None (rules and mapping first)  
**Upstream:** Phase 7C4-v2 decision-layer prototype (frozen)

---

## 1. Goal

Convert raw model scores (Phase 6, later 7C/7F) into a **product-level forensic report**: structured JSON, safe wording, segment timeline, risk levels, and limitations.

The product is a **forensic report tool**, not only a classifier.

---

## 2. Why this phase exists

Stakeholders cannot use REAL/FAKE or raw attack types in court-facing or investigative workflows. A dedicated layer:

- Separates **origin** from **manipulation**  
- Builds **suspicious_timeline** from chunk scores  
- Applies **Cases A–K** wording (no over-claim)  
- Always lists **limitations**  

Detail also in [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md).

---

## 3. Inputs

| Input | Source |
|-------|--------|
| Phase 6 JSON | `prediction`, `decision_score`, `attack_probs`, chunk stats |
| Environmental aggregates | `env_features`, `env_reasons` |
| VAD / pooling metadata | `spec_reasons`, `n_chunks_used` |
| Chunk scores (per time) | Future export or computed from chunking schedule |
| Optional 7C/7F scores | Fine-tuned hybrid, AASIST, WavLM, wav2vec |
| 7A failure patterns | Threshold and rule tuning |

---

## 4. Outputs

| Output | Description |
|--------|-------------|
| Forensic report JSON | Schema below |
| `suspicious_timeline` | `{start_time, end_time, reason, score}` entries |
| `final_forensic_interpretation` | Safe narrative paragraph(s) |
| UI-ready fields | `origin_label`, `manipulation_label`, `risk_level` |
| Future PDF/HTML | Phase 8 export from same JSON |

### Core report fields

| Field | Type |
|-------|------|
| `file_name`, `duration`, `sample_rate`, `model_checkpoint` | Metadata |
| `origin_label` | human_likely \| ai_likely \| mixed_or_partial_ai \| uncertain |
| `manipulation_label` | See [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md) |
| `attack_hint` | bonafide \| synthesis \| voice_conversion \| replay \| unknown |
| `risk_level` | low \| medium \| high \| inconclusive |
| `final_verdict` | Short UI headline |
| `confidence_note` | Reliability explanation |
| `model_scores` | Raw/detector scores (nested) |
| `suspicious_timeline` | Array of segments |
| `environmental_findings` | Features + interpretations |
| `forensic_interpretation` | Main narrative |
| `limitations` | Always non-empty array |
| `recommended_next_step` | e.g. manual review |

### Risk mapping (summary)

Combine `origin_label`, `manipulation_label`, chunk timeline, and score distance to threshold → `risk_level`. Examples:

- human_likely + clean_original + low spoof chunks → **low**  
- human_likely + replayed_or_re_recorded → **medium** (not “fake”)  
- mixed_or_partial_ai + edited_or_spliced → **high**  
- heavy VAD drop or near threshold → **inconclusive**  

### Wording rules

**Use:** likely, suggests, indicates, may indicate, consistent with  
**Avoid:** proves, confirms, legally fake, court-ready without review  

### Case H — partial fake inserted

> The recording is **mostly human-like** overall, but **one or more suspicious segments** were detected. These may indicate **partial fabrication**, inserted synthetic speech, or splicing.

Apply when `partial_region_detected` is true even if whole-file `prediction` is REAL (e.g. T5_FAB_001, 14–21 s).

---

## 5. Tasks

1. Finalize JSON schema (align with `FORENSIC_REPORT_OUTPUT_SPEC.md`).  
2. Implement mapping: Phase 6 JSON → report object.  
3. Build **suspicious_timeline** from chunk scores + overlap rules.  
4. Implement Cases A–K templates.  
5. Wire partial-fabrication logic ([PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md)).  
6. Validate on 7A manifest (expected vs derived labels).  
7. Plan API/UI field names for Phase 8.  

---

## 6. Success criteria

- [ ] Every 7A file produces a valid report JSON.  
- [ ] No report states “proven fake” from binary score alone.  
- [ ] Partial-fabrication cases produce timeline + Case H when rules fire.  
- [ ] `limitations` always populated.  
- [ ] Reviewer sign-off on wording.  

---

## 7. What not to do in this phase

- Retrain models (7C / 7E)  
- Replace detector with report-only heuristics without model scores  
- Skip timeline for long or partial-fabrication files  

---

## 8. Connection to next phase

| Phase | Relationship |
|-------|----------------|
| **7E** | Additional `model_scores` entries if transformers added |
| **7F** | Final fusion feeds same report builder |
| **8** | API, UI, PDF/HTML consume 7D JSON |

Legacy detailed spec: [../pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md](../pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md) (reference).
