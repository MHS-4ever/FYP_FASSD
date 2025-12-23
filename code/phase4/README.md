# Phase 4: Hybrid Model Training

**Status**: ✅ **READY**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3-4  
**Dependencies**: Phase 3 (Hybrid Architecture) ✅ COMPLETE, Phase 2 (Feature Extraction) ✅ COMPLETE  
**Completion Date**: December 2025

---

## 🎯 Quick Start

This folder contains scripts for training the hybrid ResNet-Environmental model on mixed data (50% ASVspoof + 50% Real-world) with speaker-independent splits.

**To start training:**

```bash
python code/phase4/run_phase4.py
```

**To train with custom settings:**

```bash
python code/phase4/train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 64 --epochs 20 --num_workers 8
```

---

## 📁 Scripts in This Folder

| Script                           | Purpose                   | When to Use                          |
| -------------------------------- | ------------------------- | ------------------------------------ |
| `hybrid_dataset.py`              | Dataset class for hybrid features | Imported by training script (automatic) |
| `train_hybrid_model.py`          | Main training script      | Run to train the hybrid model        |
| `run_phase4.py`                  | Orchestrator script       | Run to execute training with defaults |
| `README.md`                      | This documentation        | Reference for using Phase 4 scripts  |

---

## 🔧 Step-by-Step Usage

### Prerequisites

Before starting training, ensure:

1. ✅ **Phase 2 Complete**: Features extracted and packed to HDF5
   - `D:/FYP/data/features/logmel_packed.h5` exists (spectrogram features)
   - `D:/FYP/data/features/environmental_packed.h5` exists (environmental features)

2. ✅ **Phase 3 Complete**: Hybrid model architecture tested
   - Model architecture verified and working
   - Loss function tested

3. ✅ **Manifests Ready**: Speaker-independent splits created
   - `data/manifests/train_speaker_independent.csv`
   - `data/manifests/val_speaker_independent.csv`
   - `data/manifests/test_speaker_independent.csv`

4. ✅ **GPU Available**: NVIDIA GeForce RTX 3050 6GB Laptop GPU
   - CUDA 12.1 available
   - 6GB VRAM → Batch size 64 (with FP16 mixed precision)
   - TF32 enabled for faster matrix operations

5. ✅ **Fast Drive**: HDF5 files on D: drive (internal NVMe SSD)
   - D: is SK Hynix NVMe SSD (internal) - FAST
   - E: is Lenovo PS6 Portable SSD (external) - slower
   - Move `.h5` files to `D:\FYP\data\features\` for 2-3x faster I/O

---

### Step 1: Verify Data and Model

Before training, verify everything is set up correctly:

```bash
# Check HDF5 files exist
python -c "import os; print('Spectrogram HDF5:', os.path.exists('D:/FYP/data/features/logmel_packed.h5')); print('Environmental HDF5:', os.path.exists('D:/FYP/data/features/environmental_packed.h5'))"

# Check manifests exist
python -c "import os; print('Train manifest:', os.path.exists('data/manifests/train_speaker_independent.csv')); print('Val manifest:', os.path.exists('data/manifests/val_speaker_independent.csv'))"

