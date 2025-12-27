# Phase 4: Hybrid Model Training

**Status**: ✅ **COMPLETED (TRAINED + CHECKPOINTS SAVED)**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3-4  
**Dependencies**: Phase 3 (Hybrid Architecture) ✅, Phase 2 (Feature Extraction) ✅

---

## 🎯 Objective

Train the hybrid model on mixed data (50% ASVspoof + 50% Real-world) with speaker-independent splits, monitoring both binary and multiclass performance across domains.

---

## ✅ Phase 4 Final Result (Dec 2025)

**Training completed end-to-end** on the PC with RTX 3070 using the optimized FAST loader and chunked HDF5.

- **Best checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth`
- **Best overall validation EER**: **20.17%** (epoch 17)
- **RealWorld EER (full-eval epochs)**: **~11–14%** (met the Phase 4 key requirement: RealWorld EER < 20%)
- **Epoch time (PC, batch=128)**:
  - Quick-eval epochs: **~82–95 min**
  - Full-eval epochs (every 5 epochs + epoch 1/20): **~109–126 min**
- **Logs**: `models_saved/logs/training_hybrid_fast.csv`
- **Periodic checkpoints**: `models_saved/hybrid_resnet_environmental_epoch_{5,10,15,20}.pth`

**Note:** Validation loss showed spikes in some epochs (e.g., epoch 11 / 20). We treat EER/AUC as the primary performance indicators for this problem.

## 🖥️ System Resources

**Systems used in Phase 4:**

| System | Key Specs | Notes |
|---|---|---|
| **Laptop** | RTX 3050 6GB, ~16GB RAM, D: NVMe + E: external SSD | Used for conversion/repack + validation runs |
| **PC (final training)** | RTX 3070 8GB, more RAM headroom, fast local SSD | Used for full 20-epoch training |

**Optimal Settings for RTX 3050 6GB:**
- Batch size: **64** (6GB VRAM limitation, tested up to 128)
- Mixed precision: **FP16** (~30% speedup, half memory)
- Workers: **8** (matches physical CPU cores)
- HDF5 files on **D: drive** (internal NVMe = 3.5x faster than external SSD)
- HDF5 format: **Uncompressed** (100x faster than gzip)

---

## 🐛 Issues Identified & Resolved

### Issue 1: Manifest Index Mismatch (RESOLVED)

**Problem Discovered:**
- Train/val manifests use local DataFrame indices (0, 1, 2...)
- HDF5 files store features indexed by unified manifest indices
- Dataset was looking up wrong features!

**Solution Applied:**
- Updated `hybrid_dataset.py` to load unified manifest
- Created filepath → unified_index mapping
- Pre-computed all index lookups as numpy arrays for O(1) access

**Files Modified:**
- `code/phase4/hybrid_dataset.py`
- `code/phase4/train_hybrid_model.py`

---

### Issue 2: GZIP Compression Bottleneck (CRITICAL - RESOLVED)

**Problem Discovered:**
During pre-training checks, data loading was extremely slow:
- Single sample load: **470ms** (should be <10ms)
- Batch load time: **36 seconds** per batch
- Estimated epoch time: **14,041 minutes** (234 hours!) - UNACCEPTABLE

**Root Cause:**
- Phase 2 packed HDF5 files with gzip compression (compression_opts=1)
- HDF5 chunks are 1000 samples
- Reading 1 sample decompresses entire 1000-sample chunk
- Random access pattern (shuffled training) = worst case for gzip

**Benchmark Results:**
```
Compressed HDF5 (gzip):
  - Read 1 sample: 470ms
  - Read 100 samples: 465ms (decompresses same chunk)
  - Read 1000 samples (full chunk): 506ms

Uncompressed HDF5:
  - Read 1 sample: ~1-5ms (100x faster!)
  - Read 100 samples: ~10-50ms
