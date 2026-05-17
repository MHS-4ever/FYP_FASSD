# Phase 7A — Controlled Forensic Test Suite

**Status:** **NEXT** (active phase)  
**Training:** **None**  
**Inference:** Existing Phase 6 only — no logic changes in 7A planning step

---

## 1. Goal

Run the **current** `HybridResNetEnvironmental` model (Phase 6) on controlled **T1–T5** test cases to measure where the baseline succeeds and fails **before** any fine-tuning or new models.

---

## 2. Why this phase exists

- Failure types (Urdu FPs, human-replay REAL, partial fake hidden in REAL) must be **measured**, not assumed.  
- Fine-tuning without controlled tests risks **catastrophic forgetting** or wrong priorities.  
- Forensic labels and report rules need **evidence** from real local chains (phone, WhatsApp, replay, edit).  

**Gate:** No Phase 7C training until `FORENSIC_TEST_ANALYSIS.md` is reviewed.

---

## 3. Inputs

| Input | Location |
|-------|----------|
| Baseline checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` |
| Phase 6 script | `code/phase6/explain_prediction.py` |
| Test manifest | `reports/phase7_forensic_tests/forensic_test_manifest.csv` (from template) |
| Test audio | `testing_audios/` (forensic_p0, fabricated, etc.) |

Recommended inference settings: `pct_vote`, chunk_threshold **0.65**, vote_threshold **0.70**, VAD file_percentile **40**, vad_min_speech_ratio **0.40**.

---

## 4. Outputs

| Output | Path |
|--------|------|
| Per-file JSON | `reports/phase7_forensic_tests/results/json_outputs/` |
| Merged results CSV | `reports/phase7_forensic_tests/results/forensic_test_results.csv` |
| **Product CSV** | `reports/phase7_forensic_tests/results/forensic_test_results_product.csv` |
| **Product analysis (main)** | `reports/phase7_forensic_tests/results/PHASE7A_PRODUCT_LEVEL_ANALYSIS.md` |
| Legacy binary analysis | `reports/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md` |
| Chunk timelines | `reports/phase7_forensic_tests/results/chunk_timelines/` |

Run product analysis: `python code/phase7/analyze_forensic_test_results.py --results_csv reports/phase7_forensic_tests/results/forensic_test_results.csv`

**Review priority:** use **product-level** report for 7B/7C decisions; legacy binary accuracy alone understates manipulation detection on human replay.

Partial fabrication: [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md). Rows without suspicious timestamps (e.g. T4.3) → `partial_not_evaluated_missing_timestamp`, not a miss.

---

## 5. Tasks

### Test groups (T1–T5)

| Group | Focus | Examples |
|-------|--------|----------|
| **T1** | Clean / direct origin | Clean human (mobile/USB); direct AI (TTS/clone) |
| **T2** | Replay | Human → speaker → phone; AI → speaker → phone |
| **T3** | Mixer / channel processed | Human or AI through mixer/EQ/PA |
| **T4** | Compression / platform / broadcast | WhatsApp, YouTube, etc. (if available) |
| **T5** | Fabricated / partial AI insertion | Mostly real + short AI insert |

Recording rules: [PHASE7_TEST_CASE_GUIDE.md](PHASE7_TEST_CASE_GUIDE.md).

### Fabricated case (T5) — critical rules

| Property | `T5_FAB_001` reference |
|----------|-------------------------|
| Total duration | **34 s** |
| Fake insert | **14.0 s – 21.0 s** (~7 s, ~20.6% of file) |
| Ground truth | `partial_fabrication_detected=true` |
| Whole-file REAL | **Not necessarily failure** |
| Key check | Chunk spoof scores **higher inside 14–21 s** than outside |

`partial_region_detected` rules: [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md).

### Execution checklist

1. Copy manifest template → `forensic_test_manifest.csv`.  
2. Record or place audio; fill ground-truth columns.  
3. Run `code/phase7/run_forensic_test_suite.py` with `--save_chunk_timeline`.  
4. Run `code/phase7/analyze_forensic_test_results.py` → product CSV + `PHASE7A_PRODUCT_LEVEL_ANALYSIS.md`.  
5. Review product report before Phase 7B labels / 7C fine-tuning.

---

## 6. Success criteria

- [ ] All **T1–T5** priority files processed.  
- [ ] False positives and false negatives known **per group**.  
- [ ] Fabricated audio: segment **14–21 s** evaluated separately from whole-file prediction.  
- [ ] Partial-fabrication: `partial_region_detected` compared to ground truth where applicable.  
- [ ] **No training** in this phase.  
- [ ] Analysis signed off → unlock 7B/7C planning.

---

## 7. What not to do in this phase

- Fine-tune or retrain the hybrid model  
- Change Phase 6 architecture or default product thresholds without documenting experiments  
- Start Phase 7E transformers or Phase 7F ensemble  
- Treat REAL/FAKE as final forensic verdict  

---

## 8. Connection to next phase

| Next | Uses 7A results for |
|------|---------------------|
| **7B** | Which labels and recording conditions to collect for training CSV |
| **7C** | Which domains to fine-tune (Urdu, replay, mixer, WhatsApp, partial AI) |
| **7D** | Rule thresholds and wording cases validated against real failures |

---

## Inference command (reference)

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --audio_path <AUDIO_PATH> ^
  --output_dir reports/phase7_forensic_tests/results/json_outputs ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32
```
