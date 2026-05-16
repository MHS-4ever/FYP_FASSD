# Phase 7 — Forensic Testing & Adaptation (Planned)

**Status:** Documentation and templates only. **Scripts not implemented yet.**

---

## Sub-phases

| Phase | Doc | Code | Training |
|-------|-----|------|----------|
| **7A** | `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md` | Planned below | **No** |
| **7B** | TBD (dataset manifest) | TBD | Prepare data only |
| **7C** | `reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md` | `train_hybrid_fast.py` (reuse) | **Yes** (after 7A) |
| **7D** | `reports/FORENSIC_REPORT_OUTPUT_SPEC.md` | Report mapper / UI | Optional |
| **7E** | Roadmap Section 7 | Compare WavLM/wav2vec2/AASIST + ensemble | **After 7C** (12 GB VRAM — practical, not started) |

---

## Planned scripts (not created yet)

### `run_forensic_test_suite.py` (planned)

- Read `reports/phase7_forensic_tests/forensic_test_manifest.csv`
- For each row, call Phase 6 inference with fixed baseline settings
- Write JSON to `reports/phase7_forensic_tests/results/json_outputs/{test_id}.json`
- Append/merge rows into `forensic_test_results.csv`

### `analyze_forensic_test_results.py` (planned)

- Load manifest + JSON outputs
- Compute `origin_interpretation`, `manipulation_interpretation`, `failure_type` via rules in roadmap
- Update `FORENSIC_TEST_ANALYSIS.md` sections or emit markdown tables

**Until these exist:** run `code/phase6/explain_prediction.py` manually per `reports/phase7_forensic_tests/README.md`.

---

## Do not implement training here without Phase 7A sign-off

See `reports/FORENSIC_PRODUCT_ROADMAP.md` — Immediate Rule.
