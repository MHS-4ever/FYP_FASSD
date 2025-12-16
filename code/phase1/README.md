# Phase 1: Unified Dataset Preparation

**Status**: ⏳ IN PROGRESS  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2  
**Dependencies**: Phase 0 (Real-World Data Collection) ✅ COMPLETE

---

## 🎯 Objective

Combine all datasets (ASVspoof LA/DF/PA + Real-world) into a unified manifest with proper labels, metadata, and speaker-independent splits.

---

## 📋 Tasks

### 1. Create Unified Manifest ✅

**Combine Datasets:**

- ✅ ASVspoof_LA (Logical Access) - real + fake
- ✅ ASVspoof_DF (DeepFake) - real + fake
- ✅ ASVspoof_PA (Physical Access) - real + fake ⭐ **NEWLY ADDED** (was not used in previous pipeline)
- ✅ Real-world data (from Phase 0)

**Note:** ASVspoof_PA dataset was recently downloaded and is now included in this unified pipeline.
The previous pipeline only used ASVspoof_LA and ASVspoof_DF. Adding PA provides comprehensive
coverage of all attack types (synthesis, conversion, and replay attacks).

**Manifest Columns:**

- `filepath` - Path to audio file
- `label` - `bonafide` or `spoof`
- `dataset` - `LA`/`DF`/`PA`/`RealWorld`
- `attack_type` - `bonafide`/`synthesis`/`conversion`/`replay`
- `domain` - `studio`/`broadcast`/`phone`/`podcast`/`social`/`read_speech`
- `speaker_id` - Unique speaker identifier
- `source` - `clean`/`augmented`/`realworld`
- `duration` - Audio duration in seconds (optional)

**Label Mapping:**

```
ASVspoof LA:  bonafide → bonafide
              spoof → synthesis (TTS, voice cloning)

ASVspoof DF:  bonafide → bonafide
              spoof → conversion (voice conversion, swapping)

ASVspoof PA:  bonafide → bonafide
              spoof → replay (replay attacks)

Real-world:   all → bonafide (except synthetic)
              synthetic → spoof (synthesis)
              domain → broadcast/phone/podcast/social/studio/read_speech
```

### 2. Speaker-Independent Split ✅

**Split Strategy:**

- Split by **speaker** (not by sample)
- Ensure **NO speaker overlap** between train/test/val
- Balance real/fake distribution in each split
- Ensure both domains (ASVspoof + Real-world) in train and test

**Split Ratios:**

- Train: 80% of speakers
- Validation: 10% of speakers
- Test: 10% of speakers

**Requirements:**

- Each split contains both ASVspoof and Real-world data
- Each split maintains similar real/fake ratio
- Speaker IDs tracked to prevent leakage

### 3. Data Statistics ✅

**Report:**

- Total samples per dataset
- Total samples per attack type
- Total samples per domain
- Speaker count per split
- Real/fake distribution per split
- Domain distribution per split

---

## 🚀 Scripts Overview

| Script                                | Purpose                                             | Usage                                        |
| ------------------------------------- | --------------------------------------------------- | -------------------------------------------- |
| `create_unified_manifest.py`          | Combine ASVspoof + Real-world into unified manifest | `python create_unified_manifest.py`          |
| `create_speaker_independent_split.py` | Create speaker-independent train/val/test splits    | `python create_speaker_independent_split.py` |
| `analyze_unified_dataset.py`          | Generate comprehensive dataset statistics           | `python analyze_unified_dataset.py`          |
| `run_phase1.py`                       | Run all Phase 1 steps in sequence                   | `python run_phase1.py`                       |

---

## 📁 Output Files

```
data/
├── manifests/
│   ├── unified_manifest.csv              # Combined manifest (ASVspoof + Real-world)
│   ├── train_speaker_independent.csv     # Training split
│   ├── val_speaker_independent.csv       # Validation split
│   ├── test_speaker_independent.csv      # Test split
│   ├── split_statistics.json             # Split statistics
│   └── speaker_splits.json               # Speaker assignments per split
└── statistics/
    ├── unified_dataset_stats.json        # Unified dataset statistics
    └── split_statistics.json             # Split statistics (duplicate)
```

---

## 🔧 Common Commands

### Step 1: Create Unified Manifest

```bash
python code/phase1/create_unified_manifest.py \
    --asvspoof_manifest data/manifests/unified_asvspoof_manifest.csv \
    --realworld_manifest data/realworld/manifest_realworld.csv \
    --output data/manifests/unified_manifest.csv
```

**Note:** If ASVspoof manifest doesn't exist, the script will create it automatically if you provide:

```bash
python code/phase1/create_unified_manifest.py \
    --asvspoof_base_dir E:\FYP\DataSet\English \
    --realworld_manifest data/realworld/manifest_realworld.csv \
    --output data/manifests/unified_manifest.csv
```

### Step 2: Create Speaker-Independent Splits

```bash
python code/phase1/create_speaker_independent_split.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/manifests \
    --train_ratio 0.8 \
    --val_ratio 0.1 \
    --test_ratio 0.1 \
    --random_seed 42
```

