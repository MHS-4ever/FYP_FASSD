# Trump Testing Audios & Phase 6 Explanation Analysis

**Date**: February 2026  
**Purpose**: Document the full analysis of why real Trump audios (trump_r1, trump_r2, trump_r3, trump_r5) were predicted as FAKE by the Phase 6 explanation system, and to separate **duration/long-audio effects** from **model/checkpoint behaviour**.  
**Status**: Analysis complete; solutions documented for implementation.

---

## 1. Context and User Concern

- **Testing audios**: `testing_audios/` contains 8 Trump files: 6 real (`trump_r1`–`trump_r6`) and 2 fake (`trump_f1`, `trump_f2`).
- **Observed issue**: Phase 6 (`explain_prediction.py`) marked **trump_r1, trump_r2, trump_r3, trump_r5** as FAKE although they are actual Trump recordings.
- **Questions addressed**:
  1. Is **duration** (very long files, long pauses) causing the misclassifications?
  2. Does the model **lean toward predicting FAKE** (bonafide false positives)?
  3. What are the **root causes** and **concrete solutions**?

All findings below are based on **measured data and experiments**, not assumptions.

---

## 2. Testing Audios: Duration and Basic Stats

Durations were measured with `librosa.load(..., sr=16000, mono=True)`; frame-level stats use 25 ms window, 10 ms hop (aligned with pipeline).

### 2.1 File Durations (seconds)

| File          | Duration (sec) | Approx.   | n_chunks (4s, 1s overlap) |
|---------------|----------------|-----------|----------------------------|
| trump_f1.wav  | 146.78         | ~2.4 min  | 48                         |
| trump_f2.wav  | 75.28          | ~1.3 min  | 24                         |
| trump_r1.wav  | 117.05         | ~2.0 min  | 38                         |
| trump_r2.wav  | **4832.22**    | **~80.5 min** | 1610                   |
| trump_r3.wav  | **4947.01**    | **~82.5 min** | 1648                   |
| trump_r4.wav  | 2034.34        | ~34 min   | 677                        |
| trump_r5.wav  | 1648.25        | ~27 min   | 549                        |
| trump_r6.wav  | 1629.18        | ~27 min   | 542                        |

**Conclusion**: Several real files are **extremely long** (27–82 minutes). Training and Phase 2 feature extraction use **fixed 4 s windows** (400 frames @ 10 ms hop). Inference on 80-minute files is a different regime: hundreds to thousands of 4 s chunks are aggregated.

### 2.2 Silence / Low-Energy (Pipeline-Aligned)

Using 10th-percentile RMS threshold and proportion of frames below -40 dB (librosa RMS, frame_length=400, hop_length=160):

| File          | duration_sec | silence_ratio_p10 | silence_ratio_below_-40dB | rms_db_median | rms_db_p10 |
|---------------|--------------|-------------------|---------------------------|---------------|------------|
| trump_f1.wav  | 146.78       | 0.1000            | 0.2069                    | -30.26        | -50.15     |
| trump_f2.wav  | 75.28        | 0.1000            | 0.2037                    | -30.89        | -49.24     |
| trump_r1.wav  | 117.05       | 0.1000            | 0.3423                    | -34.53        | -57.50     |
| trump_r2.wav  | 4832.22      | 0.1000            | 0.0261                    | -17.13        | -33.86     |
| trump_r3.wav  | 4947.01      | 0.1000            | 0.0612                    | -37.57        | -16.24     |
| trump_r4.wav  | 2034.34      | 0.1000            | 0.4675                    | -39.14        | -58.04     |
| trump_r5.wav  | 1648.25      | 0.1000            | 0.4492                    | -37.89        | -58.55     |
| trump_r6.wav  | 1629.18      | 0.1000            | 0.2841                    | -30.23        | -51.41     |

Silence ratio (p10) is ~0.1 for all; long files still have many low-energy segments that become separate chunks. So **duration and chunk count** are the main structural difference, not a single “silence ratio” number.

