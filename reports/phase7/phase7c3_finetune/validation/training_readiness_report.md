# Phase 7C3 Training Readiness

**Update this file after feature caches are built** (run `build_phase7c3_feature_cache.py` for each split).

---

## Phase 7C2 prerequisites

| Check | Status |
|-------|--------|
| Phase 7C2 validation | PASS (0 errors, 0 warnings) |
| Train rows | 1128 (1000 old + 128 7C1) |
| Val rows | 224 |
| Test rows | 232 |
| Phase 7A holdout overlap | 0 |

---

## Feature cache status

Run three cache builds, then check:

- `validation/feature_cache_validation_train.md`
- `validation/feature_cache_validation_val.md`
- `validation/feature_cache_validation_test.md`
- `validation/feature_cache_validation_report.md` (summary)

---

## Loss mask rules (training)

| Row type | use_origin_loss | use_attack_loss |
|----------|-----------------|-----------------|
| Old replay | **false** | true |
| Human replay/mixer | **true** (human=real) | true |
| Direct AI | true (ai=fake) | true |
| Partial 7C1 | true | true |

`use_manipulation_loss` — **not used** in Phase 7C3-v1 (no manipulation head).

---

## Checkpoint paths

| Role | Path |
|------|------|
| Base (read-only) | `models_saved/hybrid_resnet_environmental_best.pth` |
| Fine-tuned best | `reports/phase7/phase7c3_finetune/training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth` |

---

## Warning

**Do not accept** the fine-tuned checkpoint until:

1. Phase 7C1 before/after comparison improves target categories  
2. Phase 7A holdout does not collapse  
3. `before_after_comparison.md` reviewed  

Partial fabrication: use **chunk-level** 7C1 baseline runner for region metrics, not clip-level H5 eval alone.
