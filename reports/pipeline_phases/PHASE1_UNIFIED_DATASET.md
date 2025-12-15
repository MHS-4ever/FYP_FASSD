# Phase 1: Unified Dataset Preparation

**Status**: ✅ **COMPLETE**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2  
**Dependencies**: Phase 0 (Real-World Data Collection) ✅ COMPLETE  
**Completion Date**: December 2025

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
- ✅ Real-world data (from Phase 0) - 157,414 files

**Important Note:** ASVspoof_PA dataset was recently downloaded and is now included in this
unified pipeline. The previous pipeline only used ASVspoof_LA and ASVspoof_DF. Adding PA provides
comprehensive coverage of all three attack types:

- LA → synthesis attacks (TTS, voice cloning)
- DF → conversion attacks (voice conversion, swapping)
- PA → replay attacks (physical replay of recordings)

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

| Script                                | Purpose                                             | Location       |
| ------------------------------------- | --------------------------------------------------- | -------------- |
| `create_unified_manifest.py`          | Combine ASVspoof + Real-world into unified manifest | `code/phase1/` |
| `create_speaker_independent_split.py` | Create speaker-independent train/val/test splits    | `code/phase1/` |
| `analyze_unified_dataset.py`          | Generate comprehensive dataset statistics           | `code/phase1/` |
| `run_phase1.py`                       | Run all Phase 1 steps in sequence                   | `code/phase1/` |

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

---

## ✅ Success Criteria

- [x] Scripts created for unified manifest creation
- [x] Scripts created for speaker-independent splitting
- [x] Scripts created for dataset statistics analysis
- [x] Orchestrator script created (`run_phase1.py`)
- [x] Unified manifest created with all required columns
- [x] All datasets (LA, DF, PA, Real-world) included
- [x] Speaker-independent splits created
- [x] No speaker overlap between train/test/val
- [x] Balanced real/fake distribution in each split
- [x] Both ASVspoof and Real-world in each split
- [x] Statistics report generated

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

**Note:** Real-world data from Phase 0: 157,414 files (152,932 bonafide + 4,502 spoof)

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

- ✅ Phase 0: Real-World Data Collection (COMPLETE - 157,414 files)
- ✅ ASVspoof datasets downloaded and extracted
- ✅ `data/realworld/manifest_realworld.csv` exists

**Next Phase:**

- Phase 2: Feature Extraction (requires unified manifest)

---

## 📝 Notes

- **ASVspoof_PA is NEW**: This dataset was recently downloaded and is now included for the first time

  - Previous pipeline only used ASVspoof_LA and ASVspoof_DF (missing PA)
  - PA adds replay attack coverage, completing all three attack types

- **Speaker ID Assumptions**:

  - ASVspoof datasets have true speaker IDs from metadata
  - Real-world data uses heuristic speaker IDs (derived from paths/filenames)
  - Speaker identity for real-world data is approximate
  - Documented here for evaluation discussions

- **Stratification is Approximate**:

  - Speaker splitting uses primary (mode) dataset/label for grouping
  - Speakers with both real/fake samples are assigned to one group
  - Provides approximately balanced splits, not perfect stratification

- **Class Imbalance Handling**:

  - Class imbalance is handled during model training (Phase-4) using weighted loss functions
  - **NOT** handled during Phase-1 dataset construction
  - No oversampling, undersampling, or augmentation in Phase-1
  - Phase-1 maintains natural data distribution

- **Freeze Phase-1 Outputs**:

  - Once complete, treat Phase-1 outputs as immutable
  - Do NOT regenerate manifest or reshuffle after completion
  - Ensures reproducibility and prevents data leakage

- **Real-World Spoof**:

  - Real-world synthetic labeled as "synthesis" (same as ASVspoof_LA)
  - Generation methods/quality may differ from ASVspoof synthetic samples

- Speaker-independent split is **CRITICAL** for true generalization
- Use `analyze_unified_dataset.py` as validation checkpoint before Phase-2
- All scripts are located in `code/phase1/` folder (similar structure to Phase 0)

---

---

## 📊 Final Results

### Dataset Statistics

**Total Samples**: 1,893,919  
**Total Speakers**: 73,421

**By Dataset:**

- PA (Physical Access): 943,110 samples (49.8%)
- DF (DeepFake): 611,829 samples (32.3%)
- LA (Logical Access): 181,566 samples (9.6%)
- RealWorld: 157,414 samples (8.3%)

**By Label:**

