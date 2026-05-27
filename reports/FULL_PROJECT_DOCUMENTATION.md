# FASSD — Full Project Documentation

**FASSD**: Forensic Acoustic Synthetic Speech Detector → evolving into **Forensic Voice Authenticity Analyzer**  
**Goal**: Detect AI-generated (deepfake) audio using a **hybrid** model that combines **log-mel spectrogram** analysis (synthetic artifacts) with **environmental acoustics** (room, noise, recording consistency).  
**Final model**: `HybridResNetEnvironmental` — checkpoint `models_saved/hybrid_resnet_environmental_best.pth`  
**Last updated**: May 2026  

This document is a single reference for: what was built, how the model works, all evaluation numbers, and every parameter shown during testing/inference.

---

## Phase 7 closed · Phase 8 initialized (May 2026)

| Phase | Status |
|-------|--------|
| **Phase 7** | **Closed** — [PHASE7_FINAL_CLOSURE_REPORT.md](phase7/PHASE7_FINAL_CLOSURE_REPORT.md) |
| **Phase 8** | **Active (planning)** — [PHASE8_START_HERE.md](phase8/PHASE8_START_HERE.md) — Multi-Axis Forensic Audio Intelligence |

**Key finding:** Single binary spoof/fake models are **insufficient** for the forensic product goal. Phase 8 begins with an **evidence table**, not another monolithic classifier.

**Do not:** run more Phase 7 AASIST/Hybrid experiments; train models until Phase 8A architecture freeze.

---

## Phase 7 Documentation Reorganization

Phase 7 planning is centralized under **`reports/phase7/`** (read-only archive).

| Document | Role |
|----------|------|
| [PHASE7_THESIS_RATIONALE.md](PHASE7_THESIS_RATIONALE.md) | Why Phase 7 exists (thesis/report style) |
| [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md) | Root-level master product plan |
| [phase7/README.md](phase7/README.md) | Phase 7 index and gates |
| [phase7/PHASE7_MASTER_PLAN.md](phase7/PHASE7_MASTER_PLAN.md) | Overall 7A–7F plan |
| [phase7/PHASE7A_CONTROLLED_TEST_SUITE.md](phase7/PHASE7A_CONTROLLED_TEST_SUITE.md) | Active phase — controlled testing |

Legacy paths (`pipeline_phases/PHASE7*.md`, `FORENSIC_PRODUCT_ROADMAP.md`) remain with a redirect note at the top. Operational 7A templates: [phase7/phase7_forensic_tests/](phase7/phase7_forensic_tests/).

---

## Phase 7 final conclusion (closed — May 2026)

Phase 7 (7A–7E) is **complete and closed**. Summary:

| Item | Status |
|------|--------|
| Phase 7A–7C2 | Signed off |
| Phase 7C3-v1 | **Rejected** |
| Phase 7C3-R2 | **Rejected** as standalone |
| Phase 7C4-v1 | **Rejected** |
| Phase 7C4-v2 | **Accepted** as decision-layer **prototype only** |
| Phase 7D | **Postponed** → Phase 8G |
| Phase 7E AASIST | **Rejected** as current solution |

**Next phase:** **Phase 8** — [PHASE8_START_HERE.md](phase8/PHASE8_START_HERE.md).

Full record: [phase7/PHASE7_FINAL_CLOSURE_REPORT.md](phase7/PHASE7_FINAL_CLOSURE_REPORT.md) · [phase7/PHASE7_TO_PHASE8_TRANSITION.md](phase7/PHASE7_TO_PHASE8_TRANSITION.md).

---

## Current Scope Update — Forensic Voice Authenticity Analyzer

The project scope has **expanded** from binary synthetic speech detection to **forensic audio authenticity analysis**.

The system will still detect AI-generated voices, but it will also analyze:

- **Replay** and re-recording (human-origin vs AI-origin)  
- **Mixer / channel** processing and equalization  
- **Platform compression** (WhatsApp, social, codec)  
- **Editing / splicing** and environmental inconsistency  
- **Partial AI insertion** inside mostly real long recordings  
- **Environmental** acoustic cues (noise, reverb, SNR, stability)  

The **final product** should generate a **forensic-style report** (origin, manipulation risk, suspicious segments, limitations) — **not only** a REAL/FAKE label.

