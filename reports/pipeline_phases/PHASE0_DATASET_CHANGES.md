# Phase 0: Dataset Changes - Practical Alternatives

## ❌ Why VoxCeleb2 and Common Voice Don't Work

### VoxCeleb2 Issues
- **Size**: 300+ GB (too large for most systems)
- **Kaggle**: Only 19-20 GB storage per session
- **Git LFS**: Required, causes "no space left on device" errors
- **Multi-part files**: Dataset split into many parts (partaa, partab, etc.)
- **Result**: Impossible to download/extract on Kaggle or limited systems

### Common Voice Issues
- **No longer public**: Moved to Mozilla Data Collective
- **Requires login**: Account and approval needed
- **Region restrictions**: 404 errors in many regions (including Pakistan)
- **HuggingFace removed**: Mirrors no longer available
- **Result**: Cannot download without special access

## ✅ Practical Alternatives That Work

### 1. LibriSpeech (OpenSLR) ⭐ RECOMMENDED

**Why it works:**
- ✅ Small file sizes (train-clean-100 = 6.3 GB)
- ✅ No login required
- ✅ No region restrictions
- ✅ Stable OpenSLR servers
- ✅ Well-organized structure
- ✅ 1,000+ hours, 2,484 speakers

**Download:**
```bash
wget http://www.openslr.org/resources/12/train-clean-100.tar.gz
tar -xzf train-clean-100.tar.gz
```

**URL**: http://www.openslr.org/12/

**Use**: 5,000-10,000 samples (enough for FYP)

### 2. VCTK Corpus ⭐ RECOMMENDED

**Why it works:**
- ✅ Manageable size (~10 GB)
- ✅ Stable academic server (Edinburgh Datashare)
- ✅ No login, no restrictions
- ✅ High-quality studio speech
- ✅ 110 speakers, different accents

**Download:**
- Visit: https://datashare.ed.ac.uk/handle/10283/3443
- Manual download (no direct wget link)

**Use**: 2,000-5,000 samples

### 3. VoxCeleb1 (Optional)

**Why it might work:**
- ✅ Smaller than VoxCeleb2 (if downloadable)
- ✅ 1,000+ speakers from YouTube
- ⚠️ Still large, may have download issues

**Download:**
- Visit: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/voxceleb1/
- Use only if you have space and can download

**Use**: 3,000-5,000 samples (if available)

## 📊 Updated Dataset Strategy

### Primary Sources (Verified Working)
1. **LibriSpeech**: 5,000-10,000 samples (read speech)
2. **VCTK**: 2,000-5,000 samples (studio speech)
3. **VoxCeleb1**: 3,000-5,000 samples (optional, if available)

### Secondary Sources
4. **YouTube**: 1,000-1,500 samples (broadcast, podcast, social)
5. **Manual**: 300-500 samples (phone, room, outdoor)
6. **TTS Generated**: 2,000-3,000 samples (fake audio)

### Total Expected
- **Raw samples**: 13,000-25,000
- **After augmentation**: 130,000-250,000 (10× expansion)

## 🔧 Updated Scripts

### New Helper Scripts
- `Code/phase0/download_librispeech.py` - Verify LibriSpeech dataset
- `Code/phase0/download_vctk.py` - Verify VCTK dataset

### Updated Scripts
- `Code/phase0/create_realworld_manifest.py` - Now recognizes LibriSpeech and VCTK
- `Code/phase0/README.md` - Updated with new dataset instructions

## 📝 Download Instructions

### LibriSpeech
```bash
# Get instructions
python Code/phase0/download_librispeech.py --instructions

# After download, verify
python Code/phase0/download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech
```

### VCTK
```bash
# Get instructions
python Code/phase0/download_vctk.py --instructions

# After download, verify
python Code/phase0/download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk
```

## ✅ Success Criteria (Updated)

- [ ] LibriSpeech downloaded and verified (5K-10K samples)
- [ ] VCTK downloaded and verified (2K-5K samples)
- [ ] VoxCeleb1 downloaded (optional, 3K-5K samples)
- [ ] YouTube audio collected (1K-1.5K samples)
- [ ] Manual collection completed (300-500 samples)
- [ ] Fake audio generated (2K-3K samples)
- [ ] All audio processed and verified
- [ ] Manifest created with all metadata

## 🎯 Result

**We now have a practical, achievable data collection plan using datasets that actually work and are accessible.**

No more impossible downloads or restricted access. All recommended datasets are:
- ✅ Downloadable
- ✅ Manageable size
- ✅ No special permissions
- ✅ Stable servers
- ✅ Well-documented

---

**Last Updated**: December 7, 2025  
**Status**: ✅ UPDATED WITH PRACTICAL ALTERNATIVES

