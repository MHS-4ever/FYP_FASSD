# Previous Pipeline Work - Detailed Explanation

**Date**: Current  
**Purpose**: Complete documentation of all work done in previous pipeline

**Note**: For phase-by-phase details, see `reports/previous_phases/` folder.

---

## Overview

We built a deepfake audio detection system using ASVspoof 2021 dataset. The pipeline achieved excellent results on ASVspoof data (2.61% EER) but failed on real-world audio due to domain mismatch.

---

## Phase 1: Setup and Foundation (Week 1-2)

### Objective
Set up environment and extract features from ASVspoof dataset.

### Work Done

1. **Environment Setup**
   - Python 3.x, PyTorch, CUDA setup
   - Conda environment: `fassd`
   - GPU: RTX 3050 (6GB VRAM)

2. **Dataset**
   - ASVspoof 2021 dataset (400GB+)
   - ASVspoof_LA: 181,566 real audio files
   - ASVspoof_DF: 611,829 fake audio files
   - Total: ~800,000 audio files

3. **Feature Extraction**
   - **LFCC**: 20 Linear Frequency Cepstral Coefficients
   - **Log-Mel Spectrograms**: 64 frequency bins
   - Extracted from all audio files
   - Packed into HDF5 for efficient loading

### Results
✅ Feature extraction pipeline working  
✅ HDF5 storage system efficient  
✅ All features extracted successfully

### Files
- `Code/features/feature_extraction.py`
- `Code/pack_features_to_hdf5.py`
- `data/features/` with packed HDF5 files

---

## Phase 2: Data Augmentation (Week 2-3)

### Objective
Add variations to training data to improve model robustness.

### Work Done

1. **Augmentation Techniques**
   - **MUSAN Noise**: Background noise addition
   - **RIR Convolution**: Room impulse response (reverb)
   - **Codec Simulation**: Downsample/upsample (compression)
   - **Random Gain**: Volume variation
   - **Clipping**: Dynamic range variation

2. **Augmentation Pipeline**
   - Applied to all training samples
   - Created 611,829 additional augmented samples
   - Combined with clean data for robust training

### Results
✅ Augmentation pipeline working  
✅ Created diverse training data  
✅ Improved model robustness

### Files
- `Code/data_augmentation.py`
- `data/features_augmented/` directory
- Augmented feature manifests

---

## Phase 3: Baseline Model (Week 3-4)

### Objective
Build and train a simple baseline model to establish performance baseline.

### Work Done

1. **LCNN Baseline Architecture**
   - Lightweight Convolutional Neural Network
   - ~5,000 parameters
   - Simple CNN with 2-3 layers

2. **Training**
   - Trained on LFCC features
   - Clean data: 9.68% EER
   - Augmented data: 15.71% EER

3. **Bug Fixes**
   - Fixed class weight bug
   - Fixed Unicode console issues
   - Fixed data loading problems

### Results
✅ Baseline model working  
✅ Established performance baseline  
✅ Identified areas for improvement

### Files
- `Code/models/baseline_cnn.py`
- `Code/train_baseline.py`
- Models: `baseline_cnn_lfcc.pth`, `baseline_cnn_lfcc_robust.pth`

---

## Phase 4.1: Feature Comparison (Week 4-5)

### Objective
Compare LFCC vs Mel features to identify best feature type.

### Work Done

1. **Mel Feature Training**
   - Trained LCNN on Log-Mel spectrograms
   - 64 frequency bins vs 20 LFCC coefficients

2. **Results Comparison**
   - LFCC: 15.71% EER (augmented)
   - Mel: 15.25% EER (augmented)
   - **Mel outperforms LFCC**

### Results
✅ Mel features identified as better  
✅ Decision made to use Mel for advanced models

### Files
- Models: `baseline_cnn_mel.pth`, `baseline_cnn_mel_robust.pth`
- `reports/PHASE4_1_RESULTS.md`

---

## Phase 4.2: Deep ResNet CNN (Week 5-6)

### Objective
Build deeper, more powerful model for better performance.

### Work Done

1. **ResNet Architecture**
   - 8 residual blocks with skip connections
   - 2.8 million parameters (vs 5K baseline)
   - Deep network with batch normalization

