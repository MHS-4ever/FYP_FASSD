# Phase 4: Hybrid Model Training

**Status**: ⏳ **IN PROGRESS**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3-4  
**Dependencies**: Phase 2 (Feature Extraction) ✅ COMPLETE, Phase 3 (Hybrid Architecture) ✅ COMPLETE  
**Completion Date**: December 2025

---

## 🎯 Quick Start

This folder contains scripts for training the hybrid ResNet-Environmental model on the unified dataset with speaker-independent splits.

**To train the hybrid model:**

```bash
python code/phase4/train_hybrid_model.py
```

**To run all Phase 4 steps:**

```bash
python code/phase4/run_phase4.py
```

---

## 📁 Scripts in This Folder

| Script                      | Purpose                                    | When to Use                          |
| --------------------------- | ------------------------------------------ | ------------------------------------ |
| `train_hybrid_model.py`     | Main training script                       | Run to train the hybrid model        |
| `hybrid_dataset.py`         | Dataset class for hybrid features          | Import in training scripts           |
| `run_phase4.py`             | Run all Phase 4 steps                      | Run to execute training in sequence  |
| `README.md`                 | This documentation                         | Reference for using Phase 4 scripts  |

---

## 🔧 Step-by-Step Usage

### Prerequisites

Before running Phase 4, ensure:

1. ✅ **Phase 2 Complete**: Features extracted and packed to HDF5
   - `data/features/logmel_packed.h5` exists
   - `data/features/environmental_packed.h5` exists
   - `data/features/features_manifest_unified.csv` exists (with feature indices)

2. ✅ **Phase 3 Complete**: Hybrid architecture implemented and tested
   - `code/phase3/hybrid_resnet_environmental.py` exists
   - `code/phase3/multi_task_loss.py` exists

3. ✅ **Speaker-Independent Splits**: Training splits created (Phase 1)
   - `data/manifests/train_speaker_independent.csv` exists
   - `data/manifests/val_speaker_independent.csv` exists

**Important**: The training manifests need to have `spectrogram_idx` and `environmental_idx` columns. If your speaker-independent splits don't have these, you need to merge them with `features_manifest_unified.csv`.

### Step 1: Prepare Manifests with Feature Indices

If your speaker-independent split manifests don't have feature indices, merge them with the features manifest:

```python
import pandas as pd

# Load speaker-independent split
train_split = pd.read_csv('data/manifests/train_speaker_independent.csv')

# Load features manifest with indices
features_manifest = pd.read_csv('data/features/features_manifest_unified.csv')

# Merge on filepath (or unique identifier)
train_with_features = train_split.merge(
    features_manifest[['filepath', 'spectrogram_idx', 'environmental_idx']],
    on='filepath',
    how='inner'
)

# Save merged manifest
train_with_features.to_csv('data/manifests/train_speaker_independent_with_features.csv', index=False)
```

Alternatively, you can use `features_manifest_unified.csv` directly and filter by speaker_id to create splits.

### Step 2: Train Hybrid Model

Run the training script with default settings:

```bash
python code/phase4/train_hybrid_model.py
```

**Customize training parameters:**

```bash
python code/phase4/train_hybrid_model.py \
    --train_manifest data/manifests/train_speaker_independent_with_features.csv \
    --val_manifest data/manifests/val_speaker_independent_with_features.csv \
    --epochs 20 \
    --batch_size 128 \
    --lr 1e-3 \
    --binary_weight 0.7 \
    --multiclass_weight 0.3
```

**Key arguments:**

- `--train_manifest`: Path to training manifest CSV (must have `spectrogram_idx`, `environmental_idx`, `label`, `attack_type`)
- `--val_manifest`: Path to validation manifest CSV
- `--spectrogram_h5`: Path to spectrogram HDF5 file (default: `data/features/logmel_packed.h5`)
- `--environmental_h5`: Path to environmental HDF5 file (default: `data/features/environmental_packed.h5`)
- `--epochs`: Number of training epochs (default: 20)
- `--batch_size`: Batch size (default: 128, adjust based on GPU memory)
- `--lr`: Initial learning rate (default: 1e-3)
- `--binary_weight`: Weight for binary classification loss (default: 0.7)
- `--multiclass_weight`: Weight for multiclass classification loss (default: 0.3)
- `--eval_subset`: Fraction of validation set for quick eval (default: 0.15 = 15%)
- `--full_eval_interval`: Full validation every N epochs (default: 5)

**Expected Output:**

