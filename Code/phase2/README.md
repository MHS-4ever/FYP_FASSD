# Phase 2: Feature Extraction

**Status**: ⏳ IN PROGRESS  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2-3  
**Dependencies**: Phase 1 (Unified Dataset Preparation) ✅ COMPLETE

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

| Script                                | Purpose                                             | Usage                                        |
| ------------------------------------- | --------------------------------------------------- | -------------------------------------------- |
| `extract_spectrogram_features.py`    | Extract log-mel spectrograms from audio files      | `python extract_spectrogram_features.py`     |
| `extract_environmental_features.py`  | Extract environmental features from audio files    | `python extract_environmental_features.py`  |
| `pack_features_to_hdf5.py`           | Pack features into HDF5 format                      | `python pack_features_to_hdf5.py`            |
| `verify_features.py`                  | Verify extracted features                          | `python verify_features.py`                  |
| `run_phase2.py`                       | Run all Phase 2 steps in sequence                  | `python run_phase2.py`                       |

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

- [ ] Spectrogram features extracted for all samples
- [ ] Environmental features extracted for all samples
- [ ] Features packed into HDF5 format
- [ ] Feature indices linked to manifest
- [ ] Feature verification passed (no missing/corrupted features)
- [ ] Statistics report generated (feature distributions)

---

## 📊 Expected Statistics

**Feature Extraction:**
```
Feature Type        | Shape        | Size (GB) | Samples
--------------------|--------------|-----------|----------
Log-Mel Spectrograms| [N, 64, 400] | ~2-3 GB   | ~1.4M
Environmental       | [N, 12]      | ~0.1 GB   | ~1.4M
```

**Processing Time (Estimated):**
- Spectrogram extraction: ~10-15 hours (for 1.4M samples)
- Environmental extraction: ~5-8 hours (for 1.4M samples)
- Packing: ~30 minutes
- Total: ~15-23 hours

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

- [ ] Spectrogram shape: `[64, 400]`
- [ ] Environmental shape: `[12]`
- [ ] No NaN or Inf values
- [ ] Feature ranges reasonable
- [ ] All samples have features
- [ ] Indices match manifest rows

---

## 🐛 Troubleshooting

### Issue: Out of Memory
**Solution**: Process in batches, use `--max_samples` to test with smaller subset first

### Issue: Missing Features
**Solution**: Check error logs in output directories, verify audio files exist

### Issue: Shape Mismatches
**Solution**: Verify audio files are valid, check extraction parameters

### Issue: Slow Extraction
**Solution**: Use `--resume` to continue, consider parallel processing (future enhancement)

---

**Last Updated**: December 2025  
**Status**: ⏳ IN PROGRESS

