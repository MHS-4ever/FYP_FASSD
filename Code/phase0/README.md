# Phase 0: Real-World Data Collection - Technical Guide

This directory contains all scripts and utilities for automated real-world data collection for Phase 0 of the FASSD project.

## 📋 Overview

**Goal**: Collect 10,000+ real-world audio samples using automated methods with minimal manual work.

**Strategy**:

1. Download public datasets (LibriSpeech, VCTK, optional VoxCeleb1)
2. Automated YouTube downloading
3. Small manual collection (300-500 clips)
4. Generate fake audio with TTS
5. Process and verify all audio

**⚠️ Important**: VoxCeleb2 (300+ GB) and Common Voice (no longer public) are NOT used. See "Dataset Alternatives" section below.

---

## 📁 Folder Structure

### Expected Directory Hierarchy

```
FYP/
├── Code/
│   └── phase0/
│       ├── README.md                    # This file
│       ├── run_phase0.py                # Master orchestrator
│       ├── download_librispeech.py      # LibriSpeech helper
│       ├── download_vctk.py             # VCTK helper
│       ├── download_youtube.py          # YouTube downloader
│       ├── generate_fake_audio.py       # TTS fake audio generator
│       ├── process_audio.py             # Audio processor
│       ├── create_realworld_manifest.py # Manifest creator
│       └── verify_realworld_data.py     # Quality verifier
│
└── data/
    └── realworld/
        ├── public_datasets/
        │   ├── librispeech/             # LibriSpeech dataset
        │   ├── vctk/                    # VCTK dataset
        │   └── voxceleb1/               # VoxCeleb1 (optional)
        ├── youtube/
        │   ├── broadcast/               # YouTube broadcast audio
        │   ├── podcast/                 # YouTube podcast audio
        │   └── social/                  # YouTube social media audio
        ├── manual/
        │   ├── phone/                   # Manual phone recordings
        │   ├── room/                    # Manual room recordings
        │   └── outdoor/                 # Manual outdoor recordings
        ├── synthetic/
        │   ├── tts/                     # TTS-generated fake audio
        │   └── replay/                  # Replay-simulated audio
        ├── processed/                   # All processed WAV files (16kHz, mono)
        ├── manifest_realworld.csv       # Main manifest file
        ├── quality_report.json          # Quality verification report
        └── statistics/
            └── collection_stats.json    # Collection statistics
```

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Core dependencies
pip install yt-dlp librosa soundfile pandas tqdm numpy

# Optional for TTS generation
pip install TTS  # For XTTS v2 (Coqui)
# OR
pip install tortoise-tts  # For Tortoise TTS
```

**Verify Installation:**

```bash
python -c "import yt_dlp, librosa, soundfile, pandas, tqdm; print('All dependencies installed!')"
```

### Step 2: Download Public Datasets (Manual)

#### LibriSpeech ⭐ RECOMMENDED

**Why**: Small size (6.3 GB), no login, stable servers, 2,484 speakers

**Download Instructions:**

```bash
# Option 1: Using wget (Linux/Mac/Git Bash)
wget http://www.openslr.org/resources/12/train-clean-100.tar.gz
tar -xzf train-clean-100.tar.gz

# Option 2: Using PowerShell (Windows)
Invoke-WebRequest -Uri "http://www.openslr.org/resources/12/train-clean-100.tar.gz" -OutFile "train-clean-100.tar.gz"
# Extract using 7-Zip or similar

