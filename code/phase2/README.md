# Phase 2: Feature Extraction

**Status**: ✅ **COMPLETE**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2-3  
**Dependencies**: Phase 1 (Unified Dataset Preparation) ✅ COMPLETE  
**Completion Date**: December 2025

---

## 🎯 Objective

Extract both spectrogram features (for ResNet CNN branch) and environmental features (for Environmental MLP branch) from all audio files in the unified dataset.

---

## 📋 Tasks

### 1. Extract Spectrogram Features ✅

**Feature Type:** Log-Mel Spectrograms

**Parameters:**

- Sample rate: 16,000 Hz
- Window size: 25ms (400 samples)
- Hop size: 10ms (160 samples)
- Mel bins: 64
- FFT size: 512
- Normalization: Log-scale
- Target length: 400 frames (~4 seconds at 10ms hop)

**Processing:**

- Extract from all audio files (ASVspoof + Real-world)
- Handle variable-length audio (pad/truncate to fixed length)
- Save as individual .npy files

**Output Format:**

- Shape: `[64, 400]` per sample
- Saved as `.npy` files in `data/features/spectrograms/`

### 2. Extract Environmental Features ✅

**Feature Set:** 12 Environmental Acoustic Features

**Features:**

1. RT60 (Reverberation Time)
2. DRR (Direct-to-Reverberant Ratio)
3. SNR (Signal-to-Noise Ratio)
4. Background Noise Level
5. Silence Ratio
6. Spectral Tilt
7. Spectral Flatness
8. Spectral Rolloff
9. Cleanliness Score
10. High-Frequency Content
11. Background Consistency
12. Environmental Stability

**Processing:**

- Extract from all audio files (ASVspoof + Real-world)
- Handle missing/invalid values
- Save as individual .npy files

**Output Format:**

- Shape: `[12]` per sample
- Saved as `.npy` files in `data/features/environmental/`

### 3. Pack Features to HDF5 ✅

**HDF5 Structure:**

```
logmel_packed.h5
├── features/          # [N, 64, 400] spectrograms
├── indices/          # Mapping to manifest rows
└── metadata/          # Dataset info

environmental_packed.h5
├── features/          # [N, 12] environmental features
├── indices/           # Mapping to manifest rows
└── metadata/          # Feature names, scaler info
```

**Manifest Update:**

- Add feature indices to manifest
- Link audio files to feature locations

---

## 🚀 Scripts Overview

| Script                              | Purpose                                         | Usage                                      |
| ----------------------------------- | ----------------------------------------------- | ------------------------------------------ |
| `extract_spectrogram_features.py`   | Extract log-mel spectrograms from audio files   | `python extract_spectrogram_features.py`   |
| `extract_environmental_features.py` | Extract environmental features from audio files | `python extract_environmental_features.py` |
| `pack_features_to_hdf5.py`          | Pack features into HDF5 format                  | `python pack_features_to_hdf5.py`          |
| `verify_features.py`                | Verify extracted features                       | `python verify_features.py`                |
| `run_phase2.py`                     | Run all Phase 2 steps in sequence               | `python run_phase2.py`                     |

---

## 📁 Output Files

```
data/
├── features/
│   ├── spectrograms/                  # Individual .npy files
│   │   ├── <audio_name>_logmel.npy
│   │   └── ...
│   ├── environmental/                 # Individual .npy files
│   │   ├── <audio_name>_env.npy
│   │   └── ...
│   ├── logmel_packed.h5               # Packed spectrogram features
│   ├── environmental_packed.h5        # Packed environmental features
│   ├── features_manifest_unified.csv # Updated manifest with indices
│   ├── packing_stats.json             # Packing statistics
│   └── verification_report.json       # Verification report
└── scalers/
    └── environmental_scaler.pkl         # StandardScaler (created in Phase 3/4)
```

---

## 🔧 Common Commands

### Step 1: Extract Spectrogram Features

```bash
python code/phase2/extract_spectrogram_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/spectrograms \
    --resume
```

