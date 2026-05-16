# Audio Testing Guide — What You Get & How Testing Works

This document explains **only the testing/inference step**: what happens when you run audio through the system, what every output field means, and which settings control the result.

**Script**: `code/phase6/explain_prediction.py`  
**Model**: `models_saved/hybrid_resnet_environmental_best.pth` (Hybrid ResNet + Environmental)

---

## Table of contents

1. [How to run a test](#1-how-to-run-a-test)
2. [Step-by-step: what happens to your audio](#2-step-by-step-what-happens-to-your-audio)
3. [Inputs you control (CLI parameters)](#3-inputs-you-control-cli-parameters)
4. [Outputs you receive](#4-outputs-you-receive)
5. [Every field in the JSON / CSV](#5-every-field-in-the-json--csv)
6. [How REAL vs FAKE is decided](#6-how-real-vs-fake-is-decided)
7. [Environmental & spectrogram explanations](#7-environmental--spectrogram-explanations)
8. [Interpreting processed or re-recorded human audio](#8-interpreting-processed-or-re-recorded-human-audio)
9. [Recommended settings](#9-recommended-settings)
10. [Example output (one file)](#10-example-output-one-file)
11. [Console messages](#11-console-messages)

---

## 1. How to run a test

### Test a folder of audio files

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --audio_dir E:/FYP/testing_audios/trump ^
  --output_dir reports/phase6_explanation_runs/my_test ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32
```

### Test a single file

```powershell
python code/phase6/explain_prediction.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --audio_path E:/FYP/testing_audios/trump/trump_r1.wav ^
  --output_dir reports/phase6_explanation_runs/single_test
```

### Where results are saved

| Output | Location |
|--------|----------|
| One JSON per audio file | `{output_dir}/{filename_stem}.json` |
| Summary table (all files) | `{output_dir}/results.csv` |

Example: `reports/phase6_explanation_runs/my_test/trump_r1.json` and `results.csv`.

Supported formats: `.wav`, `.mp3`, `.flac`, `.m4a` (searched recursively under `--audio_dir`).

---

## 2. Step-by-step: what happens to your audio

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD AUDIO                                                    │
│    • Resample to 16,000 Hz, mono                                 │
│    • Any length (seconds to hours)                               │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SPLIT INTO CHUNKS (default: 4 s each, 1 s overlap)            │
│    • Matches training: each chunk ≈ one 4-second segment         │
│    • Long file → hundreds/thousands of chunks                    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. VOICE ACTIVITY GATING (optional but recommended)              │
│    • Compute “speech ratio” per chunk                            │
│    • Drop chunks that are mostly silence/noise                   │
│    • If nothing left → use all chunks (fallback)                 │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PER-CHUNK FEATURES (for each kept chunk)                      │
│    A) Log-mel spectrogram [64 × 400] → normalize per chunk       │
│    B) 12 environmental features → normalize per chunk            │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. HYBRID MODEL (batch on GPU/CPU)                               │
│    Per chunk:                                                     │
│    • spoof probability (0 = real-like, 1 = fake-like)          │
│    • attack-type probabilities (4 classes)                       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. AGGREGATE CHUNKS → ONE FILE-LEVEL SCORE                       │
│    • Pooling: mean / median / trimmed_mean / logit_mean / pct_vote│
│    • Compare score to threshold → REAL or FAKE                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. BUILD EXPLANATIONS + SAVE JSON + CSV                          │
└─────────────────────────────────────────────────────────────────┘
```

**Important**: The model never sees the whole file as one spectrogram. It always sees **4-second windows** (after VAD), then combines them into one decision.

---

## 3. Inputs you control (CLI parameters)

These are the **settings you pass** when testing. They change how chunks are built, filtered, and combined — not the model weights.

### Required

| Parameter | Description |
|-----------|-------------|
| `--ckpt` | Path to trained model, e.g. `models_saved/hybrid_resnet_environmental_best.pth` |

### Audio source (pick one)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--audio_dir` | `E:/FYP/testing_audios` | Folder; all supported audio files inside (recursive) |
| `--audio_path` | — | Single file (overrides `--audio_dir`) |
| `--test_manifest` | — | CSV with paths in column `--manifest_audio_col` |
| `--max_files` | — | Limit how many files to process |

### Chunking (must match training)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--chunk_duration` | `4.0` | Length of each segment in **seconds** |
| `--overlap` | `1.0` | Overlap between consecutive chunks in **seconds** |
| `--batch_size` | `32` | How many chunks the GPU processes at once |

**Example**: 80-minute file → about **1,600** chunks before VAD (with 4 s / 1 s overlap).

### Decision: pooling & thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--pooling` | `median` | How chunk scores become one file score (see [Section 6](#6-how-real-vs-fake-is-decided)) |
| `--threshold` | `0.65` | Cutoff for **mean / median / trimmed_mean / logit_mean** (score ≥ threshold → **FAKE**) |
| `--chunk_threshold` | `0.65` | For **pct_vote only**: chunk counts as “spoof” if prob ≥ this |
| `--vote_threshold` | `0.50` | For **pct_vote only**: file is **FAKE** if fraction of spoof chunks ≥ this (**use 0.70** for long audio) |
| `--trim_fraction` | `0.10` | For `trimmed_mean`: drop top/bottom 10% of chunk scores before averaging |

### Voice activity (VAD) — filters silent chunks

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--vad_mode` | `file_percentile` | `file_percentile` or `abs_db` |
| `--vad_rms_percentile` | `30` | RMS threshold = this percentile of **whole file** (use **40** for broadcast) |
| `--vad_min_speech_ratio` | `0.40` | Keep chunk only if speech ratio ≥ this; set `0` to disable VAD |
| `--vad_db_threshold` | `-45` | Used when `--vad_mode abs_db` |

### Other

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--output_dir` | `reports/explanation_examples` | Where JSON and CSV are written |
| `--debug_chunk_stats` | off | Add min/median/max chunk stats to output |
| `--device` | `cuda` | `cuda` or `cpu` |

### Feature extraction (fixed — do not change for this checkpoint)

These are **not** CLI flags; they are hard-coded to match training:

| Setting | Value |
|---------|------:|
| Sample rate | 16,000 Hz |
| Mel bins | 64 |
| Time frames | 400 (~4 s) |
| FFT | 512 |
| Hop | 160 (10 ms) |
| Window | 400 (25 ms) |

---

## 4. Outputs you receive

For **each audio file** you get:

### A) JSON file (`{name}.json`)

Structured result: prediction, all scores, thresholds used, environmental values, and text explanations.

### B) Row in `results.csv`

Same fields as JSON, one row per file — easy to open in Excel.

### C) Terminal progress

Progress bar `Explaining` and messages like `[DEVICE] cuda`, `[OK] Loaded checkpoint`, `[SAVE] CSV -> ...`.

---

## 5. Every field in the JSON / CSV

Fields are grouped by what they tell you.

---

### 5.1 Main result (what you care about first)

| Field | Type | Meaning |
|-------|------|---------|
| **`prediction`** | `REAL` or `FAKE` | Final label for the whole file |
| **`confidence`** | 0.0 – 1.0 | How sure the model is: if FAKE → confidence ≈ `decision_score`; if REAL → confidence ≈ `1 - decision_score` |
| **`overall_explanation`** | text | One sentence summary, e.g. *"Model predicts REAL (bonafide) with confidence=0.844 (pooling=pct_vote, threshold=0.700)."* |

---

### 5.2 File identity

| Field | Meaning |
|-------|---------|
| `filename` | e.g. `trump_r1.wav` |
| `filepath` | Full path on disk |

If you used `--test_manifest`, optional extra columns may appear:

| Field | Meaning |
|-------|---------|
| `true_label` | Ground truth from manifest (`bonafide` / `spoof`) |
| `true_attack_type` | Ground truth attack type |
| `domain` | e.g. `LA`, `RealWorld` |

---

### 5.3 Decision score (the number that drives REAL/FAKE)

| Field | Range | Meaning |
|-------|-------|---------|
| **`decision_score`** | 0.0 – 1.0 | **The score compared to the threshold.** Higher → more likely **FAKE** |
| `spoof_prob` | 0.0 – 1.0 | Same value as `decision_score` (alias for compatibility) |

**How `decision_score` is computed** depends on `--pooling`:

| Pooling | What `decision_score` is |
|---------|--------------------------|
| `mean` | Average spoof probability over kept chunks |
| `median` | Median spoof probability |
| `trimmed_mean` | Mean after dropping extreme chunks (`--trim_fraction`) |
| `logit_mean` | Average model logits, then softmax → one probability |
| `pct_vote` | **Fraction of chunks** with spoof prob ≥ `--chunk_threshold` |

---

### 5.4 All pooling statistics (always computed, even if not used for decision)

| Field | Meaning |
|-------|---------|
| `pooling` | Which method was used for the final decision |
| `spoof_prob_mean` | Mean of per-chunk spoof probabilities |
| `spoof_prob_median` | Median of per-chunk spoof probabilities |
| `spoof_prob_trimmed` | Trimmed mean of chunk probabilities |
| `spoof_prob_logit_mean` | Logit-mean pooled probability |
| `pct_chunks_above_chunk_threshold` | % of chunks ≥ `chunk_threshold` (same as `decision_score` when pooling = `pct_vote`) |

Use these to see **why** a file was borderline (e.g. mean high but median low → a few bad chunks).

---

### 5.5 Thresholds (what was used for this run)

| Field | Meaning |
|-------|---------|
| `threshold` | `--threshold` (for non–pct_vote pooling) |
| `effective_threshold` | Threshold actually applied: `vote_threshold` if `pct_vote`, else `threshold` |
| `chunk_threshold` | Per-chunk cutoff for `pct_vote` |
| `vote_threshold` | File-level vote cutoff for `pct_vote` |

**Rule**: `prediction = FAKE` if `decision_score >= effective_threshold`.

---

### 5.6 Attack type (secondary — what kind of fake, if applicable)

The model also predicts **attack class** (averaged over chunks):

| Field | Meaning |
|-------|---------|
| `attack_type` | Name: `bonafide`, `synthesis`, `conversion`, or `replay` |
| `attack_type_idx` | 0, 1, 2, or 3 |
| `attack_type_conf` | Confidence for the winning class |
| `attack_probs` | List of 4 probabilities: `[P(bonafide), P(synthesis), P(conversion), P(replay)]` |

**Note**: A file can be labeled **REAL** (`prediction`) while `attack_type` is still `bonafide` with high confidence. For **FAKE** files, `attack_type` suggests the suspected manipulation style (not always reliable on out-of-domain audio).

---

### 5.7 Chunking & VAD (how many segments were used)

| Field | Meaning |
|-------|---------|
| `n_chunks_total` | Chunks created from the full audio (before VAD) |
| `n_chunks` / `n_chunks_used` | Chunks kept after VAD and used for the model |
| `vad_mode` | `file_percentile` or `abs_db` |
| `vad_rms_percentile` | Percentile used for file-level RMS gate |
| `vad_file_rms_threshold` | Computed RMS threshold (only in `file_percentile` mode) |
| `vad_db_threshold` | dB threshold (only in `abs_db` mode) |
| `vad_min_speech_ratio` | Minimum speech ratio to keep a chunk |
| `vad_fallback_all` | `true` if VAD removed everything → all chunks were used anyway |
| `speech_ratio_mean_used` | Average speech ratio of chunks used |
| `speech_ratio_median_used` | Median speech ratio of chunks used |

**Example**: `n_chunks_used` = 475, `n_chunks_total` = 542 → 67 chunks dropped as non-speech.

---

### 5.8 Environmental features (`env_features`)

Median of per-chunk raw values (for display). **12 numbers**:

| Key | Typical meaning | Interpretation hint |
|-----|-----------------|---------------------|
| `rt60` | Reverberation time (seconds) | 0 → very dry / processed; 0.2–2.0 → more “natural room” |
| `drr` | Direct-to-reverberant (log scale) | Room / mic geometry |
| `snr` | Signal-to-noise ratio (dB) | Very high (>40–50) → unusually clean |
| `background_level` | Background noise (dB) | Very low (< -70) → near-silent background |
| `silence_ratio` | Fraction of low-energy frames | High → lots of silence |
| `spectral_tilt` | Spectral slope | Timbre / recording chain |
| `spectral_flatness` | Noise-like vs tonal | |
| `spectral_rolloff` | Frequency below which 85% energy lies | Shown in Hz in JSON |
| `cleanliness_score` | “Too perfect” indicator | High → suspiciously clean |
| `high_freq_content` | High-frequency energy fraction | |
| `background_consistency` | Stability of background over time | Low → edits or inconsistent env |
| `env_stability` | Environmental stability | |

These are **shown to the user** in explanations; the model uses **normalized** per-chunk vectors internally.

---

### 5.9 Text explanations (lists of strings)

| Field | Content |
|-------|---------|
| **`env_reasons`** | Human-readable notes from environmental heuristics (SNR, RT60, cleanliness, etc.) |
| **`spec_reasons`** | Notes about chunk consistency, pooling stats, VAD, thresholds |

These are **not** guaranteed SHAP/Grad-CAM attributions — they are rule-based summaries to help you understand the run.

**Example `env_reasons` entries:**

- *"RT60 ≈ 0.0s → little/no measurable reverberation (can indicate synthetic or heavily processed audio)."*
- *"SNR is high (42.3 dB) → audio is very clean compared to typical recordings."*

**Example `spec_reasons` entries:**

- *"Chunk consistency: spoof prob range [0.000, 1.000] across 475 chunks."*
- *"Pooling=pct_vote: mean=0.201, median=0.022, ..."*
- *"VAD(file_percentile) kept 475/542 chunks (min speech ratio=0.40)."*

---

### 5.10 Debug fields (only with `--debug_chunk_stats`)

| Field | Meaning |
|-------|---------|
| `chunk_spoof_min` | Lowest chunk spoof probability |
| `chunk_spoof_p05` | 5th percentile |
| `chunk_spoof_p50` | Median chunk spoof probability |
| `chunk_spoof_p95` | 95th percentile |
| `chunk_spoof_max` | Highest chunk spoof probability |
| `chunk_spoof_std` | Standard deviation across chunks |
| `chunk_rt60_min` / `_med` / `_max` | RT60 spread across chunks |
| `chunk_snr_min` / `_med` / `_max` | SNR spread across chunks |
| `chunk_silence_ratio_min` / `_med` / `_max` | Silence ratio spread |

Use these when a file is borderline and you need to see if a **few outlier chunks** caused a FAKE call.

---

## 6. How REAL vs FAKE is decided

### Per chunk (inside the model)

1. Extract log-mel + 12 env features for one 4 s segment.
2. Hybrid model outputs binary logits → **spoof probability** = P(fake) ∈ [0, 1].

### Per file (after all chunks)

1. Optionally remove low-speech chunks (VAD).
2. Apply **pooling** → single `decision_score`.
3. Compare to **effective_threshold**:
   - `decision_score >= effective_threshold` → **`FAKE`**
   - else → **`REAL`**

### `pct_vote` (recommended for long / broadcast audio)

```
For each kept chunk:
  if spoof_prob >= chunk_threshold (0.65):
    count as "spoof chunk"

decision_score = (spoof chunks) / (total kept chunks)

if decision_score >= vote_threshold (0.70):
  prediction = FAKE
else:
  prediction = REAL
```

**Example**: 475 chunks kept, 74 counted as spoof → decision_score = 74/475 ≈ **0.156** → below 0.70 → **REAL**.

### `median` / `mean` (simpler, shorter files)

```
decision_score = median (or mean) of chunk spoof probabilities

if decision_score >= threshold (0.65):
  prediction = FAKE
else:
  prediction = REAL
```

**Why `pct_vote` helps on long files**: A few loud “spoof-like” chunks no longer dominate; you need **70%** of chunks to agree before calling the whole file fake.

---

## 7. Environmental & spectrogram explanations

### What the model actually uses

| Branch | Input per chunk | Role |
|--------|-----------------|------|
| ResNet | Log-mel [64×400] | Synthetic artifacts in spectrum |
| MLP | Environmental [12] | Recording environment cues |
| Fusion | Both embeddings | Combined real/fake decision |

### What you see in JSON

| Output | Source |
|--------|--------|
| `env_features` | Median of raw env stats over chunks (for reading) |
| `env_reasons` | Rules on those stats (SNR, RT60, cleanliness, …) |
| `spec_reasons` | Rules on chunk spoof prob spread + pooling + VAD |

The **prediction** comes from the **neural network**, not from the text rules. The rules only **explain** tendencies in the features.

---

## 8. Interpreting processed or re-recorded human audio

FASSD is evolving into a **Forensic Voice Authenticity Analyzer**. Phase 6 output must be read with **origin** (human vs AI) separate from **recording integrity** (clean vs replayed/processed/compressed).

### Human origin but not a “clean original” file

If speech was **recorded from a human** but the file was produced by:

- playing audio on a **laptop speaker** and re-recording on a **phone**,
- routing through a **mixer / EQ**,
- forwarding via **WhatsApp** or social apps,

the model may still classify the file as **`REAL`** because the **speech content** is human-like. That does **not** mean the WAV is an untouched original microphone capture.

**Report as:** *human-origin audio with replay/channel/platform processing risk* — not “fully authentic recording.”

### When `attack_type` is conversion or replay but `prediction` is REAL

- **`attack_type`** is an **auxiliary multiclass hint** (synthesis / conversion / replay / bonafide).
- It must **not** override the binary `prediction` in user-facing forensic text.
- If `prediction == REAL` and `conversion` or `replay` probabilities are elevated, describe **manipulation-like or channel artifacts** on human-origin audio — do not label the speaker as “AI fake” without other evidence.

### Borderline / inconclusive scores

Call a result **borderline** or **inconclusive** when:

- `decision_score` is within ~**0.05** of `vote_threshold` (e.g. 0.66–0.74 with threshold 0.70), or
- `n_chunks_used` is very small, or
- chunk spoof probabilities have **high variance** (see `spec_reasons`).

Do not present borderline scores as high-confidence proof.

### AI replay chain

**AI → speaker → phone recording** often shows **AI-origin** (high spoof vote) **plus** replay/channel effects. Forensic text should mention **both** synthetic-like speech evidence and re-recording, not only “deepfake.”

### Further reading

- [FORENSIC_PRODUCT_ROADMAP.md](FORENSIC_PRODUCT_ROADMAP.md) — interpretation rules  
- [FORENSIC_REPORT_OUTPUT_SPEC.md](FORENSIC_REPORT_OUTPUT_SPEC.md) — future report wording  
- [pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md](pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md) — controlled tests for these chains  

---

## 9. Recommended settings

### Short clips (&lt; 30 s)

```text
--pooling median --threshold 0.65 --vad_min_speech_ratio 0
```

### Long / broadcast / Trump-style (proven 8/8 on test set)

```text
--pooling pct_vote
--chunk_threshold 0.65
--vote_threshold 0.70
--vad_mode file_percentile
--vad_rms_percentile 40
--vad_min_speech_ratio 0.40
```

### If too many reals called FAKE

- Raise `--vote_threshold` (e.g. 0.75) or `--threshold` (e.g. 0.70)
- Increase `--vad_rms_percentile` (stronger silence removal)

### If fakes are missed

- Lower `--vote_threshold` (e.g. 0.60) or `--chunk_threshold` (e.g. 0.60)
- Try `--pooling mean` only on short files (not long broadcast)

---

## 10. Example output (one file)

From `reports/phase6_explanation_runs/all_testing_audios/trump_r1.json` (abbreviated):

```json
{
  "filename": "trump_r1.wav",
  "prediction": "REAL",
  "confidence": 0.844,
  "decision_score": 0.156,
  "pooling": "pct_vote",
  "spoof_prob_mean": 0.201,
  "spoof_prob_median": 0.022,
  "pct_chunks_above_chunk_threshold": 0.156,
  "effective_threshold": 0.7,
  "chunk_threshold": 0.65,
  "vote_threshold": 0.7,
  "attack_type": "bonafide",
  "attack_type_conf": 0.807,
  "attack_probs": [0.807, 0.118, 0.075, 0.000],
  "n_chunks_used": 475,
  "n_chunks_total": 542,
  "env_features": {
    "rt60": 0.0,
    "snr": 14.16,
    "background_level": -43.25,
    "...": "..."
  },
  "env_reasons": [
    "RT60 ≈ 0.0s → little/no measurable reverberation ..."
  ],
  "spec_reasons": [
    "Chunk consistency: spoof prob range [0.000, 1.000] across 475 chunks.",
    "Pooling=pct_vote: mean=0.201, median=0.022, ...",
    "VAD(file_percentile) kept 475/542 chunks ..."
  ],
  "overall_explanation": "Model predicts REAL (bonafide) with confidence=0.844 ..."
}
```

**Reading this result:**

- Only **15.6%** of speech chunks looked spoof-like (above 0.65) — below the **70%** vote bar → **REAL**.
- Mean spoof prob (0.20) is higher than median (0.02) → a **small number of harsh chunks**; `pct_vote` ignores them.
- Attack head says **bonafide** with ~81% average confidence across chunks.

---

## 11. Console messages

| Message | Meaning |
|---------|---------|
| `[DEVICE] cuda` | Using GPU (or `cpu` if no CUDA) |
| `[GPU] NVIDIA ...` | GPU name |
| `[OK] Loaded checkpoint: ...` | Model weights loaded |
| `Explaining` (progress bar) | Processing each file |
| `[WARN] Missing audio file, skipping: ...` | Path in manifest not found |
| `[ERROR] filename: ...` | That file failed (corrupt path, etc.) |
| `[SAVE] CSV -> ...` | `results.csv` written |
| `[WARN] No results to save.` | No valid files processed |

---

## Quick reference card

| You want… | Look at… |
|-----------|----------|
| Final label | `prediction` |
| How sure | `confidence` |
| Score vs cutoff | `decision_score` vs `effective_threshold` |
| Why long file went REAL/FAKE | `pct_chunks_above_chunk_threshold`, `n_chunks_used`, `spec_reasons` |
| Kind of fake | `attack_type`, `attack_probs` |
| Recording environment | `env_features`, `env_reasons` |
| Compare many files | `results.csv` |
| Outlier chunks | Re-run with `--debug_chunk_stats` |

---

**Related docs**

- Full project overview: `reports/FULL_PROJECT_DOCUMENTATION.md`
- Forensic product direction: `reports/FORENSIC_PRODUCT_ROADMAP.md`
- Phase 6 pipeline notes: `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`
- Phase 7A test plan: `reports/pipeline_phases/PHASE7A_FORENSIC_TEST_SUITE.md`
- Past test runs: `reports/phase6_explanation_runs/README.md`
- Code: `code/phase6/explain_prediction.py`
