# FASSD — Project State Audit

**Audit date:** May 2026  
**Workspace:** `E:\FYP`  
**Project:** Forensic Acoustic Synthetic Speech Detector (FASSD)  
**Deployed / production model ID:** `hybrid_resnet_environmental_best`

This file is a **point-in-time inventory** of the repo, model, data, evaluation, inference, custom tests, limitations, and hardware. Use it for FYP reporting, handoff, and Phase 7 planning.

---

## Table of contents

1. [Repository tree (important paths)](#1-repository-tree-important-paths)
2. [Current model](#2-current-model)
3. [Current datasets](#3-current-datasets)
4. [Current evaluation (Phase 5)](#4-current-evaluation-phase-5)
5. [Current Phase 6 inference](#5-current-phase-6-inference)
6. [Custom test audio inventory](#6-custom-test-audio-inventory)
7. [Current limitations](#7-current-limitations)
8. [Hardware constraints](#8-hardware-constraints)

---

## 1. Repository tree (important paths)

Legend: `✓` = present in workspace at audit time | `○` = documented/planned but absent or external

```
E:\FYP\
├── code/
│   ├── phase0/                          ✓ Real-world collection
│   │   ├── download_librispeech.py
│   │   ├── download_vctk.py
│   │   ├── download_youtube.py
│   │   ├── create_realworld_manifest.py
│   │   ├── process_audio.py
│   │   ├── generate_fake_audio.py
│   │   ├── verify_realworld_data.py
│   │   └── run_phase0.py
│   ├── phase1/                          ✓ Unified manifest + speaker splits
│   │   ├── create_unified_manifest.py
│   │   ├── create_speaker_independent_split.py
│   │   ├── analyze_unified_dataset.py
│   │   └── run_phase1.py
│   ├── phase2/                          ✓ Feature extraction
│   │   ├── extract_spectrogram_features.py
│   │   ├── extract_environmental_features.py
│   │   ├── pack_features_to_hdf5.py
│   │   ├── verify_features.py
│   │   └── run_phase2.py
│   ├── phase3/                          ✓ Hybrid architecture
│   │   ├── hybrid_resnet_environmental.py   ← **architecture**
│   │   ├── multi_task_loss.py
│   │   ├── test_hybrid_architecture.py
│   │   └── run_phase3.py
│   ├── phase4/                          ✓ Training
│   │   ├── train_hybrid_fast.py             ← **used for final training**
│   │   ├── train_hybrid_model.py
│   │   ├── hybrid_dataset_fast.py
│   │   ├── hybrid_dataset.py
│   │   ├── convert_h5_uncompressed.py
│   │   ├── repack_h5_chunked.py
│   │   ├── pre_training_check.py
│   │   └── run_phase4.py
│   ├── phase5/                          ✓ Evaluation
│   │   ├── evaluate_hybrid_model.py
│   │   └── run_phase5.py
│   ├── phase6/                          ✓ Raw-audio inference + explanations
│   │   ├── explain_prediction.py          ← **testing / reference inference**
│   │   └── run_phase6.py                  (defaults: threshold 0.5, not tuned)
│   ├── features/
│   │   └── environmental_features.py
│   ├── models/
│   │   ├── resnet_cnn.py                  (legacy single-branch)
│   │   └── baseline_cnn.py
│   ├── data_loading/
│   ├── utils_metrics.py
│   ├── test_audio_simple.py               (legacy ResNet-only tester)
│   └── predict_hybrid.py
│
├── models_saved/                        ✓ Checkpoints
│   ├── hybrid_resnet_environmental_best.pth    ← **primary checkpoint (~33.5 MB)**
│   ├── hybrid_resnet_environmental_epoch_{5,10,15,20}.pth
│   ├── logs/training_hybrid_fast.csv
│   └── (legacy) resnet_cnn_mel_robust.pth, baseline_*, environment_classifier.pkl
│
├── data/
│   ├── manifests/                       ✓
│   │   ├── unified_manifest.csv              (1,893,919 rows)
│   │   ├── train_speaker_independent.csv     (1,483,741)
│   │   ├── val_speaker_independent.csv       (155,604)
│   │   ├── test_speaker_independent.csv      (254,574)
│   │   ├── split_statistics.json
│   │   └── speaker_splits.json
│   ├── features/                        ✓ (HDF5; large)
│   │   ├── logmel_chunked.h5                 (training/eval I/O)
│   │   ├── environmental_packed.h5
│   │   └── (optional) logmel_packed.h5
│   └── realworld/                       ✓ ~365k audio files under collection tree
│
├── DataSet/                             ✓ ASVspoof paths (sample: LA eval clips)
│   └── English/ASVspoof2021_* ...
│
├── testing_audios/                      ✓ Manual test set (17 files)
│   ├── trump/           (8)
│   ├── pakistani/       (8)
│   └── synthetic_fake/  (1)
│
├── reports/
│   ├── evaluation/                      ✓ Phase 5 outputs
│   │   ├── comprehensive_evaluation_report.md
│   │   ├── overall_metrics.csv, per_domain_metrics.csv, per_attack_metrics.csv
│   │   ├── threshold_sweep.csv, asvspoof_evaluation.csv, realworld_evaluation.csv
│   │   ├── confusion_matrices/*.png
│   │   └── figures/roc_*.png
│   ├── phase6_explanation_runs/         ✓ Inference experiment outputs
│   │   ├── all_testing_audios/        ← **latest full custom test run**
│   │   ├── v3_pctvote_tuned/, v3_pctvote_p40/, baseline/, v2_*, pak_*, test_manifest/
│   │   └── README.md
│   ├── pipeline_phases/PHASE0–7.md
│   ├── PROJECT_STATE_AUDIT.md           ← this file
│   ├── FULL_PROJECT_DOCUMENTATION.md
│   ├── AUDIO_TESTING_OUTPUT_GUIDE.md
│   └── website/PARTNER_INTEGRATION_GUIDE.md   (Next.js + FastAPI layout; may live on D:\FASSD)
│
├── release/                             ○ Planned Gradio demo (README only; no app.py in E:\FYP)
└── requirements.txt
```

**Not in `E:\FYP` workspace (documented elsewhere):**

- `inference_api/` + TorchScript `model/hybrid_resnet_environmental_best.ts` — described in `reports/website/PARTNER_INTEGRATION_GUIDE.md` (typical root `D:\FASSD`).

---

## 2. Current model

### 2.1 Identity

| Item | Value |
|------|--------|
| **Architecture class** | `HybridResNetEnvironmental` |
| **Architecture file** | `code/phase3/hybrid_resnet_environmental.py` |
| **Base ResNet blocks** | `code/models/resnet_cnn.py` (`ResidualBlock`) |
| **Environmental features** | `code/features/environmental_features.py` |
| **Loss** | `code/phase3/multi_task_loss.py` (`MultiTaskLoss`) |
| **Primary checkpoint** | `models_saved/hybrid_resnet_environmental_best.pth` |
| **Checkpoint size** | ~34,980,034 bytes (~33.4 MB) |
| **Parameter count** | **2,902,822** (verified Phase 3) |

### 2.2 Architecture summary

```
Inputs:
  spectrogram:     [B, 1, 64, 400]   log-mel, per-sample normalized
  environmental:   [B, 12]           per-sample normalized

Branches:
  ResNetBranch      → [B, 128]   (~2.83M params)
  EnvironmentalBranch (MLP 12→64→128→128) → [B, 128]   (~26K params)

Fusion:
  concat → Linear(256→128) → [B, 128]

Heads:
  BinaryHead        → [B, 2]   classes: index 0 = bonafide/real, 1 = spoof/fake
  MultiClassHead    → [B, 4]   bonafide | synthesis | conversion | replay
```

### 2.3 Training objective

| Component | Setting |
|-----------|---------|
| **Total loss** | `0.7 × CrossEntropy(binary) + 0.3 × CrossEntropy(multiclass)` |
| **Binary class weights** | `[1.661, 0.339]` → bonafide, spoof (inverse frequency on train) |
| **Multiclass class weights** | `[1.032, 1.999, 0.568, 0.401]` → bonafide, synthesis, conversion, replay |
| **Optimizer** | AdamW, `lr=1e-3`, `weight_decay=1e-4`, betas (0.9, 0.999) |
| **Scheduler** | `ReduceLROnPlateau`, mode=min, factor=0.5, patience=3, `min_lr=1e-6` |
| **Mixed precision** | FP16 (training script) |
| **Epochs run** | 20 |
| **Training script** | `code/phase4/train_hybrid_fast.py` |
| **Training log** | `models_saved/logs/training_hybrid_fast.csv` |

### 2.4 Best epoch selection

| Field | Value |
|-------|--------|
| **Best epoch** | **17** (of 20) |
| **Selection criterion** | **Lowest validation binary EER** (`val_binary_eer`) |
| **Best val binary EER** | **0.2017** (20.17%) |
| **Best val binary AUC** | 0.8650 |
| **Best val binary accuracy** | 86.34% |
| **Best val multiclass accuracy** | 50.41% |
| **Why not epoch 20** | Epoch 20 val loss/EER degraded (`val_binary_eer` ≈ 0.308); checkpoint tracks best EER, not last epoch |

**Note:** Validation loss can spike (e.g. epoch 11, 20); **EER is the checkpoint metric**, not raw loss.

### 2.5 Inference scoring

- Per chunk: `spoof_prob = softmax(binary_logits)[1]`.
- File-level: pooling + threshold (Phase 6); test-set metrics use threshold **0.5** unless sweep specifies otherwise.

---

## 3. Current datasets

### 3.1 Training datasets used (unified pipeline)

| Dataset | Role | Attack types | In unified manifest |
|---------|------|--------------|---------------------|
| **ASVspoof 2021 LA** | Logical access (TTS/cloning) | synthesis + bonafide | ✓ |
| **ASVspoof 2021 DF** | Deepfake / conversion | conversion + bonafide | ✓ |
| **ASVspoof 2021 PA** | Physical access / **replay** | replay + bonafide | ✓ |
| **RealWorld (Phase 0)** | In-the-wild bonafide + some synthetic | bonafide / synthesis | ✓ |

**Not used in unified pipeline:** legacy runs that trained on LA+DF only (pre–Phase 1 PA addition).

### 3.2 Sample counts (full unified manifest)

| Dataset | Samples | % of total |
|---------|----------:|-----------:|
| PA | 943,110 | 49.8% |
| DF | 611,829 | 32.3% |
| LA | 181,566 | 9.6% |
| RealWorld | 157,414 | 8.3% |
| **Total** | **1,893,919** | 100% |

### 3.3 Sample counts by label (full manifest)

| Label | Samples | % |
|-------|----------:|--:|
| spoof | 1,573,308 | 83.07% |
| bonafide | 320,611 | 16.93% |

### 3.4 Sample counts by attack type (full manifest)

| Attack type | Samples | % |
|-------------|----------:|--:|
| replay | 816,480 | 43.1% |
| conversion | 589,212 | 31.1% |
| bonafide | 320,611 | 16.9% |
| synthesis | 167,616 | 8.9% |

### 3.5 Speaker-independent splits

| Split | Speakers | Samples | Bonafide % | Spoof % |
|-------|----------|----------:|-----------:|--------:|
| Train | 58,734 | 1,483,741 | 16.9% | 83.1% |
| Val | 7,338 | 155,604 | 19.0% | 81.0% |
| Test | 7,349 | 254,574 | 15.6% | 84.4% |

- **Overlap train∩test speakers:** **0** (verified Phase 5).
- **Split unit:** speaker ID (not clip).
- **Manifests:** `data/manifests/train_speaker_independent.csv`, `val_*`, `test_*`.

### 3.6 Language / domain distribution

**Manifest columns:** `filepath`, `speaker_id`, `label`, `duration`, `file_id`, `dataset`, `filename`, `attack_type`, `domain`, `source` — **no `language` column**.

| Domain (all data) | Samples | % |
|-------------------|----------:|--:|
| studio | 1,819,660 | 96.1% |
| read_speech | 28,539 | 1.5% |
| broadcast | 17,994 | 0.9% |
| podcast | 17,512 | 0.9% |
| social | 5,712 | 0.3% |
| synthetic | 4,502 | 0.2% |
| **phone** | **0** in `split_statistics.json` | (planned in Phase 0, not populated in final counts) |

**Language (inferred, not labeled in manifest):**

| Source | Typical language |
|--------|------------------|
| ASVspoof LA/DF/PA | English |
| LibriSpeech / VCTK (RealWorld) | English |
| YouTube broadcast/podcast/social (RealWorld) | Mostly English (some channels may include other languages; not tagged) |
| **Urdu / Pakistani custom tests** | **Not in training manifest** |

### 3.7 Pakistani / Urdu in training?

| Question | Answer |
|----------|--------|
| Dedicated Urdu/Pakistani training set? | **No** |
| Urdu in manifest metadata? | **No language field** |
| South-Asian broadcast in RealWorld? | Possible in YouTube crawl but **not quantified**; dominated by English read/studio/broadcast |

### 3.8 Replay and manipulated human audio in training?

| Type | In training? | How |
|------|--------------|-----|
| **ASVspoof PA replay attacks** | **Yes** | ~816k replay-labeled spoof segments (replay of bonafide recordings) |
| **ASVspoof synthesis** | Yes | LA spoof |
| **ASVspoof conversion** | Yes | DF spoof |
| **Real-world “human replay” (e.g. phone speaker)** | **Not as a dedicated class** | Only if captured under RealWorld bonafide collection |
| **Mixer-processed / WhatsApp** | **Not labeled** | No WhatsApp-specific domain in final stats |
| **Custom Pakistani “fake” clips** | **No** | Test-only under `testing_audios/pakistani/` |

### 3.9 Raw audio availability

| Data | Status |
|------|--------|
| **ASVspoof clips** | Manifest paths point to `E:\FYP\DataSet\English\ASVspoof2021_*` — **path exists** at audit (`ASVspoof2021_LA_eval` verified) |
| **RealWorld** | **`data/realworld/`** — **~365,234 files** on disk |
| **Training features** | Pre-extracted HDF5 (`logmel_chunked.h5`, `environmental_packed.h5`) — primary training path |
| **Custom tests** | `testing_audios/` — **17 wav files** present |

---

## 4. Current evaluation (Phase 5)

**Report:** `reports/evaluation/comprehensive_evaluation_report.md` (generated 2026-02-13)  
**Checkpoint:** `models_saved/hybrid_resnet_environmental_best.pth`  
**Test manifest:** `data/manifests/test_speaker_independent.csv` (254,574 segments)

### 4.1 Overall metrics (@ threshold 0.5)

| Metric | Value |
|--------|------:|
| **Binary EER** | **16.21%** |
| **Binary AUC** | **0.9167** |
| **Binary accuracy** | **89.78%** |
| **Multiclass accuracy** | **64.36%** |

### 4.2 Per split (dataset group)

| Split | Samples | EER ↓ | AUC ↑ | Acc @0.5 | Multiclass acc |
|-------|--------:|------:|------:|---------:|---------------:|
| ASVspoof (LA+DF+PA) | 237,490 | 18.15% | 0.8947 | 90.65% | 63.39% |
| RealWorld | 17,084 | **16.14%** | **0.9236** | 77.68% | 77.89% |

### 4.3 Per ASVspoof subset

| Dataset | Samples | EER ↓ | AUC ↑ | Acc @0.5 | Multiclass acc |
|---------|--------:|------:|------:|---------:|---------------:|
| LA | 24,388 | 6.30% | 0.9847 | 94.53% | 56.52% |
| DF | 94,032 | 8.33% | 0.9763 | 92.16% | 88.65% |
| PA | 119,070 | 16.23% | 0.9095 | 88.66% | 44.84% |
| RealWorld | 17,084 | 16.14% | 0.9236 | 77.68% | 77.89% |

### 4.4 Per attack type (test)

| Attack type | Samples | Acc @0.5 | Multiclass acc | Notes |
|-------------|--------:|---------:|---------------:|-------|
| bonafide | 39,737 | 58.72% | 61.05% | High false spoof rate at 0.5 |
| synthesis | 22,192 | 94.71% | 51.60% | |
| conversion | 90,585 | 92.20% | 88.51% | |
| replay | 102,060 | 98.65% | 46.98% | Binary easy; multiclass weak |

### 4.5 Threshold sweep (full test set)

| Threshold | Accuracy % | Bonafide FPR % |
|----------:|-------------:|---------------:|
| 0.50 | 89.78 | **41.28** |
| 0.65 | 89.61 | 39.28 |
| 0.70 | 89.52 | 38.43 |

Source: `reports/evaluation/threshold_sweep.csv`

### 4.6 Confusion matrices & ROC

| Artifact | Path |
|----------|------|
| Binary confusion matrix | `reports/evaluation/confusion_matrices/overall_binary_cm.png` |
| Multiclass confusion matrix | `reports/evaluation/confusion_matrices/overall_multiclass_cm.png` |
| ROC overall | `reports/evaluation/figures/roc_overall.png` |
| ROC ASVspoof | `reports/evaluation/figures/roc_asvspoof.png` |
| ROC RealWorld | `reports/evaluation/figures/roc_realworld.png` |

### 4.7 False positive / false negative examples

**Phase 5** evaluates **254k pre-segmented clips**; it does **not** export a per-file FP/FN CSV. Below are **documented failure modes** and **manual-test examples**.

#### Aggregate false positives (bonafide called spoof @ 0.5)

- **~41.3% bonafide FPR** on full test set (threshold sweep).
- **Pattern:** Real/bonafide segments from broadcast-like or dry/processed conditions often score high spoof probability.
- **RealWorld accuracy @0.5:** 77.68% (worse than ASVspoof ~90.7%) — domain still harder despite EER &lt; 20%.

#### Multiclass “logical” errors

- **Replay:** 98.7% binary acc but **47.0%** multiclass acc — model detects “fake” but mis-labels attack type.
- **Synthesis:** low precision (0.16) in sklearn report — confusion with other spoof classes.

#### Manual custom-test false positives (REAL → FAKE)  
**Run:** `reports/phase6_explanation_runs/all_testing_audios/` (`pct_vote`, vote 0.70)

| File | Ground truth | Prediction | decision_score |
|------|--------------|------------|----------------:|
| imran_khan_r2.wav | REAL | FAKE | 0.828 |
| imran_khan_r3.wav | REAL | FAKE | 0.941 |
| imran_khan_real1.wav | REAL | FAKE | 0.960 | *(file removed from disk; result from run when file existed)* |
| saqib_nisar_son_r1.wav | REAL | FAKE | 0.900 |

#### Manual custom-test false negatives (FAKE → REAL)

| File | Ground truth | Prediction | decision_score |
|------|--------------|------------|----------------:|
| imran_khan_f2.wav | FAKE | REAL | 0.611 |

#### Historical false positives (baseline Phase 6, mean @ 0.5, file-level env)

**Run:** `reports/phase6_explanation_runs/baseline/`

| File | Ground truth | Prediction | Notes |
|------|--------------|------------|-------|
| trump_r1.wav | REAL | FAKE | spoof_prob 0.932 |
| trump_r2.wav | REAL | FAKE | spoof_prob 0.689 |
| trump_r3.wav | REAL | FAKE | (baseline; fixed under pct_vote) |
| trump_r5.wav | REAL | FAKE | (baseline) |

---

## 5. Current Phase 6 inference

### 5.1 Canonical offline command (research / matches latest custom tests)

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

### 5.2 Latest full custom-test command (all 17 files)

Same as above with:

```text
--audio_dir E:/FYP/testing_audios
--output_dir reports/phase6_explanation_runs/all_testing_audios
```

**Note:** `imran_khan_r1.wav` exists on disk but was **not** in `all_testing_audios/results.csv` (run may predate file or skip). `imran_khan_real1.wav` appears in CSV but **not on disk** (renamed/removed).

### 5.3 Website / backend (if deployed per partner guide)

Documented in `reports/website/PARTNER_INTEGRATION_GUIDE.md` (typically **`D:\FASSD`**, not `E:\FYP`):

| Setting | Value |
|---------|--------|
| Model artifact | `model/hybrid_resnet_environmental_best.ts` (TorchScript) |
| `POOLING` | `pct_vote` |
| `CHUNK_THRESHOLD` | `0.65` |
| `VOTE_THRESHOLD` | `0.70` |
| `VAD_RMS_PERCENTILE` | `40` |
| `VAD_MIN_SPEECH_RATIO` | `0.40` |
| Entrypoint | `uvicorn app.main:app` on port 8000 |

**Difference from CLI:** API uses `.ts`; CLI uses `.pth`. API omits some `spec_reasons` chunk-consistency lines unless ported.

### 5.4 Inference settings (latest recommended)

| Parameter | Value |
|-----------|--------|
| Chunk duration | 4.0 s |
| Overlap | 1.0 s |
| Pooling | **pct_vote** |
| chunk_threshold | **0.65** |
| vote_threshold | **0.70** |
| threshold (non-pct) | 0.65 (unused when pooling=pct_vote) |
| VAD mode | file_percentile |
| VAD RMS percentile | **40** |
| VAD min speech ratio | **0.40** |
| batch_size | 32 |

### 5.5 JSON output fields (per file)

See `reports/AUDIO_TESTING_OUTPUT_GUIDE.md` for full definitions. Core fields:

`filename`, `filepath`, `prediction`, `confidence`, `decision_score`, `spoof_prob`, `pooling`, `spoof_prob_mean`, `spoof_prob_median`, `spoof_prob_trimmed`, `spoof_prob_logit_mean`, `pct_chunks_above_chunk_threshold`, `threshold`, `effective_threshold`, `chunk_threshold`, `vote_threshold`, `attack_type`, `attack_type_idx`, `attack_type_conf`, `attack_probs`, `n_chunks`, `n_chunks_total`, `n_chunks_used`, `vad_*`, `speech_ratio_*`, `env_features`, `env_reasons`, `spec_reasons`, `overall_explanation`

### 5.6 Recent Phase 6 run folders (`results.csv` present)

| Folder | Purpose |
|--------|---------|
| **all_testing_audios** | **Latest 17-file custom test** |
| v3_pctvote_tuned | Trump 8/8 tuned |
| v3_pctvote_p40 / p40_only | VAD percentile 40–50 |
| v2_pct70, v2_median | Threshold / pooling experiments |
| v3_pctvote | vote_threshold 0.50 |
| baseline | Old mean @ 0.5, file-level env |
| pak_pctvote_c65_v70, c75_v70, c80_v70 | Pakistani threshold sweeps |
| pak_median_t65 | Pakistani median |
| test_manifest | 100 clips from test CSV |

Per-file JSONs: each folder contains `{stem}.json` + `results.csv` (where run completed).

---

## 6. Custom test audio inventory

**Convention:** `r` = real (human), `f` = fake (AI/synthetic) in filenames.  
**Latest predictions:** `reports/phase6_explanation_runs/all_testing_audios/` (`pct_vote`, vote 0.70, VAD p40).

Metadata columns marked **unknown** were not recorded in the repo; fill in manually if needed for thesis.

| Filename | Source type (inferred) | Language | Speaker | Device / mic | Ground truth | Prediction | decision_score | attack_probs [bonafide, synth, conv, replay] |
|----------|------------------------|----------|---------|--------------|--------------|------------|---------------:|-----------------------------------------------|
| trump_f1.wav | AI direct (synthetic) | English | Donald Trump | unknown | **FAKE** | FAKE | 1.000 | [0.001, 0.172, 0.826, 0.000] |
| trump_f2.wav | AI direct | English | Donald Trump | unknown | **FAKE** | FAKE | 1.000 | [0.000, 0.056, 0.944, 0.000] |
| trump_f3.wav | AI direct | English | Donald Trump | unknown | **FAKE** | FAKE | 0.944 | [0.058, 0.492, 0.450, 0.000] |
| trump_r1.wav | YouTube / broadcast (human) | English | Donald Trump | unknown | **REAL** | REAL | 0.156 | [0.807, 0.118, 0.075, 0.000] |
| trump_r2.wav | YouTube / broadcast (long) | English | Donald Trump | unknown | **REAL** | REAL | 0.676 | [0.310, 0.219, 0.466, 0.006] |
| trump_r3.wav | YouTube / broadcast (long) | English | Donald Trump | unknown | **REAL** | REAL | 0.486 | [0.493, 0.237, 0.270, 0.000] |
| trump_r4.wav | YouTube / broadcast | English | Donald Trump | unknown | **REAL** | REAL | 0.220 | [0.712, 0.196, 0.087, 0.005] |
| trump_r5.wav | YouTube / broadcast | English | Donald Trump | unknown | **REAL** | REAL | 0.535 | [0.484, 0.140, 0.376, 0.000] |
| imran_khan_f1.wav | AI direct (inferred) | Urdu | Imran Khan | unknown | **FAKE** | FAKE | 0.742 | [0.327, 0.237, 0.436, 0.000] |
| imran_khan_f2.wav | AI direct (inferred) | Urdu | Imran Khan | unknown | **FAKE** | REAL ❌ | 0.611 | [0.418, 0.138, 0.444, 0.000] |
| imran_khan_f3.wav | AI direct (inferred) | Urdu | Imran Khan | unknown | **FAKE** | FAKE | 0.733 | [0.268, 0.166, 0.566, 0.000] |
| imran_khan_r1.wav | human direct / broadcast (inferred) | Urdu | Imran Khan | unknown | **REAL** | *not in latest CSV* | — | — |
| imran_khan_r2.wav | human / broadcast (inferred) | Urdu | Imran Khan | unknown | **REAL** | FAKE ❌ | 0.828 | [0.175, 0.618, 0.108, 0.099] |
| imran_khan_r3.wav | human / broadcast (inferred) | Urdu | Imran Khan | unknown | **REAL** | FAKE ❌ | 0.941 | [0.091, 0.658, 0.251, 0.000] |
| saqib_nisar_f1.wav | AI direct (inferred) | Urdu | Saqib Nisar | unknown | **FAKE** | FAKE | 1.000 | [0.013, 0.667, 0.241, 0.079] |
| saqib_nisar_son_r1.wav | human (inferred) | Urdu | Saqib Nisar (son) | unknown | **REAL** | FAKE ❌ | 0.900 | [0.072, 0.001, 0.928, 0.000] |
| synthetic_f1.wav | AI direct | unknown | unknown | unknown | **FAKE** | FAKE | 0.900 | [0.214, 0.468, 0.318, 0.000] |

**Latest run accuracy:** 12/17 (70.6%) — Trump 8/8, Synthetic 1/1, Pakistani 3/8.

---

## 7. Current limitations

### 7.1 Where the model fails

| Area | Symptom | Evidence |
|------|---------|----------|
| **Bonafide @ 0.5** | Many reals called spoof | 41.3% bonafide FPR on test sweep |
| **Urdu / Pakistani speech** | Reals called FAKE | 4/5 Pakistani reals wrong in latest manual run |
| **Long broadcast (untuned)** | REAL → FAKE | baseline Phase 6 on Trump (fixed with pct_vote) |
| **Attack typing** | Wrong spoof subclass | Multiclass 64%; replay multiclass ~47% |
| **PA subset** | Weaker multiclass | PA multiclass acc 44.84% on test |
| **Legacy ResNet-only** | 100% FAKE on Trump | `test_audio_simple.py` + old checkpoint |

### 7.2 Weak domains

| Domain | Test EER | Acc @0.5 | Comment |
|--------|---------:|---------:|---------|
| studio (ASVspoof) | ~low EER on LA/DF | high | Dominates training (96% studio) |
| RealWorld | 16.14% | 77.68% | MVP met for EER; accuracy still moderate |
| broadcast / podcast / social | small % of train | — | Underrepresented vs studio |
| **Urdu / South Asian** | **not in eval split** | **~37.5% manual** | **Out-of-distribution** |
| phone | 0 train samples in stats | — | Not in final unified counts |

### 7.3 Data gaps (confirmed)

| Gap | Status |
|-----|--------|
| Pakistani / Urdu in training | **No dedicated data** |
| WhatsApp-compressed test track | **Not in training labels** |
| Mixer-processed human replay as class | **Not labeled** (PA replay is different: ASVspoof replay attack) |
| Balanced bonafide at inference threshold | Needs **0.65–0.70** or pct_vote |

### 7.4 What works well

- Speaker-independent test EER **16.21%** overall; RealWorld **16.14%** (&lt; 20% target).
- Trump English broadcast set **8/8** with tuned Phase 6 settings.
- DF/LA subsets: strong AUC (&gt; 0.97).

---

## 8. Hardware constraints

### 8.1 Systems used in project

| Machine | GPU | VRAM | RAM | Role |
|---------|-----|------|-----|------|
| **Laptop** | NVIDIA RTX **3050** | **6 GB** | ~16 GB | Feature extraction, repack, smaller batch training |
| **PC** | NVIDIA RTX **3070** | **8 GB** | more headroom | **Final 20-epoch hybrid training** (batch 128) |

### 8.2 Verified training limits (RTX 3050 6 GB)

| Batch size | VRAM usage | Status |
|------------|------------|--------|
| 32 | ~18.7% | Safe |
| 64 | ~33.3% | **Recommended** |
| 96 | ~49.7% | Safe |
| 128 | ~64.4% | Possible with FP16 |

- **FP16 mixed precision:** ~30% speedup, required for comfortable 6 GB training.
- **HDF5:** Must use uncompressed + chunked `logmel_chunked.h5` on **NVMe** (gzip was ~470 ms/sample).

### 8.3 SSL / transformers (Phase 7E) — when and on what hardware

| System | GPU | VRAM | Role |
|--------|-----|------|------|
| Laptop (historical) | RTX 3050 | 6 GB | Feature extraction, small-batch experiments |
| PC (training) | RTX 3070 | 8 GB | Final hybrid 20-epoch training |
| **PC (current for 7E)** | *(see project notes)* | **12 GB** | **Practical for Phase 7E after 7A + 7C** |

**Phase order (do not skip):** 7A test → 7B data → **7C hybrid fine-tune** → 7D report/UI → **7E SSL/transformer compare + possible ensemble**.

Phase **7E** is delayed for **process reasons** (need hybrid baseline + forensic tests), **not** because transformers are impossible.

| Model / approach | After 7A + 7C on **12 GB VRAM** |
|------------------|----------------------------------|
| **Current hybrid** | **Proven** — Phase 7C fine-tune first |
| **wav2vec2-base** | Practical: frozen backbone + head, LoRA/adapters, small-batch fine-tune |
| **WavLM-base** | Same as wav2vec2-base |
| **AASIST-style** | Practical as experiment vs hybrid on 7A manifest |
| **WavLM-large** | Still heavy; not default 7E choice |
| **Ensemble** | Only after side-by-side metrics vs fine-tuned hybrid |

**Do not start 7E yet.** See [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md).

---

## Audit checklist (quick reference)

| Item | Status |
|------|--------|
| Hybrid checkpoint in `models_saved/` | ✓ |
| Phase 5 evaluation reports | ✓ |
| Phase 6 tuned inference documented | ✓ |
| Speaker-independent 1.89M dataset | ✓ |
| Urdu in training | ✗ |
| Phone domain in training counts | ✗ |
| Replay attacks in training (PA) | ✓ |
| Gradio `release/app.py` in E:\FYP | ○ not present |
| FastAPI `inference_api/` in E:\FYP | ○ see partner guide (D:\FASSD) |

---

**Related docs:** `reports/FULL_PROJECT_DOCUMENTATION.md`, `reports/AUDIO_TESTING_OUTPUT_GUIDE.md`, `reports/pipeline_phases/PHASE*.md`

---

## Next direction based on audit

### Baseline suitability

| Assessment | Detail |
|------------|--------|
| **Keep hybrid as baseline** | `HybridResNetEnvironmental` is trained, evaluated (RealWorld EER 16.14%), and wired to Phase 6. |
| **Not final forensic product** | Outputs are binary + auxiliary attack class; missing origin/manipulation layers. |
| **Do not train yet** | Phase **7A** controlled forensic tests must run first. |

### Biggest gaps (priority order for 7A)

1. **Urdu / Pakistani** — not in training; poor manual accuracy.  
2. **Phone / social / WhatsApp compression** — not in manifest domain counts.  
3. **Mixer / channel-processed human audio** — likely FPs or wrong user interpretation.  
4. **Human replay** (speaker → phone) — model may say REAL while recording is not original.  
5. **Multiclass attack hints** — weak; do not use as forensic verdict.  

### Next required action

1. Read [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md).  
2. Fill [phase7_forensic_tests/forensic_test_manifest.csv](phase7_forensic_tests/forensic_test_manifest_template.csv) from template (~40 P0 cases).  
3. Execute [PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md).  
4. Follow [NEXT_ACTIONS.md](NEXT_ACTIONS.md).  

Fine-tuning (**Phase 7C**) only after `FORENSIC_TEST_ANALYSIS.md` is reviewed. **Phase 7E** (SSL/transformer/AASIST) only after **7C** — 12 GB VRAM makes 7E practical, not immediate.

---

**End of audit**