```
[GPU] Using device: cuda (CUDA available: True)

[DATA] Loading training manifest: data/manifests/train_speaker_independent_with_features.csv
[DATA] Training samples: 1,515,135
[DATA] Training label distribution:
label
spoof      1439376
bonafide     75759
Name: count, dtype: int64

[SCALER] Loading environmental scaler from: models_saved/environment_scaler.pkl

[LOADER] Initializing datasets...
[HYBRID DATASET] Initialized with 1,515,135 samples
[HYBRID DATASET] Spectrogram HDF5: data/features/logmel_packed.h5
[HYBRID DATASET] Environmental HDF5: data/features/environmental_packed.h5
[HYBRID DATASET] Using environmental scaler

[CLASS WEIGHTS] Computing class weights...
[CLASS WEIGHTS] Binary weights: [10.0, 0.527]
[CLASS WEIGHTS] Multiclass weights: [0.526, 0.702, 1.052, 2.104]

[MODEL] Hybrid ResNet-Environmental initialized
[INFO] Total parameters: 2,902,822
[INFO] Trainable parameters: 2,902,822

[TRAIN] Starting training...
[INFO] Quick eval on 15% of validation set per epoch
[INFO] Full validation every 5 epochs

Epoch 01/20 [Training]: 100%|██████████| 11837/11837 [45:23<00:00, loss=0.8234, b_loss=0.6234, mc_loss=0.2000]
[METRICS] [QUICK] Epoch 01 | TrainLoss 0.8234 (B:0.6234, MC:0.2000) | ValEER 12.34% | AUC 0.923 | BinaryAcc 88.12% | MulticlassAcc 76.45% | LR 1.00e-03
         Binary CM: TN=18954, FP=1205, FN=3567, TP=24567
[SAVE] Best model saved (EER 12.34%) -> models_saved/hybrid_resnet_environmental.pth

...

[OK] Training complete.
[RESULTS] Best validation EER: 8.76% (epoch 15)
[SAVE] Checkpoint saved at: models_saved/hybrid_resnet_environmental.pth

[LOG] Training metrics saved -> reports/logs/training_hybrid_model.csv
[PLOT] Learning curves saved -> reports/figures/learning_curves_hybrid.png
```

**Training Time:**

- Per epoch: ~30-45 minutes (for ~1.5M training samples, batch_size=128)
- Total (20 epochs): ~10-15 hours (with quick eval)

### Step 3: Run All Phase 4 Steps (Orchestrator)

Run all steps using the orchestrator:

```bash
python code/phase4/run_phase4.py
```

**Options:**

```bash
# Skip training (if already trained)
python code/phase4/run_phase4.py --skip-training

# Only run training
python code/phase4/run_phase4.py --train-only
```

---

## 📊 Expected Results

### Training Metrics

**Target Performance:**

| Metric                    | ASVspoof Domain | Real-world Domain | Overall |
| ------------------------- | --------------- | ----------------- | ------- |
| Binary EER                | < 5%            | < 20%             | < 10%   |
| Binary AUC                | > 0.98          | > 0.85            | > 0.95  |
| Binary Accuracy           | > 95%           | > 80%             | > 90%   |
| Multiclass Accuracy       | > 90%           | N/A               | > 85%   |

**Key Metric**: Real-world domain EER < 20% (critical requirement)

### Output Files

After training, you should have:

```
models_saved/
└── hybrid_resnet_environmental.pth       # Best model checkpoint

reports/
├── logs/
│   └── training_hybrid_model.csv         # Training metrics (CSV)
└── figures/
    └── learning_curves_hybrid.png        # Learning curves (plot)
```

---

## ✅ Success Criteria Checklist

After running training, verify:

- [ ] Model trains successfully (loss decreases over epochs)
- [ ] Both tasks learn (binary + multiclass losses decrease)
- [ ] Validation EER < 10% on ASVspoof domain
- [ ] Validation EER < 20% on Real-world domain (KEY METRIC)
- [ ] No overfitting (train/val loss gap reasonable)
- [ ] Best model checkpoint saved
- [ ] Training metrics logged to CSV
- [ ] Learning curves generated
- [ ] Both binary and multiclass accuracies improve

---

## 🐛 Troubleshooting

### Issue: FileNotFoundError: Manifest not found

**Error Message:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'data/manifests/train_speaker_independent.csv'
```

**Solution:**

1. Ensure Phase 1 is complete and speaker-independent splits exist
2. Check that manifest paths are correct
3. If using feature indices, merge manifests as described in Step 1

---

### Issue: KeyError: 'spectrogram_idx' or 'environmental_idx'

**Error Message:**

```
KeyError: 'spectrogram_idx'
```

**Solution:**

1. Your manifest doesn't have feature indices
2. Merge with `features_manifest_unified.csv` as shown in Step 1
3. Or use `features_manifest_unified.csv` directly and filter by speaker splits

---

### Issue: CUDA out of memory

**Error Message:**

```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Solution:**

