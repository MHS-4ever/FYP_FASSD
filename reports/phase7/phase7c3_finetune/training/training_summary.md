# Phase 7C3 Training Summary

- Base checkpoint (unchanged): `E:\FYP\models_saved\hybrid_resnet_environmental_best.pth`
- Train rows: 1128 | Val rows: 224
- Epochs run: 12 | Best epoch: **12**
- Best val loss: **3.0445**
- AMP: **False**

- val_loss: 3.0445205414933816
- val_origin_accuracy: 0.6379310344827587
- val_attack_accuracy: 0.4343891402714932
- val_human_clean_acceptance: 0.9433962264150944
- val_direct_ai_detection: 0.5242718446601942
- val_replay_detection: 0.35714285714285715
- val_partial_rows_count: 6

- Partial fabrication: clip-level cache only; region metrics via 7C1 baseline runner.
- Accept checkpoint only after Phase 7C1 + 7A holdout before/after review.