# Extract to: data/realworld/public_datasets/librispeech/
```

**Verify Download:**

```bash
python Code/phase0/download_librispeech.py --instructions
python Code/phase0/download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech
```

**URL**: http://www.openslr.org/12/

#### VCTK ⭐ RECOMMENDED

**Why**: Manageable size (~10 GB), stable server, 110 speakers, different accents

**Download Instructions:**

1. Visit: https://datashare.ed.ac.uk/handle/10283/3443
2. Click "Download All" or download individual parts
3. Extract to `data/realworld/public_datasets/vctk/`

**Verify Download:**

```bash
python Code/phase0/download_vctk.py --instructions
python Code/phase0/download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk
```

#### VoxCeleb1 (Optional)

**Warning**: Large dataset, may have download issues. Only use if you have space and bandwidth.

1. Visit: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/voxceleb1/
2. Download VoxCeleb1 (if available and manageable)
3. Extract to `data/realworld/public_datasets/voxceleb1/`

**⚠️ Skip VoxCeleb2**: 300+ GB, requires Git LFS, causes space errors

### Step 3: Download YouTube Audio (Automated)

**Broadcast Audio:**

```bash
python Code/phase0/download_youtube.py --domain broadcast --max_videos 300 --output_dir data/realworld/youtube/broadcast
```

**Podcast Audio:**

```bash
python Code/phase0/download_youtube.py --domain podcast --max_videos 500 --output_dir data/realworld/youtube/podcast
```

**Social Media Audio:**

```bash
python Code/phase0/download_youtube.py --domain social --max_videos 300 --output_dir data/realworld/youtube/social
```

**Expected Output:**

- Downloads audio from YouTube videos
- Automatically splits long videos into 10-20 second clips
- Saves as WAV files (16kHz, mono)
- Auto-labels based on domain

**Time Estimate**: ~2-4 hours per domain (depends on internet speed)

### Step 4: Generate Fake Audio (Automated)

**Using XTTS v2 (Recommended):**

```bash
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method xtts --output_dir data/realworld/synthetic
```

**Using Simple Placeholder (If TTS not available):**

```bash
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method simple --output_dir data/realworld/synthetic
```

**Expected Output:**

- Generates 3,000 fake audio clips using TTS
- Creates both synthesis and replay-simulated fake audio
- Saves as WAV files (16kHz, mono)
- Auto-labeled as "spoof"

**Time Estimate**: ~3-6 hours (depends on GPU availability)

### Step 5: Process All Audio (Automated)

**Process all collected audio:**

```bash
python Code/phase0/process_audio.py --input_dir data/realworld --output_dir data/realworld/processed --target_sr 16000 --min_duration 1.0 --max_duration 10.0
```

**What it does:**

- Converts all audio to WAV format
- Resamples to 16kHz
- Converts to mono
- Truncates/pads to 1-10 seconds
- Normalizes audio levels
- Removes corrupted files

**Expected Output:**

- All processed audio in `data/realworld/processed/`
- Maintains directory structure
- All files are WAV, 16kHz, mono, 1-10 seconds

**Time Estimate**: ~4-8 hours (depends on number of files)

### Step 6: Create Manifest (Automated)

**Create manifest CSV:**

```bash
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv --recursive
```

**Expected Output:**

- Creates `manifest_realworld.csv` with all metadata
- Auto-infers: domain, dataset, label, attack_type, speaker_id
- Includes: filepath, duration, source, etc.

**Manifest Columns:**

- `filepath` - Full path to audio file
- `label` - `bonafide` or `spoof`
- `dataset` - `librispeech`/`vctk`/`voxceleb1`/`youtube`/`manual`/`synthetic`
- `domain` - `broadcast`/`phone`/`podcast`/`social`/`studio`/`read_speech`
- `speaker_id` - Unique speaker identifier
- `source` - `public_dataset`/`youtube`/`manual`/`synthetic`
- `duration` - Audio duration in seconds
- `attack_type` - `bonafide`/`synthesis`/`replay`

**Time Estimate**: ~10-30 minutes

### Step 7: Verify Quality (Automated)

**Verify audio quality:**

```bash
python Code/phase0/verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv --output data/realworld/quality_report.json
```

**What it checks:**

- Audio file existence
- File corruption
- Duration (1-10 seconds)
- Sample rate (16kHz)
- Format (WAV)
- Label accuracy

**Expected Output:**

- Quality report JSON with statistics
- List of problematic files
- Summary statistics

**Time Estimate**: ~15-30 minutes

---

## 🔧 Script Reference

### `run_phase0.py` - Master Orchestrator

Runs all Phase 0 steps in sequence.

**Usage:**

```bash
# Run all steps
python Code/phase0/run_phase0.py --all

# Run specific steps
python Code/phase0/run_phase0.py --youtube --fake --process --manifest --verify