# Test model import
python -c "import sys; sys.path.insert(0, 'code/phase3'); from hybrid_resnet_environmental import HybridResNetEnvironmental; print('Model import OK')"
```

**Expected Output:**

```
Spectrogram HDF5: True
Environmental HDF5: True
Train manifest: True
Val manifest: True
Model import OK
```

---

### Step 2: Start Training

#### Option A: Use Orchestrator (Recommended)

Run with default settings:

```bash
python code/phase4/run_phase4.py
```

**With custom settings:**

```bash
python code/phase4/run_phase4.py --epochs 30 --output-dir models_saved_phase4
```

#### Option B: Direct Training Script

For more control, run the training script directly:

```bash
python code/phase4/train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 128 --epochs 20 --num_workers 8
```

**Key Arguments:**

- `--train_manifest`: Path to training manifest CSV
- `--val_manifest`: Path to validation manifest CSV
- `--spectrogram_h5`: Path to spectrogram HDF5 file (on fast drive)
- `--environmental_h5`: Path to environmental HDF5 file (on fast drive)
- `--output_dir`: Directory to save models and logs
- `--batch_size`: Batch size (default: 64, optimized for RTX 3050 6GB)
- `--epochs`: Number of training epochs (default: 20)
- `--num_workers`: Data loading workers (default: 8, adjust based on CPU cores)
- `--lr`: Initial learning rate (default: 1e-3)
- `--mixed_precision`: Use FP16 mixed precision (default: True, faster training)

**Performance Optimization Arguments:**

- `--num_workers 8`: Use 8 parallel workers for data loading (adjust to CPU cores)
- `--pin_memory`: Pin memory for faster GPU transfer (default: True)
- `--prefetch_factor 2`: Prefetch batches (default: 2)
- `--persistent_workers`: Keep workers alive between epochs (default: True, faster)

---

### Step 3: Monitor Training

During training, you'll see:

```
================================================================================
EPOCH 1/20
================================================================================
Training: 100%|████████████| 11592/11592 [45:23<00:00,  4.26it/s, loss=0.5234, b_loss=0.4123, mc_loss=0.1111]

[EVAL] Running full validation evaluation...
Evaluating: 100%|████████████| 1216/1216 [02:15<00:00,  8.98it/s]

[EPOCH 1] Training:
  Loss: 0.5234 (Binary: 0.4123, Multiclass: 0.1111)

[EPOCH 1] Validation:
  Loss: 0.4892 (Binary: 0.3856, Multiclass: 0.1036)
  Binary EER: 8.45%
  Binary AUC: 0.9234
  Binary Accuracy: 91.23%
  Multiclass Accuracy: 87.45%
  ASVspoof Domain EER: 5.23%
  ASVspoof Domain AUC: 0.9823
  Real-world Domain EER: 18.45%
  Real-world Domain AUC: 0.8543
  Learning Rate: 1.00e-03

[CHECKPOINT] Saved best model (EER: 8.45%) -> models_saved/hybrid_resnet_environmental_best.pth

