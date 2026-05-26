# Phase 7C3 — Hybrid Fine-Tuning Plan

**Status:** Scripts ready — training/evaluation run manually  
**Prerequisite:** Phase 7C2 manifests signed off (train 1128 / val 224 / test 232)

---

## 1. Goal

Fine-tune **HybridResNetEnvironmental** from `models_saved/hybrid_resnet_environmental_best.pth` on Phase 7C2 data with sample weights and loss masks, then evaluate before/after on Phase 7C1 and Phase 7A holdout.

---

## 2. Inputs

| Input | Path |
|-------|------|
| Train manifest | `reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv` |
| Val manifest | `reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv` |
| Test manifest | `reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv` |
| Base checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` (read-only) |

---

## 3. Why fine-tuning is now allowed

- Phase 7C1 collected and baselined  
- Phase 7C2 manifests validated (0 errors)  
- Holdout protected  
- Balanced old subset (250/50/50) + weighted 7C1  

---

## 4. What model is trained

**HybridResNetEnvironmental** only — no architecture change.

- Binary head → **origin proxy** (human=0, ai|mixed=1)  
- Attack head → bonafide / synthesis / voice_conversion / replay  

---

## 5. What losses are used

```
total_loss = origin_loss + 0.5 * attack_loss
```

- Weighted `CrossEntropy` on masked rows  
- `sample_weight` from manifest  
- **No partial head** in v1  

---

## 6. What is not trained yet

- Separate **manipulation** head (`use_manipulation_loss` stored for future)  
- **Partial fabrication** direct supervision (evaluate via chunk baseline runner)  

---

## 7. Feature cache process

`build_phase7c3_feature_cache.py` — first **4 seconds** of each file, log-mel `[64,400]` + env `[12]`, HDF5 per split.

---

## 8. Training process

`train_phase7c3_hybrid.py` — freeze backbone 2 epochs, early stopping, saves:

- `training/checkpoints/hybrid_resnet_environmental_phase7c3_best.pth`  
- `training/checkpoints/hybrid_resnet_environmental_phase7c3_last.pth`  

**Never** overwrites base checkpoint.

---

## 9. Evaluation process

1. `evaluate_phase7c3_hybrid.py` on val/test H5  
2. `run_phase7c1_baseline.py` with fine-tuned ckpt  
3. `run_forensic_test_suite.py` on Phase 7A holdout  
4. `compare_phase7c3_before_after.py`  

---

## 10. Acceptance criteria

- Clean human **false alarms** decrease (7C1)  
- Direct AI **detection** improves  
- Partial fabrication detection **stable** (not large drop)  
- Human replay/mixer sensitivity **acceptable**  
- Phase 7A holdout **does not collapse**  

---

## 11. Failure criteria

- Increased clean human false alarms  
- Direct AI still 0/N at file level with no segment improvement  
- Holdout origin confusion spikes  
- Partial detection collapses  

---

## 12. Next step after training

Sign off checkpoint → document in Phase 7C → optional Phase 7D report layer tuning.
