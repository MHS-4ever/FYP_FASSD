# Phase 0: Real-World Data Collection

**Status**: 🟡 IN PROGRESS  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 1-2 (2-3 days with automation)

---

## 🎯 Objective

Collect diverse real-world audio data to complement ASVspoof dataset using **practical automated methods**. This is **CRITICAL** because ASVspoof alone is insufficient for generalization to real-world audio.

**Strategy**: Use existing public datasets + automated collection + minimal manual work (300-500 clips)

---

## 📋 Tasks

### 1. Download Public Datasets (AUTOMATED - Step 1)

**⭐ Primary Sources (Instant Download):**

**A. VoxCeleb1 + VoxCeleb2** (PERFECT for broadcast/podcast)

- **1.2M+ clips** from YouTube interviews, news, speeches
- **7,000+ speakers** (excellent for speaker independence)
- Contains: Broadcast (TV interviews), Podcasts, Social media-like videos
- **Use subset: 5,000-10,000 samples** (enough for FYP)
- Download: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/

**B. Mozilla Common Voice**

- **9,000+ hours** of real speech
- Many languages, natural environments, background noise
- **Use subset: 5,000-8,000 samples**
- Download: https://commonvoice.mozilla.org/

**C. VCTK Corpus**

- Studio-quality speech, different accents
- Perfect for "clean/studio" domain
- **Use: 500-1,000 samples**
- Download: https://datashare.ed.ac.uk/handle/10283/3443

**Total from Public Datasets: ~10,000-19,000 samples** ✅

### 2. Automated YouTube Collection (AUTOMATED - Step 2)

**Use `yt-dlp` for automated downloading:**

**A. Broadcast Audio (News, Speeches)**

- Channels: Geo News, ARY News, BBC News, DW News, CNN, Fox News
- Download: 200-300 videos → auto-split into 10-20 sec clips
- Auto-label as "broadcast"

**B. Podcast Audio**

- Search: "podcast interviews"
- Download: 500+ videos
- Auto-label as "podcast"

**C. Social Media Audio**

- Search: "tiktok real voice", "ytshorts"
- Download: 200-300 videos
- Auto-label as "social"

**Total from YouTube: ~1,000-1,500 samples** ✅

### 3. Small Manual Collection (MANUAL - Step 3)

**Only 300-500 clips needed for originality:**

| Domain             | Target | Method                            |
| ------------------ | ------ | --------------------------------- |
| Phone              | 50-100 | WhatsApp voice notes from friends |
| Room recordings    | 50     | Record using mobile phone         |
| Outdoor recordings | 30-50  | Record your own environment       |
| Social media       | 100    | Download manually (or automate)   |

**Total Manual: ~300-500 samples** ✅

### 4. Generate Fake Audio (AUTOMATED - Step 4)

**Use TTS models to generate fake clips:**

**Open-Source TTS:**

- XTTS v2 (Coqui)
- Tortoise TTS
- Bark
- StyleTTS 2
- MetaVoice 1B

**Script to auto-generate:**

- 5 voices × 300 sentences = 1,500 fake clips
- Add replay simulation → +1,500 clips
- **Total fake: ~3,000 clips** ✅

### 5. Data Augmentation (AUTOMATED - Step 5)

**Multiply dataset 10× using augmentation:**

- Noise addition
- Room impulse responses (RIR)
- Codec distortion
- Microphone simulation
- Replay simulation

**From 2,000 raw samples → 20,000 effective samples** ✅

### 6. Label and Organize Audio

**Auto-Labeling Strategy:**

- Public datasets: Auto-label based on dataset name
- YouTube downloads: Auto-label based on search query/channel
- Manual collection: Label during collection
- TTS generated: Auto-label as "spoof"

**Manifest Columns:**

- `filepath` - Path to audio file
- `label` - `bonafide` or `spoof`
- `dataset` - `voxceleb`/`commonvoice`/`vctk`/`youtube`/`manual`/`tts`
- `domain` - `broadcast`/`phone`/`podcast`/`social`/`studio`
- `speaker_id` - Unique speaker identifier (if available)
- `source` - `public_dataset`/`youtube`/`manual`/`synthetic`
- `duration` - Audio duration in seconds
- `attack_type` - `bonafide`/`synthesis`/`replay` (for fake audio)

### 7. Verify Data Quality (AUTOMATED)

**Quality Checks (Automated Script):**

- ✅ Audio quality (no corruption)
- ✅ Duration (minimum 1 second, maximum 10 seconds)
- ✅ Sample rate (16kHz preferred, auto-resample if needed)
- ✅ Format (WAV preferred, auto-convert if needed)
- ✅ Label accuracy (verify against source)
- ✅ Domain distribution balance

**Statistics to Report:**

- Total samples per domain
- Total samples per dataset source
- Average duration per domain
- Speaker count (if available)
- Quality issues found and fixed

---

## 📁 Output Files

```
data/
└── realworld/
    ├── manifest_realworld.csv          # Main manifest
    ├── public_datasets/
    │   ├── voxceleb/                  # VoxCeleb samples
    │   ├── commonvoice/               # Common Voice samples
    │   └── vctk/                      # VCTK samples
    ├── youtube/
    │   ├── broadcast/                 # YouTube broadcast audio
    │   ├── podcast/                   # YouTube podcast audio
    │   └── social/                    # YouTube social media audio
    ├── manual/
    │   ├── phone/                     # Manual phone recordings
    │   └── room/                      # Manual room recordings
    ├── synthetic/
    │   ├── tts/                       # TTS-generated fake audio
    │   └── replay/                    # Replay-simulated audio
    └── statistics/
        └── collection_stats.json      # Collection statistics
```