| Point | Detail |
|-------|--------|
| **Canonical scope** | [FASSD — Project Scope](../FASSD%20-%20Scope.md) (complete FYP scope) |
| **Expanded scope detail** | Six areas — [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md) |
| **Baseline checkpoint** | `HybridResNetEnvironmental` + Phase 6 — **evidence source**; not final product alone. |
| **Accepted prototype** | Phase **7C4-v2** decision layer (frozen artifact). |
| **Next step** | **Phase 8A** — multi-axis architecture freeze. **No training** until reviewed. |
| **Phase order** | 7 (closed) → **8A–8H** (multi-axis evidence + fusion + reports) |
| **P0 recording** | **20–30 s** default; **≥ 8 s** min; partial-AI cases **30–45 s** or **60–120 s** as specified in 7A |

**Read next:**

- [FASSD — Project Scope](../FASSD%20-%20Scope.md) — **canonical** complete project scope  
- [UPDATED_PROJECT_SCOPE.md](UPDATED_PROJECT_SCOPE.md) — expanded scope detail (Scopes 1–6)  
- [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md) — master product plan  
- [PHASE7_THESIS_RATIONALE.md](PHASE7_THESIS_RATIONALE.md) — thesis rationale for Phase 7  
- [phase7/README.md](phase7/README.md) — Phase 7 index  
- [phase7/PHASE7A_CONTROLLED_TEST_SUITE.md](phase7/PHASE7A_CONTROLLED_TEST_SUITE.md) — test plan (archive)  
- [phase8/PHASE8_START_HERE.md](phase8/PHASE8_START_HERE.md) — **active** Phase 8 entry  
- [phase7/PHASE7D_FORENSIC_REPORT_LAYER.md](phase7/PHASE7D_FORENSIC_REPORT_LAYER.md) — report layer (postponed → 8G)  
- [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md) — report fields  
- [NEXT_ACTIONS.md](NEXT_ACTIONS.md) — immediate checklist  

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [What we did — pipeline phases](#2-what-we-did--pipeline-phases)
3. [The model — architecture and design](#3-the-model--architecture-and-design)
4. [Data and features](#4-data-and-features)
5. [Training (Phase 4)](#5-training-phase-4)
6. [Formal evaluation (Phase 5)](#6-formal-evaluation-phase-5)
7. [Testing on raw audio (Phase 6)](#7-testing-on-raw-audio-phase-6)
8. [Legacy work (before the unified pipeline)](#8-legacy-work-before-the-unified-pipeline)
9. [File locations and commands](#9-file-locations-and-commands)
10. [Targets vs achieved](#10-targets-vs-achieved)
11. [Known limitations and next steps](#11-known-limitations-and-next-steps)

---

## 1. Executive summary

### What the project delivers

| Component | Description |
|-----------|-------------|
| **Unified dataset** | ASVspoof 2021 LA + DF + PA + real-world audio (~1.89M segments), speaker-independent splits |
| **Features** | Log-mel `[64, 400]` + 12 environmental features per 4 s segment |
| **Model** | Hybrid ResNet + environmental MLP, multi-task (binary real/fake + 4-class attack type) |
| **Training** | 20 epochs on mixed ASVspoof + RealWorld data; best val EER **20.17%** (epoch 17) |
| **Test evaluation** | Speaker-independent test: overall EER **16.22%**, RealWorld EER **16.14%** (MVP met: &lt; 20%) |
| **Inference / testing UI** | `code/phase6/explain_prediction.py` — chunked raw-audio inference with explanations (JSON + CSV) |

### Headline results

| Metric | Value | MVP target | Status |
|--------|------:|------------|--------|
| **RealWorld test EER** | **16.14%** | &lt; 20% | Met |
| **Overall test EER** | **16.22%** | &lt; 10% | Not met |
| **Overall test AUC** | **0.9167** | — | Strong |
| **Binary accuracy @ 0.5** | **89.78%** | — | Good (bonafide FPR high) |
| **Multiclass accuracy** | **64.36%** | &gt; 80% | Not met |
| **Trump test audios (tuned Phase 6)** | **8/8** | — | Met |
| **All custom test audios (17 files)** | **12/17 (70.6%)** | — | Pakistani domain weak |

---

## 2. What we did — pipeline phases

The current pipeline (Phases 0–6) replaces an earlier approach that used only 2 ASVspoof subsets and failed on broadcast audio. Below is what each phase accomplished.

### Phase 0 — Real-world data collection ✅

- Collected **real-world bonafide** audio to complement ASVspoof (studio/controlled).
- Sources: LibriSpeech, VCTK, optional VoxCeleb; YouTube (broadcast, podcast, social) via `yt-dlp`.
- Domains labeled: `broadcast`, `podcast`, `social`, `phone`, `read_speech`, etc.
- **Why**: ASVspoof alone does not match broadcast/processed audio in the wild.

**Doc**: `reports/pipeline_phases/PHASE0_DATA_COLLECTION.md`

### Phase 1 — Unified dataset ✅

- Merged **ASVspoof LA, DF, PA** + **RealWorld** into one manifest.
- **PA added** (replay attacks) — earlier work used only LA + DF.
- **Speaker-independent splits**: no speaker overlap between train / val / test.
- Attack-type labels: `bonafide`, `synthesis` (LA), `conversion` (DF), `replay` (PA).

| Split | Samples | Bonafide % | Spoof % |
|-------|--------:|-----------:|--------:|
| Train | 1,483,741 | 16.9% | 83.1% |
| Val | 155,604 | ~same ratio | |
| Test | 254,574 | 15.6% | 84.4% |
| **Total** | **1,893,919** | | |

**Manifests**: `data/manifests/unified_manifest.csv`, `train_speaker_independent.csv`, `val_speaker_independent.csv`, `test_speaker_independent.csv`

**Doc**: `reports/pipeline_phases/PHASE1_UNIFIED_DATASET.md`

### Phase 2 — Feature extraction ✅

- **Log-mel spectrograms**: 1,893,919 × `[64, 400]` → HDF5 (`logmel_packed.h5` / `logmel_chunked.h5`).
- **Environmental features**: 1,893,919 × `[12]` → `environmental_packed.h5`.
- Fixed 4 s windows (400 frames @ 10 ms hop).

**Doc**: `reports/pipeline_phases/PHASE2_FEATURE_EXTRACTION.md`

### Phase 3 — Hybrid architecture ✅

- Implemented `HybridResNetEnvironmental` + multi-task loss.
- **2,902,822 parameters** (~12 MB).
- All architecture tests passed (7/7).

**Doc**: `reports/pipeline_phases/PHASE3_HYBRID_ARCHITECTURE.md`  
**Code**: `code/phase3/hybrid_resnet_environmental.py`

### Phase 4 — Training ✅

- Trained hybrid model on speaker-independent train/val with **~50% ASVspoof / ~50% RealWorld** mix in training manifest.
- Fixed HDF5 gzip bottleneck (470 ms → ~2 ms per sample) and chunk-aligned fast loader.
- **Best checkpoint**: epoch **17**, validation binary EER **20.17%**.
- RealWorld validation EER on full-eval epochs: **~11–14%** during training.

**Doc**: `reports/pipeline_phases/PHASE4_TRAINING.md`  
**Log**: `models_saved/logs/training_hybrid_fast.csv`

### Phase 5 — Comprehensive evaluation ✅

- Evaluated best checkpoint on **254,574** test segments (speaker overlap = **0**).
- Generated CSVs, ROC plots, confusion matrices, threshold sweep.

**Doc**: `reports/pipeline_phases/PHASE5_EVALUATION.md`  
**Report**: `reports/evaluation/comprehensive_evaluation_report.md`

### Phase 6 — Explanation & raw-audio testing ✅

- Built `explain_prediction.py`: chunk raw audio → features → hybrid model → JSON/CSV + human-readable reasons.
- Tuned pooling, thresholds, and VAD for long broadcast files (Trump set **8/8**).

**Doc**: `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`  
**Runs**: `reports/phase6_explanation_runs/`

### Phase 7 — Domain adaptation 🟢 (optional / next)

- **Trigger**: Real-world EER &gt; 20% → skip; we achieved **16.14%**, so Phase 7 is optional.
- Planned for Pakistani / other out-of-domain speech if needed.

**Doc**: `reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md`

---

## 3. The model — architecture and design

### Name and checkpoint

| Item | Value |
|------|--------|
| Class | `HybridResNetEnvironmental` |
| File | `code/phase3/hybrid_resnet_environmental.py` |
| Checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` |
| Parameters | **2,902,822** |
| Tasks | Binary (real vs fake) + multiclass (attack type) |

### High-level diagram

```
                    Input audio (16 kHz)
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
   Log-mel [1,64,400]              Environmental [12]
           │                               │
   ResNet Branch (CNN)              Environmental MLP
   2.83M params                     26K params
           │                               │
           └───────────┬───────────────────┘
                       ▼
              Fusion (concat → FC)
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
    Binary head [2]        Multiclass head [4]
   (bonafide, spoof)    (bonafide, synthesis,
                        conversion, replay)
```

### Branch 1 — ResNet (spectrogram)

| Layer | Detail |
|-------|--------|
| Input | `[B, 1, 64, 400]` log-mel (per-sample normalized in training/inference) |
| Conv init | 1 → 32 channels, 3×3 |
| Res blocks | 32→32 (×2), 32→64 (×2, ↓2), 64→128 (×2, ↓2), 128→256 (×2, ↓2) |
| Pool | Global average pool |
| Dropout | 0.3 |
| Output embedding | `[B, 128]` |

**Purpose**: Detect synthetic artifacts in the spectrogram (vocoder / conversion cues).

### Branch 2 — Environmental MLP

| Layer | Detail |
|-------|--------|
| Input | `[B, 12]` environmental vector (per-sample normalized) |
| MLP | 12→64→128→128, ReLU, dropout 0.2 |
| Output embedding | `[B, 128]` |

**Purpose**: Capture recording environment consistency (reverb, noise, “too clean” cues).

### Fusion and heads

| Component | Architecture |
|-----------|--------------|
| Fusion | Concat `[128+128]` → FC 256→128, ReLU, dropout 0.2 |
| Binary head | 128→64→**2** logits |
| Multiclass head | 128→64→**4** logits |

### Loss (multi-task)

```
Total loss = 0.7 × Binary_CE + 0.3 × Multiclass_CE
```

**Class weights (training):**

| Task | Weights | Purpose |
|------|---------|---------|
| Binary | `[1.661, 0.339]` | Upweight bonafide (minority) |
| Multiclass | `[1.032, 1.999, 0.568, 0.401]` | Balance attack types |

### Inference scoring

- **Spoof probability** = `softmax(binary_logits)[1]` (class index 1 = spoof/fake).
- **Prediction**: FAKE if spoof_prob ≥ threshold (default 0.5 on test set; **0.65–0.70** recommended for long real-world files in Phase 6).
- **Attack type** = argmax of multiclass softmax → `bonafide` / `synthesis` / `conversion` / `replay`.

---

## 4. Data and features

### Audio processing (training & Phase 6)

| Parameter | Value |
|-----------|------:|
| Sample rate | 16,000 Hz |
| Segment length | ~4 s (400 mel frames) |
| FFT size | 512 |
| Hop length | 160 (10 ms) |
| Window length | 400 (25 ms) |
| Mel bins | 64 |
| Power | 2.0 (power mel) |
| Log scale | `librosa.power_to_db(..., ref=np.max)` |
| Spectrogram norm | Per-sample: `(x - mean) / (std + 1e-5)` |

### 12 environmental features (order used in model)

| # | Feature | Meaning (short) |
|---|---------|-----------------|
| 1 | `rt60` | Reverberation decay time |
| 2 | `drr` | Direct-to-reverberant ratio (log-scaled) |
| 3 | `snr` | Signal-to-noise ratio |
| 4 | `background_level` | Background noise level (dB) |
| 5 | `silence_ratio` | Fraction of low-energy frames |
| 6 | `spectral_tilt` | Spectral slope |
| 7 | `spectral_flatness` | Noise-like vs tonal |
| 8 | `spectral_rolloff` | Stored as rolloff/1000 in vector |
| 9 | `cleanliness_score` | “Too clean” indicator |
| 10 | `high_freq_content` | High-frequency energy |
| 11 | `background_consistency` | Temporal noise stability |
| 12 | `env_stability` | Environmental stability over time |

**Extractor**: `code/features/environmental_features.py`  
**Env norm (training/inference)**: Per-sample mean/std normalization (same as Phase 4 dataset).

### Datasets in unified manifest

| Dataset | Role | Attack type mapping |
|---------|------|---------------------|
| **LA** | Logical access | synthesis |
| **DF** | Deep fake | conversion |
| **PA** | Physical access | replay |
| **RealWorld** | In-the-wild bonafide (+ some synthetic) | bonafide / synthesis |

---

## 5. Training (Phase 4)

### Configuration

| Setting | Value |
|---------|--------|
| Optimizer | AdamW |
| Learning rate | 1e-3 → reduced on plateau (min 1e-6) |
| Weight decay | 1e-4 |
| Scheduler | ReduceLROnPlateau (factor 0.5, patience 3) |
| Epochs | 20 |
| Batch size (PC) | 128 (RTX 3070) |
| Mixed precision | FP16 |
| Train manifest | `data/manifests/train_speaker_independent.csv` |
| Val manifest | `data/manifests/val_speaker_independent.csv` |
| Spectrogram H5 | `logmel_chunked.h5` (chunk size 256 for I/O) |
| Environmental H5 | `environmental_packed.h5` |

### Training set composition (approximate)

| Category | Share |
|----------|------:|
| Spoof | 83.1% |
| Bonafide | 16.9% |
| PA / DF / LA / RealWorld | ~50% / 32% / 10% / 8% of samples |
| Attack types | replay 44%, conversion 31%, bonafide 17%, synthesis 9% |

### Best epoch (from `training_hybrid_fast.csv`)

| Field | Epoch 17 (best) |
|-------|-----------------|
| `val_binary_eer` | **0.2017** (20.17%) |
| `val_binary_auc` | 0.8650 |
| `val_binary_accuracy` | 86.34% |
| `val_multiclass_accuracy` | 50.41% |
| `learning_rate` | 0.000125 |

Epoch 20 showed validation loss spike; **EER-based checkpoint selection** (epoch 17) is the model used for Phase 5/6.

---

## 6. Formal evaluation (Phase 5)

**Script**: `code/phase5/evaluate_hybrid_model.py`  
**Checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth`  
**Test manifest**: `data/manifests/test_speaker_independent.csv`  
**Speaker leakage**: **0** overlapping speakers (train vs test)

### 6.1 Overall test metrics

| Split | Samples | Binary EER ↓ | Binary AUC ↑ | Acc @0.5 | Multiclass Acc |
|-------|--------:|-------------:|-------------:|---------:|---------------:|
| **Overall** | 254,574 | **16.21%** | **0.9167** | 89.78% | 64.36% |
| ASVspoof | 237,490 | 18.15% | 0.8947 | 90.65% | 63.39% |
| RealWorld | 17,084 | **16.14%** | **0.9236** | 77.68% | 77.89% |

### 6.2 Per-dataset (ASVspoof + RealWorld)

| Dataset | Samples | EER ↓ | AUC ↑ | Acc @0.5 | Multiclass Acc |
|---------|--------:|------:|------:|---------:|---------------:|
| LA | 24,388 | 6.30% | 0.9847 | 94.53% | 56.52% |
| DF | 94,032 | 8.33% | 0.9763 | 92.16% | 88.65% |
| PA | 119,070 | 16.23% | 0.9095 | 88.66% | 44.84% |
| RealWorld | 17,084 | 16.14% | 0.9236 | 77.68% | 77.89% |

### 6.3 Per attack type (binary slice accuracy; EER N/A for single-class slices)

| Attack type | Samples | Acc @0.5 | Multiclass Acc |
|-------------|--------:|---------:|---------------:|
| bonafide | 39,737 | 58.72% | 61.05% |
| synthesis | 22,192 | 94.71% | 51.60% |
| conversion | 90,585 | 92.20% | 88.51% |
| replay | 102,060 | 98.65% | 46.98% |

**Note**: ~**41.3%** of bonafide samples are predicted as spoof at threshold **0.5** (high bonafide false-positive rate). Raising threshold reduces FPR (see sweep below).

### 6.4 Threshold sweep (full test set)

| Threshold | Accuracy (%) | Bonafide FPR (%) |
|----------:|-------------:|-----------------:|
| 0.50 | 89.78 | 41.28 |
| 0.65 | 89.61 | 39.28 |
| 0.70 | 89.52 | 38.43 |

- **Bonafide FPR**: % of real samples incorrectly called spoof. Lower is better.
- **File**: `reports/evaluation/threshold_sweep.csv`

### 6.5 Multiclass report (overall)

```
              precision    recall  f1-score   support
    bonafide     0.6983    0.6105    0.6515     39737
   synthesis     0.1631    0.5160    0.2479     22192
  conversion     0.7992    0.8851    0.8399     90585
      replay     0.9727    0.4698    0.6336    102060
    accuracy                         0.6436    254574
```

**Confusion matrices & ROC**: `reports/evaluation/confusion_matrices/`, `reports/evaluation/figures/`

---

## 7. Testing on raw audio (Phase 6)

Phase 6 is how you **test arbitrary `.wav` / `.mp3` files** (not pre-extracted HDF5). It chunks long files, runs the hybrid model, and writes **JSON per file** + **`results.csv`**.

**Script**: `code/phase6/explain_prediction.py`

### 7.1 Recommended command (Trump / long broadcast audio)

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --audio_dir E:/FYP/testing_audios/trump ^
  --output_dir reports/phase6_explanation_runs/trump_run ^
  --batch_size 32 ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40
```

### 7.2 All CLI parameters (what you can set in testing)

| Parameter | Default | What it does |
|-----------|---------|--------------|
| `--ckpt` | *(required)* | Path to `hybrid_resnet_environmental_best.pth` |
| `--audio_dir` | `E:/FYP/testing_audios` | Folder of audio (recursive `.wav/.mp3/.flac/.m4a`) |
| `--audio_path` | — | Single file (overrides `--audio_dir`) |
| `--test_manifest` | — | CSV with audio paths (manifest mode) |
| `--manifest_audio_col` | `filepath` | Column name in manifest |
| `--max_files` | — | Limit number of files |
| `--output_dir` | `reports/explanation_examples` | Where JSON/CSV are saved |
| `--chunk_duration` | **4.0** | Seconds per chunk (matches training) |
| `--overlap` | **1.0** | Overlap between chunks (seconds) |
| `--batch_size` | **32** | GPU batch size for chunks |
| `--threshold` | **0.65** | Decision threshold for non–`pct_vote` pooling |
| `--pooling` | `median` | `median`, `trimmed_mean`, `mean`, `logit_mean`, **`pct_vote`** |
| `--trim_fraction` | **0.10** | For `trimmed_mean`: fraction trimmed each tail |
| `--chunk_threshold` | **0.65** | For `pct_vote`: chunk is “spoof” if prob ≥ this |
| `--vote_threshold` | **0.50** | For `pct_vote`: file is FAKE if % spoof chunks ≥ this (**use 0.70** tuned) |
| `--vad_mode` | `file_percentile` | `file_percentile` or `abs_db` |
| `--vad_rms_percentile` | **30** | File-level RMS threshold percentile (**40** recommended) |
| `--vad_min_speech_ratio` | **0.40** | Drop chunks below this speech ratio (0 = off) |
| `--vad_db_threshold` | **-45** | Used when `vad_mode=abs_db` |
| `--debug_chunk_stats` | off | Add min/p50/max chunk spoof stats to output |
| `--device` | `cuda` | `cuda` or `cpu` |

### 7.3 How `pct_vote` decides REAL vs FAKE

1. Split audio into 4 s chunks (1 s overlap).
2. For each chunk: compute log-mel + env features → spoof probability.
3. Optionally **VAD**: drop non-speech chunks (`vad_min_speech_ratio`).
4. Count chunks with `spoof_prob >= chunk_threshold` (0.65).
5. **`decision_score`** = fraction of kept chunks above chunk threshold.
6. **FAKE** if `decision_score >= vote_threshold` (0.70); else **REAL**.

### 7.4 Every field in testing output (JSON / CSV)

When you run Phase 6, each file produces a JSON like `reports/phase6_explanation_runs/all_testing_audios/trump_r1.json`. Fields:

#### Prediction & confidence

| Field | Example | Meaning |
|-------|---------|---------|
| `filename` | `trump_r1.wav` | Base name |
| `filepath` | full path | Absolute path to audio |
| `prediction` | `REAL` or `FAKE` | Final label |
| `confidence` | `0.844` | Model confidence in predicted class |
| `spoof_prob` | `0.156` | Same as `decision_score` for pct_vote |
| `decision_score` | `0.156` | Score used for final decision |
| `overall_explanation` | text | One-line human summary |

#### Pooling & thresholds

| Field | Example | Meaning |
|-------|---------|---------|
| `pooling` | `pct_vote` | Aggregation method |
| `spoof_prob_mean` | `0.201` | Mean chunk spoof prob |
| `spoof_prob_median` | `0.022` | Median chunk spoof prob |
| `spoof_prob_trimmed` | `0.132` | Trimmed mean |
| `spoof_prob_logit_mean` | `0.014` | Mean of logit-transformed probs |
| `pct_chunks_above_chunk_threshold` | `0.156` | Fraction of chunks ≥ chunk_threshold |
| `threshold` | `0.65` | Legacy / non-pct threshold |
| `effective_threshold` | `0.70` | Threshold actually used for decision |
| `chunk_threshold` | `0.65` | Per-chunk spoof cutoff |
| `vote_threshold` | `0.70` | File-level vote cutoff |

#### Attack type (multiclass)

| Field | Example | Meaning |
|-------|---------|---------|
| `attack_type` | `bonafide` | Predicted attack class name |
| `attack_type_idx` | `0` | 0=bonafide, 1=synthesis, 2=conversion, 3=replay |
| `attack_type_conf` | `0.807` | Softmax confidence for predicted class |
| `attack_probs` | `[0.81, 0.12, 0.07, 0.00]` | Probabilities for all 4 classes |

#### Chunking & VAD

| Field | Example | Meaning |
|-------|---------|---------|
| `n_chunks` | `475` | Chunks after VAD (used in aggregation) |
| `n_chunks_total` | `542` | Total chunks before VAD |
| `n_chunks_used` | `475` | Same as `n_chunks` |
| `vad_mode` | `file_percentile` | VAD method |
| `vad_rms_percentile` | `40.0` | Percentile for RMS gate |
| `vad_min_speech_ratio` | `0.40` | Min speech to keep chunk |
| `vad_db_threshold` | `-45.0` | For abs_db mode |
| `vad_fallback_all` | `false` | True if VAD kept all chunks (fallback) |
| `speech_ratio_mean_used` | `0.64` | Mean speech ratio of used chunks |
| `speech_ratio_median_used` | `0.59` | Median speech ratio |
| `vad_file_rms_threshold` | `0.023` | Computed RMS threshold (file_percentile) |

#### Environmental explanation (display only in JSON)

| Field | Meaning |
|-------|---------|
| `env_features` | Raw 12 features (median over chunks for summary) |
| `env_reasons` | List of strings (e.g. low RT60 → suspicious) |
| `spec_reasons` | List of strings (chunk variance, pooling stats, VAD) |

Optional with `--debug_chunk_stats`: `chunk_spoof_min`, `chunk_spoof_p05`, `chunk_spoof_p50`, `chunk_spoof_p95`, `chunk_spoof_max`, `chunk_spoof_std`, and min/med/max for RT60, SNR, silence_ratio.

### 7.5 Test audio layout

```
testing_audios/
├── trump/          # 8 files (trump_r1–r5 real, trump_f1–f3 fake)
├── pakistani/      # 8 files (Imran Khan, Saqib Nisar, etc.)
└── synthetic_fake/ # synthetic_f1
```

**Naming**: **`r` = real (human)**, **`f` = fake (AI/synthetic)**.

### 7.6 Test results summary (`all_testing_audios` run)

Config: `pct_vote`, `chunk_threshold=0.65`, `vote_threshold=0.70`, `vad_rms_percentile=40`.

| Category | Correct | Total | Accuracy |
|----------|--------:|------:|---------:|
| **Trump** | 8 | 8 | **100%** |
| Pakistani | 3 | 8 | 37.5% |
| Synthetic | 1 | 1 | 100% |
| **Overall** | **12** | **17** | **70.6%** |

#### Trump (8/8) — all correct

| File | True | Predicted | decision_score | n_chunks_used |
|------|------|-----------|---------------:|--------------:|
| trump_f1 | FAKE | FAKE | 1.000 | 47/48 |
| trump_f2 | FAKE | FAKE | 1.000 | 24/24 |
| trump_f3 | FAKE | FAKE | 0.944 | 36/38 |
| trump_r1 | REAL | REAL | 0.156 | 475/542 |
| trump_r2 | REAL | REAL | 0.676 | 1326/1610 |
| trump_r3 | REAL | REAL | 0.486 | 1278/1648 |
| trump_r4 | REAL | REAL | 0.220 | 522/677 |
| trump_r5 | REAL | REAL | 0.535 | 523/549 |

#### Pakistani (3/8) — domain shift

| File | True | Predicted | Notes |
|------|------|-----------|-------|
| imran_khan_f1 | FAKE | FAKE | OK |
| imran_khan_f2 | FAKE | REAL | FN (score 0.61 &lt; 0.70) |
| imran_khan_f3 | FAKE | FAKE | OK |
| imran_khan_r2 | REAL | FAKE | FP |
| imran_khan_r3 | REAL | FAKE | FP |
| imran_khan_real1 | REAL | FAKE | FP |
| saqib_nisar_f1 | FAKE | FAKE | OK |
| saqib_nisar_son_r1 | REAL | FAKE | FP |

**Analysis file**: `reports/phase6_explanation_runs/all_testing_audios/RESULTS_ANALYSIS.md`

### 7.7 Phase 6 tuning history (Trump 8-file)

| Run folder | Pooling | Thresholds | Trump accuracy |
|------------|---------|------------|----------------|
| `baseline` | mean @ 0.5, file-level env | — | 4/8 |
| `v2_median` | median @ 0.65 | — | 5/8 |
| `v2_pct70` | pct_vote @ 0.70 both | — | 7/8 |
| `v3_pctvote_tuned` | pct_vote, vote **0.70** | chunk 0.65 | **8/8** |
| `v3_pctvote_p40` | + VAD percentile **40** | — | **8/8** |

---

## 8. Legacy work (before the unified pipeline)

Earlier experiments (documented in `reports/COMPLETE_PROJECT_STORY.md`) include:

| Item | Result on ASVspoof | Result on Trump broadcast |
|------|-------------------|---------------------------|
| LCNN baseline | ~15.7% EER (augmented) | Poor |
| Deep ResNet CNN (mel only) | **2.61% EER** (augmented test) | **0%** (all 8 called FAKE) |
| Environmental classifier only | ~81.7% acc | Scores overlap real/fake |
| `test_audio_simple.py` | Uses old `resnet_cnn_mel_robust.pth` | Not the hybrid checkpoint |

The **current production path** is the **hybrid model** + **Phase 6** inference, not `test_audio_simple.py`.

---

## 9. File locations and commands

### Key paths

| Path | Description |
|------|-------------|
| `models_saved/hybrid_resnet_environmental_best.pth` | Best model |
| `data/manifests/test_speaker_independent.csv` | Official test split |
| `data/features/logmel_chunked.h5` | Fast spectrogram store |
| `data/features/environmental_packed.h5` | Environmental store |
| `reports/evaluation/` | Phase 5 CSVs, figures, report |
| `reports/phase6_explanation_runs/` | All inference test runs |
| `testing_audios/` | Custom wav/mp3 for manual testing |

### Re-run Phase 5 evaluation

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --test_manifest data/manifests/test_speaker_independent.csv ^
  --train_manifest data/manifests/train_speaker_independent.csv ^
  --spectrogram_h5 E:/FYP/data/features/logmel_chunked.h5 ^
  --environmental_h5 E:/FYP/data/features/environmental_packed.h5 ^
  --output_dir reports/evaluation ^
  --batch_size 128
```

### Environment

- Conda env: **`fassd`**
- GPU: RTX 3050 (laptop) / RTX 3070 (PC training)
- PyTorch + CUDA, `librosa`, `h5py`, etc. (`requirements.txt`)

---

## 10. Targets vs achieved

| Metric | MVP / target | Achieved (test) | Status |
|--------|-------------|-----------------|--------|
| Real-world EER | &lt; 20% | **16.14%** | Met |
| Real-world AUC | &gt; 0.85 | **0.9236** | Met |
| Overall EER | &lt; 10% | 16.22% | Not met |
| ASVspoof EER | &lt; 5% | 18.15% | Not met |
| Multiclass accuracy | &gt; 80% | 64.36% | Not met |
| Speaker-independent test | No leakage | Overlap = 0 | Met |
| Trump custom audios (tuned) | — | 8/8 | Met |

---

## 11. Known limitations and next steps

1. **Bonafide false positives at 0.5**: ~41% of real test segments called spoof; use **0.65–0.70** threshold or `pct_vote` for deployment-style testing.
2. **Multiclass weakness on replay/synthesis**: High binary accuracy on replay (98.7%) but multiclass replay recall ~47%; synthesis precision low.
3. **Pakistani / Urdu speech**: 37.5% on custom set — likely **language/domain shift**; measure further in Phase 7A before fine-tuning.
4. **Long files**: Must use chunking + robust pooling; naive mean @ 0.5 fails on Trump reals.
5. **Binary REAL/FAKE is not enough for the final product**: Users need **origin** (human vs AI) separate from **manipulation** (replay, mixer, compression, edit).
6. **Human-origin replayed / mixer-processed audio**: Model may output **REAL** (human speech) while the recording is **not** clean/original — report as manipulation risk, not “authentic file.”
7. **Phone / WhatsApp / social platform chains**: Not labeled in training; priority gaps for Phase 7A testing and Phase 7B–7C data.
8. **Phase 7C fine-tuning**: Only after Phase 7A controlled tests are reviewed — see [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md).

### Related documentation

| Document | Content |
|----------|---------|
| `reports/COMPLETE_PROJECT_STORY.md` | Narrative of early failure on broadcast audio |
| `reports/pipeline_phases/PHASE*.md` | Per-phase technical specs |
| `reports/evaluation/comprehensive_evaluation_report.md` | Auto-generated Phase 5 report |
| `reports/phase6_explanation_runs/README.md` | All Phase 6 run folders |
| `code/phase6/README.md` | CLI help for inference |
| `reports/FORENSIC_PRODUCT_ROADMAP.md` | Forensic product direction |
| `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md` | Pre-training test plan |
| `reports/FORENSIC_REPORT_OUTPUT_SPEC.md` | Future report specification |
| `reports/NEXT_ACTIONS.md` | Immediate action list |

---

**End of full project documentation**
