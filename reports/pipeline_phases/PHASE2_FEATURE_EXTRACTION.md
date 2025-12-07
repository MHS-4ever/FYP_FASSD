# Phase 2: Feature Extraction

**Status**: ⏳ PENDING  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2-3  
**Dependencies**: Phase 1 (Unified Dataset Preparation)

---

## 🎯 Objective

Extract both spectrogram features (for ResNet CNN branch) and environmental features (for Environmental MLP branch) from all audio files in the unified dataset.

---

## 📋 Tasks

### 1. Extract Spectrogram Features

**Feature Type:** Log-Mel Spectrograms

**Parameters:**
- Sample rate: 16,000 Hz
- Window size: 25ms
- Hop size: 10ms
- Mel bins: 64
- FFT size: 512
- Normalization: Log-scale

**Processing:**
- Extract from all audio files (ASVspoof + Real-world)
- Handle variable-length audio (pad/truncate to fixed length)
- Target length: 400 frames (~4 seconds at 10ms hop)

**Output Format:**
- Shape: `[num_samples, 64, 400]`
- Packed into HDF5 for efficient loading

### 2. Extract Environmental Features

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
- Normalize features (StandardScaler)
- Handle missing/invalid values

**Output Format:**
- Shape: `[num_samples, 12]`
- Packed into HDF5 or CSV

### 3. Pack Features

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

## 📁 Output Files

```
data/
├── features/
│   ├── logmel_packed.h5              # Spectrogram features
│   ├── environmental_packed.h5      # Environmental features
│   └── features_manifest_unified.csv # Updated manifest with indices
└── scalers/
    └── environmental_scaler.pkl      # StandardScaler for environmental features
```

---

## 🔧 Scripts Needed

### Existing:
- ✅ `Code/features/environmental_features.py` - Environmental feature extraction

### To Modify:
- `Code/features/feature_extraction.py` - Add both feature types
- `Code/pack_features_to_hdf5.py` - Pack both feature types

### To Create:
- `Code/extract_unified_features.py` - Unified extraction script
- `Code/verify_features.py` - Feature verification script

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
- Total: ~15-23 hours

---

## ⚠️ Challenges & Solutions

### Challenge 1: Memory Constraints
**Problem**: Loading all features into memory  
**Solution**: Use HDF5 with chunked storage, streaming loading

### Challenge 2: Variable-Length Audio
**Problem**: Audio files have different durations  
**Solution**: Pad/truncate to fixed length (400 frames), or use variable-length handling

### Challenge 3: Feature Extraction Speed
**Problem**: Extracting 1.4M samples takes time  
**Solution**: Parallel processing, batch extraction, resume capability

### Challenge 4: Invalid Audio Files
**Problem**: Some files may be corrupted  
**Solution**: Error handling, skip corrupted files, log issues

---

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 1: Unified Dataset Preparation
- ✅ Audio files accessible at specified paths

**Next Phase:**
- Phase 3: Hybrid Model Architecture (requires extracted features)

---

## 📝 Notes

- Feature extraction is **time-consuming** - plan accordingly
- Verify features match expected shapes and ranges
- Keep feature extraction scripts modular for reuse
- Document any preprocessing steps applied
- Consider caching intermediate results

---

## 🔍 Feature Verification Checklist

- [ ] Spectrogram shape: `[N, 64, 400]`
- [ ] Environmental shape: `[N, 12]`
- [ ] No NaN or Inf values
- [ ] Feature ranges reasonable
- [ ] All samples have features
- [ ] Indices match manifest rows

---

**Last Updated**: [Date]  
**Status**: ⏳ PENDING

