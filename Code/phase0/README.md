# Phase 0: Real-World Data Collection - Automation Scripts

This directory contains scripts for automated data collection for Phase 0.

## 📋 Overview

**Goal**: Collect 10,000+ real-world audio samples using automated methods.

**Strategy**:

1. Download public datasets (LibriSpeech, VCTK, optional VoxCeleb1)
2. Automated YouTube downloading
3. Small manual collection (300-500 clips)
4. Generate fake audio with TTS
5. Process and verify all audio

**⚠️ Important**: VoxCeleb2 (300+ GB) and Common Voice (no longer public) are NOT used.

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install yt-dlp librosa soundfile pandas tqdm numpy
# Optional for TTS:
pip install TTS  # For XTTS v2
# or
pip install tortoise-tts  # For Tortoise TTS
```

### Step 2: Download Public Datasets (Manual)

**⭐ LibriSpeech (RECOMMENDED - Works perfectly):**

```bash
# Download train-clean-100 (6.3 GB, 251 speakers)
wget http://www.openslr.org/resources/12/train-clean-100.tar.gz
tar -xzf train-clean-100.tar.gz
# Extract to: data/realworld/public_datasets/librispeech/
```

- **Why it works**: Small size, no login, no restrictions, stable server
- **URL**: http://www.openslr.org/12/

**⭐ VCTK (RECOMMENDED - Works perfectly):**

- Visit: https://datashare.ed.ac.uk/handle/10283/3443
- Download (~10 GB, 110 speakers)
- Extract to `data/realworld/public_datasets/vctk/`
- **Why it works**: Manageable size, stable academic server, no restrictions

**VoxCeleb1 (Optional - if you have space):**

- Visit: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/voxceleb1/
- Download VoxCeleb1 (if available and manageable)
- Extract to `data/realworld/public_datasets/voxceleb1/`
- **Note**: VoxCeleb2 is 300+ GB - skip it

**⚠️ NOT AVAILABLE:**

- ❌ **VoxCeleb2**: Too large (300+ GB), requires Git LFS, not feasible
- ❌ **Common Voice**: No longer publicly available, requires login/approval

### Step 3: Download YouTube Audio (Automated)

```bash
# Broadcast audio
python Code/phase0/download_youtube.py --domain broadcast --max_videos 300

# Podcast audio
python Code/phase0/download_youtube.py --domain podcast --max_videos 500

# Social media audio
python Code/phase0/download_youtube.py --domain social --max_videos 300
```

### Step 4: Generate Fake Audio (Automated)

```bash
# Generate 3000 fake clips using TTS
python Code/phase0/generate_fake_audio.py --num_clips 3000 --method xtts
```

**Note**: Requires TTS library. If not available, use `--method simple` (creates placeholders).

### Step 5: Process All Audio (Automated)

```bash
# Process all audio files (convert to WAV, resample to 16kHz)
python Code/phase0/process_audio.py --input_dir data/realworld --output_dir data/realworld/processed
```

### Step 6: Create Manifest (Automated)

```bash
# Create manifest CSV
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv
```

### Step 7: Verify Quality (Automated)

```bash
# Verify audio quality
python Code/phase0/verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv --output data/realworld/quality_report.json
```

## 📁 Scripts Description

### `download_youtube.py`

- Downloads audio from YouTube videos
- Supports broadcast, podcast, and social media domains
- Automatically splits long videos into clips
- Uses `yt-dlp` for downloading

**Usage:**

```bash
python download_youtube.py --domain broadcast --max_videos 300
```

### `generate_fake_audio.py`

- Generates fake audio using TTS models
- Supports XTTS v2, Tortoise TTS, or simple placeholder
- Creates both TTS and replay-simulated fake audio

**Usage:**

```bash
python generate_fake_audio.py --num_clips 3000 --method xtts
```

### `process_audio.py`

- Converts audio to WAV format
- Resamples to 16kHz
- Truncates/pads to desired duration (1-10 seconds)
- Normalizes audio levels

**Usage:**

```bash
python process_audio.py --input_dir data/realworld --output_dir data/realworld/processed
```

### `create_realworld_manifest.py`

- Scans processed audio directory
- Creates manifest CSV with metadata
- Infers domain, dataset, label from file paths
- Extracts speaker IDs and durations

**Usage:**

```bash
python create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv
```

### `verify_realworld_data.py`

- Verifies audio quality
- Checks duration, sample rate, corruption
- Generates quality report JSON

**Usage:**

```bash
python verify_realworld_data.py --manifest data/realworld/manifest_realworld.csv
```

## 📊 Expected Output Structure

```
data/
└── realworld/
    ├── public_datasets/
    │   ├── librispeech/    # LibriSpeech dataset
    │   ├── vctk/           # VCTK dataset
    │   └── voxceleb1/      # VoxCeleb1 (optional)
    ├── youtube/
    │   ├── broadcast/
    │   ├── podcast/
    │   └── social/
    ├── manual/
    │   ├── phone/
    │   └── room/
    ├── synthetic/
    │   ├── tts/
    │   └── replay/
    ├── processed/          # All processed WAV files
    ├── manifest_realworld.csv
    └── quality_report.json
```

## ⚠️ Notes

1. **YouTube Downloads**: Respect YouTube ToS. Use rate limiting if needed.
2. **TTS Models**: Large models require GPU. Use CPU if needed (slower).
3. **Storage**: 10K+ audio files need significant storage (~5-10 GB).
4. **Processing Time**: Processing 10K files takes several hours.
5. **Public Datasets**: Download manually (large files, may take time).

## 🔧 Troubleshooting

### YouTube download fails

- Check internet connection
- Verify `yt-dlp` is installed: `pip install yt-dlp`
- Try with `--verbose` flag for debugging

### TTS generation fails

- Install TTS library: `pip install TTS`
- For XTTS, download model first (automatic on first use)
- Use `--method simple` as fallback

### Audio processing slow

- Use `--recursive False` to process single directory
- Process in batches if needed
- Check available disk space

### Manifest creation errors

- Verify audio files exist at specified paths
- Check file permissions
- Ensure files are WAV format

## 📝 Manual Collection

For manual collection (300-500 clips):

1. **Phone recordings**: Use WhatsApp voice notes, record calls (with consent)
2. **Room recordings**: Record using mobile phone in different rooms
3. **Outdoor recordings**: Record in outdoor environments
4. **Social media**: Download manually from platforms (with permission)

Save manual recordings to `data/realworld/manual/` with subdirectories:

- `phone/` - Phone recordings
- `room/` - Room recordings
- `outdoor/` - Outdoor recordings
- `social/` - Social media downloads

Then process with `process_audio.py` and include in manifest.

## ✅ Success Criteria

- [ ] At least 10,000 audio samples collected
- [ ] All samples processed (WAV, 16kHz, 1-10s)
- [ ] Manifest created with all metadata
- [ ] Quality verification passed (>95% valid)
- [ ] Domain distribution documented

---

**Estimated Time**: 2-3 days (mostly automated, minimal manual work)
