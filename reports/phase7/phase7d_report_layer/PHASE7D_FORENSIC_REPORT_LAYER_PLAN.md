# Phase 7D — Forensic Report Layer Plan

**Version:** 1.0 (planning)  
**Status:** Specification — implement in Phase **7D1**  
**Upstream:** Phase 7C4-v2 (accepted decision-layer prototype only)  
**Training:** None

---

## 1. Purpose

Phase 7D defines how FASSD presents forensic analysis results to human reviewers. It does **not** replace the detector or the 7C4-v2 decision layer. It **translates** calibrated decisions and supporting evidence into:

1. **Machine-readable JSON** — API-ready, traceable, versioned  
2. **Human-readable Markdown** — review workflow, thesis/demo, audit trail  
3. **Later:** PDF export (Phase 8+)  
4. **Later:** Web UI report view (Phase 8+)

The report layer must use **cautious forensic language** suitable for decision support, not automated legal verdicts.

---

## 2. Problem statement

Phase 7C showed that:

- A single checkpoint cannot serve as the final product.  
- Phase 7C4-v2 meets controlled Phase 7C1 targets by **fusing** baseline + R2 evidence with borderline / manual-review states.  
- Even on 7C1, only **1/23** clean-human clips are auto-accepted; **15/23** are borderline; **7/23** remain false-alarm category.  

Raw `calibrated_status` values and internal scores are not suitable for end users. Reviewers need:

- Clear **risk level** and **recommended action**  
- Separated **origin** vs **manipulation** hints  
- **Segment-level** explanations where file-level scores conflict  
- Explicit **limitations** and **manual review** flags  
- Traceability to underlying model evidence  

---

## 3. Scope

### In scope (7D planning + 7D1 implementation)

| Area | Deliverable |
|------|-------------|
| Report schema | `PHASE7D_REPORT_OUTPUT_SCHEMA.md`, `PHASE7D_JSON_SCHEMA_EXAMPLE.json` |
| Wording | `PHASE7D_REPORT_WORDING_GUIDE.md` |
| Status mapping | `PHASE7D_DECISION_TO_REPORT_MAPPING.md` |
| Limitations | `PHASE7D_REPORT_LIMITATIONS_AND_DISCLAIMERS.md` |
| Templates | `PHASE7D_MARKDOWN_REPORT_TEMPLATE.md` |
| QA expectations | `PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md` |
| Examples | `examples/*.md` |
| Builder script (7D1) | `code/phase7/build_phase7d_forensic_report.py` |

### Out of scope

