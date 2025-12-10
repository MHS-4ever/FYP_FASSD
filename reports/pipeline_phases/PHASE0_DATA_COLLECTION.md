# Phase 0: Real-World Data Collection

**Status**: 🟡 IN PROGRESS  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 1-2  
**Dependencies**: None (starting phase)

---

## 🎯 Objective

Collect diverse real-world audio data to complement ASVspoof dataset using **practical automated methods**. This is **CRITICAL** because ASVspoof alone is insufficient for generalization to real-world audio.

**Strategy**: Use existing public datasets + automated collection + minimal manual work (300-500 clips)

---

## 📋 Tasks

### 1. Download Public Datasets (AUTOMATED - Step 1)

**⭐ Primary Sources (Verified Working & Downloadable):**

#### A. LibriSpeech (OpenSLR) ⭐ RECOMMENDED

- **1,000+ hours** of read English speech
- **2,484 speakers** (excellent for speaker independence)
- Well-organized, stable download servers
- **Use subset: 5,000-10,000 samples** (enough for FYP)
- Download: http://www.openslr.org/12/ (train-clean-100 = 6.3 GB)
- **Why it works**: Small file sizes, no login, no region restrictions, stable OpenSLR servers

#### B. VCTK Corpus ⭐ RECOMMENDED

- **110 speakers** with different accents
- Studio-quality speech
- Perfect for "clean/studio" domain
- **Use: 2,000-5,000 samples**
- Download: https://datashare.ed.ac.uk/handle/10283/3443 (~10 GB)
- **Why it works**: Manageable size, stable academic server, no login, no restrictions

#### C. VoxCeleb1 (Optional - if available)

- **1,000+ speakers** from YouTube interviews
- Contains: Broadcast (TV interviews), Podcasts
- **Use subset: 3,000-5,000 samples** (if downloadable)
- Download: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/voxceleb1/
- **Note**: VoxCeleb2 is 300+ GB (too large), skip it

**⚠️ NOT AVAILABLE:**

- ❌ **VoxCeleb2**: Too large (300+ GB), requires Git LFS, causes "no space left on device" errors, not feasible
- ❌ **Mozilla Common Voice**: No longer publicly available, moved to Mozilla Data Collective, requires login/approval, region restrictions (404 errors in many regions including Pakistan)

**Total from Public Datasets: ~10,000-20,000 samples** ✅

### 2. Automated YouTube Collection (AUTOMATED - Step 2)

**Use `yt-dlp` for automated downloading:**

#### A. Broadcast Audio (News, Speeches)

- Channels: Geo News, ARY News, BBC News, DW News, CNN, Fox News
- Download: 200-300 videos → auto-split into 10-20 sec clips
- Auto-label as "broadcast"

#### B. Podcast Audio

- Search: "podcast interviews"
- Download: 500+ videos
- Auto-label as "podcast"

#### C. Social Media Audio

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
- `dataset` - `librispeech`/`vctk`/`voxceleb1`/`youtube`/`manual`/`synthetic`
- `domain` - `broadcast`/`phone`/`podcast`/`social`/`studio`/`read_speech`
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
    │   ├── librispeech/               # LibriSpeech samples
    │   ├── vctk/                      # VCTK samples
    │   └── voxceleb1/                 # VoxCeleb1 samples (optional)
    ├── youtube/
    │   ├── broadcast/                 # YouTube broadcast audio
    │   ├── podcast/                   # YouTube podcast audio
    │   └── social/                    # YouTube social media audio
    ├── manual/
    │   ├── phone/                     # Manual phone recordings
    │   ├── room/                      # Manual room recordings
    │   └── outdoor/                   # Manual outdoor recordings
    ├── synthetic/
    │   ├── tts/                       # TTS-generated fake audio
    │   └── replay/                    # Replay-simulated audio
    ├── processed/                     # All processed WAV files
    └── statistics/
        └── collection_stats.json      # Collection statistics