# Customize parameters
python Code/phase0/run_phase0.py --youtube --youtube_max 500 --fake --fake_num 3000
```

**Options:**

- `--all` - Run all automated steps
- `--youtube` - Download YouTube audio
- `--fake` - Generate fake audio
- `--process` - Process audio files
- `--manifest` - Create manifest
- `--verify` - Verify quality
- `--youtube_max N` - Max videos per domain (default: 300)
- `--fake_num N` - Number of fake clips (default: 3000)
- `--data_dir DIR` - Base data directory (default: data/realworld)

---

### `download_librispeech.py` - LibriSpeech Helper

Provides download instructions and verification for LibriSpeech dataset.

**Usage:**

```bash
# Get download instructions
python Code/phase0/download_librispeech.py --instructions

# Verify downloaded dataset
python Code/phase0/download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech
```

**What it does:**

- Prints download instructions
- Verifies dataset structure
- Checks file counts
- Validates audio files

---

### `download_vctk.py` - VCTK Helper

Provides download instructions and verification for VCTK dataset.

**Usage:**

```bash
# Get download instructions
python Code/phase0/download_vctk.py --instructions

# Verify downloaded dataset
python Code/phase0/download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk
```

**What it does:**

- Prints download instructions
- Verifies dataset structure
- Checks file counts
- Validates audio files

---

### `download_youtube.py` - YouTube Audio Downloader

Downloads audio from YouTube videos based on search queries or channels.

**Usage:**

```bash
# Download broadcast audio
python Code/phase0/download_youtube.py --domain broadcast --max_videos 300 --output_dir data/realworld/youtube/broadcast

# Download podcast audio
python Code/phase0/download_youtube.py --domain podcast --max_videos 500 --output_dir data/realworld/youtube/podcast

# Download social media audio
python Code/phase0/download_youtube.py --domain social --max_videos 300 --output_dir data/realworld/youtube/social
```

**Options:**

- `--domain {broadcast,podcast,social}` - Domain type
- `--max_videos N` - Maximum number of videos (default: 300)
- `--output_dir DIR` - Output directory
- `--clip_length N` - Clip length in seconds (default: 10)
- `--overlap N` - Overlap between clips in seconds (default: 1)

**What it does:**

- Downloads audio from YouTube videos
- Splits long videos into clips
- Converts to WAV (16kHz, mono)
- Saves with domain labels

**Dependencies**: `yt-dlp`, `librosa`, `soundfile`

**Time**: ~30-60 seconds per video (depends on length)

---

### `generate_fake_audio.py` - TTS Fake Audio Generator

Generates synthetic speech using TTS models.

**Usage:**

```bash
# Using XTTS v2 (requires: pip install TTS)
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method xtts --output_dir data/realworld/synthetic

# Using Tortoise TTS (requires: pip install tortoise-tts)
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method tortoise --output_dir data/realworld/synthetic

# Using simple placeholder (no TTS library needed)
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method simple --output_dir data/realworld/synthetic
```

**Options:**

- `--num_clips N` - Number of fake clips to generate (default: 3000)
- `--method {xtts,tortoise,simple}` - TTS method (default: simple)
- `--output_dir DIR` - Output directory
- `--include_replay` - Also generate replay-simulated audio (default: True)

**What it does:**

- Generates fake audio using TTS models
- Creates synthesis attacks (TTS-generated)
- Optionally creates replay attacks (simulated)
- Saves as WAV files (16kHz, mono)
- Auto-labeled as "spoof"

**Dependencies**: `TTS` (for XTTS), `tortoise-tts` (for Tortoise), or none (for simple)

**Time**:

- XTTS: ~0.5-1 second per clip (with GPU)
- Tortoise: ~2-5 seconds per clip (with GPU)
- Simple: ~0.1 second per clip (fast but low quality)

---

### `process_audio.py` - Audio Processor

Processes all audio files: converts format, resamples, normalizes.

**Usage:**

```bash
# Process all audio
python Code/phase0/process_audio.py --input_dir data/realworld --output_dir data/realworld/processed --target_sr 16000

# Process specific directory
python Code/phase0/process_audio.py --input_dir data/realworld/youtube --output_dir data/realworld/processed/youtube --recursive False
```

**Options:**

- `--input_dir DIR` - Input directory (required)
- `--output_dir DIR` - Output directory (required)
- `--target_sr N` - Target sample rate (default: 16000)
- `--min_duration N` - Minimum duration in seconds (default: 1.0)
- `--max_duration N` - Maximum duration in seconds (default: 10.0)
- `--recursive` - Process subdirectories recursively (default: True)

**What it does:**

- Converts all audio to WAV format
- Resamples to target sample rate (16kHz)
- Converts to mono
- Truncates/pads to min-max duration
- Normalizes audio levels
- Removes corrupted files
- Preserves directory structure

**Dependencies**: `librosa`, `soundfile`, `tqdm`

**Time**: ~0.1-0.5 seconds per file (depends on file size)

---

### `create_realworld_manifest.py` - Manifest Creator

Creates manifest CSV with all metadata for collected audio files.

**Usage:**

```bash
# Create manifest
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv

# Non-recursive (single directory)
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output manifest.csv --recursive False
```

**Options:**

- `--data_dir DIR` - Directory containing processed audio (required)
- `--output PATH` - Output manifest CSV path (required)
- `--recursive` - Scan subdirectories recursively (default: True)

**What it does:**

- Scans directory for WAV files
- Auto-infers metadata from file paths:
  - Domain (broadcast/podcast/phone/etc.)
  - Dataset (librispeech/vctk/youtube/etc.)
  - Label (bonafide/spoof)
  - Attack type (synthesis/replay)
- Extracts speaker IDs from filenames
- Calculates audio duration
- Creates manifest CSV with all metadata

**Dependencies**: `pandas`, `librosa`, `pathlib`, `tqdm`

**Output Format**: CSV with columns: filepath, label, dataset, domain, speaker_id, source, duration, attack_type

---

### `verify_realworld_data.py` - Quality Verifier

Verifies audio quality and generates quality report.

**Usage:**

```bash
# Verify from manifest
python Code/phase0/verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv --output data/realworld/quality_report.json

# Verify directory directly
python Code/phase0/verify_realworld_data.py --data_dir data/realworld/processed --output quality_report.json
```

**Options:**

- `--manifest PATH` - Manifest CSV file (if provided, uses manifest)
- `--data_dir DIR` - Data directory (if no manifest provided)
- `--output PATH` - Output quality report JSON (required)
- `--min_duration N` - Minimum valid duration (default: 1.0)
- `--max_duration N` - Maximum valid duration (default: 10.0)
- `--target_sr N` - Expected sample rate (default: 16000)

**What it checks:**

- ✅ File existence
- ✅ File corruption (can load audio)
- ✅ Duration (within min-max range)
- ✅ Sample rate (matches target)
- ✅ Format (WAV)
- ✅ Label accuracy (infers from path and checks)

**Output Format**: JSON with:

- Total files checked
- Valid files count
- Invalid files list
- Statistics (duration, sample rate, domain distribution)
- Issues found

**Dependencies**: `pandas`, `librosa`, `json`, `tqdm`

---

## 📊 Expected Outcomes

### After Completion

**File Counts:**

- Public datasets: 10,000-20,000 files
- YouTube: 1,000-1,500 files
- Manual: 300-500 files
- Synthetic: 2,000-3,000 files
- **Total**: 13,000-25,000 files

**Storage:**

- Raw audio: ~5-10 GB
- Processed audio: ~5-10 GB
- Total: ~10-20 GB

**Time:**

- Manual dataset download: 2-4 hours (depends on bandwidth)
- YouTube downloading: 4-8 hours (automated)
- TTS generation: 3-6 hours (depends on GPU)
- Audio processing: 4-8 hours (automated)
- Total: 2-3 days (mostly automated)

**Manifest:**

- Single CSV file: `manifest_realworld.csv`
- ~13K-25K rows
- All required metadata columns
- Ready for Phase 1

---

## ⚠️ Troubleshooting

### YouTube Download Fails

**Problem**: `yt-dlp` not found or download fails

**Solutions:**

```bash
# Reinstall yt-dlp
pip install --upgrade yt-dlp

# Check if installed
yt-dlp --version

# Try with verbose output
python Code/phase0/download_youtube.py --domain broadcast --max_videos 10 --verbose
```

**Common Issues:**

- Network timeout: Use `--max_videos` with smaller numbers, run in batches
- Rate limiting: YouTube may temporarily block, wait 1-2 hours and retry
- Video unavailable: Script automatically skips unavailable videos

---

### TTS Generation Fails

**Problem**: TTS model not available or generation fails

**Solutions:**

```bash
# Install TTS library
pip install TTS

# For XTTS, model downloads automatically on first use
# First run will be slow (downloading model)