---

## 3. Phase 5 Evaluation: Model Behaviour on Test Set

Source: `reports/evaluation/comprehensive_evaluation_report.md`, `overall_metrics.csv`, `per_attack_metrics.csv`, and binary confusion matrix.

### 3.1 Overall Test Metrics (Speaker-Independent)

- **Samples**: 254,574  
- **Binary EER**: 16.22%  
- **Binary AUC**: 0.9167  
- **Binary Accuracy @0.5**: 89.78%  
- **Multiclass Accuracy**: 64.36%

### 3.2 Real-World Subset

- **Samples**: 17,084  
- **Binary EER**: 16.14%  
- **Binary AUC**: 0.9236  
- **Binary Accuracy @0.5**: 77.68%

So on the **labelled test set**, RealWorld accuracy at threshold 0.5 is ~77.7%.

### 3.3 Bonafide vs Spoof (Per-Attack Metrics)

From `per_attack_metrics.csv` and the **binary confusion matrix**:

- **Bonafide (real)**: 39,737 samples → **Binary accuracy on bonafide ~58.72%** (many real samples predicted as spoof).
- **Confusion matrix (binary)**:
  - True bonafide → predicted bonafide: 23,334  
  - **True bonafide → predicted spoof (false positives): 16,403**  
  - True spoof → predicted bonafide: 9,614  
  - True spoof → predicted spoof: 205,223  

So **16,403 / 39,737 ≈ 41.3% of bonafide samples** are predicted as FAKE at threshold 0.5. The checkpoint is **bonafide-fragile**: it tends to call real audio “fake” more often than desired.

---

## 4. Phase 6 Trump Results (Full Files, Threshold 0.5)

Source: `reports/explanation_examples/results.csv` (and per-file JSONs).

| File          | True label | Prediction | spoof_prob | n_chunks |
|---------------|------------|------------|------------|----------|
| trump_f1.wav  | FAKE       | FAKE       | 0.999      | 48       |
| trump_f2.wav  | FAKE       | FAKE       | 1.000      | 24       |
| trump_r1.wav  | REAL       | **FAKE**  | 0.932      | 38       |
| trump_r2.wav  | REAL       | **FAKE**  | 0.689      | 1610     |
| trump_r3.wav  | REAL       | **FAKE**  | 0.529      | 1648     |
| trump_r4.wav  | REAL       | REAL       | 0.275      | 677      |
| trump_r5.wav  | REAL       | **FAKE**  | 0.580      | 549      |
| trump_r6.wav  | REAL       | REAL       | 0.199      | 542      |

- **Accuracy on 8 Trump files @0.5**: 4/8 correct (50%). Four real files (r1, r2, r3, r5) predicted FAKE.
- **Chunk consistency**: For r2, r3, r4, r5, r6 the reported spoof prob range across chunks is **[0.000, 1.000]** — high variance. Mean aggregation is therefore strongly influenced by a minority of high-spoof chunks.

---

## 5. Threshold Sweep (Trump 8-File Set)

Using `reports/explanation_examples/results.csv`, treating `_f` as true spoof (1) and `_r` as real (0); prediction = (spoof_prob >= threshold).

| Threshold | Accuracy | False positives (real→FAKE) | False negatives (fake→REAL) |
|-----------|----------|-----------------------------|-----------------------------|
| 0.50      | 0.500    | 4                           | 0                           |
| 0.55      | 0.625    | 3                           | 0                           |
| 0.60      | 0.750    | 2                           | 0                           |
| 0.65      | 0.750    | 2                           | 0                           |
| 0.70      | 0.875    | 1                           | 0                           |
| 0.75–0.90 | 0.875    | 1                           | 0                           |

**Conclusion**: On this small set, raising threshold from 0.5 to ~0.7 improves accuracy (e.g. 87.5%); one real file (trump_r1) remains misclassified even at 0.9. So **operating point (threshold)** is part of the issue; **duration/aggregation** is another.

