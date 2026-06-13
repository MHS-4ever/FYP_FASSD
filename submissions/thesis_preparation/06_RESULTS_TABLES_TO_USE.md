# Results Tables for Thesis

Organized thesis-ready tables with sources, chapter placement, interpretation, and cautions.  
**Rule:** Do not present internal leakage-safe metrics without also discussing external limitations where applicable.

---

## Table 4.1 — Baseline CNN LFCC Results

| Model / setting | EER |
|-----------------|----:|
| LFCC CNN on clean data | 9.68% |
| LFCC CNN on augmented data | 15.71% |

- **Source:** `PROJECT_STORY_FROM_DAY_ONE.md` §6; `reports/PREVIOUS_PIPELINE_WORK.md`  
- **Chapter:** 4.2  
- **Interpretation:** Established training pipeline; EER too high for final detector.  
- **Cautions:** ASVspoof-domain only; not forensic product metrics.

---

## Table 4.2 — LFCC vs Log-Mel / MFCC-Style Comparison

| Feature / model | Clean test EER | Augmented test EER |
|-----------------|---------------:|-------------------:|
| LFCC robust baseline | not best clean | 15.71% |
| Log-Mel clean model | 8.57% | 36.33% |
| Log-Mel robust model | 9.69% | 15.25% |

- **Source:** `PROJECT_STORY_FROM_DAY_ONE.md` §7  
- **Chapter:** 4.3  
- **Interpretation:** Log-mel robust (15.25%) slightly beats LFCC robust (15.71%); clean-only training fails under augmentation.  
- **Cautions:** Led toward log-mel for deeper models; still benchmark-domain.

---

## Table 4.3 — Deep ResNet CNN Results

| Evaluation | EER |
|------------|----:|
| Clean test | 0.57% |
| Augmented test | 2.61% |

- **Source:** `PROJECT_STORY_FROM_DAY_ONE.md` §8; `reports/PREVIOUS_PIPELINE_WORK.md`  
- **Chapter:** 4.4  
- **Interpretation:** Strong ASVspoof anti-spoof performance (~2.8M parameters).  
- **Cautions:** Broadcast real-world test: 8/8 called fake in small Trump-style test — domain mismatch. Do **not** cite as final FASSD performance.

---

## Table 4.4 — Environmental Classifier Results

| Approach | Result |
|----------|--------|
| Isolation Forest anomaly | ~24.5–25% accuracy — rejected |
| Supervised environmental classifier | 81.69% accuracy on ASVspoof-style test |

- **Source:** `PROJECT_STORY_FROM_DAY_ONE.md` §10  
- **Chapter:** 4.5  
- **Interpretation:** Environmental features informative in-domain but insufficient alone for broadcast generalization.  
- **Cautions:** Trump/broadcast score overlap documented in same source.

---

## Table 4.5 — Unified Dataset Statistics

| Dataset / group | Samples |
|-----------------|--------:|
| PA | 943,110 |
| DF | 611,829 |
| LA | 181,566 |
| RealWorld | 157,414 |
| **Total** | **1,893,919** |

| Label | Samples |
|-------|--------:|
| spoof | 1,573,308 |
| bonafide | 320,611 |

| Attack type | Samples |
|-------------|--------:|
| replay | 816,480 |
| conversion | 589,212 |
| synthesis | 167,616 |
| bonafide | 320,611 |

- **Source:** `data/statistics/unified_dataset_stats.json`  
- **Chapter:** 3.3, 4.6  
- **Interpretation:** Large unified corpus with PA replay coverage and RealWorld domains.  
- **Cautions:** Studio-dominated (1,819,660 studio domain samples); RealWorld still minority by count.

---

## Table 4.6 — HybridResNetEnvironmental Test Evaluation

| Metric | Value |
|--------|------:|
| Test samples | 254,574 |
| Speaker overlap | 0 |
| Binary EER | 16.21% |
| Binary AUC | 0.9167 |
| Binary accuracy @0.5 | 89.78% |
| Multiclass accuracy | 64.36% |

| Subset | Samples | Binary EER | Binary AUC |
|--------|--------:|-----------:|-----------:|
| ASVspoof test | 237,490 | 18.15% | 0.8947 |
| RealWorld test | 17,084 | 16.14% | 0.9236 |

| Threshold | Accuracy (%) | Bonafide FPR (%) |
|-----------|-------------:|-----------------:|
| 0.50 | 89.78 | 41.28 |
| 0.65 | 89.61 | 39.28 |
| 0.70 | 89.52 | 38.43 |

- **Source:** `reports/evaluation/comprehensive_evaluation_report.md`; `reports/FULL_PROJECT_DOCUMENTATION.md`  
- **Chapter:** 4.6  
- **Interpretation:** Met RealWorld EER MVP (<20%); did not meet overall EER <10%; high bonafide FPR at operational thresholds.  
- **Cautions:** Model later **inactive** in release (`reject_for_now`); evidence branch only.

---