# If still fails, use simple method
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method simple
```

**Common Issues:**

- GPU not available: TTS will use CPU (much slower but works)
- Out of memory: Reduce `--num_clips` or use `--method simple`
- Model download fails: Check internet connection, retry

---

### Audio Processing Slow

**Problem**: Processing takes too long

**Solutions:**

```bash
# Process in batches (specific directories)
python Code/phase0/process_audio.py --input_dir data/realworld/youtube --output_dir data/realworld/processed/youtube --recursive False

# Check available disk space
# Processing creates temporary files
```

**Common Issues:**

- Disk space: Ensure 20+ GB free space
- Too many files: Process in smaller batches
- Corrupted files: Script automatically skips them

---

### Manifest Creation Errors

**Problem**: Manifest creation fails or missing metadata

**Solutions:**

```bash
# Verify audio files exist
ls data/realworld/processed/

# Check file permissions
# Ensure all files are readable

# Verify file format
file data/realworld/processed/*.wav  # Should show WAV audio
```

**Common Issues:**

- Files not found: Check `--data_dir` path is correct
- Permission errors: Fix file permissions
- Invalid audio: Run `verify_realworld_data.py` first to find problematic files

---

### Quality Verification Fails

**Problem**: Many files fail quality checks

**Solutions:**

```bash
# Check quality report
cat data/realworld/quality_report.json

# Re-process problematic files
python Code/phase0/process_audio.py --input_dir data/realworld/raw --output_dir data/realworld/processed
```

**Common Issues:**

- Duration too short/long: Adjust `--min_duration` and `--max_duration`
- Wrong sample rate: Ensure processing used `--target_sr 16000`
- Corrupted files: Remove and re-download/re-generate

---

## 📝 Manual Collection Guide

For manual collection (300-500 clips), follow these steps:

### Phone Recordings (50-100 clips)

1. Use WhatsApp voice notes from friends (with permission)
2. Record phone calls (with consent, check legal requirements)
3. Save to: `data/realworld/manual/phone/`
4. Naming: `phone_spk001_clip001.wav`

### Room Recordings (50 clips)

1. Record in different rooms using mobile phone
2. Vary: bedroom, living room, kitchen, bathroom
3. Save to: `data/realworld/manual/room/`
4. Naming: `room_bedroom_spk001_clip001.wav`

### Outdoor Recordings (30-50 clips)

1. Record in outdoor environments
2. Vary: park, street, market, quiet area
3. Save to: `data/realworld/manual/outdoor/`
4. Naming: `outdoor_park_spk001_clip001.wav`

### Social Media (100 clips)

1. Download from platforms (with permission, check ToS)
2. Save to: `data/realworld/manual/social/`
3. Naming: `social_platform_source_spk001_clip001.wav`

**After Manual Collection:**

1. Process all manual files:
   ```bash
   python Code/phase0/process_audio.py --input_dir data/realworld/manual --output_dir data/realworld/processed/manual
   ```
2. Include in manifest (will be auto-detected)

---

## ✅ Checklist

Use this checklist to track progress:

- [ ] Dependencies installed (`yt-dlp`, `librosa`, `soundfile`, `pandas`, `tqdm`)
- [ ] LibriSpeech downloaded and verified (5K-10K samples)
- [ ] VCTK downloaded and verified (2K-5K samples)
- [ ] VoxCeleb1 downloaded (optional, 3K-5K samples)
- [ ] YouTube broadcast audio collected (200-300 videos)
- [ ] YouTube podcast audio collected (500+ videos)
- [ ] YouTube social audio collected (200-300 videos)
- [ ] Fake audio generated (2K-3K clips)
- [ ] Manual collection completed (300-500 clips)
- [ ] All audio processed (WAV, 16kHz, 1-10s)
- [ ] Manifest created (`manifest_realworld.csv`)
- [ ] Quality verified (>95% valid)
- [ ] Statistics report generated
- [ ] Total samples: 10,000+

---

## 🔗 Next Steps

After completing Phase 0:

1. **Verify Output**: Check `manifest_realworld.csv` has all required columns
2. **Review Statistics**: Check `quality_report.json` and `collection_stats.json`
3. **Proceed to Phase 1**: Use `manifest_realworld.csv` in Phase 1 (Unified Dataset Preparation)

---

**Last Updated**: 10 December 2025  
**Status**: Ready for Use
