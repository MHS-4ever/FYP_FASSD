# Phase 7E3C — AASIST-L Fine-Tune Training Summary

**Generated:** 2026-05-26T21:59:13.647462+00:00

## Run config

```json
{
  "train_manifest": "E:\\FYP\\reports\\phase7\\phase7e_aasist_experiment\\phase7e3b_finetune_prep\\aasist_train_manifest.csv",
  "val_manifest": "E:\\FYP\\reports\\phase7\\phase7e_aasist_experiment\\phase7e3b_finetune_prep\\aasist_val_manifest.csv",
  "aasist_src": "E:\\FYP\\code\\phase7\\aasist\\vendor\\AASIST",
  "config_path": "E:\\FYP\\code\\phase7\\aasist\\vendor\\AASIST\\config\\AASIST-L.conf",
  "base_checkpoint": "E:\\FYP\\code\\phase7\\aasist\\vendor\\AASIST\\models\\weights\\AASIST-L.pth",
  "output_dir": "E:\\FYP\\reports\\phase7\\phase7e_aasist_experiment\\phase7e3c_finetune\\training",
  "device": "cuda",
  "batch_size": 8,
  "num_workers": 0,
  "epochs": 10,
  "lr": 2e-06,
  "weight_decay": 0.0001,
  "balanced_sampler": true,
  "use_sample_weight": true,
  "class_balanced_loss": false,
  "amp": false,
  "freeze_frontend_epochs": 0,
  "patience": 4,
  "limit_train": null,
  "limit_val": null,
  "random_seed": 42,
  "grad_clip": 1.0,
  "disable_progress": false
}
```

## Checkpoint load

```json
{
  "status": "loaded",
  "base_checkpoint": "E:\\FYP\\code\\phase7\\aasist\\vendor\\AASIST\\models\\weights\\AASIST-L.pth",
  "missing_keys_count": 0,
  "unexpected_keys_count": 0,
  "missing_keys_sample": [],
  "unexpected_keys_sample": []
}
```

## Best checkpoints

- **best_loss:** `E:\FYP\reports\phase7\phase7e_aasist_experiment\phase7e3c_finetune\training\checkpoints\aasist_l_phase7e3c_best_loss.pth`
- **best_product:** `E:\FYP\reports\phase7\phase7e_aasist_experiment\phase7e3c_finetune\training\checkpoints\aasist_l_phase7e3c_best_product.pth`

## Notes

- Default design uses **balanced sampler + sample weights**, with **class-balanced loss disabled** unless explicitly enabled.
- Product score heavily penalizes clean-human false alarms.
- Classifier logits taken from `model(x)[-1]` (official AASIST tuple output).

## Warnings

- early_stopping: no product improvement for 4 epochs

