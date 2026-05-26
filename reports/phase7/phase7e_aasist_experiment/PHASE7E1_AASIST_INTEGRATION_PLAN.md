# Phase 7E1 — AASIST Integration Plan

**Status:** Active (integration + smoke test only)  
**Prerequisite:** Phase 7E0.5 audit `PASS` or `PASS_WITH_WARNINGS`  
**Training:** **Forbidden** in 7E1

---

## 1. Goal

Verify that a **real** AASIST source can be integrated safely before building the Phase 7E2 dataset adapter or any training (7E3A/7E3B).

Answer:

1. Valid AASIST source present or clearly missing?  
2. Python imports work?  
3. Model/config can be instantiated (with upstream config)?  
4. Dummy or real-audio forward pass possible?  
5. Expected input format (sample rate, length, labels)?  
6. Checkpoint format expectations?  
7. GPU VRAM during smoke test?  
8. What 7E2 must implement?

---

## 2. Why no training yet

- Phase 7C is **frozen**; HybridResNet remains evidence for replay/mixer/partial.  
- AASIST must be evaluated as a **candidate branch**, not assumed final model.  
- Without source + IO clarity, training would risk wrong labels, wrong audio format, or holdout leakage.  
- **7E3A** requires a pretrained checkpoint eval **before** 7E3B fine-tuning.

---

## 3. Source policy

| Rule | Detail |
|------|--------|
| No fake AASIST | Do not implement architecture manually in FASSD |
| Mode A | Local tree under `vendor/AASIST` or `external/AASIST` |
| Mode B | Importable package in `(fassd)` |
| Mode C | `SOURCE_REQUIRED` verdict with explicit user actions |
| No auto-download | User provides source or approves download in a later step |

See [PHASE7E1_SOURCE_REQUIREMENTS.md](PHASE7E1_SOURCE_REQUIREMENTS.md).

---

## 4. Required source files (typical upstream)

Depends on upstream repo; audit script searches for:

- Python modules with classes `AASIST`, `Model`, `AASISTModel`, etc.  
- Config files (`.yaml`, `.json`, …)  
- README / LICENSE  
- Optional `.pth` checkpoints (for 7E3A, not required for 7E1 import-only pass)

---

## 5. Environment check

**Script:** `code/phase7/aasist/integration/check_phase7e1_environment.py`

Checks: Python executable, conda env, torch, CUDA, GPU VRAM, pandas, librosa, soundfile, h5py, yaml, sklearn, scipy.

**Output:** `audit/phase7e1_environment_check.{md,json}`

---

## 6. Source audit

**Script:** `code/phase7/aasist/integration/audit_aasist_source.py`

Scans source tree (AST + file lists). Verdicts include `SOURCE_REQUIRED`, `PASS`, `PASS_IMPORT_ONLY`.

**Output:** `audit/phase7e1_aasist_source_audit.{md,json}`

---

## 7. Import smoke test

**Script:** `code/phase7/aasist/integration/smoke_test_aasist_import.py`

Verdicts: `PASS`, `PASS_IMPORT_ONLY`, `SOURCE_REQUIRED`, `CONFIG_REQUIRED`, `CHECKPOINT_REQUIRED`, `FAILED`.

**Output:** `phase7e1_smoke_test/phase7e1_smoke_test_{report.md,result.json}`

---

## 8. Expected IO discovery

**Script:** `code/phase7/aasist/integration/inspect_aasist_expected_io.py`

Heuristic scan of configs and dataset modules for sample rate, lengths, labels.

**Output:** `audit/phase7e1_expected_io_report.{md,json}`

---

## 9. Pass / fail for Phase 7E1 gate

| Verdict | Proceed to 7E2? |
|---------|-----------------|
| Environment `PASS` | Required |
| Source `PASS` or `PASS_IMPORT_ONLY` + smoke `PASS` / `PASS_IMPORT_ONLY` | Yes, with documented config/checkpoint needs |
| `SOURCE_REQUIRED` (no source yet) | **No** — provide source first; 7E1 scaffolding OK |
| `FAILED` (CUDA/env) | Fix environment before 7E2 |
| Smoke `CONFIG_REQUIRED` | Provide upstream config; re-run smoke |

**7E1 scaffolding complete** when all four scripts run and reports exist — even if source is still `SOURCE_REQUIRED`.

**7E2 gate:** Source audit + smoke test show `PASS` or `PASS_IMPORT_ONLY` with a documented path to config/checkpoint for 7E3A.

---

## 10. Next phase after pass

**Phase 7E2** — Build dataset adapter from `phase7e0_selected_paths.json` manifests; binary `risk_target` per [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md); protect Phase 7A holdout.

---

## Related

- [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md)  
- [../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md)