## Table 4.7 — HybridResNet Multiclass Attack-Type Performance (Test)

| Class | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| bonafide | 0.6983 | 0.6105 | 0.6515 | 39,737 |
| synthesis | 0.1631 | 0.5160 | 0.2479 | 22,192 |
| conversion | 0.7992 | 0.8851 | 0.8399 | 90,585 |
| replay | 0.9727 | 0.4698 | 0.6336 | 102,060 |

- **Source:** `reports/evaluation/comprehensive_evaluation_report.md`  
- **Chapter:** 4.6  
- **Interpretation:** Replay class high precision but low recall; synthesis weak precision.  
- **Cautions:** Attack typing not shipped as final forensic labels.

---

## Table 4.8 — Phase 7C1 Hybrid Baseline (Controlled Forensic)

| Metric | Count |
|--------|------:|
| clean_human_accepted | 4/23 |
| clean_human_false_alarm | 17/23 |
| direct_ai_detected (file-level) | 0/23 |
| direct_ai_file_missed_but_segment_suspicious | 19/23 |
| human_replay_detected | 23/23 |
| ai_replay_detected_or_segment_suspicious | 23/23 |
| human_mixer_detected | 23/23 |
| ai_mixer_detected | 23/23 |
| partial_fabrication_detected | 43/46 |

- **Source:** `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`  
- **Chapter:** 4.7  
- **Interpretation:** Strong manipulation sensitivity; poor clean-human specificity; segment evidence rescues many direct-AI cases.  
- **Cautions:** Small n=23 per category; controlled local corpus.

---

## Table 4.9 — Phase 7C4-v2 Decision Layer Prototype (Controlled)

| Metric | Count |
|--------|------:|
| clean_human_false_alarm | 7/23 |
| clean_human_accepted | 1/23 |
| clean_human_borderline | 15/23 |
| direct_ai_detected_or_segment_suspicious | 19/23 |
| partial_fabrication_detected | 44/46 |

- **Source:** `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`  
- **Chapter:** 4.7  
- **Interpretation:** Improved clean-human vs raw Hybrid; **prototype only**.  
- **Cautions:** Not final release fusion alone; historical reference.

---

## Table 4.10 — AASIST-L Pretrained on Phase 7C1

| Metric | Count |
|--------|------:|
| clean_human_false_alarm | 22/23 |
| clean_human_accepted | 1/23 |
| direct_ai_detected_or_segment_suspicious | 18/23 |
| partial_fabrication_detected | 45/46 |

- **Source:** `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`  
- **Chapter:** 4.8  
- **Interpretation:** Anti-spoof bias — unacceptable clean-human FPR for forensic product.  
- **Cautions:** **Rejected** (`reject_for_now`); reference only.

---

## Table 4.11 — Phase 8E-1 Cross-Validated Axis Models (Experimental)

| Task / feature | Balanced accuracy | F1 |
|----------------|------------------:|---:|
| origin / ssl | 1.0000 | 1.0000 |
| origin / acoustic | 0.9300 | 0.9442 |
| replay / acoustic | 0.9693 | 0.9616 |
| mixer / acoustic | 0.9909 | 0.9867 |

- **Source:** `reports/phase8/models/phase8e1/phase8e1_training_report.md`  
- **Chapter:** 4.9  
- **Interpretation:** Small controlled dataset (46–92 rows per task); SSL origin perfect on CV — requires caution.  
- **Cautions:** OOF experimental metrics; not deployment-certified. Release uses retrained origin (Phase 2 audit).

---

## Table 4.12 — Release Audit Origin Model (Phase 2)

| Scope | n | Balanced accuracy | Recall | Specificity |
|-------|--:|------------------:|-------:|------------:|
| phase7_test_all_conditions | 40 | 0.9500 | 0.9000 | 1.0000 |
| testing_audios_binary_human_ai | 23 | 0.8731 | 0.9000 | 0.8462 |

**Known failures:** T1.2, T4.1 (clean FP); T4.5 (WhatsApp AI FN)

- **Source:** `reports/release_audit/phase2_origin_release_2026-06-13/phase2_origin_release_report.md`  
- **Chapter:** 4.10  
- **Interpretation:** Processed-AI origin retrain improved replayed-AI detection vs old release.  
- **Cautions:** testing_audios still has 2 clean FPs and 1 AI FN.

---

## Table 4.13 — Phase 3 Controlled Experiment Decisions (Closed Questions)

| Experiment | Decision |
|------------|----------|
| 3A Resampling ablation | **CLOSE** — no chain beat ssl_16k_direct |
| 3B Window-level origin aggregation | **Do not pursue** — no aggregator beat file mean |
| 3C Dual-resolution replay/mixer | **Do not pursue** — no gain on testing_audios |

- **Source:** `reports/release_audit/phase3_controlled_experiments_2026-06-13/phase3_controlled_experiments_decision.md`  
- **Chapter:** 4.10, 5.3  
- **Interpretation:** Negative results are valid thesis contributions — prevents overclaiming alternate front-ends.  
- **Cautions:** Document as audit decisions not new training contributions.

