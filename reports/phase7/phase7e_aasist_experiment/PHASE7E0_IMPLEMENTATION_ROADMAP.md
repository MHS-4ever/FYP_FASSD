# Phase 7E0 — AASIST Implementation Roadmap

**Status:** Planning roadmap (7E0 hardened)  
**Code root (future):** `code/phase7/aasist/` — **do not create until 7E0.5 + 7E0 review pass**  
**Reports root:** `reports/phase7/phase7e_aasist_experiment/`

---

## Evidence branch roles

| Branch | Best expected role |
|--------|-------------------|
| **HybridResNet baseline** | Replay / mixer / partial fabrication evidence |
| **AASIST** | Direct AI / synthetic spoof evidence candidate |
| **Phase 7C4-v2** | Current decision-layer prototype |
| **Future 7E5 fusion** | Combines AASIST + HybridResNet evidence |

AASIST does **not** need to replace HybridResNet. It only needs to improve a weak axis (especially **direct AI**) within [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md) numeric gates.

---

## Overview

```text
7E0 Planning + locked benchmark + hardened gates
  ↓ review hardened docs
7E0.5 Path / artifact / environment audit (script)  →  audit/phase7e0_*.md|csv|json
  ↓ PASS or PASS_WITH_WARNINGS
7E1 Smoke test (imports, forward, VRAM) — still no train
  ↓ review
7E2 Dataset adapter (manifests, holdout guard)
  ↓ review
7E3A Pretrained AASIST eval on 7C1 + 7A  (NO fine-tune first)
  ↓
7E3B Fine-tune only if 7E3A insufficient or documented no checkpoint
  ↓
7E4 Full evaluation + acceptance matrix (numeric gates)
  ↓ accept / branch-only / reject
7E5 Fusion decision layer v3
  ↓
7D implementation resumes
```

---

## Phase 7E0 — Planning and locked benchmark

| Item | Status |
|------|--------|
| Experiment plan | ✅ |
| Locked benchmark protocol | ✅ |
| Label strategy (risk ≠ origin) | ✅ hardened |
| Acceptance criteria (numeric gates) | ✅ hardened |
| Resource constraints | ✅ |
| Do-not-do list | ✅ |
| Path audit script | ✅ `code/phase7/audit_phase7e0_paths.py` |

**Exit criteria:** Review hardened docs + complete **7E0.5** audit.

**Forbidden:** Training, weight downloads, `code/phase7/aasist/`.

---

## Phase 7E0.5 — Path, Artifact, and Environment Audit

**Gate:** Verdict must be **`PASS`** or **`PASS_WITH_WARNINGS`** before **7E1** and **7E2**. **`FAIL`** blocks AASIST code integration.

**Purpose:** Verify canonical vs legacy paths, critical artifacts, CSV columns, and `(fassd)` PyTorch/CUDA — without moving or copying files.

**Command** (run from repo root, **`(fassd)`** activated):

```text
python code/phase7/audit_phase7e0_paths.py --output_dir reports/phase7/phase7e_aasist_experiment/audit
```

**Script:** `code/phase7/audit_phase7e0_paths.py`

- Checks each artifact at **canonical** (`reports/phase7/...`) and **legacy** (`reports/phase7c1_.../`) paths.  
- **Selected path priority:** canonical → legacy → missing.  
- Legacy-only hits produce warnings, not automatic FAIL.  
- Inspects CSV row/column counts and expected columns.  
- Records environment + GPU/VRAM when PyTorch CUDA is available.

**Outputs** (under `reports/phase7/phase7e_aasist_experiment/audit/`):

| File | Use |
|------|-----|
| `phase7e0_path_artifact_audit.md` | Human-readable summary + verdict |
| `phase7e0_path_artifact_audit.csv` | Full artifact table |
| `phase7e0_selected_paths.json` | **Use in 7E1/7E2** — resolved path map |
| `phase7e0_environment_report.json` | Python/torch/CUDA/packages |
| `phase7e0_missing_or_warning_items.csv` | Missing paths + column warnings |

**Verdicts:**

| Verdict | Meaning |
|---------|---------|
| `PASS` | All critical artifacts found; torch + CUDA OK |
| `PASS_WITH_WARNINGS` | Critical OK; optional missing and/or legacy path used |
| `FAIL` | Critical artifact missing, or PyTorch/CUDA unavailable |

**Exit criteria:** Run script; review `phase7e0_selected_paths.json`; proceed to 7E1 only on PASS / PASS_WITH_WARNINGS.

