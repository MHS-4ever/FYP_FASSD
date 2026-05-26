# Phase 7E — AASIST integration (`code/phase7/aasist/`)

**Status:** Phase **7E2 + 7E3A** — dataset adapter + pretrained evaluation  
**Training:** **Not in this folder** (7E3B fine-tune only after 7E3A review)

---

## Purpose

Integrate a **verified** upstream AASIST anti-spoofing implementation as an **evidence branch** for FASSD. This package does **not** implement AASIST architecture from scratch.

Planning docs: [reports/phase7/phase7e_aasist_experiment/](../../../reports/phase7/phase7e_aasist_experiment/README.md)

---

## Official source

Upstream AASIST lives at:

- `code/phase7/aasist/vendor/AASIST/`

Default eval variant: **AASIST-L** (`config/AASIST-L.conf`, `models/weights/AASIST-L.pth`).

**Class convention (7E3A):**

| Index | Training label | Meaning |
|-------|----------------|---------|
| 0 | spoof | `softmax[:, 0]` used as **spoof_score** (higher = more forensic risk) |
| 1 | bonafide | Official `produce_evaluation_file` uses `logits[:, 1]` (higher = more bonafide) |

---

## Phase 7E2 + 7E3A scripts

| Script | Role |
|--------|------|
| `integration/build_aasist_eval_manifest.py` | Normalize 7C1/7A manifests |
| `integration/run_aasist_pretrained_eval.py` | Pretrained AASIST-L inference |
| `integration/analyze_aasist_pretrained_eval.py` | Metrics vs Phase 7E0 gates |
| `integration/compare_aasist_with_hybrid.py` | vs HybridResNet + 7C4-v2 |
| `integration/aasist_eval_common.py` | Shared load/window/score helpers |

Full commands: [phase7e_aasist_experiment README](../../../reports/phase7/phase7e_aasist_experiment/README.md).

---

## Outputs

| Path | Content |
|------|---------|
| `reports/.../phase7e2_dataset_adapter/` | Eval manifests + validation MD |
| `reports/.../phase7e3a_pretrained_eval/phase7c1/` | `aasist_l_predictions.csv`, analysis, timelines |
| `reports/.../phase7e3a_pretrained_eval/phase7a/` | Holdout predictions + analysis |
| `reports/.../phase7e3a_pretrained_eval/comparison/` | vs Hybrid comparison + recommendation |

---

## Phase 7E1 (complete)

Smoke test and audit scripts remain in `integration/` — see [PHASE7E1_AASIST_INTEGRATION_PLAN.md](../../../reports/phase7/phase7e_aasist_experiment/PHASE7E1_AASIST_INTEGRATION_PLAN.md).

---

## Do not

- Train or fine-tune from this phase without explicit 7E3B gate  
- Modify `vendor/AASIST/` upstream source  
- Treat pretrained AASIST-L as product-final without 7E0 acceptance pass
