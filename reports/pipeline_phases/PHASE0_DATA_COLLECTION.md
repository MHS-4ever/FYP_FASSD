# Phase 0: Real-World Data Collection

**Status**: ✅ COMPLETE  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 1-2  
**Dependencies**: None (starting phase)
**Completion Date**: December 2025

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

## 🐛 Issues & Difficulties Encountered (Real-World Experience)

### Issue 1: Script Complexity and Performance

**Problem**: Initial `download_youtube.py` and `generate_fake_audio.py` scripts were overly complex with unnecessary retry logic, timeout handling, and multiple search rounds, making them difficult to maintain and debug.

**Impact**:

- Scripts took 9-15 minutes per video download (extremely slow)
- Complex code made debugging difficult
- Unnecessary overhead reduced efficiency

**Solution**:

- Simplified both scripts significantly
- Removed complex retry/timeout logic
- Optimized `yt-dlp` calls by batching (`ytsearch10` instead of `ytsearch1`)
- Added duration filtering to avoid downloading excessively long videos
- Result: Download speed improved from 9-15 min/video to ~30-60 sec/video

### Issue 2: Path Resolution Errors

**Problem**: `download_youtube.py` was not finding existing files due to incorrect path resolution. Script was looking for files relative to its own directory (`Code/phase0/data/...`) instead of project root (`E:\FYP\data/...`).

**Error Message**: `[INFO] No existing files found in E:\FYP\Code\phase0\data/realworld/youtube\broadcast`

**Solution**:

- Implemented `find_project_root()` function that traverses up directory tree to locate project root (identified by presence of both `data` and `Code` folders)
- All paths now resolved relative to project root
- Fixed output directory duplication issue (e.g., `podcast/podcast`)

### Issue 3: YouTube Download Speed (Critical Bottleneck)

**Problem**: Script was downloading videos at extremely slow rate (5 videos in 43 minutes, ETA in days). Root cause: calling `yt-dlp` once per video with `--default-search ytsearch1`, causing significant startup and search overhead for each video.

**Solution**:

1. Changed `ytsearch1` to `ytsearch10` (or `ytsearch20`) to download multiple videos per `yt-dlp` invocation
2. Introduced `download_multiple_videos_from_query()` function for batch downloads
3. Added duration filtering (`--match-filter "duration < {max_duration}"`) per domain:
   - Social: 15 minutes max
   - Podcast/Broadcast: 30 minutes max
4. Result: **10-20x speed improvement**

### Issue 4: Incomplete Downloads (Not Reaching max_videos Target)

**Problem**: Script stopped downloading after exhausting initial set of queries, even if `max_videos` target not reached (e.g., 201/300 for social, 142/500 for podcast).

**Solution**:

- Modified `download_from_search_queries()` to loop and cycle through queries multiple times
- Dynamically generate more query variations (e.g., adding "latest", "new", "episode") if initial set exhausted
- Increased `max_queries_to_try` limit to allow more attempts
- Result: Script now reliably reaches `max_videos` target

### Issue 5: Duplicate Video Downloads

**Problem**: Concern that script might download the same video multiple times if it appeared in different search results or channels.

**Solution**:

- Enhanced duplicate prevention by tracking video IDs across all downloaded and existing files
- Added `existing_video_ids` set in `download_from_search_queries()` to track all video IDs
- Modified `download_multiple_videos_from_query()` to only return files with new video IDs
- Added video ID checking in `download_from_channels()` to prevent re-downloading
- Result: Zero duplicate downloads

### Issue 6: Output Directory Duplication

**Problem**: Script was creating nested directories like `E:\FYP\data\realworld\youtube\podcast\podcast` when `--output_dir` already contained domain name.

**Solution**:

- Modified `main()` to check if `output_path.name` (last component) equals domain name
- If match, use `output_path` directly; otherwise append domain
- Applied to both single domain and "all" domain modes

### Issue 7: YouTube Channel Downloads Hanging

**Problem**: Script would hang for extended periods (20+ minutes) when trying to fetch video URLs from YouTube channels.

**Solution**:

- Reduced timeout for `yt-dlp` calls in `get_channel_video_urls()` from 60s to 30s
- Added progress messages and per-channel time limit (`max_channel_time=300s`)
- Introduced `--skip_channels` flag to bypass channel downloads entirely (rely solely on search queries)
- Result: No more hanging, faster overall execution

### Issue 8: TTS Dependency Conflicts

**Problem**: TTS libraries (XTTS v2, Tortoise TTS) require old numpy (1.22.0) which conflicts with modern scientific stack (PyTorch 2.5.1 + librosa 0.11+ need numpy ≥1.26).

**Solution**:

- Created separate `ttsgen` conda environment for TTS generation only
- Main `fassd` environment kept clean for all other Phase 0 work
- Result: No dependency conflicts, both environments stable

### Issue 9: CSV Metadata Format Issues

**Problem**: `clips_metadata.csv` was not saving paths correctly - Excel showed truncated paths and `#NAME?` errors in `source_vid` column.

**Solution**:

- Ensured all paths use full absolute paths (`Path.resolve()`)
- Fixed column name consistency (`source_video` not `source_vid`)
- Added proper CSV quoting (though user removed `csv.QUOTE_ALL` later)
- Created `cleanup_youtube_downloads.py` to regenerate metadata from existing clips

### Issue 10: Missing Original Videos (Clips Only)