---

## 6. Shortened-Clips Experiment (Duration Effect)

To test whether **length** (and thus number of chunks and aggregation) causes the FAKE prediction for some reals, we created shortened clips from the **first** N seconds of each misclassified real file, then re-ran Phase 6.

### 6.1 How the Experiment Was Done

- **Source files**: trump_r1, trump_r2, trump_r3, trump_r5 (the four reals predicted FAKE on full file).
- **Clip lengths**: 30 s, 120 s, 300 s (from start of file).
- **Tool**: `librosa.load` + `soundfile.write`; Phase 6 run with same checkpoint and options (e.g. `--audio_dir` pointing to clip folder, `--threshold 0.5`).
- **Outputs**: Stored under `reports/debug_clips/` (audio) and `reports/debug_clips_explanations/` (CSV + JSON). **These have been removed** after documentation; only the findings are kept here.

### 6.2 Results Summary

| Base file   | Full-file prediction | 30 s clip    | 120 s clip   | 300 s clip   |
|------------|----------------------|-------------|-------------|-------------|
| trump_r1   | FAKE (0.932)         | FAKE (0.910)| FAKE (0.932)| FAKE (0.932)|
| trump_r2   | FAKE (0.689)         | **REAL** (0.444)| **REAL** (0.235)| **REAL** (0.185)|
| trump_r3   | FAKE (0.529)         | **REAL** (0.298)| **REAL** (0.461)| **REAL** (0.449)|
| trump_r5   | FAKE (0.580)         | FAKE (0.858)| FAKE (0.805)| FAKE (0.702)|

**Interpretation**:

- **trump_r2, trump_r3**: Shortening the file **flips** the decision to REAL. So for these, **duration / number of chunks / aggregation** is a direct cause of the FAKE prediction on the full file.
- **trump_r1, trump_r5**: Remain FAKE even at 30 s. For these, the cause is **not** primarily length; it is **content/domain/checkpoint** (e.g. spectral/env pattern, or checkpoint bias).

So: **Duration is a real factor for some files (r2, r3) but not for others (r1, r5).**

---

## 7. Phase 6 Design vs Training (Relevant to Long Audio)

### 7.1 Training (Phase 2 / Phase 4)

- Each **sample** is a **fixed 4 s** segment: spectrogram shape `[64, 400]`, one environmental vector per segment.
- Environmental features in the dataset are computed **per 4 s segment** (per row in the manifest), not over whole files.

### 7.2 Phase 6 Inference (Current)

- Long audio is split into **overlapping 4 s chunks** (e.g. 4 s duration, 1 s overlap).
- **One** environmental feature vector is computed over the **entire file** and **reused for every chunk** (`extract_env_features(..., path, y=y)` then `env_tensor.repeat(spec.size(0), 1)` in `explain_prediction.py`).
- Chunk spoof probabilities are **averaged** (mean) to get file-level `spoof_prob`.
- Decision: FAKE if `spoof_mean >= threshold` (default 0.5).

**Issues for long files**:

1. **Env mismatch**: Model was trained on per-segment env; inference uses one global env vector for 80 minutes of audio → distribution shift.
2. **Mean aggregation**: A minority of high-spoof chunks (e.g. silence, noise, or odd segments) can pull the mean above 0.5 even when most chunks are real.
3. **No robustness**: No median, no “majority vote” of chunks, no trimming of outliers.

---

## 8. Root Causes (Ranked)

1. **Bonafide-fragile operating point**  
   At 0.5, the checkpoint has ~41% false positive rate on bonafide on the full test set. So the model **does** lean toward FAKE for real audio in general.

2. **Long-form inference vs training**  
   Training is on 4 s segments; inference on 80-minute files uses hundreds/thousands of chunks and one global env vector. This is a structural mismatch.

