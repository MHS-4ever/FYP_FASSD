# FASSD Next Actions

**Direction:** [Forensic Voice Authenticity Analyzer](FORENSIC_PRODUCT_ROADMAP.md)  
**Gate:** No training until [Phase 7A](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) is reviewed.

---

## Immediate

1. **Read** `reports/FORENSIC_PRODUCT_ROADMAP.md` and agree on layered output (origin + manipulation + risk).
2. **Copy** `reports/phase7_forensic_tests/forensic_test_manifest_template.csv` → `forensic_test_manifest.csv`.
3. **Record or collect** ~40 P0 test clips per `notes/recording_protocols.md` (not done yet).
4. **Fill** manifest: paths, ground truth, `manipulation_type`, language, device chain.
5. **Run** Phase 6 on each file (command in `phase7_forensic_tests/README.md`).
6. **Merge** results into `results/forensic_test_results.csv` (manual or future script).
7. **Complete** `results/FORENSIC_TEST_ANALYSIS.md` from template.
8. **List** false positives / false negatives **by condition** (not only overall accuracy).
9. **Decide** fine-tuning dataset priorities for Phase 7B–7C.

---

## After Phase 7A (only when analysis is signed off)

1. Build **controlled local dataset** with `ground_truth_origin` + `ground_truth_manipulation` labels (Phase 7B).
2. Record clips per duration rules: **20–30 s** default P0, **≥ 8 s** minimum, paired same-script sets.
3. **Fine-tune** current `HybridResNetEnvironmental` (Phase 7C) — not a new architecture.
4. Implement **forensic report mapper** per `FORENSIC_REPORT_OUTPUT_SPEC.md` (Phase 7D).
5. Update UI/API wording (avoid “proved fake”).
6. **Only after 7C review:** Phase 7E — compare WavLM-base / wav2vec2-base / AASIST-style on same forensic manifest; consider ensemble (12 GB VRAM makes frozen-backbone, LoRA, and small SSL experiments practical).

## Recording checklist (when creating P0 audio)

- [ ] **20–30 s** speech per default test case  
- [ ] No clip **&lt; 8 s**  
- [ ] **0.5–1 s** silence at start/end  
- [ ] **Paired** clean / AI / replay / mixer / WhatsApp from same script where possible  
- [ ] **30–45 s** only for edited or partial-AI cases (P1+)  
- [ ] **60–120 s** reserved for later long-evidence tests only  

---

## Do not do yet

- Do **not** train or fine-tune blindly on Pakistani/Trump clips only.
- Do **not** replace `HybridResNetEnvironmental` without 7A + 7C baseline comparison.
- Do **not** start Phase **7E** (WavLM / wav2vec2 / AASIST) before 7C is reviewed — even with 12 GB VRAM available.
- Do **not** claim forensic proof from binary `REAL`/`FAKE` alone.
- Do **not** ignore **human-origin replayed/processed** cases (REAL ≠ original recording).
- Do **not** permanently change thresholds without per-condition 7A stats.
- Do **not** implement Phase 7 Python automation until you explicitly request it.

---

## Quick links

| Doc | Use |
|-----|-----|
| [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) | Product direction |
| [PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) | Test plan |
| [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md) | Future report fields |
| [PROJECT_STATE_AUDIT.md](PROJECT_STATE_AUDIT.md) | Current baseline state |
| [AUDIO_TESTING_OUTPUT_GUIDE.md](AUDIO_TESTING_OUTPUT_GUIDE.md) | Phase 6 output fields |
