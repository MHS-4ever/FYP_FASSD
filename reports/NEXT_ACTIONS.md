# FASSD Next Actions

> **Note:** Phase 7 planning has been reorganized. The canonical Phase 7 documentation now lives in `reports/phase7/`. This file is retained for reference/backward compatibility.

**Product:** [Forensic Voice Authenticity Analyzer](UPDATED_PROJECT_SCOPE.md)  
**Scope:** [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md) (Scopes 1–6)  
**Roadmap:** [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md)  
**Gate:** No training until [Phase 7A](phase7/PHASE7A_CONTROLLED_TEST_SUITE.md) is reviewed.

---

## Immediate

1. Read [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md) and [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) (layered output + product rules).
2. **Complete P0 controlled test audios** (~40 core + partial-fabrication cases in 7A spec).
3. **Include partial-fabrication test cases** — start with **`T5_FAB_001`** (34 s, fake **14–21 s**); see [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md).
4. Copy `forensic_test_manifest_template.csv` → `forensic_test_manifest.csv` and fill forensic label columns.
5. **Run Phase 7A** — Phase 6 inference per file (no training).
6. **Review whole-file predictions** and **chunk-level suspicious behavior** (can current logic flag segments when file is REAL?).
7. Merge `forensic_test_results.csv` and complete `FORENSIC_TEST_ANALYSIS.md`.
8. **Do not fine-tune** until failure patterns are documented and agreed.

---

## After Phase 7A (signed off)

1. **Implement Phase 7D report layer** — schema, mapping, timeline, wording ([PHASE7D_FORENSIC_REPORT_LAYER.md](phase7/PHASE7D_FORENSIC_REPORT_LAYER.md)).
2. **Add suspicious timeline detection** (chunk-level → `suspicious_timeline`).
3. **Prepare forensic-labeled dataset** (Phase 7B fields).
4. **Fine-tune hybrid model** (Phase 7C) on priority domains.
5. **Test AASIST separately** (Phase 7E step 1).
6. **Test WavLM-base** if needed (Phase 7E step 2).
7. **Test wav2vec2-base** if needed (Phase 7E step 3).
8. **Consider late fusion / ensemble** (Phase 7F) only if standalone comparisons improve metrics.

---

## Recording checklist (P0 + partial fabrication)

- [ ] **20–30 s** speech for standard P0 cases  
- [ ] No clip **&lt; 8 s**  
- [ ] **0.5–1 s** silence at start/end  
- [ ] **Paired** same-script across clean / AI / replay / mixer / WhatsApp  
- [ ] **Partial-fabrication** cases per 7A §5.2 (e.g. 120 s + 10 s AI insert)  
- [ ] **30–45 s** for edited/spliced; **60–120 s** only where 7A specifies long files  

---

## Do not do yet

- Do **not** train or fine-tune blindly.
- Do **not** claim **“authentic”** only because `prediction` is REAL.
- Do **not** ignore **suspicious segments** inside long mostly-real audio.
- Do **not** **early-fuse** all models before separate 7E evaluation.
- Do **not** start Phase **7E** before 7C (and 7D spec) review.
- Do **not** start Phase **7F** before 7E comparisons.
- Do **not** implement Phase 7 Python automation until explicitly requested.
- Do **not** change Phase 6 core inference until a documented bug requires it.

---

## Quick links

| Doc | Use |
|-----|-----|
| [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md) | Official six scopes |
| [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) | Roadmap + rules |
| [pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md](pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md) | Phase 7A–7F |
| [pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) | Test plan |
| [pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md](pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md) | Report layer |
| [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md) | Report fields |
| [PROJECT_STATE_AUDIT.md](PROJECT_STATE_AUDIT.md) | Baseline state |
| [AUDIO_TESTING_OUTPUT_GUIDE.md](AUDIO_TESTING_OUTPUT_GUIDE.md) | Phase 6 outputs |