3. **Aggregation method**  
   Mean of chunk spoof probs is sensitive to a few high-spoof chunks; no robust (e.g. median) or voting-based rule.

4. **Full-file environmental vector**  
   One env vector for the whole file is out-of-distribution relative to per-segment env in training.

5. **Domain / content**  
   Some real files (e.g. trump_r1, trump_r5) are predicted FAKE even when shortened; broadcast/processing and spectral/env content play a role.

---

## 9. Solutions (To Be Implemented)

The following are the agreed directions for implementation (next steps).

### 9.1 Inference / Phase 6

- **Per-chunk environmental features**: Compute env features **per 4 s chunk** (or per segment) and pass one env vector per chunk to the model, instead of one vector per file.
- **Robust aggregation**: Replace mean with:
  - **Median** spoof probability across chunks, and/or  
  - **Top-k rule** (e.g. use median of top-k most “real” chunks), and/or  
  - **Fraction of chunks above threshold** (e.g. report “% chunks > 0.5”) and optionally derive file label from majority vote or median.
- **Output**: Add to JSON/CSV at least: `spoof_median`, `pct_chunks_above_threshold`, and optionally `spoof_mean` (current) for comparison.

### 9.2 Operating Point

- **Threshold**: Do not fix at 0.5 for all use cases. Calibrate on validation or RealWorld hold-out (e.g. EER-optimal or target FPR). For Trump-like long broadcast, a higher threshold (e.g. 0.6–0.7) may reduce false positives.
- **Optional**: Expose `--threshold` and document recommended values per scenario (e.g. “for long broadcast, try 0.65”).

### 9.3 Input Policy (Long Audio)

- **VAD / silence-aware processing**: Optionally skip or down-weight non-speech chunks when aggregating.
- **Cap or segment**: Option “use first N minutes” or “decide per segment and report segment-level results” so that one 80-minute file does not force a single global mean over thousands of chunks.
- **Documentation**: In Phase 6 README / PHASE6 doc, state that very long files (>X minutes) are not the primary training regime and recommend clipping or segment-based reporting for production.

### 9.4 Model / Training (Later)

- **Domain adaptation (Phase 7)**: Fine-tune or adapt on real-world/broadcast-style data including hard negatives (real files currently predicted FAKE) to reduce bonafide false positives.
- **Calibration**: Consider temperature scaling or Platt scaling so that scores better reflect confidence and threshold choice is more interpretable.

---

## 10. References

- Pipeline design: `reports/COMPLETE_PIPELINE_TO_GOAL.md`, `reports/COMPLETE_PROJECT_STORY.md`
- Phase 2 feature design: `reports/pipeline_phases/PHASE2_FEATURE_EXTRACTION.md` (4 s, 400 frames)
- Phase 5 evaluation: `reports/pipeline_phases/PHASE5_EVALUATION.md`, `reports/evaluation/comprehensive_evaluation_report.md`
- Phase 6 design: `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`, `code/phase6/explain_prediction.py`
- Previous pipeline / domain issues: `reports/PREVIOUS_PIPELINE_WORK.md`, `reports/ENVIRONMENTAL_CLASSIFIER_RESULTS.md`

---

## 11. Cleanup Performed

After this report was written, the following temporary artifacts from the shortened-clips experiment were **deleted**:

- `reports/debug_clips/` — 12 WAV files (trump_r1/r2/r3/r5 at 30s, 120s, 300s).
- `reports/debug_clips_explanations/` — `results.csv` and 12 per-file JSONs.

The only remaining outputs from the Trump analysis are:

- This document: `reports/TRUMP_ANALYSIS_AND_PHASE6_FINDINGS.md`
- The original Phase 6 run on full Trump files: `reports/explanation_examples/` (results.csv and per-file JSONs).

---

**End of report.** Next step: implement the solutions in Section 9 (Phase 6 inference changes, threshold/calibration, and documentation).
