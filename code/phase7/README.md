# Phase 7 — Forensic Product Upgrade (Planned)

**Status:** Documentation and templates only. **No Python implementation yet.**

**Master plan:** [reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md](../../reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md)  
**Scope:** [reports/UPDATED_PROJECT_SCOPE.md](../../reports/UPDATED_PROJECT_SCOPE.md)

---

## Sub-phases (fixed order)

| Phase | Doc | Code | Training |
|-------|-----|------|----------|
| **7A** | [PHASE7A_FORENSIC_TEST_SUITE.md](../../reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) | Planned batch runner | **No** |
| **7B** | PHASE7_DOMAIN_ADAPTATION §7B | TBD | Labels only |
| **7C** | PHASE7_DOMAIN_ADAPTATION §7C | Reuse `train_hybrid_fast.py` | **Yes** (after 7A) |
| **7D** | [PHASE7D_FORENSIC_REPORT_LAYER.md](../../reports/pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md) | Planned report mapper | **Mandatory** (rules) |
| **7E** | Roadmap §7E | AASIST → WavLM → wav2vec2 **separate** | After 7C |
| **7F** | Roadmap §7F | Late fusion / ensemble | After 7E |

---

## Planned scripts (not created yet)

- `run_forensic_test_suite.py` — loop manifest → Phase 6 JSON  
- `analyze_forensic_test_results.py` — merge CSV, chunk-level partial-fabrication analysis  
- `build_forensic_report.py` (7D) — Phase 6 JSON → forensic report schema  

Until then: manual Phase 6 per [phase7_forensic_tests/README.md](../../reports/phase7_forensic_tests/README.md).

---

## Do not start yet

- Training (7C), transformers (7E), ensemble (7F)  
- Phase 6 inference logic changes  
- Early model fusion  
