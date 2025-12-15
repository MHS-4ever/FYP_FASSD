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

- Shape: `[64, 400]` per sample (saved as individual .npy files)
- Packed into HDF5: `[N, 64, 400]` for efficient loading

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
- Handle missing/invalid values
- Normalization (StandardScaler) will be applied during training (Phase 4)

**Output Format:**

- Shape: `[12]` per sample (saved as individual .npy files)
- Packed into HDF5: `[N, 12]` for efficient loading

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
│   ├── spectrograms/                 # Individual .npy files
│   │   ├── <audio_name>_logmel.npy
│   │   └── ...
│   ├── environmental/                # Individual .npy files
│   │   ├── <audio_name>_env.npy
│   │   └── ...
│   ├── logmel_packed.h5              # Packed spectrogram features [N, 64, 400]
│   ├── environmental_packed.h5       # Packed environmental features [N, 12]
│   ├── features_manifest_unified.csv # Updated manifest with indices
│   ├── packing_stats.json           # Packing statistics
│   └── verification_report.json     # Feature verification report
└── scalers/
    └── environmental_scaler.pkl      # StandardScaler (created in Phase 4)
```

---

## 🔧 Scripts Overview

### Created Scripts (in `code/phase2/`):

| Script                              | Purpose                                         | Status     |
| ----------------------------------- | ----------------------------------------------- | ---------- |
| `extract_spectrogram_features.py`   | Extract log-mel spectrograms from audio files   | ✅ Created |
| `extract_environmental_features.py` | Extract environmental features from audio files | ✅ Created |
| `pack_features_to_hdf5.py`          | Pack features into HDF5 format                  | ✅ Created |
| `verify_features.py`                | Verify extracted features                       | ✅ Created |
| `run_phase2.py`                     | Run all Phase 2 steps in sequence               | ✅ Created |
| `README.md`                         | Phase 2 documentation and usage guide           | ✅ Created |

### Existing Dependencies:

- ✅ `code/features/environmental_features.py` - Environmental feature extraction class

---

## ✅ Success Criteria

- [x] Scripts created for spectrogram feature extraction
- [x] Scripts created for environmental feature extraction
- [x] Scripts created for packing features to HDF5
- [x] Scripts created for feature verification
- [x] Orchestrator script created (`run_phase2.py`)
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
- ✅ Python packages: `h5py`, `librosa`, `numpy`, `pandas`, `tqdm` (see `requirements.txt`)

**Next Phase:**

- Phase 3: Hybrid Model Architecture (requires extracted features)

---

## 🚀 Usage Examples

### Quick Start (Test Mode)

```bash
# Test with first 1000 samples
python code/phase2/run_phase2.py --max_samples 1000
```

### Full Extraction

```bash
# Run all steps with resume capability
python code/phase2/run_phase2.py --resume
```

### Individual Steps

```bash
# Step 1: Extract spectrograms
python code/phase2/extract_spectrogram_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/spectrograms \
    --resume

# Step 2: Extract environmental features
python code/phase2/extract_environmental_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/environmental \
    --resume

# Step 3: Pack to HDF5
python code/phase2/pack_features_to_hdf5.py \
    --manifest data/manifests/unified_manifest.csv \
    --spectrogram_dir data/features/spectrograms \
    --environmental_dir data/features/environmental \
    --output_dir data/features

# Step 4: Verify features
python code/phase2/verify_features.py \
    --manifest data/features/features_manifest_unified.csv \
    --spectrogram_h5 data/features/logmel_packed.h5 \
    --environmental_h5 data/features/environmental_packed.h5
```

For detailed usage instructions, see `code/phase2/README.md`.

---

## 📝 Notes

- Feature extraction is **time-consuming** - plan accordingly (15-23 hours for full dataset)
- Use `--resume` flag to continue from where you left off
- Test with `--max_samples` before running full extraction
- Verify features match expected shapes and ranges
- All scripts are located in `code/phase2/` folder (consistent with phase0 and phase1)
- Scripts follow the same structure and conventions as previous phases

---

## 🔍 Feature Verification Checklist

- [ ] Spectrogram shape: `[N, 64, 400]`
- [ ] Environmental shape: `[N, 12]`
- [ ] No NaN or Inf values
- [ ] Feature ranges reasonable
- [ ] All samples have features
- [ ] Indices match manifest rows

---

**Last Updated**: December 2025  
**Status**: ⏳ IN PROGRESS (Scripts created, ready for execution)