### Step 3: Analyze Dataset Statistics

```bash
python code/phase1/analyze_unified_dataset.py \
    --manifest data/manifests/unified_manifest.csv \
    --split_dir data/manifests \
    --output data/statistics/unified_dataset_stats.json
```

### Run All Steps (Orchestrator)

```bash
python code/phase1/run_phase1.py
```

**⚠️ Important**: Before running the orchestrator, it's recommended to run each script manually once to inspect outputs and verify correctness:

```bash
# Step 1: Manual verification
python code/phase1/create_unified_manifest.py
# Inspect output manifest

# Step 2: Manual verification
python code/phase1/create_speaker_independent_split.py
# Inspect split manifests and statistics

# Step 3: Validation checkpoint
python code/phase1/analyze_unified_dataset.py
# Review statistics - this is your validation checkpoint before Phase-2

# Then use orchestrator for repeatability
python code/phase1/run_phase1.py
```

---

## ✅ Success Criteria

- [x] Unified manifest created with all required columns
- [ ] All datasets (LA, DF, PA, Real-world) included
- [ ] Speaker-independent splits created
- [ ] No speaker overlap between train/test/val
- [ ] Balanced real/fake distribution in each split
- [ ] Both ASVspoof and Real-world in each split
- [ ] Statistics report generated

---

## 📊 Expected Statistics

**Target Distribution:**

```
Dataset     | Samples | Real | Fake | Percentage
------------|---------|------|------|------------
ASVspoof LA | ~600K   | ~20K | ~580K| ~85%
ASVspoof DF | ~260K   | ~20K | ~240K| ~10%
ASVspoof PA | ~540K   | ~20K | ~520K| ~5%
Real-world  | ~157K   | ~152K| ~5K  | <1%
-----------------------------------------------
Total       | ~1.5M   | ~212K| ~1.3M| 100%
```

**Split Distribution:**

```
Split       | Speakers | Samples | Real % | Fake %
------------|----------|---------|--------|--------
Train       | 80%      | ~1.2M   | ~14%   | ~86%
Validation  | 10%      | ~150K   | ~14%   | ~86%
Test        | 10%      | ~150K   | ~14%   | ~86%
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Speaker ID Extraction

**Problem**: Not all datasets have speaker IDs  
**Solution**: Extract from filenames or assign unique IDs based on metadata

### Challenge 2: Imbalanced Classes

**Problem**: Heavy fake/real imbalance (86/14)  
**Solution**: Use class weighting during training, stratified splitting

### Challenge 3: Domain Balance

**Problem**: ASVspoof dominates (99%+ of data)  
**Solution**: Ensure Real-world data in all splits, consider oversampling

---

## 🔗 Dependencies

**Prerequisites:**

- ✅ Phase 0: Real-World Data Collection
- ✅ ASVspoof datasets downloaded and extracted
- ✅ `data/realworld/manifest_realworld.csv` exists

**Next Phase:**

- Phase 2: Feature Extraction (requires unified manifest)

---

## 📝 Notes

- **ASVspoof_PA is NEW**: This dataset was recently downloaded and is now included for the first time

  - Previous pipeline only used ASVspoof_LA and ASVspoof_DF (missing PA)
  - PA adds replay attack coverage, completing all three attack types (synthesis, conversion, replay)

- **Speaker ID Assumptions**:

  - ASVspoof datasets have true speaker IDs from metadata
  - Real-world data uses heuristic speaker IDs (derived from paths/filenames or assigned)
  - Speaker identity for real-world data is approximate and may not always be accurate
  - This is acceptable for Phase-1, but should be documented in evaluation discussions

- **Stratification is Approximate**:

  - Speaker splitting uses primary (mode) dataset/label for grouping
  - Speakers appearing in both real and fake samples are assigned to one group
  - This may slightly skew balance but provides approximately balanced splits
  - Perfect stratification is not required for Phase-1

- **Class Imbalance Handling**:

  - Class imbalance is NOT handled during Phase-1 dataset construction
  - No oversampling, undersampling, or augmentation in Phase-1
  - Class imbalance will be handled during model training (Phase-4) using weighted loss functions
  - Phase-1 maintains the natural distribution of the data

- **Freeze Phase-1 Outputs**:

  - Once Phase-1 is complete and verified, treat outputs as immutable
  - Do NOT regenerate unified manifest or reshuffle speakers after Phase-1
  - Use Phase-1 outputs consistently for all subsequent phases
  - This ensures reproducibility and prevents data leakage

- **Real-World Spoof Note**:

  - Real-world synthetic samples are labeled as "synthesis" (same as ASVspoof_LA)
  - However, generation methods and quality may differ between ASVspoof and real-world synthetic
  - This distinction may be relevant in later analysis phases

- Speaker-independent split is **CRITICAL** for true generalization
- Keep track of which speakers are in which split
- Use `analyze_unified_dataset.py` as a validation checkpoint before Phase-2
- All scripts are located in `code/phase1/` folder (similar structure to Phase 0)

---

**Last Updated**: December 2025  
**Status**: ⏳ IN PROGRESS