**Test mode (first 1000 samples):**

```bash
python code/phase2/extract_spectrogram_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/spectrograms \
    --max_samples 1000
```

### Step 2: Extract Environmental Features

```bash
python code/phase2/extract_environmental_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/environmental \
    --resume
```

**Test mode (first 1000 samples):**

```bash
python code/phase2/extract_environmental_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/environmental \
    --max_samples 1000
```

### Step 3: Pack Features to HDF5

```bash
python code/phase2/pack_features_to_hdf5.py \
    --manifest data/manifests/unified_manifest.csv \
    --spectrogram_dir data/features/spectrograms \
    --environmental_dir data/features/environmental \
    --output_dir data/features
```

### Step 4: Verify Features

```bash
python code/phase2/verify_features.py \
    --manifest data/features/features_manifest_unified.csv \
    --spectrogram_h5 data/features/logmel_packed.h5 \
    --environmental_h5 data/features/environmental_packed.h5
```

### Run All Steps (Orchestrator)

```bash
python code/phase2/run_phase2.py
```

**With resume (skip existing files):**

```bash
python code/phase2/run_phase2.py --resume
```

**Test mode:**

```bash
python code/phase2/run_phase2.py --max_samples 1000
```

**Skip specific steps:**

```bash
python code/phase2/run_phase2.py --skip-steps pack,verify
```

---

## ✅ Success Criteria

- [x] Spectrogram features extracted for all samples (1,893,919 samples)
- [x] Environmental features extracted for all samples (1,893,919 samples)
- [x] Features packed into HDF5 format (103.04 GB + 0.07 GB)
- [x] Feature indices linked to manifest
- [x] Feature verification passed (no missing/corrupted features)
- [x] Statistics report generated (feature distributions)

---

## 📊 Final Results

**Status**: ✅ **PHASE 2 COMPLETE**

### Final Dataset:

| Feature Type               | Samples       | Shape     | File Size | Status      |
| -------------------------- | ------------- | --------- | --------- | ----------- |
| **Log-Mel Spectrograms**   | **1,893,919** | [64, 400] | 103.04 GB | ✅ Complete |
| **Environmental Features** | **1,893,919** | [12]      | 0.07 GB   | ✅ Complete |

### Processing Results:

- **Total Samples Processed**: 1,893,919 (100% of unified manifest)
- **Spectrogram Extraction**: 1,893,919 successful (all samples)
- **Environmental Extraction**: 1,893,919 successful (all samples)
- **Packing**: Both HDF5 files created successfully
- **Verification**: All features valid (no NaN/Inf values)

### Feature Statistics:

**Spectrogram Features:**

- Value range: [-80.00, 0.00] dB
- Mean: -39.11 dB
- Standard deviation: 31.01 dB
- Shape: (1,893,919, 64, 400) ✓
- No NaN or Inf values ✓

**Environmental Features:**

- Value range: [-81.73, 58.54]
- Mean: -1.14
- Standard deviation: 13.85
- Shape: (1,893,919, 12) ✓
- No NaN or Inf values ✓

### Processing Time (Actual):

- **Spectrogram Extraction**: 6 hours 37 minutes (1,893,919 samples)
- **Environmental Extraction**: 5 hours 26 minutes (for remaining 754,890 samples)
- **Packing to HDF5**: Optimized with batching (~3-4 hours for spectrograms)
- **Verification**: 48 minutes 17 seconds (spectrograms), ~1 second (environmental)
- **Total**: ~15-16 hours (with optimizations)

### Output Files:

- `data/features/logmel_packed.h5` (103.04 GB)
- `data/features/environmental_packed.h5` (0.07 GB)
- `data/features/features_manifest_unified.csv` (1,893,919 rows)
- `data/features/verification_report.json`
- `data/features/packing_stats.json`

**⚠️ Disk Space Optimization:**

After successful packing and verification, you can **delete the individual .npy files** to free up ~103 GB of disk space:

```bash
# Windows PowerShell
Remove-Item -Recurse -Force data\features\spectrograms
Remove-Item -Recurse -Force data\features\environmental

# Linux/Mac
rm -r data/features/spectrograms
rm -r data/features/environmental
```

**Why safe to delete**: The HDF5 files contain all features in a more efficient format. Individual .npy files are only needed during extraction and packing phases.

---

## ⚠️ Challenges & Solutions

### Challenge 1: Memory Constraints

**Problem**: Loading all features into memory  
**Solution**: Use HDF5 with chunked storage, streaming loading

### Challenge 2: Variable-Length Audio

**Problem**: Audio files have different durations  
**Solution**: Pad/truncate to fixed length (400 frames)

### Challenge 3: Feature Extraction Speed

**Problem**: Extracting 1.4M samples takes time  
**Solution**: Resume capability (`--resume` flag), batch processing

### Challenge 4: Invalid Audio Files

**Problem**: Some files may be corrupted  
**Solution**: Error handling, skip corrupted files, log issues

---

## 🔗 Dependencies

**Prerequisites:**

- ✅ Phase 1: Unified Dataset Preparation
- ✅ Audio files accessible at specified paths
- ✅ `data/manifests/unified_manifest.csv` exists

**Required Python Packages:**

- `h5py` - For HDF5 file operations (install with `pip install h5py`)
- `librosa` - For audio processing and feature extraction
- `numpy`, `pandas`, `tqdm` - Standard data processing libraries
- All dependencies listed in `requirements.txt`

**Next Phase:**

- Phase 3: Hybrid Model Architecture (requires extracted features)

---

## 📝 Notes

- Feature extraction is **time-consuming** - plan accordingly
- Use `--resume` flag to continue from where you left off
- Test with `--max_samples 1000` before running full extraction
- Verify features match expected shapes and ranges
- Keep feature extraction scripts modular for reuse
- Document any preprocessing steps applied
- Consider caching intermediate results

---

## 🔍 Feature Verification Checklist

- [x] Spectrogram shape: `[64, 400]` ✓
- [x] Environmental shape: `[12]` ✓
- [x] No NaN or Inf values ✓
- [x] Feature ranges reasonable ✓
- [x] All samples have features ✓
- [x] Indices match manifest rows ✓

**Verification Status**: ✅ **ALL CHECKS PASSED**

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'h5py'

**Solution**: Install h5py with `pip install h5py` or install all requirements: `pip install -r requirements.txt`

### Issue: Out of Memory

**Solution**: Process in batches, use `--max_samples` to test with smaller subset first

### Issue: Missing Features

**Solution**: Check error logs in output directories, verify audio files exist

### Issue: Shape Mismatches

**Solution**: Verify audio files are valid, check extraction parameters

### Issue: Slow Extraction

**Solution**: Use `--resume` to continue, consider parallel processing (future enhancement)

### Issue: DtypeWarning when loading manifest

**Solution**: Scripts now use `low_memory=False` to handle mixed types correctly

---

---

## ✅ Phase 2 Completion Summary

**All Steps Completed Successfully:**

- ✅ Step 1: Spectrogram features extracted (1,893,919 samples)
- ✅ Step 2: Environmental features extracted (1,893,919 samples)
- ✅ Step 3: Features packed to HDF5 (103.04 GB + 0.07 GB)
- ✅ Step 4: Features verified (all valid, no errors)
- ✅ Step 5: Manifest updated with feature indices
- ✅ Step 6: Statistics and verification reports generated

**Output Files Ready for Phase 3:**

- `data/features/logmel_packed.h5` (103.04 GB)
- `data/features/environmental_packed.h5` (0.07 GB)
- `data/features/features_manifest_unified.csv` (1,893,919 rows)
- `data/features/verification_report.json`
- `data/features/packing_stats.json`

**Next Phase**: Phase 3 - Hybrid Model Architecture

---

**Last Updated**: December 2025  
**Status**: ✅ **COMPLETE**