```

**Solution Applied:**
Created `code/phase4/convert_h5_uncompressed.py` to:
1. Delete duplicate .h5 files from D: drive (frees ~103 GB)
2. Convert E: drive gzip-compressed .h5 to uncompressed on D: drive

---

### Issue 3: Uncompressed but Still Slow (Chunking + Access Pattern) (CRITICAL - RESOLVED)

**Symptom (PC RTX 3070, batch=256):**
- Training still ~**6.4s/batch** → **~9–10 hours/epoch**

**Root Cause:**
- Even after removing compression, the original spectrogram HDF5 had **chunks=(1,64,400)** → 1 chunk per sample.
- After repacking to **chunks=(256,64,400)**, training was still slow because the loader frequently fell back to **h5py fancy indexing** (non-contiguous indices due to train/val split gaps), which behaves like many small reads.

**Final Fix:**
1. Repack the spectrogram file with larger chunks (batch-aligned):
   - `code/phase4/repack_h5_chunked.py` → produces `logmel_chunked.h5` with `chunks=(256,64,400)` and **no compression**
2. Update the fast loader to **avoid h5py fancy indexing** and instead:
   - Group indices by HDF5 chunk
   - Read **chunk-aligned slices** (works even with gaps in train indices)
   - Read only the minimal slice range needed inside each chunk (reduces CPU/mem copying)
   - Cache environmental features in RAM (small: ~0.09 GB) to remove tiny-read overhead
   - Implementation: `code/phase4/hybrid_dataset_fast.py` (`get_batch_direct()` + `_read_h5_by_chunks()`)
3. Add per-batch timing visibility to confirm bottleneck removal:
   - `code/phase4/train_hybrid_fast.py` shows `load_ms` in tqdm
   - Optional `--profile_batches N` prints `load_ms / h2d_ms / step_ms` for first N batches

**Expected Impact:**
- Batch load time should drop from **~6000ms** to typically **<200ms** on NVMe, bringing epoch time down from **hours** to **tens of minutes** (depending on GPU compute).

**File Sizes:**
| File | Compressed (gzip) | Uncompressed | Speed Improvement |
|------|-------------------|--------------|-------------------|
| logmel_packed.h5 | 103 GB | 193 GB | 100x faster reads |
| environmental_packed.h5 | 0.07 GB | 0.09 GB | 100x faster reads |

**Disk Space Solution:**
- D: drive had 142.5 GB free
- Deleted D: duplicates: +103 GB → 245 GB free
- Uncompressed files need: ~193 GB
- Result: Fits with 52 GB to spare

---

### Issue 4: Low Available RAM (WARNING)

**Observation:**
- RAM available: 3.6-7.3 GB (varies)
- Total RAM: 16.89 GB
- Using 73% RAM before training

**Impact:** May limit number of data loading workers

**Mitigation:**
- Close unnecessary applications before training
- Use 8 workers (not more)
- Dataset pre-computes indices as numpy arrays (memory efficient)

---

## 📋 Tasks

### 1. Prepare Training Data

**Data Loading:**

- Use unified manifest with speaker-independent splits
- Load both spectrogram and environmental features from HDF5
- HDF5 files on D: drive for fast I/O (internal NVMe SSD)
- Ensure both domains in train/val/test

**DataLoader Configuration (Optimized for RTX 3050 6GB):**

- Batch size: **64** (optimized for 6GB VRAM with FP16)
- Workers: **8** (matches physical CPU cores)
- Prefetch factor: **2** (pipeline next batches)
- Shuffle: True (training), False (validation/test)
- Pin memory: True (faster GPU transfer)
- Persistent workers: True (faster epoch transitions)

**Class Weighting:**

- Compute class weights for imbalanced data
- Apply to both binary and multiclass losses
- Automatic computation from training manifest

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
├── hybrid_resnet_environmental_best.pth    # Best model checkpoint (lowest EER)
├── hybrid_resnet_environmental_epoch_N.pth # Periodic checkpoints (every 5 epochs)
└── logs/
    └── training_hybrid_fast.csv            # Training metrics per epoch (FAST trainer)

D:\FYP\data\features\  (UNCOMPRESSED - Fast I/O)
├── logmel_packed.h5                        # Spectrogram features (194.07 GB)
└── environmental_packed.h5                 # Environmental features (0.11 GB)
                                            # Total: 194.18 GB on fast NVMe
```

---

## 🔧 Scripts

### Created (Phase 4):

| Script | Purpose | Status |
|--------|---------|--------|
| `code/phase4/train_hybrid_model.py` | Main training script with mixed precision, per-domain metrics, checkpointing | ✅ Ready |
| `code/phase4/hybrid_dataset.py` | Dataset class for hybrid HDF5 features with optimized index lookup | ✅ Ready |
| `code/phase4/run_phase4.py` | Orchestrator script to run all Phase 4 steps | ✅ Ready |
| `code/phase4/pre_training_check.py` | Comprehensive pre-training verification (GPU, data, model, speed tests) | ✅ Ready |
| `code/phase4/convert_h5_uncompressed.py` | Convert gzip HDF5 to uncompressed for 100x faster loading | ✅ Ready |
| `code/phase4/repack_h5_chunked.py` | Repack spectrogram HDF5 to larger chunks `(256,64,400)` for fast batch reads | ✅ Used |
| `code/phase4/hybrid_dataset_fast.py` | FAST dataset + chunk-aligned batch reader + ChunkedDataLoader | ✅ Used |
| `code/phase4/train_hybrid_fast.py` | FAST training script (batch reads + optional profiling) | ✅ Used |
| `code/phase4/README.md` | Practical usage guide with troubleshooting | ✅ Ready |