2. **Training Optimizations**
   - Mixed precision training (FP16)
   - Quick evaluation (15% subset) during training
   - Full evaluation every 5 epochs
   - TF32 acceleration for Ampere GPUs
   - Class weighting for imbalanced data

3. **Results**
   - Clean test: **0.57% EER** ⭐
   - Augmented test: **2.61% EER** ⭐
   - **83% improvement** over baseline

### Results
✅ **OUTSTANDING SUCCESS** on ASVspoof dataset  
✅ Production-ready model for ASVspoof domain  
✅ Best model: `resnet_cnn_mel_robust.pth`

### Files
- `Code/models/resnet_cnn.py`
- `Code/train_resnet.py`
- Model: `models_saved/resnet_cnn_mel_robust.pth`
- `reports/PHASE4_2_RESULTS.md`

---

## Phase 4.3: Environmental Features (Week 6-8)

### Objective
Build environmental acoustic analysis system to detect deepfakes based on environmental inconsistencies.

### Work Done

1. **Environmental Feature Extractor**
   - RT60 (reverberation time)
   - SNR (signal-to-noise ratio)
   - Spectral tilt, flatness, rolloff
   - Background noise analysis
   - "Too clean" detection
   - 12 environmental features total

2. **Anomaly Detection Approach**
   - Isolation Forest trained on bonafide samples only
   - Learn "normal" environmental patterns
   - Flag anomalies as fake
   - **Result**: 24.5% accuracy (poor)

3. **Supervised Classification Approach**
   - Random Forest trained on both real and fake
   - Learn differences between real and fake environmental features
   - **Result**: 81.69% accuracy on ASVspoof

4. **Real-World Testing**
   - Tested on Trump audio (broadcast/processed)
   - **Result**: Complete failure
   - Cannot distinguish real from fake broadcast audio

### Critical Discovery

**Domain Mismatch Problem**:
- Models trained on ASVspoof (studio recordings)
- Tested on real-world audio (broadcast/processed)
- **Environmental features overlap** after processing
- Real broadcast audio looks similar to fake after processing

### Results
✅ Environmental feature extractor working  
✅ Works on ASVspoof (81.69% accuracy)  
❌ **Fails on real-world audio** (domain mismatch)

### Files
- `Code/features/environmental_features.py`
- `Code/train_environment_classifier.py`
- `Code/predict_hybrid.py`
- Model: `models_saved/environment_classifier.pkl`
- Multiple analysis reports

---

## Key Findings

### What Worked

1. ✅ **Feature Extraction Pipeline**: Efficient and working
2. ✅ **Data Augmentation**: Improves robustness
3. ✅ **ResNet CNN**: Excellent on ASVspoof (2.61% EER)
4. ✅ **Environmental Features**: Work on ASVspoof (81.69% accuracy)

### What Didn't Work

1. ❌ **Real-World Audio Detection**: Complete failure (100% false positives)
2. ❌ **Domain Generalization**: Models don't work on different domains
3. ❌ **Environmental Features on Real-World**: Cannot distinguish real vs fake after processing

### Root Causes

1. **Domain Mismatch**: ASVspoof (studio) ≠ Real-world (broadcast/processed)
2. **Missing Real-World Data**: No real-world audio in training
3. **Environmental Features Overlap**: After processing, real and fake look similar
4. **No Speaker Independence**: Same speakers in train and test
5. **Missing Dataset**: Only used 2 out of 3 ASVspoof datasets (missing PA)

---

## Lessons Learned

1. **Domain Mismatch is Critical**: Models need training data from target domain
2. **Real-World Data is Essential**: Cannot rely on studio data alone
3. **Environmental Features Need Real-World Training**: Studio patterns don't transfer
4. **Speaker Independence Matters**: Random split doesn't test true generalization
5. **All Datasets Needed**: Missing PA dataset limits attack type coverage

---

## Current Status

- ✅ Excellent performance on ASVspoof dataset
- ❌ Complete failure on real-world audio
- ⚠️ Need real-world data collection
- ⚠️ Need hybrid architecture (ResNet + Environmental)
- ⚠️ Need speaker-independent evaluation

---

**End of Previous Pipeline Work Documentation**