```

---

## 🔧 Scripts Needed

### Existing:

- ✅ `Code/phase0/download_librispeech.py` - Download/verify LibriSpeech dataset
- ✅ `Code/phase0/download_vctk.py` - Download/verify VCTK dataset
- ✅ `Code/phase0/download_youtube.py` - Automated YouTube downloading
- ✅ `Code/phase0/generate_fake_audio.py` - TTS fake audio generation
- ✅ `Code/phase0/process_audio.py` - Audio processing (convert, resample, split)
- ✅ `Code/phase0/create_realworld_manifest.py` - Manifest creation
- ✅ `Code/phase0/verify_realworld_data.py` - Quality verification
- ✅ `Code/phase0/run_phase0.py` - Master orchestrator script

**⚠️ Note**: Most public datasets require manual download due to size/access restrictions (scripts provide verification only)

### Manual Tasks (Minimal):

- Download public datasets manually (one-time, automated scripts help verify)
- Record 300-500 manual clips (phone, room, outdoor)
- Verify labels (spot-check, not full manual labeling)

---

## ✅ Success Criteria

- [ ] LibriSpeech downloaded and verified (5K-10K samples)
- [ ] VCTK downloaded and verified (2K-5K samples)
- [ ] VoxCeleb1 downloaded (optional, 3K-5K samples)
- [ ] YouTube audio collected (1K-1.5K samples: broadcast, podcast, social)
- [ ] Manual collection completed (300-500 samples)
- [ ] Fake audio generated (2K-3K TTS clips)
- [ ] At least 10,000+ real-world audio samples collected
- [ ] All samples processed (converted to WAV, resampled to 16kHz)
- [ ] All samples labeled and verified
- [ ] Manifest created with all required columns
- [ ] Quality checks passed (>95% valid)
- [ ] Domain distribution documented
- [ ] Statistics report generated

---

## 📊 Expected Statistics

**Target Distribution (After Collection):**

```
Source              | Samples | Domain Breakdown
--------------------|---------|------------------
Public Datasets     | 10K-20K | LibriSpeech (read speech), VCTK (studio), VoxCeleb1 (optional)
YouTube (Auto)      | 1K-1.5K | Broadcast, Podcast, Social
Manual Collection   | 300-500 | Phone, Room, Outdoor
TTS Generated       | 2K-3K   | Synthetic (fake)
-----------------------------------
Total Raw           | 13K-25K |
After Augmentation  | 130K-250K | (10× expansion)
```

**Domain Distribution (Target):**

```
Domain      | Samples | Percentage | Sources
------------|---------|------------|------------------
Read Speech | 5,000+  | ~35%       | LibriSpeech
Broadcast   | 3,000+  | ~21%       | YouTube, VoxCeleb1 (optional)
Studio      | 2,000+  | ~14%       | VCTK
Podcast     | 2,000+  | ~14%       | YouTube
Phone       | 500+    | ~4%        | Manual
Social      | 1,000+  | ~7%        | YouTube, Manual
Synthetic   | 2,000+  | ~14%       | TTS generated
-----------------------------------
Total       | 14,500+ | 100%       |
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Dataset Availability

**Problem**: VoxCeleb2 (300+ GB) too large, Common Voice no longer available  
**Solution**: Use LibriSpeech + VCTK (both work, manageable sizes, no restrictions)

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

- Phase 1: Unified Dataset Preparation (requires this phase's output: `manifest_realworld.csv`)

---

## 📝 Notes

- This phase is **NON-NEGOTIABLE** - cannot proceed without real-world data
- **Automation is key** - manual collection should be minimal (300-500 clips)
- Use public datasets as primary source (saves weeks of work)
- Document all data sources and licensing information
- Respect YouTube ToS and dataset licenses
- Quality over quantity - verify samples are usable
- Consider ethical implications of data collection
- **Practical alternatives**: LibriSpeech and VCTK are verified working alternatives to VoxCeleb2 and Common Voice

---

**Last Updated**: 10 December 2025  
**Status**: 🟡 IN PROGRESS