### Existing (Reuse from Phase 3):

- ✅ `code/phase3/hybrid_resnet_environmental.py` - Model architecture (2,902,822 parameters)
- ✅ `code/phase3/multi_task_loss.py` - Multi-task loss function (binary + multiclass)
- ✅ `code/utils_metrics.py` - Evaluation metrics (EER, AUC, confusion matrix)

---

## 📊 Dataset Statistics

**Training Set (1,483,741 samples):**

| Category | Distribution |
|----------|--------------|
| **Label** | spoof: 83.1% (1,232,473) / bonafide: 16.9% (251,268) |
| **Dataset** | PA: 50.3% / DF: 31.9% / LA: 9.5% / RealWorld: 8.3% |
| **Attack Type** | replay: 43.6% / conversion: 30.8% / bonafide: 16.9% / synthesis: 8.7% |

**Validation Set (155,604 samples):**
- Same distribution as training (stratified split)
- Speaker-independent (no speaker overlap with training)

**Class Weights Computed:**
- Binary: [1.661 (bonafide), 0.339 (spoof)] - upweights minority bonafide class
- Multiclass: [1.032, 1.999, 0.568, 0.401] - balances attack types

---

## ✅ Success Criteria

### Pre-Training (Setup)
- [x] Dataset class with correct index mapping
- [x] Training script with mixed precision support
- [x] Pre-training check script created
- [x] HDF5 files converted to uncompressed on D: drive (194.18 GB total)
- [x] Pre-training check passes (10/10 tests) ✅
- [x] Data loading speed verified: **2.17ms per sample** (was 470ms)

### Training (Model Performance)
- [x] Model trains successfully (loss decreases)
- [x] Checkpoints save correctly (best + periodic)
- [x] Training time is practical on PC (≈ 1.5h/epoch avg at batch 128 with full eval every 5 epochs)
- [x] **Real-world EER < 20%** on full evaluation epochs (**KEY METRIC MET**)
- [ ] ASVspoof EER < 10% (not met in training logs; investigate in Phase 5 test evaluation)
- [ ] Multiclass accuracy target (investigate in Phase 5; metric appears unstable)

### Post-Training (Outputs)
- [x] Best model checkpoint saved (`models_saved/hybrid_resnet_environmental_best.pth`)
- [x] Training metrics logged (`models_saved/logs/training_hybrid_fast.csv`)
- [x] Periodic checkpoints saved (epoch 5/10/15/20)

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

**Training Time (Estimated for RTX 3050 6GB with UNCOMPRESSED HDF5):**

| Configuration | Per Epoch | Total (20 epochs) |
| ------------- | --------- | ----------------- |
| Batch 64, FP16, Uncompressed | ~25-35 min | ~8-12 hours |
| Batch 64, FP32, Uncompressed | ~35-45 min | ~12-15 hours |
| Batch 128 (66% VRAM), FP16 | ~15-25 min | ~5-8 hours |

**Speed Optimizations Applied:**

| Optimization | Speedup | Implementation |
|--------------|---------|----------------|
| Uncompressed HDF5 | **100x** faster I/O | `convert_h5_uncompressed.py` |
| Mixed precision (FP16) | ~30% faster | `torch.cuda.amp.autocast()` |
| HDF5 on D: (NVMe) | ~3.5x faster than E: | Internal NVMe vs external SSD |
| 8 data workers | Parallel loading | Matches physical CPU cores |
| Persistent workers | No restart overhead | `persistent_workers=True` |
| TF32 on Ampere | ~2x matmul speed | RTX 30xx automatic |
| Pre-computed indices | O(1) label lookup | Numpy arrays in dataset |
| Pin memory | Faster GPU transfer | `pin_memory=True` |

**Before vs After Optimization (Verified Dec 24, 2025):**

| Metric | Before (gzip) | After (uncompressed) | Improvement |
|--------|---------------|----------------------|-------------|
| Single sample load | 470ms | **2.17ms** | **216x faster** |
| HDF5 file size | 103 GB | 194 GB | +91 GB |
| Conversion time | - | 71.5 min | One-time cost |
| Estimated epoch time | 14,041 min | ~25-35 min | **400x faster** |
| Training feasibility | ❌ Impossible | ✅ Practical | ✅ |

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