---

## Table 4.14 — Phase 4 Two-Stage Manipulation v3 (Stopped)

| Metric | Result | Required |
|--------|--------|----------|
| testing_audios Stage-1 recall | 20% (3/15) | ≥70% |
| Decision | **STOP — not shipped** | — |

- **Source:** `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/phase4_two_stage_manipulation_v3_decision.md`  
- **Chapter:** 4.10, 4.13  
- **Interpretation:** Unified manipulation classifier failed generalization despite train fit.  
- **Cautions:** Separate replay/mixer axes retained independently.

---

## Table 4.15 — Phase 5 Partial Redesign (Oracle Stop Rule)

| Metric | Result | Required |
|--------|--------|----------|
| Partial-file top-5 hit rate (leakage-safe test) | 10/10 (100%) | ≥50% |
| Localized rate | 10/10 | — |
| Clean broad-activation rate | 0% | — |
| Selected threshold | 0.95 | — |

**testing_audios primary:** T4.3 localized 46–50 s (label 35–58 s); T5_FAB_001 localized 18–22 s (label 14–21 s)

- **Source:** `reports/release_audit/phase5_partial_redesign_2026-06-13/phase5_partial_redesign_decision.md`  
- **Chapter:** 4.10  
- **Interpretation:** Removing F9 features fixed broad activation; primary partial cases pass.  
- **Cautions:** T1.2/T1.3 single-window spikes remain; manual review only.

---

## Table 4.16 — Final Release testing_audios Axis Matrix

| Axis | n | TP | TN | FP | FN | Balanced accuracy | Recall | Specificity |
|------|--:|---:|---:|---:|---:|------------------:|-------:|------------:|
| Origin | 18 | 9 | 6 | 2 | 1 | 0.8250 | 0.9000 | 0.7500 |
| Replay | 25 | 5 | 15 | 3 | 2 | 0.7738 | 0.7143 | 0.8333 |
| Mixer | 25 | 0 | 22 | 1 | 2 | 0.4783 | 0.0000 | 0.9565 |
| Partial | 25 | 2 | 23 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

- **Source:** `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_matrix.md`  
- **Chapter:** 4.11  
- **Interpretation:** **Primary external honesty table** for final release.  
- **Cautions:** Origin n=18 excludes mixed partial-origin rows; partial metrics are gated; mixer recall 0% must be discussed prominently.

---

## Table 4.17 — Phase 6 Evidence Calibration Bands

| Axis | low_max | medium_max | threshold |
|------|--------:|-----------:|----------:|
| origin | 0.0444 | 0.0986 | 0.92 |
| replay | 0.5338 | 0.9891 | 0.65 |
| mixer | 0.2201 | 0.9663 | 0.75 |
| partial_segment | 0.2638 | 0.8139 | 0.95 |

- **Source:** `release/config/evidence_calibration.json`  
- **Chapter:** 3.16, 4.12  
- **Interpretation:** User-facing Low/Medium/High bands from leakage-safe dev.  
- **Cautions:** Not calibrated legal probabilities.

---

## Table 4.18 — Phase 9 Demo Freeze Validation

| Check | Result |
|-------|--------|
| Overall P4B validation | PASS |
| P3 full 184 files | 184 present |
| human_clean_false_suspicious_rate | 0.0 |
| Active models | origin, replay, mixer, partial only |
| AASIST / HybridResNet | reject_for_now |
| Demo 8 variants | all PASS (0 failures) |

- **Source:** `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`  
- **Chapter:** 4.12  
- **Interpretation:** Release packaging and wording regression passed on Phase 7C1-scale corpus.  
- **Cautions:** Does not prove real-world generalization beyond controlled 184 + testing_audios.

---

## Table 4.19 — Final Active Release Model Summary

| Model | Axis | Threshold | Feature | Status |
|-------|------|----------:|---------|--------|
| origin_file_model | origin | 0.92 | ssl | active experimental |
| replay_file_model | replay | 0.65 | acoustic | active experimental |
| mixer_file_model | mixer | 0.75 | acoustic | active experimental |
| partial_segment_model | partial | 0.95 | combined_no_f9 | active experimental |

- **Source:** `release/MODEL_REGISTRY.md`  
- **Chapter:** 3.2, 4.11, Appendix F  
- **Interpretation:** Final shipped evidence axes after release audit.  
- **Cautions:** All `.joblib` models are experimental; forbidden uses listed in registry.

---

## Table Usage Guidance

| Audience question | Primary table(s) |
|-------------------|-------------------|
| "Did early baselines work on ASVspoof?" | 4.1–4.3 |
| "What is the unified dataset scale?" | 4.5 |
| "Why move beyond Hybrid?" | 4.6, 4.8, 4.16 |
| "What is the final honest external performance?" | **4.16** |
| "What improved in release audit?" | 4.12, 4.15, 4.16 + narrative in phase7_final_release_report |