---

## 🔧 Scripts Needed

### To Create:

- ✅ `Code/phase0/download_voxceleb.py` - Download VoxCeleb dataset
- ✅ `Code/phase0/download_commonvoice.py` - Download Common Voice dataset
- ✅ `Code/phase0/download_vctk.py` - Download VCTK dataset
- ✅ `Code/phase0/download_youtube.py` - Automated YouTube downloading
- ✅ `Code/phase0/generate_fake_audio.py` - TTS fake audio generation
- ✅ `Code/phase0/process_audio.py` - Audio processing (convert, resample, split)
- ✅ `Code/phase0/create_realworld_manifest.py` - Manifest creation
- ✅ `Code/phase0/verify_realworld_data.py` - Quality verification

### Manual Tasks (Minimal):

- Download public datasets (one-time, automated scripts help)
- Record 300-500 manual clips (phone, room, outdoor)
- Verify labels (spot-check, not full manual labeling)

---

## ✅ Success Criteria

- [ ] Public datasets downloaded (VoxCeleb, Common Voice, VCTK)
- [ ] YouTube audio collected (broadcast, podcast, social)
- [ ] Manual collection completed (300-500 clips)
- [ ] Fake audio generated (2,000-3,000 TTS clips)
- [ ] At least 10,000+ real-world audio samples collected
- [ ] All samples processed (converted to WAV, resampled to 16kHz)
- [ ] All samples labeled and verified
- [ ] Manifest created with all required columns
- [ ] Quality checks passed
- [ ] Domain distribution documented
- [ ] Statistics report generated

---

## 📊 Expected Statistics

**Target Distribution (After Collection):**

```
Source              | Samples | Domain Breakdown
--------------------|---------|------------------
Public Datasets     | 10K-19K | VoxCeleb (broadcast/podcast), Common Voice (mixed), VCTK (studio)
YouTube (Auto)      | 1K-1.5K | Broadcast, Podcast, Social
Manual Collection   | 300-500 | Phone, Room, Outdoor
TTS Generated       | 2K-3K   | Synthetic (fake)
-----------------------------------
Total Raw           | 13K-24K |
After Augmentation  | 130K-240K | (10× expansion)
```

**Domain Distribution (Target):**

```
Domain      | Samples | Percentage | Sources
------------|---------|------------|------------------
Broadcast   | 5,000+  | ~40%       | VoxCeleb, YouTube
Phone       | 500+    | ~4%        | Manual, Common Voice
Podcast     | 3,000+  | ~24%       | VoxCeleb, YouTube
Social      | 2,000+  | ~16%       | YouTube, Manual
Studio      | 1,000+  | ~8%        | VCTK, VoxCeleb
Synthetic   | 2,000+  | ~16%       | TTS generated
-----------------------------------
Total       | 13,500+ | 100%       |
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Dataset Download Size

**Problem**: VoxCeleb and Common Voice are very large (100GB+)  
**Solution**: Download subsets only (5-10K samples), use download scripts with resume capability

### Challenge 2: YouTube Download Limits

**Problem**: YouTube may rate-limit downloads  
**Solution**: Use `yt-dlp` with rate limiting, download in batches, respect ToS

### Challenge 3: TTS Model Setup

**Problem**: TTS models require setup and may be slow  
**Solution**: Use lightweight models (XTTS v2), batch generation, GPU acceleration

### Challenge 4: Audio Processing Time

**Problem**: Processing 10K+ files takes time  
**Solution**: Parallel processing, batch operations, progress tracking, resume capability

### Challenge 5: Storage Space

**Problem**: 10K+ audio files need significant storage  
**Solution**: Use compression, delete intermediate files, store only final processed WAVs

---

## 🔗 Dependencies

**Prerequisites:**

- None (starting phase)

**Next Phase:**

- Phase 1: Unified Dataset Preparation (requires this phase's output)

---

## 📝 Notes

- This phase is **NON-NEGOTIABLE** - cannot proceed without real-world data
- **Automation is key** - manual collection should be minimal (300-500 clips)
- Use public datasets as primary source (saves weeks of work)
- Document all data sources and licensing information
- Respect YouTube ToS and dataset licenses
- Quality over quantity - verify samples are usable
- Consider ethical implications of data collection

## 🚀 Quick Start Guide

**Step 1: Install Dependencies**

```bash
pip install yt-dlp librosa soundfile pandas tqdm
# For TTS: pip install TTS  # or specific TTS library
```

**Step 2: Download Public Datasets**

```bash
python Code/phase0/download_voxceleb.py --max_samples 10000
python Code/phase0/download_commonvoice.py --max_samples 8000
python Code/phase0/download_vctk.py --max_samples 1000
```

**Step 3: Download YouTube Audio**

```bash
python Code/phase0/download_youtube.py --domain broadcast --max_videos 300
python Code/phase0/download_youtube.py --domain podcast --max_videos 500
python Code/phase0/download_youtube.py --domain social --max_videos 300
```

**Step 4: Generate Fake Audio**

```bash
python Code/phase0/generate_fake_audio.py --num_clips 3000
```

**Step 5: Process and Verify**

```bash
python Code/phase0/process_audio.py --input_dir data/realworld --output_dir data/realworld/processed
python Code/phase0/verify_realworld_data.py --data_dir data/realworld/processed
python Code/phase0/create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv
```

**Estimated Time: 2-3 days** (mostly automated, minimal manual work)

---

**Last Updated**: December 7, 2025  
**Status**: 🟡 IN PROGRESS