- ✅ Phase 2: Feature Extraction (HDF5 files ready, 1,893,919 samples)
- ✅ Phase 3: Hybrid Architecture (model tested, 2.9M parameters)

**Next Phase:**

- Phase 5: Evaluation (requires trained model)

---

## 🏗️ Technical Architecture

### Model Architecture (from Phase 3)

```
HybridResNetEnvironmental
├── ResNet Branch (spectrogram input)
│   ├── Conv2D(1→32) + BatchNorm + ReLU
│   ├── ResidualBlock(32→32)
│   ├── ResidualBlock(32→64, stride=2)
│   ├── ResidualBlock(64→128, stride=2)
│   ├── ResidualBlock(128→256, stride=2)
│   ├── AdaptiveAvgPool2D
│   └── FC(256→128) → Spectrogram Embedding
├── Environmental Branch (12 features)
│   ├── FC(12→64) + ReLU + Dropout
│   ├── FC(64→128) + ReLU + Dropout
│   └── FC(128→128) → Environmental Embedding
├── Fusion Layer
│   └── Concat(spec_emb, env_emb) → FC(256→128)
├── Binary Head → FC(128→64) → FC(64→2)
└── Multi-class Head → FC(128→64) → FC(64→4)
```

**Parameters:** 2,902,822 (11.61 MB)

### Loss Function

```
Total Loss = α × Binary_CE + β × Multiclass_CE
           = 0.7 × Binary_Loss + 0.3 × Multiclass_Loss
```

With class weighting to handle imbalance:
- Binary: [1.661, 0.339] (upweight bonafide)
- Multiclass: [1.032, 1.999, 0.568, 0.401] (balance attack types)

### Data Pipeline

```
Manifest CSV → HybridDataset → DataLoader → GPU
     ↓              ↓             ↓
filepath      Pre-computed    Batch of:
label         index arrays    - spectrogram [B,1,64,400]
attack_type   HDF5 lookup     - environmental [B,12]
dataset       Normalization   - labels, domain
```

**Key Optimizations:**
1. Pre-computed filepath → HDF5 index mapping (O(1) lookup)
2. Pre-computed labels as numpy arrays
3. Uncompressed HDF5 for fast random access
4. 512MB HDF5 chunk cache per worker

---

## 📝 Notes

- **KEY METRIC**: Real-world domain EER < 20% (this is the critical requirement)
- Monitor per-domain performance throughout training
- If Real-world performance is poor, may need Phase 7 (Domain Adaptation)
- Keep training logs for analysis
- Document any training issues or adjustments

---

## 🔍 Verification Checklists

### Pre-Training Check Results (run `pre_training_check.py`) - ✅ ALL PASSED

| Test | Expected | Actual Result | Status |
|------|----------|---------------|--------|
| 1. File Checks | All 5 files exist | All files found | ✅ |
| 2. GPU Check | CUDA available, RTX 3050 6GB | CUDA 12.1, cuDNN enabled, TF32 enabled | ✅ |
| 3. CPU/RAM Check | 8 cores, 16GB RAM | 8 physical / 12 logical, 16.89 GB | ✅ |
| 4. HDF5 File Check | Shapes match, indices exist | (1893919, 64, 400), chunks (1,64,400) | ✅ |
| 5. Manifest Check | 1.48M train, 155K val samples | 1,483,741 train, 155,604 val | ✅ |
| 6. Model Check | 2,902,822 parameters, forward pass OK | 11.61 MB, forward pass OK | ✅ |
| 7. GPU Memory Test | Batch 64 uses <50% VRAM | Batch 64: 33.3%, Batch 128: 64.4% | ✅ |
| 8. Data Loading Speed | < 10ms per sample | **2.17ms** (216x faster than gzip!) | ✅ |
| 9. DataLoader Speed | Reasonable batch time | ~2.6s for 1000 samples (4 workers) | ✅ |
| 10. Loss Function Check | Loss computes correctly | total=1.0833 | ✅ |

### GPU Memory Usage by Batch Size

| Batch Size | VRAM Used | % of 6GB | Status |
|------------|-----------|----------|--------|
| 32 | 1,207 MB | 18.7% | ✅ Safe |
| 64 | 2,148 MB | 33.3% | ✅ **Recommended** |
| 96 | 3,201 MB | 49.7% | ✅ Safe |
| 128 | 4,151 MB | 64.4% | ✅ Possible (faster) |