1. Reduce batch size: `--batch_size 64` (or lower)
2. Reduce number of workers: `--num_workers 4`
3. Use gradient accumulation (requires code modification)
4. Close other GPU-using applications

---

### Issue: No module named 'phase3'

**Error Message:**

```
ModuleNotFoundError: No module named 'phase3'
```

**Solution:**

1. Ensure Phase 3 is complete
2. Check that `code/phase3/hybrid_resnet_environmental.py` exists
3. Run from project root directory (`E:\FYP`)
4. Verify import paths in `train_hybrid_model.py`

---

### Issue: Training loss is NaN

**Error Message:**

```
loss=nan
```

**Solution:**

1. Check input data for NaN/Inf values
2. Reduce learning rate: `--lr 1e-4`
3. Enable gradient clipping (requires code modification)
4. Check class weights (may be too extreme)
5. Verify environmental scaler is properly fitted

---

### Issue: Slow training

**Problem**: Training is very slow (hours per epoch)

**Solution:**

1. Use quick eval mode (default: 15% of validation set)
2. Increase `--eval_subset` to 0.1 (10%) for faster epochs
3. Increase `--full_eval_interval` to 10 (full eval every 10 epochs)
4. Reduce batch size if causing memory issues
5. Increase `--num_workers` if I/O bound (but test first)

---

### Issue: Poor performance on Real-world domain

**Problem**: Model performs well on ASVspoof but poorly on Real-world

**Solution:**

1. Ensure 50/50 mix of ASVspoof and Real-world in training data
2. Monitor per-domain metrics during training (requires code modification)
3. Adjust loss weights (`--binary_weight`, `--multiclass_weight`)
4. Consider Phase 7 (Domain Adaptation) if needed
5. Check data quality and feature extraction

---

### Issue: Multiclass accuracy not improving

**Problem**: Binary accuracy improves but multiclass stays low

**Solution:**

1. Increase multiclass loss weight: `--multiclass_weight 0.5`
2. Check class weights for multiclass (may need adjustment)
3. Verify attack_type labels are correct in manifest
4. Monitor both losses separately during training
5. Consider class imbalance in attack types

---

## 📝 Notes

- **Training is time-consuming**: Plan for 10-15 hours total training time
- **GPU required**: Training on CPU is not recommended (will be extremely slow)
- **Monitor training**: Watch for loss decreasing and metrics improving
- **Save checkpoints**: Best model is saved automatically, but consider periodic saves
- **Key metric**: Real-world domain EER < 20% is the critical requirement
- **Per-domain analysis**: Currently per-domain metrics are not computed automatically, may need code modification

---

## 🔗 Dependencies

**Prerequisites:**

- ✅ Phase 1: Unified Dataset Preparation (speaker-independent splits)
- ✅ Phase 2: Feature Extraction (HDF5 files with features)
- ✅ Phase 3: Hybrid Architecture (model code)

**Required Python Packages:**

- `torch`, `torchvision` - PyTorch
- `h5py` - HDF5 file operations
- `pandas`, `numpy` - Data processing
- `tqdm` - Progress bars
- `matplotlib` - Plotting
- `sklearn` - Scaler and metrics
- All dependencies listed in `requirements.txt`

**Next Phase:**

- Phase 5: Evaluation (evaluate trained model on test set)

---

## 🔍 Training Verification Checklist

Before starting training, verify:

- [ ] HDF5 files exist and are accessible
- [ ] Manifests have required columns (spectrogram_idx, environmental_idx, label, attack_type)
- [ ] Phase 3 model code is available and tested
- [ ] GPU is available and has sufficient memory
- [ ] Training data is properly balanced (50/50 ASVspoof/Real-world ideally)
- [ ] Environmental scaler exists or can be created

---

## 📈 Monitoring Training

During training, monitor:

1. **Loss values**: Should decrease over epochs
   - Total loss should decrease
   - Both binary and multiclass losses should decrease

2. **Validation EER**: Should decrease (lower is better)
   - Target: < 10% overall
   - Real-world domain: < 20% (critical)

3. **AUC**: Should increase (higher is better)
   - Target: > 0.95 overall

4. **Accuracy**: Should increase
   - Binary accuracy: > 90%
   - Multiclass accuracy: > 85%

5. **Learning rate**: Should decrease when scheduler triggers
   - Should reduce when validation EER plateaus

6. **Confusion matrices**: Check per-class performance
   - Binary: Check TN, FP, FN, TP
   - Multiclass: Check per attack type accuracy

---

**Last Updated**: December 2025  
**Status**: ⏳ **IN PROGRESS**

