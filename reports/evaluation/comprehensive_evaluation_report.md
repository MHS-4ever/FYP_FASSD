# Phase 5: Comprehensive Evaluation Report

- Generated: 2025-12-27T16:15:33
- Checkpoint: `models_saved/hybrid_resnet_environmental_best.pth`
- Test manifest: `data/manifests/test_speaker_independent.csv`
- Spectrogram H5: `D:/FYP/data/features/logmel_chunked.h5`
- Environmental H5: `D:/FYP/data/features/environmental_packed.h5`
- Batch size: 128

## Speaker Overlap Check

- Overlap count: **0**
- Example IDs: `[]`

## Overall (Test)

- Samples: **254574**
- Binary EER: **16.22%**
- Binary AUC: **0.9167**
- Binary Accuracy (@0.5): **89.78%**
- Multiclass Accuracy: **64.36%**

## ASVspoof (Test)

- Samples: **237490**
- Binary EER: **18.15%**
- Binary AUC: **0.8947**

## RealWorld (Test)

- Samples: **17084**
- Binary EER: **16.14%**
- Binary AUC: **0.9236**

## Multiclass (Attack Type) Classification Report (Overall)

```text
              precision    recall  f1-score   support

    bonafide     0.6984    0.6105    0.6515     39737
   synthesis     0.1631    0.5160    0.2479     22192
  conversion     0.7992    0.8852    0.8400     90585
      replay     0.9727    0.4699    0.6336    102060

    accuracy                         0.6436    254574
   macro avg     0.6583    0.6204    0.5933    254574
weighted avg     0.7975    0.6436    0.6762    254574

```

## Saved Figures

- `confusion_matrices/overall_binary_cm.png`
- `confusion_matrices/overall_multiclass_cm.png`
- `figures/roc_overall.png`
- `figures/roc_asvspoof.png`
- `figures/roc_realworld.png`