- Training, fine-tuning, architecture changes  
- Modifying 7C4-v2 decision logic (unless a separate calibration phase is approved)  
- PDF engine, web frontend, authentication, billing  
- Claiming market-ready or court-ready accuracy  

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Audio file + metadata                                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 6 / 7C1 inference (frozen) — evidence only            │
│  baseline + R2 product/loss CSVs, chunk timelines, partial   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 7C4-v2 decision layer (frozen)                        │
│  phase7c4_v2_candidate_decisions.csv                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 7D report builder (7D1)                               │
│  mapping + wording + evidence assembly + limitations         │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     forensic_report.json          forensic_report.md
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    (later) PDF / Web UI
```

**Design principle:** The report layer is **deterministic** given fixed inputs and `report_version`. No new ML in 7D.

---

## 5. Inputs and join keys

| Source | Join key | Use in report |
|--------|----------|---------------|
| `phase7c4_v2_candidate_decisions.csv` | `sample_id` | Primary: `calibrated_status`, hints, scores, `evidence_summary` |
| `phase7c4_v2_error_cases.csv` | `sample_id` | Flag evaluation mismatches; strengthen limitations |
| `phase7c1_baseline_results.csv` | `sample_id` | `baseline_status`, file-level prediction, chunk stats |
| R2 product/loss CSVs | `sample_id` | Model agreement/disagreement, traceability |
| `phase7c1_partial_fabrication_analysis.csv` | `sample_id` | Inside/outside region metrics, `partial_region_delta` |
| Chunk timeline CSV/JSON | `sample_id` | `suspicious_segments[]` |
| Manifest (optional) | `sample_id` | `input_audio_path`, duration, ground-truth metadata (internal QA only) |

---

## 6. Output types

### 6.1 JSON report

- One file per analyzed audio: `{sample_id}_forensic_report.json`  
- Schema: [PHASE7D_REPORT_OUTPUT_SCHEMA.md](PHASE7D_REPORT_OUTPUT_SCHEMA.md)  
- Example: [PHASE7D_JSON_SCHEMA_EXAMPLE.json](PHASE7D_JSON_SCHEMA_EXAMPLE.json)  

### 6.2 Markdown report

- Rendered from template: [PHASE7D_MARKDOWN_REPORT_TEMPLATE.md](PHASE7D_MARKDOWN_REPORT_TEMPLATE.md)  
- Same semantic content as JSON; optimized for human reading  

### 6.3 Future PDF / UI

- Consume the **same JSON**; no parallel business logic in the UI layer  
- PDF styling in Phase 8+; not part of 7D planning implementation  

---

## 7. Report sections (human-readable)

1. Report Header  
2. Audio Metadata  
3. Executive Summary  
4. Final Risk Assessment  
5. Origin and Manipulation Hints  
6. Evidence Table  
7. Suspicious Segment Analysis  
8. Model Agreement / Disagreement  
9. Recommended Human Review Actions  
10. Limitations  
11. Technical Traceability Appendix  

Section order is fixed in the template to support consistent reviewer training.

---

## 8. Core logic modules (7D1)

| Module | Responsibility |
|--------|----------------|
| `load_decision_row` | Read v2 CSV row + optional error-case flag |
| `map_status_to_report` | Apply [PHASE7D_DECISION_TO_REPORT_MAPPING.md](PHASE7D_DECISION_TO_REPORT_MAPPING.md) |
| `build_evidence_blocks` | File / chunk / segment evidence from merged CSVs |
| `build_suspicious_segments` | Top chunks + partial region + labeled suspicious window |
| `compute_model_agreement` | Compare baseline vs R2 product vs R2 loss statuses/scores |
| `render_wording` | Template strings from [PHASE7D_REPORT_WORDING_GUIDE.md](PHASE7D_REPORT_WORDING_GUIDE.md) |
| `attach_limitations` | Standard + status-specific blocks |
| `write_json` / `write_markdown` | Serializers |

---

## 9. Risk and review policy

| `overall_risk_level` | Typical `manual_review_required` | Notes |
|----------------------|----------------------------------|-------|
| `low` | `false` (policy may still require review) | Rare on 7C1 for clean human (only 1/23 accepted) |
| `medium` | `true` | Borderline, false-alarm-prone categories, missed partial |
| `high` | `true` | AI, replay, mixer, partial fabrication indicators |
| `inconclusive` | `true` | Missing timestamps, errors, unknown status |

**Product policy default:** `manual_review_required=true` for all `medium` and `high` risk unless organizational policy explicitly waives low-stakes screening.

---

## 10. Phased delivery

| Sub-phase | Goal | Status |
|-----------|------|--------|
| **7D0** | Planning docs (this folder) | **Current** |
| **7D1** | `build_phase7d_forensic_report.py` — JSON + MD for 7C1 manifest | Planned |
| **7D2** | Phase 7A holdout reports + holdout-specific limitation text | Planned |
| **7D3** | Batch CLI, report index CSV, diff vs ground truth (internal) | Planned |
| **7D4** | API contract stub for Phase 8 | Planned |

---

## 11. Success criteria (7D1)

- [ ] Every row in `phase7c4_v2_candidate_decisions.csv` produces valid JSON + MD.  
- [ ] No report uses forbidden absolute claims (see wording guide).  
- [ ] `limitations` and `disclaimer` are always non-empty.  
- [ ] `manual_review_required` aligns with mapping table.  
- [ ] Partial-fabrication cases include `suspicious_segments` when timestamps exist.  
- [ ] Segment-suspicious AI cases explain file-level vs segment-level evidence.  
- [ ] 6–8 example reports match [PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md](PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md).  
- [ ] Internal reviewer sign-off on wording before external demo.  

---

## 12. Dependencies and constraints

- **Do not change** 7C4-v2 thresholds or status rules in 7D.  
- Align field names with [FORENSIC_REPORT_OUTPUT_SPEC.md](../../FORENSIC_REPORT_OUTPUT_SPEC.md) where practical; 7D schema is a superset with traceability fields.  
- Ground-truth labels from manifests may appear in **internal QA appendices only**, not in user-facing narrative as “correct answer.”  

---

## 13. References

- [PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md)  
- [phase7c4_calibration_v2/README.md](../phase7c4_calibration_v2/README.md)  
- [PHASE7_LABEL_SCHEMA.md](../PHASE7_LABEL_SCHEMA.md)  
- [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md)  
