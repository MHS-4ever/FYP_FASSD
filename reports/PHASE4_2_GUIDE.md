# Phase 4.2: Deep ResNet CNN Architecture

**Status:** Ready to train  
**Goal:** Improve upon 15.25% EER baseline with deeper architecture

---

## 🏗️ Architecture Improvements

### Baseline LCNN vs Deep ResNet CNN

| Aspect | Baseline LCNN | Deep ResNet CNN |
|--------|---------------|-----------------|
| **Layers** | 3 conv blocks | 4 residual layers (8 blocks) |
| **Parameters** | ~5K | ~500K |
| **Skip Connections** | ❌ None | ✅ ResNet-style |
| **Capacity** | 16→32→64 | 32→64→128→256 |
| **Regularization** | None | Dropout (0.3) + Weight Decay |
| **Learning Rate** | Fixed | Adaptive (ReduceLROnPlateau) |

### Key Features

1. **Residual Blocks**: Skip connections prevent vanishing gradients in deeper networks
2. **Increased Capacity**: 256-dimensional features vs 64 in baseline
3. **Better Regularization**: Dropout + L2 weight decay prevent overfitting
4. **Adaptive Learning**: Learning rate reduces when validation plateaus
5. **He Initialization**: Proper weight initialization for ReLU activations

---

## 📊 Expected Improvements

### Target Performance

| Metric | Baseline (Mel) | Target (ResNet) | Improvement |
|--------|----------------|-----------------|-------------|
| Clean EER | 9.69% | < 9.0% | -0.7% |
| Aug EER | 15.25% | **< 13.0%** | **-2.25%** |
| Clean AUC | 0.966 | > 0.970 | +0.004 |
| Aug AUC | 0.926 | > 0.935 | +0.009 |

### Why It Should Work

1. **More Feature Abstraction**: Deeper layers capture complex patterns
2. **Skip Connections**: Preserve low-level features while learning high-level ones
3. **Better Generalization**: Regularization prevents overfitting seen in shallow models
4. **Longer Training**: 15 epochs vs 10 allows better convergence

---

## 🚀 Training Instructions

### Step 1: Test the Model Architecture

```bash
python models/resnet_cnn.py
```

Expected output:
- Model summary
- Parameter count (~500K parameters)
- Test forward pass successful

### Step 2: Train on Clean Data (Optional - for comparison)

```bash
python train_resnet.py --manifest E:\FYP\data\features\features_manifest_labeled.csv --feature_type mel --epochs 15 --batch_size 128 --save E:\FYP\models_saved\resnet_cnn_mel.pth
```

**Training Time:** ~2 hours (**75% faster** with optimizations)  
**Expected Val EER:** < 9%

### Step 3: Train Robust Model (RECOMMENDED)

```bash
python train_resnet.py --manifest E:\FYP\data\features_merged\features_manifest_combined.csv --feature_type mel --epochs 15 --batch_size 128 --save E:\FYP\models_saved\resnet_cnn_mel_robust.pth
```

**Training Time:** ~3-4 hours (**75% faster** with optimizations)  
**Expected Val EER:** < 13%

**Note:** Uses optimized quick evaluation (15% of val set per epoch) with full validation every 5 epochs.

---

## ⚙️ Training Configuration

### Hyperparameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| **Batch Size** | 128 | Reduced for deeper model (GPU memory) |
| **Learning Rate** | 0.001 | Standard Adam starting point |
| **Weight Decay** | 0.0001 | L2 regularization |
| **Dropout** | 0.3 | Prevent overfitting |
| **Epochs** | 15 | Longer training for convergence |
| **Optimizer** | AdamW | Adam with decoupled weight decay |
| **LR Scheduler** | ReduceLROnPlateau | Adaptive learning rate |

### Memory Requirements

- **Training**: ~4.5GB VRAM (batch_size=128)
- **Inference**: ~1GB VRAM
- **Model Size**: ~2MB on disk

---

## 📈 Monitoring Training

### What to Watch

1. **Training Loss**: Should decrease smoothly (target: < 0.25)
2. **Validation EER**: Should decrease below 13% by epoch 10-12
3. **Learning Rate**: Will reduce automatically if EER plateaus
4. **Overfitting**: Train loss much lower than val EER indicates overfitting

### Expected Training Curve

```
Epoch 01: Loss 0.48 | EER 18-20% (initialization)
Epoch 03: Loss 0.36 | EER 15-17% (learning features)
Epoch 05: Loss 0.31 | EER 13-15% (approaching baseline)
Epoch 08: Loss 0.27 | EER 11-13% (beating baseline)
Epoch 12: Loss 0.24 | EER 10-12% (target achieved)
Epoch 15: Loss 0.22 | EER 9-11% (convergence)
```

---

## 🔍 Evaluation After Training

### Evaluate Robust Model

```bash
python evaluate_model.py --ckpt E:\FYP\models_saved\resnet_cnn_mel_robust.pth --model_type resnet --feature_type mel --output_csv E:\FYP\reports\logs\evaluation_resnet_robust.csv
```

**Note:** `evaluate_model.py` (renamed from `evaluate_baseline.py`) now supports both baseline and ResNet models via `--model_type` flag.

### Create Comparison Report

After evaluation, compare:
- Baseline Mel: 15.25% EER
- ResNet Mel: TBD

---

## 🛠️ Troubleshooting

### Issue: CUDA Out of Memory

**Solution**: Reduce batch size
```bash
python train_resnet.py --batch_size 96 ...
```

### Issue: Training too slow

**Solution**: Reduce num_workers if disk I/O is bottleneck
```bash
python train_resnet.py --num_workers 4 ...
```

### Issue: Overfitting (val EER increases)

**Solutions**:
1. Increase dropout: `--dropout 0.4`
2. Increase weight decay: `--weight_decay 5e-4`
3. Early stopping (model saves best automatically)

### Issue: Underfitting (val EER not improving)

**Solutions**:
1. Train longer: `--epochs 20`
2. Increase learning rate: `--lr 2e-3`
3. Reduce regularization: `--dropout 0.2 --weight_decay 5e-5`

---

## 📁 Output Files

After training, you'll have:

```
E:\FYP\
├── models_saved\
│   ├── resnet_cnn_mel.pth           # Clean model (optional)
│   └── resnet_cnn_mel_robust.pth    # Robust model (main)
├── reports\
│   ├── figures\
│   │   └── learning_curves_resnet_mel.png
│   └── logs\
│       └── evaluation_resnet_robust.csv
```

---

## 🎯 Success Criteria

Phase 4.2 is successful if:

- ✅ Model trains without errors
- ✅ Validation EER < 13% (beats 15.25% baseline)
- ✅ Clean test EER < 10%
- ✅ Augmented test EER < 14%
- ✅ No severe overfitting (train-val gap reasonable)

---

## 🚧 Next Steps After Phase 4.2

If successful:
1. **Phase 4.3**: Environmental features for replay detection
2. **Phase 4.4**: Multi-task learning (3-way classification)

If not meeting targets:
1. Try attention mechanisms
2. Implement AASIST architecture
3. Ensemble multiple models

---

**Ready to train?** Run the command and monitor the results! 🚀

