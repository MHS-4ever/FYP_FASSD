# Phase 0: Real-World Data Collection

**Status**: ✅ **COMPLETE**  
**Final Dataset**: 157,414 valid audio files (6.3x target)

---

## 📋 Quick Reference

### Environment Setup

**Two environments required:**

1. **`fassd`** - Main environment (most scripts)
2. **`ttsgen`** - TTS generation only (isolated to prevent dependency conflicts)

```bash
# Main work
conda activate fassd

# TTS generation only
conda activate ttsgen
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method xtts
conda activate fassd  # Switch back after
```

---

## 🚀 Scripts Overview

| Script                         | Purpose                                           | Environment                      |
| ------------------------------ | ------------------------------------------------- | -------------------------------- |
| `download_youtube.py`          | Download YouTube audio (broadcast/podcast/social) | `fassd`                          |
| `generate_fake_audio.py`       | Generate synthetic audio (TTS)                    | `ttsgen` (or `fassd` for simple) |
| `process_audio.py`             | Process all audio (convert, resample, normalize)  | `fassd`                          |
| `create_realworld_manifest.py` | Create manifest CSV                               | `fassd`                          |
| `verify_realworld_data.py`     | Verify quality                                    | `fassd`                          |
| `remove_invalid_files.py`      | Remove corrupted files from manifest              | `fassd`                          |

---

## 📊 Final Results

**Dataset Statistics:**

- **Total Files**: 157,414 (valid)
- **Bonafide**: 152,932 (97.1%)
- **Spoof**: 4,502 (2.9%)
- **Quality**: 100% valid (exceeds >95% target)

**Distribution:**

- Studio (VCTK): 83,155
- Read Speech (LibriSpeech): 28,539
- Broadcast (YouTube): 17,996
- Podcast (YouTube): 17,529
- Social (YouTube): 5,713
- Synthetic (TTS): 4,502

**Output Files:**

- `data/realworld/manifest_realworld.csv` - Main manifest
- `data/realworld/statistics/collection_stats.json` - Statistics
- `data/realworld/statistics/quality_report.json` - Quality report

---

## 🔧 Common Commands

### Download YouTube Audio

```bash
# Broadcast
python Code/phase0/download_youtube.py --domain broadcast --max_videos 300 --output_dir data/realworld/youtube/broadcast --skip_channels

# Podcast
python Code/phase0/download_youtube.py --domain podcast --max_videos 500 --output_dir data/realworld/youtube/podcast --skip_channels

# Social
python Code/phase0/download_youtube.py --domain social --max_videos 300 --output_dir data/realworld/youtube/social --skip_channels
```

### Generate Fake Audio

```bash
# Using TTS (requires ttsgen environment)
conda activate ttsgen
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method xtts --output_dir data/realworld/synthetic
conda activate fassd

# Simple method (no TTS required)
conda activate fassd
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method simple --output_dir data/realworld/synthetic
```

### Process Audio

```bash
python Code/phase0/process_audio.py --input_dir data/realworld --output_dir data/realworld/processed --target_sr 16000 --min_duration 1.0 --max_duration 10.0
```

### Create Manifest

```bash
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv --recursive
```

### Verify Quality

```bash
# Sample test (1000 files)
python Code/phase0/verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv --output data/realworld/statistics/quality_report.json --sample 1000

# Full verification
python Code/phase0/verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv --output data/realworld/statistics/quality_report.json
```

### Remove Invalid Files

```bash
python Code/phase0/remove_invalid_files.py --manifest data/realworld/manifest_realworld.csv --quality_report data/realworld/statistics/quality_report.json --output data/realworld/manifest_realworld_clean.csv
```

---

## ⚠️ Important Notes

### Two-Environment Setup

**Why?** TTS libraries (XTTS, Tortoise) require old dependencies that conflict with modern PyTorch/librosa.

**Solution:**

- Keep TTS isolated in `ttsgen` environment
- Use `fassd` for all other Phase 0 work
- Never install TTS in `fassd` environment

### Public Datasets

**Download manually:**

- **LibriSpeech**: http://www.openslr.org/12/ (train-clean-100, 6.3 GB)
- **VCTK**: https://datashare.ed.ac.uk/handle/10283/3443 (~10 GB)

**Verify after download:**

```bash
python Code/phase0/download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech
python Code/phase0/download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk
```

---

## 📁 Output Structure

```
data/realworld/
├── manifest_realworld.csv          # Main manifest (157,414 files)
├── statistics/
│   ├── collection_stats.json       # Collection statistics
│   └── quality_report.json         # Quality verification
├── processed/                      # All processed audio (WAV, 16kHz, mono)
│   ├── public_datasets/
│   ├── youtube/
│   └── synthetic/
└── [raw data folders]
```

---

## ✅ Checklist

- [x] Public datasets downloaded (LibriSpeech, VCTK)
- [x] YouTube audio collected (broadcast, podcast, social)
- [x] Synthetic audio generated (TTS + replay)
- [x] All audio processed (16kHz, mono, 1-10s)
- [x] Manifest created
- [x] Quality verified (>95% valid)
- [x] Invalid files removed
- [x] Statistics generated

**Phase 0 Status**: ✅ **COMPLETE**

---

## 🔗 Next Steps

**Phase 1**: Unified Dataset Preparation

- Combine ASVspoof datasets with real-world data
- Create speaker-independent splits
- Generate unified manifests

---

**Last Updated**: December 2025  
**Status**: ✅ Complete (157,414 valid files)