[EPOCH 1] Completed in 47.8 minutes
```

**Key Metrics to Monitor:**

- **Binary EER**: Lower is better (target: < 10% overall, < 20% Real-world)
- **Binary AUC**: Higher is better (target: > 0.95 overall, > 0.85 Real-world)
- **Per-Domain EER**: Monitor ASVspoof vs Real-world performance
- **Loss Values**: Should decrease over epochs
- **Learning Rate**: Will decrease automatically if validation loss plateaus

---

### Step 4: Check Training Results

After training completes, check outputs:

```bash
# List saved models
ls models_saved/*.pth

# View training logs
head -20 models_saved/logs/training_hybrid_model.csv
```

**Output Files:**

- `models_saved/hybrid_resnet_environmental_best.pth` - Best model checkpoint (lowest validation EER)
- `models_saved/hybrid_resnet_environmental_epoch_N.pth` - Periodic checkpoints (every 5 epochs)
- `models_saved/logs/training_hybrid_model.csv` - Training metrics per epoch

**Training Log Format:**

```csv
epoch,train_loss,val_loss,val_binary_eer,val_binary_auc,val_asvspoof_eer,val_realworld_eer,learning_rate
1,0.5234,0.4892,0.0845,0.9234,0.0523,0.1845,0.001
2,0.4567,0.4321,0.0723,0.9456,0.0432,0.1654,0.001
...
```

---

## ✅ Success Criteria Checklist

After training, verify:

- [ ] Model trains successfully (loss decreases over epochs)
- [ ] Both tasks learn (binary + multiclass losses decrease)
- [ ] Validation EER < 10% on ASVspoof domain
- [ ] Validation EER < 20% on Real-world domain (KEY METRIC)
- [ ] No overfitting (train/val loss gap reasonable)
- [ ] Best model checkpoint saved
- [ ] Training metrics logged to CSV

**✅ Phase 4 is complete when all criteria are met.**

---

## 📊 Expected Performance

### Target Metrics

| Metric                    | ASVspoof Domain | Real-world Domain | Overall |
| -------------------------- | --------------- | ----------------- | ------- |
| Binary EER                 | < 5%            | < 20%             | < 10%   |
| Binary AUC                  | > 0.98          | > 0.85            | > 0.95  |
| Binary Accuracy            | > 95%           | > 80%             | > 90%   |
| Multiclass Accuracy        | > 90%           | N/A               | > 85%   |

### Training Time (Estimated)

**Per Epoch:**
- ~30-45 minutes (for 1.1M training samples)
- Depends on: GPU, batch size, data loading speed

**Total (20 epochs):**
- ~10-15 hours
- With mixed precision (FP16): ~30% faster

**Optimization Tips:**
- Use fast drive (D: drive) for HDF5 files
- Increase `num_workers` if CPU has many cores
- Use `mixed_precision` for faster training
- Adjust `batch_size` to maximize GPU utilization

---

## ⚙️ Performance Optimization

### Best Practices for Fast Training

1. **HDF5 Files on Fast Drive**
   - Move `.h5` files to `D:\FYP\data\features\` (fast SSD)
   - Reduces I/O bottleneck significantly

2. **Data Loading Optimization**
   - `num_workers`: Set to number of CPU cores (default: 8)
   - `pin_memory`: True (faster GPU transfer)
   - `prefetch_factor`: 2-4 (prefetch batches)
   - `persistent_workers`: True (keep workers alive)

3. **GPU Optimization**
   - `mixed_precision`: True (FP16, ~30% faster)
   - `batch_size`: 64 for 6GB VRAM (with FP16), 128 for 8GB+ VRAM
   - Enable TF32 on Ampere+ GPUs (automatic)

4. **Memory Management**
   - Use gradient accumulation if batch size limited by memory
   - Close datasets after training (automatic cleanup)

### Your System Configuration

| Resource | Specification | Status |
| -------- | ------------- | ------ |
| **GPU** | NVIDIA RTX 3050 6GB Laptop GPU | ✅ CUDA 12.1 |
| **CPU** | 8 physical / 12 logical cores | ✅ 8 workers |
| **RAM** | 16.89 GB total | ✅ Sufficient |
| **D: Drive** | SK Hynix NVMe SSD (internal) | ✅ Fast I/O |
| **E: Drive** | Lenovo PS6 Portable SSD (external) | Project location |

**Optimal Settings for RTX 3050 6GB:**
- Batch size: **64** (with FP16, fits in 6GB VRAM)
- Workers: **8** (matches physical CPU cores)
- Mixed precision: **FP16** (~30% faster, half memory)
- HDF5 on **D: drive** (2-3x faster than external SSD)

---

## 🐛 Troubleshooting

### Issue: CUDA Out of Memory

**Error Message:**

```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Solutions:**

1. **Reduce batch size:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --batch_size 64
   ```

2. **Use gradient accumulation** (if implemented):
   - Accumulate gradients over multiple batches
   - Effective batch size = batch_size × accumulation_steps

3. **Close other GPU applications:**
   - Close browser, other ML processes
   - Check GPU usage: `nvidia-smi`

4. **Use mixed precision** (already enabled by default):
   - FP16 uses half the memory

---

### Issue: Slow Data Loading

**Symptoms:**
- GPU utilization < 50%
- Long wait times between batches
- "Training" progress bar slow

**Solutions:**

1. **Move HDF5 files to fast drive:**
   ```bash
   # Move files to D: drive (fast SSD)
   move E:\FYP\data\features\*.h5 D:\FYP\data\features\
   ```

2. **Increase number of workers:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --num_workers 16
   ```

3. **Check disk I/O:**
   - Use Task Manager to monitor disk usage
   - Ensure no other heavy I/O operations

4. **Use persistent workers:**
   - Already enabled by default
   - Keeps workers alive between epochs

---

### Issue: HDF5 File Not Found

**Error Message:**

```
FileNotFoundError: Spectrogram HDF5 not found: D:/FYP/data/features/logmel_packed.h5
```

**Solutions:**

1. **Check file location:**
   ```bash
   # Windows PowerShell
   Test-Path D:\FYP\data\features\logmel_packed.h5
   ```

2. **Update path in command:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --spectrogram_h5 E:/FYP/data/features/logmel_packed.h5
   ```

3. **Verify Phase 2 completed:**
   - Check Phase 2 outputs
   - Re-run Phase 2 if needed

---

### Issue: Import Errors

**Error Message:**

```
ModuleNotFoundError: No module named 'phase3.hybrid_resnet_environmental'
```

**Solutions:**

1. **Run from project root:**
   ```bash
   cd E:\FYP
   python code/phase4/train_hybrid_model.py ...
   ```

2. **Check import paths:**
   - Verify `code/phase3/hybrid_resnet_environmental.py` exists
   - Verify `code/phase3/multi_task_loss.py` exists

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Issue: Training Loss Not Decreasing

**Symptoms:**
- Loss stays constant or increases
- Metrics don't improve

**Solutions:**

1. **Check learning rate:**
   - Try lower learning rate: `--lr 1e-4`
   - Learning rate scheduler should adjust automatically

2. **Check class weights:**
   - Verify class weights computed correctly
   - Check label distribution in manifest

3. **Check data:**
   - Verify features loaded correctly
   - Check for NaN/Inf in features

4. **Reduce learning rate:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --lr 5e-4
   ```

---

### Issue: Per-Domain Metrics Missing

**Symptoms:**
- ASVspoof/Real-world EER not shown
- Only overall metrics displayed

**Explanation:**

- Per-domain metrics only computed during full evaluation (every 5 epochs)
- Quick evaluation (every epoch) only shows overall metrics
- This is normal behavior to save time

**To see per-domain metrics every epoch:**

- Modify `train_hybrid_model.py` to always run full evaluation
- Or wait for full evaluation epochs (every 5 epochs)

---

### Issue: Windows Multiprocessing Errors

**Error Message:**

```
RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase.
```

**Solutions:**

1. **Reduce number of workers:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --num_workers 4
   ```

2. **Use persistent workers:**
   - Already enabled by default
   - Helps with Windows multiprocessing

3. **Check HDF5 file handles:**
   - Dataset class opens HDF5 files per worker (safe)
   - Should not cause issues

---

## 📝 Notes

- **KEY METRIC**: Real-world domain EER < 20% (this is the critical requirement)
- Monitor per-domain performance throughout training
- If Real-world performance is poor, may need Phase 7 (Domain Adaptation)
- Keep training logs for analysis
- Document any training issues or adjustments
- Best model is saved automatically (lowest validation EER)

---

## 🔗 Next Steps

**After Phase 4 is complete:**

1. **Phase 5: Evaluation** - Evaluate trained model on test set
   - Use `models_saved/hybrid_resnet_environmental_best.pth`
   - Generate comprehensive evaluation reports
   - Compare with baseline models

2. **Phase 6: Analysis** - Analyze model performance
   - Per-domain analysis
   - Error analysis
   - Feature importance

3. **Phase 7: Domain Adaptation** (if needed)
   - If Real-world performance < 20% EER
   - Fine-tune on Real-world data

---

**Last Updated**: December 2025  
**Status**: ✅ **READY FOR TRAINING**

---

## ✅ Phase 4 Completion Summary

**Scripts Created:**

- ✅ `hybrid_dataset.py` - Dataset class for hybrid features
- ✅ `train_hybrid_model.py` - Main training script
- ✅ `run_phase4.py` - Orchestrator script
- ✅ `README.md` - This documentation

**Ready for Training:**

- ✅ All dependencies met (Phase 2, Phase 3)
- ✅ HDF5 files ready (user will move to D: drive)
- ✅ Manifests ready (speaker-independent splits)
- ✅ Model architecture tested
- ✅ Loss function tested

**Next Phase**: Phase 5 - Evaluation (requires trained model from Phase 4)

