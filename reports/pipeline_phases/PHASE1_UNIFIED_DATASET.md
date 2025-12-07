# Phase 1: Unified Dataset Preparation

**Status**: ⏳ PENDING  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 2  
**Dependencies**: Phase 0 (Real-World Data Collection)

---

## 🎯 Objective

Combine all datasets (ASVspoof LA/DF/PA + Real-world) into a unified manifest with proper labels, metadata, and speaker-independent splits.

---

## 📋 Tasks

### 1. Create Unified Manifest

**Combine Datasets:**
- ✅ ASVspoof_LA (Logical Access) - real + fake
- ✅ ASVspoof_DF (DeepFake) - real + fake
- ✅ ASVspoof_PA (Physical Access) - real + fake
- ✅ Real-world data (from Phase 0)

**Manifest Columns:**
- `filepath` - Path to audio file
- `label` - `bonafide` or `spoof`
- `dataset` - `LA`/`DF`/`PA`/`RealWorld`
- `attack_type` - `bonafide`/`synthesis`/`conversion`/`replay`
- `domain` - `studio`/`broadcast`/`phone`/`podcast`/`social`
- `speaker_id` - Unique speaker identifier
- `source` - `clean`/`augmented`/`realworld`

**Label Mapping:**
```
ASVspoof LA:  bonafide → bonafide
              spoof → synthesis (TTS, voice cloning)

ASVspoof DF:  bonafide → bonafide
              spoof → conversion (voice conversion, swapping)

ASVspoof PA:  bonafide → bonafide
              spoof → replay (replay attacks)

Real-world:   all → bonafide
              domain → broadcast/phone/podcast/social
```

### 2. Speaker-Independent Split

**Split Strategy:**
- Split by **speaker** (not by sample)
- Ensure **NO speaker overlap** between train/test
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

### 3. Data Statistics

**Report:**
- Total samples per dataset
- Total samples per attack type
- Total samples per domain
- Speaker count per split
- Real/fake distribution per split
- Domain distribution per split

---

## 📁 Output Files

```
data/
├── manifests/
│   ├── unified_asvspoof_manifest.csv      # Combined manifest
│   ├── train_speaker_independent.csv       # Training split
│   ├── val_speaker_independent.csv        # Validation split
│   └── test_speaker_independent.csv        # Test split
└── statistics/
    └── unified_dataset_stats.json          # Dataset statistics
```

---

## 🔧 Scripts Needed

### Existing:
- ✅ `Code/create_unified_manifest.py` - Already created

### To Create:
- `Code/create_speaker_independent_split.py` - Speaker-based splitting
- `Code/analyze_unified_dataset.py` - Statistics generation

---

## ✅ Success Criteria

- [ ] Unified manifest created with all required columns
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
Real-world  | ~13K    | ~13K | 0    | <1%
-----------------------------------------------
Total       | ~1.4M   | ~73K | ~1.3M| 100%
```

**Split Distribution:**
```
Split       | Speakers | Samples | Real % | Fake %
------------|----------|---------|--------|--------
Train       | 80%      | ~1.1M   | ~5%    | ~95%
Validation  | 10%      | ~140K   | ~5%    | ~95%
Test        | 10%      | ~140K   | ~5%    | ~95%
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Speaker ID Extraction
**Problem**: Not all datasets have speaker IDs  
**Solution**: Extract from filenames or assign unique IDs based on metadata

### Challenge 2: Imbalanced Classes
**Problem**: Heavy fake/real imbalance (95/5)  
**Solution**: Use class weighting during training, stratified splitting

### Challenge 3: Domain Balance
**Problem**: ASVspoof dominates (99%+ of data)  
**Solution**: Ensure Real-world data in all splits, consider oversampling

---

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 0: Real-World Data Collection
- ✅ ASVspoof datasets downloaded and extracted

**Next Phase:**
- Phase 2: Feature Extraction (requires unified manifest)

---

## 📝 Notes

- Speaker-independent split is **CRITICAL** for true generalization
- Document any assumptions made about speaker IDs
- Keep track of which speakers are in which split
- Consider stratified sampling to maintain distributions

---

**Last Updated**: [Date]  
**Status**: ⏳ PENDING