### Training Verification (during training)

- [ ] Loss decreases over epochs
- [ ] Both tasks learn (binary + multiclass losses decrease)
- [ ] No NaN or Inf in loss values
- [ ] GPU utilization > 80%
- [ ] Validation EER improves
- [ ] Checkpoint saves correctly
- [ ] Per-domain metrics tracked (ASVspoof vs RealWorld)

---

## 🚀 Quick Start Commands

### Step 1: Convert HDF5 to Uncompressed (One-time, ~30-60 min)

```powershell
cd E:\FYP
conda activate fassd
python code/phase4/convert_h5_uncompressed.py
```

**What this does:**
1. Deletes duplicate .h5 files from D: drive (frees ~103 GB)
2. Converts E: gzip-compressed .h5 to uncompressed on D: drive
3. Verifies conversion and tests read speed

**Expected output:**
```
STEP 1: Delete duplicate .h5 files from D: drive
  Deleting: D:/FYP/data/features/logmel_packed.h5 (95.97 GB)
  [DELETED]
  Freed: 103.04 GB
  D: drive free space now: 245.5 GB

STEP 2: Convert spectrogram HDF5 (this will take ~30-60 minutes)
  Converting: E:/FYP/data/features/logmel_packed.h5
  Shape: (1893919, 64, 400)
  Uncompressed size: 193.22 GB
  Converting: 100%|████████████| 1894/1894 [35:42<00:00]
  Read 1 sample: 2.3ms (was ~470ms)
  
CONVERSION COMPLETE!
```

---

### Step 2: Run Pre-Training Check

```powershell
python code/phase4/pre_training_check.py
```

**Verifies:**
- All files exist
- GPU available and configured
- Data loading speed (should be ~1-5ms per sample now)
- Model forward pass works
- Loss function works

---

### Step 3: Start Training

```powershell
python code/phase4/train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 64 --epochs 20 --num_workers 8
```

### PC (RTX 3070) Final Recommended Command (PROVEN)

1) Ensure you are using the chunked spectrogram file:
- `C:/FYP/data/features/logmel_chunked.h5`

2) Run training:

```powershell
cd C:\FYP
conda activate fassd
python code/phase4/train_hybrid_fast.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 C:/FYP/data/features/logmel_chunked.h5 --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 128 --epochs 20 --profile_batches 0
```

**Why batch 128 (not 256):**
- Batch 256 on RTX 3070 showed very slow step time (~seconds/it) despite low `load_ms` (compute/VRAM behavior).
- Batch 128 achieved stable ~2.4–2.7 it/s and completed training.

**Alternative: Use orchestrator**
```powershell
python code/phase4/run_phase4.py
```

---

## 📋 Pre-Training Checklist

All items verified ✅:

- [x] Phase 2 complete (features extracted - 1,893,919 samples)
- [x] Phase 3 complete (model architecture tested - 2.9M parameters)
- [x] Manifest index mapping fixed (filepath → unified_index)
- [x] HDF5 files converted to uncompressed on D: drive (194.18 GB)
- [x] Pre-training check passes (10/10 tests) ✅
- [x] Data loading speed: **2.17ms per sample** (was 470ms)
- [x] Sufficient disk space on D: (~51 GB free after conversion)
- [ ] Close unnecessary applications before training (recommended)

---

## 📅 Timeline

| Date | Event | Result |
|------|-------|--------|
| Dec 2025 | Phase 2 complete | 1,893,919 samples extracted |
| Dec 2025 | Phase 3 complete | Model architecture validated |
| Dec 2025 | Discovered gzip bottleneck | 470ms/sample = 234 hours/epoch |
| Dec 2025 | Converted to uncompressed HDF5 | 2.17ms/sample = **216x speedup** |
| Dec 2025 | Pre-training check passed | 10/10 tests ✅ |
| Dec 2025 | **Training completed (PC)** | 20 epochs finished; best val EER **20.17%** (epoch 17); RealWorld EER ~11–14% on full-eval epochs |

---

## ✅ Phase 4 Completion Artifacts (Final)

- **Best checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth` (best val EER = **20.17%**, epoch 17)
- **Periodic checkpoints**: `models_saved/hybrid_resnet_environmental_epoch_{5,10,15,20}.pth`
- **Training log**: `models_saved/logs/training_hybrid_fast.csv`

**Last Updated**: December 27, 2025  
**Status**: ✅ **COMPLETED**
