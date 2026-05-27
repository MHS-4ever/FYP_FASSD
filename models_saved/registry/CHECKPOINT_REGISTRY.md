# Model Checkpoint Registry

**Generated:** 2026-05-27T19:55:20.904097+00:00
**Models root:** `E:\FYP\models_saved`

Original experiment paths are preserved. This registry documents **copies** only.

## 1. Active Product/Evidence Checkpoints

| asset_id | action | target | sha256 (prefix) | size_mb |
| --- | --- | --- | --- | --- |
| hybrid_resnet_environmental_best | copied | `hybrid_resnet_environmental_best.pth` | `52dcf67f5e20137e…` | 33.36 |

## 2. Prototype Evidence Checkpoints

| asset_id | action | target | sha256 (prefix) | size_mb |
| --- | --- | --- | --- | --- |
| phase7c3_r2_best_product | copied | `phase7c3_r2_best_product_rejected_standalone.pth` | `de827350aeaeef89…` | 11.146 |
| phase7c3_r2_best_loss | copied | `phase7c3_r2_best_loss_rejected_standalone.pth` | `008e48aa69bd5718…` | 11.145 |

## 3. Pretrained Reference Checkpoints

| asset_id | action | target | sha256 (prefix) | size_mb |
| --- | --- | --- | --- | --- |
| aasist_l_official_pretrained | copied | `aasist_l_official_pretrained_reference.pth` | `814331d088032bb4…` | 0.407 |
| aasist_official_pretrained | copied | `aasist_official_pretrained_reference.pth` | `51d2d9cf0738172f…` | 1.222 |

## 4. Rejected Archive Checkpoints

| asset_id | action | target | sha256 (prefix) | size_mb |
| --- | --- | --- | --- | --- |
| aasist_l_phase7e3c_best_product | copied | `aasist_l_phase7e3c_best_product_rejected.pth` | `a3211b4663d3bf0b…` | 0.409 |
| aasist_l_phase7e3c_best_loss | copied | `aasist_l_phase7e3c_best_loss_rejected.pth` | `d085feefbb522a62…` | 0.408 |

## 5. Missing / Warnings

_None._

## 6. Usage Rules

- Only `models_saved/active/` is allowed for the current production/evidence pipeline by default.
- `prototype_evidence/` may be used only to reproduce Phase 7C4-v2 prototype results.
- `pretrained_reference/` is reference only (AASIST rejected as current solution).
- `rejected_archive/` must **not** be used in product decisions.
- Do not treat HybridResNet as a final forensic classifier.
- Phase 8 must use multi-axis evidence fusion, not binary fake/real classification alone.