- Spoof: 1,573,308 samples (83.07%)
- Bonafide: 320,611 samples (16.93%)

**By Attack Type:**

- Replay: 816,480 samples (43.1%)
- Conversion: 589,212 samples (31.1%)
- Bonafide: 320,611 samples (16.9%)
- Synthesis: 167,616 samples (8.9%)

**By Domain:**

- Studio: 1,819,660 samples (96.1%)
- Read Speech: 28,539 samples (1.5%)
- Broadcast: 17,994 samples (0.9%)
- Podcast: 17,512 samples (0.9%)
- Social: 5,712 samples (0.3%)
- Synthetic: 4,502 samples (0.2%)

### Split Distribution

| Split      | Speakers     | Samples   | Real % | Fake % |
| ---------- | ------------ | --------- | ------ | ------ |
| Train      | 58,734 (80%) | 1,483,741 | 16.93% | 83.07% |
| Validation | 7,338 (10%)  | 155,604   | 19.03% | 80.97% |
| Test       | 7,349 (10%)  | 254,574   | 15.61% | 84.39% |

**Validation Checks:** ✅ ALL PASSED

- ✅ No speaker overlap between splits
- ✅ Each split contains both ASVspoof and Real-world data
- ✅ Each split contains both bonafide and spoof samples
- ✅ Real/fake ratios approximately similar across splits
- ✅ No missing datasets in any split

---

## 📁 Generated Files and Their Purpose

### Manifest Files (`data/manifests/`)

#### 1. `unified_manifest.csv` (1,893,919 rows)

**Purpose**: Master manifest containing all datasets combined into a single file.  
**Use**:

- Reference for entire dataset
- Starting point for feature extraction (Phase 2)
- Data analysis and exploration
- Contains all required metadata columns

**Columns:**

- `filepath`: Absolute/relative path to audio file
- `label`: `bonafide` or `spoof`
- `dataset`: `LA`, `DF`, `PA`, or `RealWorld`
- `attack_type`: `bonafide`, `synthesis`, `conversion`, or `replay`
- `domain`: `studio`, `broadcast`, `phone`, `podcast`, `social`, `read_speech`
- `speaker_id`: Unique speaker identifier
- `source`: `clean`, `augmented`, or `realworld`
- `duration`: Audio duration in seconds (optional)

**Why Created**: Single source of truth for all datasets, enables consistent processing across phases.

#### 2. `train_speaker_independent.csv` (1,483,741 rows)

**Purpose**: Training split with 80% of speakers.  
**Use**:

- Primary dataset for model training (Phase 4)
- Feature extraction for training samples
- Data augmentation source

**Why Created**: Speaker-independent split ensures no speaker overlap with test/val sets, enabling true generalization evaluation.

#### 3. `val_speaker_independent.csv` (155,604 rows)

**Purpose**: Validation split with 10% of speakers.  
**Use**:

- Model validation during training
- Hyperparameter tuning
- Early stopping decisions

**Why Created**: Separate validation set prevents overfitting and provides unbiased performance estimates during training.

#### 4. `test_speaker_independent.csv` (254,574 rows)

**Purpose**: Test split with 10% of speakers (unseen during training).  
**Use**:

- Final model evaluation (Phase 5)
- Generalization assessment
- Performance reporting

**Why Created**: Unseen speakers test true generalization ability of the model to new voices and recording conditions.

### Statistics Files

#### 5. `split_statistics.json` (in `data/manifests/` and `data/statistics/`)

**Purpose**: Comprehensive statistics for each split.  
**Use**:

- Quick reference for split distributions
- Validation of split quality
- Documentation for reports

**Contents**:

- Sample counts per split
- Speaker counts per split
- Distribution by dataset, label, attack_type, domain
- Real/fake ratios per split

**Why Created**: Enables quick verification of split quality without loading large CSV files.

#### 6. `speaker_splits.json` (in `data/manifests/`)

**Purpose**: Lists which speakers are assigned to which split.  
**Use**:

- Verify no speaker overlap
- Reproducibility (same speakers in same splits)
- Debugging split issues
- Documentation of speaker assignments

**Why Created**: Ensures reproducibility and enables verification of speaker independence.

#### 7. `unified_dataset_stats.json` (in `data/statistics/`)

**Purpose**: Complete statistics for entire unified dataset.  
**Use**:

- Dataset documentation
- Analysis and reporting
- Validation checkpoint reference

**Contents**:

