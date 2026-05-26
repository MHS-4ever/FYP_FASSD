# Phase 7E0 — Locked Benchmark Protocol (AASIST)

**Status:** **LOCKED** for Phase 7E evaluation  
**Version:** 7E0-v1 (May 2026)  
**Change policy:** Do not alter metrics, baselines, or holdout rules without a new phase gate document and explicit sign-off.

**Training:** Not part of this protocol execution in 7E0.

---

## 1. Purpose

Provide a **fixed** evaluation contract so AASIST results are comparable across runs and against existing HybridResNet / 7C3-R2 / 7C4-v2 artifacts. This protocol applies to **Phase 7E4** and any interim inference smoke tests that write benchmark CSVs.

---

## 2. Evaluation datasets

### 2.1 Primary — Phase 7C1 full dataset

| Item | Path / reference |
|------|------------------|
| Manifest | `reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv` |
| Baseline results | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` |
| Partial fabrication | `reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv` |
| Chunk timelines | `reports/phase7/phase7c1_baseline/results/chunk_timelines/` (for segment metrics) |

**File count reference:** 184 files (23 base IDs × 8 variants) unless manifest version changes with documented reason.

### 2.2 Holdout — Phase 7A controlled suite

| Item | Path / reference |
|------|------------------|
| Manifest | `reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv` |
| Baseline product CSV | `reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv` |

**Rule:** Phase 7A T1–T5 files (`controlled_holdout`, `use_for_training=false`) must **never** appear in AASIST training manifests. Violation invalidates the run.

### 2.3 Forbidden as training input

- Any row with `dataset_role=controlled_holdout` or Phase 7A `test_id` prefix T1–T5 in training adapters.
- Phase 7C4-v2 decision CSV used as labels.

---

## 3. Required metrics — Phase 7C1

Report **counts and rates** per category below. Use the same category keys as Phase 7C1 baseline analysis (`analyze_phase7c1_baseline.py` conventions) unless a dedicated AASIST analyzer documents a deliberate mapping table.

| Metric ID | Description | Notes |
|-----------|-------------|-------|
| `clean_human_accepted` | Clean human clips accepted as low forensic risk | Not the same as “borderline” |
| `clean_human_borderline` | Within review band (if using hybrid-style thresholds) | Document threshold |
| `clean_human_false_alarm` | Clean human flagged as high risk / spoof | Must improve vs baseline for standalone accept |
| `direct_ai_detected` | Direct AI file-level detection | Compare baseline 7C1 rates |
| `direct_ai_segment_suspicious` | Segment-level suspicious on direct AI | If chunk pipeline available |
| `human_replay_detected` | Human-origin replay chain flagged | Forensic-risk positive, not “AI-generated” |
| `ai_replay_detected` | AI replay flagged | Must not **collapse** vs baseline |
| `human_mixer_detected` | Human mixer / channel processing flagged | |
| `ai_mixer_detected` | AI through mixer flagged | |
| `partial_fabrication_detected` | Partial fab cases flagged | Use suspicious-region windows when trained/evaluated with region metadata |

**Output artifacts (7E4):**

- `reports/phase7/phase7e_aasist_experiment/evaluation/phase7c1_aasist_results.csv`
- `reports/phase7/phase7e_aasist_experiment/evaluation/PHASE7C1_AASIST_ANALYSIS.md`
- Optional: `phase7c1_aasist_error_cases.csv`, partial-fab sidecar CSV

---

## 4. Required metrics — Phase 7A holdout

| Metric area | Behavior to document |
|-------------|----------------------|
| Clean human | Accepted / borderline / false alarm |
| Direct AI | File-level and segment-suspicious if applicable |
| Processed human manipulation | Replay / mixer / channel cases per T-groups |
| AI replay / processed AI | Must not regress catastrophically vs baseline |
| Partial fabrication | Segment behavior (e.g. T5), not whole-file REAL alone |

**Output artifacts (7E4):**

- `reports/phase7/phase7e_aasist_experiment/evaluation/phase7a_aasist_results.csv`
- `reports/phase7/phase7e_aasist_experiment/evaluation/PHASE7A_AASIST_ANALYSIS.md`

---

## 5. Comparison baselines (mandatory)

Every 7E4 report must include side-by-side tables against:

| Baseline | Role | Canonical paths |
|----------|------|-----------------|
| **Original HybridResNet** | Primary evidence comparison | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` |
| **7C3-R2 best_product** | R2 evidence reference | `reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv` |
| **7C3-R2 best_loss** | R2 partial/segment reference | `reports/phase7/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv` |
| **Phase 7C4-v2 decision layer** | Prototype fusion comparison | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` |

**7A holdout baselines:**

- HybridResNet: `reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv`
- R2 holdout evals under `phase7c3_finetune_r2/evaluation/*/phase7a_holdout_after_r2/`
- 7C4-v2 holdout impact: `check_phase7c4_holdout_impact.py` outputs (reference)

**Comparison report (7E4):**

- `reports/phase7/phase7e_aasist_experiment/evaluation/AASIST_BASELINE_COMPARISON.md`
- `reports/phase7/phase7e_aasist_experiment/evaluation/aasist_acceptance_matrix.csv` (aligned with 7C4-v2 acceptance matrix style)

---

## 6. Inference settings (lock at 7E1/7E4 start)

Document and freeze per checkpoint:

| Setting | Requirement |
|---------|-------------|
| Audio sample rate | Match AASIST recipe (typically 16 kHz — confirm in 7E1) |
| Chunk length / hop | Document; align with Phase 6/7 chunk philosophy where comparable |
| Pooling | File-level score derivation (mean / max / vote) — same rule for all eval runs |
| Thresholds | Primary + sensitivity sweep **documented**; product threshold chosen in 7E4 report, not silently changed |
| VAD | If used, document; compare fairly to hybrid VAD settings or report limitation |

Do not tune thresholds on **7A holdout** to “pass” acceptance.

---

## 7. Segment and partial-fabrication rules

- **Partial fabrication:** Evaluate suspicious-region clips or chunk scores overlapping `suspicious_start_time` / `suspicious_end_time` from 7C1 manifest (same principle as 7C3-R2 feature cache centering).
- **Human replay / human mixer:** Count as **detected** when forensic-risk score exceeds threshold — label is risk-positive, wording in reports remains **human-origin manipulation risk** (see label strategy doc).

---

## 8. Acceptance gate linkage

Standalone accept/reject uses [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md). This protocol does **not** define success by accuracy alone — it defines **which counters** must be reported.

Minimum reporting checklist before any “accepted” claim:

- [ ] All §3 metrics on 7C1
- [ ] All §4 areas on 7A
- [ ] All §5 baselines in comparison table
- [ ] Holdout training leak check passed (7E2 validation artifact)
- [ ] Threshold and pooling documented

---

## 9. What changing this document requires

1. New version id (e.g. `7E0-v2`) with changelog.  
2. Re-run or explicit “not comparable” flag on prior AASIST CSVs.  
3. Update [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md) if gates change.

---

## 10. Related

- [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md)  
- [PHASE7A_CONTROLLED_TEST_SUITE.md](../PHASE7A_CONTROLLED_TEST_SUITE.md)  
- [PHASE7_TEST_CASE_GUIDE.md](../PHASE7_TEST_CASE_GUIDE.md)
