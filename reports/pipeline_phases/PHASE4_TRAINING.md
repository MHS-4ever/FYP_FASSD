# Phase 4: Hybrid Model Training

**Status**: ⏳ PENDING  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3-4  
**Dependencies**: Phase 3 (Hybrid Architecture), Phase 2 (Feature Extraction)

---

## 🎯 Objective

Train the hybrid model on mixed data (50% ASVspoof + 50% Real-world) with speaker-independent splits, monitoring both binary and multiclass performance across domains.

---

## 📋 Tasks

### 1. Prepare Training Data

**Data Loading:**

- Use unified manifest with speaker-independent splits
- Load both spectrogram and environmental features
- Mix: 50% ASVspoof + 50% Real-world (stratified)
- Ensure both domains in train/val/test

**DataLoader Configuration:**

- Batch size: 128 (adjust based on GPU memory)
- Workers: 4-8 (for parallel loading)
- Shuffle: True (training), False (validation/test)
- Pin memory: True (for GPU transfer)

**Class Weighting:**

- Compute class weights for imbalanced data
- Apply to both binary and multiclass losses
- Bonafide weight: ~13.5 (based on 95/5 split)

### 2. Training Configuration

**Optimizer:**

- Type: AdamW
- Learning rate: 1e-3 (initial)
- Weight decay: 1e-4
- Beta1: 0.9, Beta2: 0.999

**Learning Rate Scheduler:**

- Type: ReduceLROnPlateau
- Factor: 0.5
- Patience: 3 epochs
- Min LR: 1e-6

**Training Strategy:**

- Epochs: 20 (with early stopping if needed)
- Mixed precision: FP16 (for speed)
- Gradient clipping: 1.0 (if needed)

**Loss Weights:**

- Binary loss weight (α): 0.7
- Multiclass loss weight (β): 0.3
- Adjust based on task importance

### 3. Training Loop

**Per Epoch:**

1. Train on training set
2. Validate on validation set
3. Monitor metrics:
   - Binary EER, AUC, Accuracy
   - Multiclass Accuracy (attack type)
   - Per-domain performance (ASVspoof vs Real-world)
   - Loss values (total, binary, multiclass)

**Evaluation Strategy:**

- Quick eval: 15% of validation set (every epoch)
- Full eval: 100% of validation set (every 5 epochs)
- Save best model based on validation EER (both domains)

**Checkpointing:**

- Save best model (lowest validation EER)
- Save every 5 epochs (for recovery)
- Include optimizer state, epoch, metrics

### 4. Monitoring & Logging

**Metrics to Track:**

- Training loss (total, binary, multiclass)
- Validation EER (binary)
- Validation AUC (binary)
- Validation Accuracy (binary + multiclass)
- Per-domain EER (ASVspoof domain, Real-world domain)
- Learning rate
- Confusion matrices

**Logging:**

- Console output (progress bars, metrics)
- TensorBoard logs (optional)
- CSV logs (metrics per epoch)
- Learning curves (plots)

---

## 📁 Output Files

```
models_saved/
└── hybrid_resnet_environmental.pth       # Best model checkpoint

reports/
├── logs/
│   └── training_hybrid_model.csv         # Training metrics
└── figures/
    └── learning_curves_hybrid.png       # Learning curves
```

---

## 🔧 Scripts Needed

### To Create:

- `Code/train_hybrid_model.py` - Main training script
- `Code/datasets/hybrid_dataset.py` - Dataset class for hybrid features

### Existing (Reuse):

- ✅ `Code/utils/evaluation.py` - Evaluation metrics
- ✅ `Code/utils/confusion.py` - Confusion matrix

---

## ✅ Success Criteria

- [ ] Model trains successfully (loss decreases)
- [ ] Both tasks (binary + multiclass) learn
- [ ] Validation EER < 10% on ASVspoof domain
- [ ] Validation EER < 20% on Real-world domain (KEY METRIC)
- [ ] No overfitting (train/val loss gap reasonable)
- [ ] Best model checkpoint saved
- [ ] Training metrics logged

---

## 📊 Expected Performance

**Target Metrics:**

```
Metric                    | ASVspoof Domain | Real-world Domain | Overall
--------------------------|-----------------|-------------------|----------
Binary EER                | < 5%            | < 20%             | < 10%
Binary AUC                | > 0.98          | > 0.85            | > 0.95
Binary Accuracy           | > 95%           | > 80%             | > 90%
Multiclass Accuracy       | > 90%           | N/A               | > 85%
```

**Training Time (Estimated):**

- Per epoch: ~30-45 minutes (for 1.1M training samples)
- Total (20 epochs): ~10-15 hours

---

## ⚠️ Challenges & Solutions

### Challenge 1: Domain Mismatch

**Problem**: Model may perform well on ASVspoof but poorly on Real-world  
**Solution**:

- Ensure 50/50 mix in training
- Monitor per-domain metrics
- Adjust loss weights if needed
- Consider domain adaptation (Phase 7)

### Challenge 2: Multi-Task Balance

**Problem**: Binary task may dominate multiclass task  
**Solution**:

- Adjust loss weights (α, β)
- Monitor both tasks separately
- Balance task importance

### Challenge 3: Class Imbalance

**Problem**: 95% fake, 5% real  
**Solution**:

- Use class weighting
- Monitor per-class metrics
- Ensure both classes in validation set

### Challenge 4: Training Stability

**Problem**: Training may be unstable with two branches  
**Solution**:

- Proper initialization
- Gradient clipping
- Learning rate scheduling
- Consider freezing one branch initially

---

## 🔗 Dependencies

**Prerequisites:**

- ✅ Phase 2: Feature Extraction (need features)
- ✅ Phase 3: Hybrid Architecture (need model)

**Next Phase:**

- Phase 5: Evaluation (requires trained model)

---

## 📝 Notes

- **KEY METRIC**: Real-world domain EER < 20% (this is the critical requirement)
- Monitor per-domain performance throughout training
- If Real-world performance is poor, may need Phase 7 (Domain Adaptation)
- Keep training logs for analysis
- Document any training issues or adjustments

---

## 🔍 Training Verification Checklist

- [ ] Data loads correctly (both feature types)
- [ ] Model forward pass works
- [ ] Loss decreases over epochs
- [ ] Both tasks learn (binary + multiclass)
- [ ] No NaN or Inf in loss
- [ ] GPU utilization good (>80%)
- [ ] Checkpoint saves/loads correctly
- [ ] Validation metrics improve

---

**Last Updated**: [Date]  
**Status**: ⏳ PENDING