- Total samples and speakers
- Distribution by dataset, label, attack_type, domain, source
- Cross-tabulations (dataset×label, dataset×domain, label×attack_type)
- Speakers per dataset

**Why Created**: Comprehensive record of dataset composition for documentation and analysis.

---

## ⚠️ Problems Encountered and Solutions

### Problem 1: Performance Issue in Speaker Splitting

**Issue**: Script hung for 15+ minutes during speaker grouping phase.

**Root Cause**: Inefficient implementation using loop with dataframe filtering:

```python
for speaker_id in all_speakers:  # 73,421 iterations
    speaker_data = df[df['speaker_id'] == speaker_id]  # Filters 1.9M rows each time
```

**Solution**: Optimized using pandas `groupby` operation:

```python
speaker_groups = df.groupby('speaker_id').agg({
    'dataset': lambda x: x.mode()[0],
    'label': lambda x: x.mode()[0]
})
```

**Result**: Reduced execution time from 15+ minutes to seconds.

**Lesson Learned**: Always use vectorized pandas operations instead of loops with dataframe filtering for large datasets.

### Problem 2: DtypeWarning During CSV Loading

**Issue**: Pandas DtypeWarning about mixed types in columns.

**Root Cause**: Large CSV files with mixed data types causing pandas to infer dtypes per chunk.

**Solution**: Added `low_memory=False` parameter to `pd.read_csv()`:

```python
df = pd.read_csv(args.manifest, low_memory=False)
```

**Result**: Eliminated warnings and ensured consistent dtype handling.

### Problem 3: FutureWarning About DataFrame Concatenation

**Issue**: FutureWarning about concatenation with empty/all-NA entries.

**Root Cause**: Some columns had all None values causing dtype inference issues.

**Solution**: Improved column alignment and dtype handling before concatenation:

```python
# Align dtypes before concat
for col in common_columns:
    if col in df_asvspoof_aligned.columns and col in df_realworld_aligned.columns:
        if df_asvspoof_aligned[col].dtype != df_realworld_aligned[col].dtype:
            try:
                df_realworld_aligned[col] = df_realworld_aligned[col].astype(
                    df_asvspoof_aligned[col].dtype
                )
            except (ValueError, TypeError):
                pass
```

**Result**: Warning suppressed, cleaner output.

---

## 🔍 Key Implementation Details

### Speaker-Independent Split Strategy

**Approach**: Stratified splitting by speaker groups.

1. **Group Speakers**: Group speakers by primary (mode) dataset and label

   - Example groups: `LA_spoof`, `DF_bonafide`, `RealWorld_bonafide`, etc.
   - Speakers with mixed labels/datasets assigned to one group based on mode

2. **Split Groups**: Within each group, split speakers 80/10/10

   - Maintains approximate balance across splits
   - Ensures both ASVspoof and Real-world in each split

3. **Verify Independence**: Assert no speaker overlap between splits
   - Critical for true generalization testing

**Why This Approach**:

- Preserves dataset diversity in each split
- Maintains approximately balanced distributions
- Ensures speaker independence (no leakage)
- Handles speakers with mixed labels/datasets gracefully

### Label and Attack Type Mapping

**ASVspoof LA**:

- `bonafide` → `bonafide` (attack_type: `bonafide`)
- `spoof` → `spoof` (attack_type: `synthesis`)

**ASVspoof DF**:

- `bonafide` → `bonafide` (attack_type: `bonafide`)
- `spoof` → `spoof` (attack_type: `conversion`)

**ASVspoof PA**:

- `bonafide` → `bonafide` (attack_type: `bonafide`)
- `spoof` → `spoof` (attack_type: `replay`)

**Real-world**:

- All non-synthetic → `bonafide` (attack_type: `bonafide`)
- Synthetic domain → `spoof` (attack_type: `synthesis`)
- Domains preserved: `broadcast`, `podcast`, `social`, `studio`, `read_speech`, `synthetic`

**Important Note**: Real-world synthetic samples use same "synthesis" label as ASVspoof_LA, but generation methods/quality may differ. This distinction may be relevant in later analysis phases.

---

## 🎯 Validation Results Summary

### Split Quality Metrics

**Speaker Distribution**:

- Train: 58,734 speakers (exactly 80% of 73,421)
- Validation: 7,338 speakers (10%)
- Test: 7,349 speakers (10%)
- **Total**: 73,421 speakers ✓

**Sample Distribution**:

- Train: 1,483,741 samples (78.3%)
- Validation: 155,604 samples (8.2%)
- Test: 254,574 samples (13.4%)
- **Total**: 1,893,919 samples ✓

**Note**: Test set has more samples despite similar speaker count, indicating some test speakers have more samples. This is expected and acceptable.

**Real/Fake Balance**:

- Train: 16.93% real / 83.07% fake
- Validation: 19.03% real / 80.97% fake
- Test: 15.61% real / 84.39% fake
- **Variation**: ±3.42% (acceptable for approximate stratification)

**Dataset Coverage per Split**:
All splits contain:

- ✅ ASVspoof LA samples
- ✅ ASVspoof DF samples
- ✅ ASVspoof PA samples
- ✅ Real-world samples
- ✅ Both bonafide and spoof samples

**Speaker Independence**: ✅ VERIFIED

- No speaker overlap between train/val/test
- All speakers assigned to exactly one split

---

## 💡 Design Decisions and Rationale

### 1. Why Speaker-Independent Splits?

**Decision**: Split by speaker, not by sample.

**Rationale**:

- Prevents data leakage (same speaker's samples in train and test)
- Enables true generalization testing
- Critical for evaluating model performance on unseen voices
- Industry standard for speaker recognition tasks

**Trade-off**: Some imbalance in sample counts across splits (acceptable).

### 2. Why Approximate Stratification?

**Decision**: Use mode (most common) label/dataset for grouping speakers with mixed labels.

**Rationale**:

- Speakers with both real/fake samples are rare but exist
- Perfect stratification would require complex multi-label handling
- Approximate stratification maintains balance while being practical
- Acceptable for Phase-1 dataset construction

**Trade-off**: Slight skew in balance (documented and acceptable).

### 3. Why No Data Balancing in Phase-1?

**Decision**: Maintain natural class imbalance (83% fake / 17% real).

**Rationale**:

- Phase-1 is for dataset construction, not preprocessing
- Class imbalance will be handled during training (Phase-4) with weighted loss
- Preserves original data distribution for analysis
- Separates concerns (data construction vs. model training)

**Trade-off**: Imbalanced splits (handled in Phase-4).

### 4. Why Freeze Phase-1 Outputs?

**Decision**: Treat Phase-1 outputs as immutable after validation.

**Rationale**:

- Ensures reproducibility across all subsequent phases
- Prevents accidental data leakage from regeneration
- Provides stable foundation for all experiments
- Critical for scientific rigor

**Implementation**: Once validated, outputs should not be regenerated or reshuffled.

---

## 📈 Dataset Comparison: Expected vs. Actual

| Metric          | Expected | Actual        | Status                              |
| --------------- | -------- | ------------- | ----------------------------------- |
| Total Samples   | ~1.5M    | 1,893,919     | ✅ More (PA larger than expected)   |
| Real/Fake Ratio | ~14%/86% | 16.93%/83.07% | ✅ Close match                      |
| ASVspoof LA     | ~600K    | 181,566       | ℹ️ Different (eval set only)        |
| ASVspoof DF     | ~260K    | 611,829       | ℹ️ Different (larger than expected) |
| ASVspoof PA     | ~540K    | 943,110       | ℹ️ Different (larger than expected) |
| Real-world      | ~157K    | 157,414       | ✅ Match                            |
| Total Speakers  | Unknown  | 73,421        | ✅ Recorded                         |

**Notes**:

- Actual ASVspoof counts differ from expected because we're using the evaluation sets, which have different distributions than training sets.
- PA dataset is significantly larger than expected, but this is beneficial for comprehensive replay attack coverage.
- Overall dataset size exceeds expectations, providing more data for training.

---

## 🔗 Integration with Other Phases

### Input from Phase 0:

- `data/realworld/manifest_realworld.csv` (157,414 files)
- Real-world audio files in `data/realworld/processed/`

### Output for Phase 2 (Feature Extraction):

- `data/manifests/train_speaker_independent.csv` - Training samples for feature extraction
- `data/manifests/val_speaker_independent.csv` - Validation samples
- `data/manifests/test_speaker_independent.csv` - Test samples (for final evaluation only)

### Output for Phase 4 (Training):

- All split manifests for model training
- Statistics for class weighting calculations

### Output for Phase 5 (Evaluation):

- Test split for final model evaluation
- Statistics for performance reporting

---

**Last Updated**: December 2025  
**Status**: ✅ **COMPLETE**  
**Validated**: ✅ All checks passed  
**Ready for Phase 2**: ✅ Yes
