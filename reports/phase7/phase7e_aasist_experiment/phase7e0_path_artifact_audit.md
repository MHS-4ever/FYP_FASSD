# Phase 7E0.5 — Path and Artifact Audit

**Status:** Superseded — use automated audit outputs in [`audit/`](audit/phase7e0_path_artifact_audit.md)  
**Audit script:** `code/phase7/audit_phase7e0_paths.py`

---

## Purpose

Verify that documented paths exist and the `(fassd)` environment can run GPU inference **before** any AASIST code is written under `code/phase7/aasist/`.

---

## Required checks

| # | Check | Path / command | Pass? | Notes |
|---|-------|----------------|-------|-------|
| 1 | Train manifest | `reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv` | ☐ | |
| 2 | Val manifest | `reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv` | ☐ | |
| 3 | Test manifest | `reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv` | ☐ | |
| 4 | 7C1 collection manifest | `reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv` | ☐ | |
| 5 | 7C1 baseline results | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` | ☐ | |
| 6 | 7A forensic manifest | `reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv` | ☐ | |
| 7 | 7A product results | `reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv` | ☐ | |
| 8 | HybridResNet checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` | ☐ | |
| 9 | PyTorch + CUDA in `fassd` | `conda activate fassd` then `python -c "import torch; print(torch.cuda.is_available())"` | ☐ | Expect `True` on laptop GPU |

**Optional (recommended before 7E4):**

| Check | Path |
|-------|------|
| 7C1 partial analysis | `reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv` |
| 7C4-v2 decisions | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` |
| Holdout protection report | `reports/phase7/phase7c2_training_prep/phase7c2_holdout_protection_report.md` |

---

## Audit result

| Field | Value |
|-------|-------|
| Date | |
| Machine | |
| Auditor | |
| Overall | ☐ PASS — proceed to 7E1 ☐ FAIL — fix paths before code |

### Failures (if any)

_List missing files, wrong working directory, or CUDA false._

---

## Sign-off

Run:

```text
python code/phase7/audit_phase7e0_paths.py --output_dir reports/phase7/phase7e_aasist_experiment/audit
```

Review verdict in [audit/phase7e0_path_artifact_audit.md](audit/phase7e0_path_artifact_audit.md) and paths in [audit/phase7e0_selected_paths.json](audit/phase7e0_selected_paths.json).

**Related:** [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md) § Phase 7E0.5