**Forbidden:** Training; AASIST downloads; creating `code/phase7/aasist/`; moving/copying artifacts.

---

## Phase 7E1 — Source integration + smoke test

**Prerequisite:** 7E0.5 `PASS` or `PASS_WITH_WARNINGS`.

| Deliverable | Location |
|-------------|----------|
| Integration package | `code/phase7/aasist/integration/` |
| Environment report | `audit/phase7e1_environment_check.*` |
| Source audit | `audit/phase7e1_aasist_source_audit.*` |
| Expected IO | `audit/phase7e1_expected_io_report.*` |
| Smoke test | `phase7e1_smoke_test/phase7e1_smoke_test_*` |

**Commands:** See [README.md](README.md) § Phase 7E1.

**Gate to 7E2:** Verified AASIST source present; smoke `PASS` or `PASS_IMPORT_ONLY` with documented config/checkpoint path for 7E3A.

**Forbidden:** Training; fake AASIST architecture; weight downloads in 7E1.

---

## Phase 7E2 — Dataset adapter

**Prerequisite:** 7E0.5 PASS + 7E1 reviewed.

| Deliverable | Location |
|-------------|----------|
| Builder script | `code/phase7/aasist/build_aasist_manifests.py` (TBD) |
| Lists | `manifests/` |
| Holdout report | `phase7e2_holdout_protection_report.md` |

**Exit criteria:** Zero 7A rows in train/val; labels per [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md).

---

## Phase 7E3A — Pretrained AASIST evaluation (before fine-tuning)

**Prerequisite:** 7E1 + 7E2 reviewed.

| Item | Rule |
|------|------|
| Checkpoint | Use an **available pretrained** AASIST anti-spoof checkpoint if usable (document source, license, path) |
| Fine-tuning | **Forbidden** in 7E3A |
| Datasets | Phase **7C1** full eval + Phase **7A** holdout |
| Outputs | Separate folder, e.g. `evaluation/pretrained_7e3a/` — **not** mixed with 7E3B |

**Reason:** Measure whether AASIST already improves **direct AI** before spending GPU time on 7E3B.

**Tasks:**

1. Run locked benchmark inference (same thresholds documented for all 7E3A runs).  
2. Score against [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md).  
3. If standalone or branch-only gates met → 7E3B may be **optional** (document decision).  

**Exit criteria:** `PHASE7E3A_PRETRAINED_EVAL_REPORT.md` with counts vs numeric gates.

**If no suitable pretrained checkpoint:** Document why in 7E3A report → only then proceed to 7E3B.

---

## Phase 7E3B — Fine-tuning (conditional)

**Prerequisite:** 7E3A complete **or** documented impossibility of pretrained eval.

| Deliverable | Location |
|-------------|----------|
| Training script | `train_aasist.py` (TBD) |
| Checkpoints | `models_saved/aasist_phase7e/` or `checkpoints/finetuned_7e3b/` |
| Run log | `phase7e3b_training_run.md` |

**Tasks:** Conservative fine-tune on 7E2 manifests; separate checkpoint prefix; never overwrite HybridResNet.

**Exit criteria:** Checkpoint ready for 7E4; manifest hash matches 7E2.

---

## Phase 7E4 — Evaluation

| Deliverable | Location |
|-------------|----------|
| Results | `evaluation/` (tag `pretrained_7e3a` vs `finetuned_7e3b`) |
| Comparison | `AASIST_BASELINE_COMPARISON.md`, `aasist_acceptance_matrix.csv` |

**Tasks:** Apply numeric gates in [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md); 7C1 + 7A; compare HybridResNet, 7C3-R2, 7C4-v2.

**Exit criteria:** Written **standalone** / **branch-only** / **reject** / **postpone**.

---

## Phase 7E5 — Fusion decision layer v3

**Prerequisite:** 7E4 accept or branch-only.

Combine **HybridResNet** (replay/mixer/partial) + **AASIST** (direct AI / synthetic per sign-off). Calibration only — no new training.

**Exit criteria:** Documented vs 7C4-v2 matrix; holdout check.

---

## Phase 7D resumption (after 7E)

Report generator / external demo only after 7E4/7E5 evidence sign-off.

---

## Phase 7F / WavLM (later)

After AASIST 7E4 decision if gaps remain.

---

## Related

- [PHASE7E0_DO_NOT_DO.md](PHASE7E0_DO_NOT_DO.md)  
- [../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md)