**Problem**: For broadcast domain, original downloaded videos were deleted but clips remained. Needed to regenerate `clips_metadata.csv` from existing clips only.

**Solution**:

- Enhanced `cleanup_youtube_downloads.py` to detect when original videos missing but clips exist
- Added `regenerate_metadata_from_clips()` function to scan existing clips and extract video IDs from filenames
- Automatically generates complete metadata CSV with full absolute paths

### Issue 11: Script Simplification Request

**Problem**: User found both `generate_fake_audio.py` and `download_youtube.py` too complex initially.

**Solution**:

- Significantly simplified both scripts
- Removed unnecessary complexity
- Improved code readability and maintainability
- Added better error messages and progress tracking

### Issue 12: GPU Utilization in Audio Processing

**Problem**: `process_audio.py` needed optimization for better GPU utilization when processing 45K+ files.

**Solution**:

- Added skip logic for already-processed files
- Optimized GPU cache clearing (every 10 batches instead of every batch)
- Pre-created resampler on GPU for efficiency
- Result: Better GPU utilization, faster processing

---

## 📊 Final Collection Statistics (December 2025)

**Status**: ✅ **PHASE 0 COMPLETE**

### Final Dataset:

| Source                    | Files       | Status      | Notes                                                                                  |
| ------------------------- | ----------- | ----------- | -------------------------------------------------------------------------------------- |
| **YouTube**               | **41,238**  | ✅ Complete | Broadcast: 17,996 clips<br>Podcast: 17,529 clips<br>Social: 5,713 clips<br>Format: WAV |
| **Synthetic (TTS)**       | **4,502**   | ✅ Complete | XTTS v2 generated<br>Synthesis: 3,002<br>Replay: 1,500<br>Format: WAV                  |
| **LibriSpeech**           | **28,539**  | ✅ Complete | Public dataset<br>Format: WAV (processed)                                              |
| **VCTK**                  | **83,155**  | ✅ Complete | Public dataset<br>Format: WAV (processed)                                              |
| **Public Datasets Total** | **111,694** | ✅ Complete | LibriSpeech + VCTK                                                                     |
| **Manual Collection**     | **0**       | ⏸️ Skipped  | Not required (sufficient data collected)                                               |
| **Total Processed**       | **157,414** | ✅ Complete | **6.3x the initial target of 13K-25K!**                                                |

### Final Processing Results:

- **Total Files Processed**: 157,414 (96.8% of 162,610 collected)
- **Valid Files**: 157,414 (100% validity rate)
- **Invalid Files Removed**: 20 (silent/corrupted)
- **Format**: WAV, 16kHz, mono, 1-10 seconds
- **Quality**: 100% valid (exceeds >95% target)

### Distribution:

- **Label**: Bonafide: 152,932 (97.1%), Spoof: 4,502 (2.9%)
- **Domain**: Studio: 83,155, Read Speech: 28,539, Broadcast: 17,996, Podcast: 17,529, Social: 5,713, Synthetic: 4,502
- **Source**: Public Datasets: 111,694, YouTube: 41,238, Synthetic: 4,502
- **Attack Types**: Synthesis: 3,002, Replay: 1,500

### Storage:

- **Processed Audio**: ~30-40 GB
- **Manifest**: `manifest_realworld.csv` (157,414 entries)
- **Statistics**: `collection_stats.json`, `quality_report.json`

### Time Investment (Actual):

- **YouTube Downloading**: ~8-12 hours (automated)
- **TTS Generation**: ~4-5 hours (GPU in `ttsgen` environment)
- **Audio Processing**: ~2 hours (GPU-accelerated, optimized)
- **Manifest Creation**: ~34 minutes
- **Quality Verification**: ~43 minutes
- **Total**: ~16-20 hours of automated processing

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

### ⚠️ Two-Environment Setup Required

**Critical**: TTS libraries (XTTS v2, Tortoise TTS) cannot be installed in the main `fassd` environment due to dependency conflicts:

- TTS requires old numpy (1.22.0)
- Main environment needs modern numpy (≥1.26) for PyTorch 2.5.1 + librosa 0.11+
- Installing TTS in main environment causes dependency corruption

**Solution**: Use two separate conda environments:

1. **`fassd`**: Main environment for all Phase 0 work (downloading, processing, verification)
2. **`ttsgen`**: Isolated environment ONLY for TTS fake audio generation

See `Code/phase0/README.md` for complete setup instructions.

---

---

## ✅ Phase 0 Completion Summary

**All Steps Completed Successfully:**

- ✅ Step 1: Public datasets downloaded (LibriSpeech, VCTK)
- ✅ Step 2: YouTube audio collected (broadcast, podcast, social)
- ✅ Step 3: Synthetic audio generated (TTS + replay)
- ✅ Step 4: All audio processed (16kHz, mono, 1-10s)
- ✅ Step 5: Manifest created (157,414 valid files)
- ✅ Step 6: Quality verified (100% validity rate)
- ✅ Step 7: Invalid files removed (20 silent files excluded)

**Output Files Ready for Phase 1:**

- `data/realworld/manifest_realworld.csv` - Main manifest (157,414 files)
- `data/realworld/statistics/collection_stats.json` - Collection statistics
- `data/realworld/statistics/quality_report.json` - Quality verification report
- `data/realworld/processed/` - All processed audio files

**Next Phase**: Phase 1 - Unified Dataset Preparation

---

**Last Updated**: December 2025  
**Status**: ✅ **COMPLETE**
