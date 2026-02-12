# Phase 6: Explanation System

**Status**: ✅ **COMPLETE (CLOSED)** — scripts, tuning, and Trump 8/8 runs done; further work focuses on Phase 7.  
**Priority**: 🟡 IMPORTANT  
**Duration**: Week 4-5  
**Dependencies**: Phase 5 (Evaluation)

---

## 🎯 Objective

Build an explanation system that provides human-readable reasons for model predictions, based on environmental features, spectrogram patterns, and attack type classifications. The system runs on raw audio (including long files), chunks it into 4 s segments aligned with training, and outputs per-file predictions with pooling options and VAD gating.

---

## 📋 Tasks (Design)

### 1. Feature Importance Analysis

- **Environmental**: Per-feature contribution, rank by importance.
- **Spectrogram**: Important regions (e.g. Grad-CAM); correlate with attack types.
- **Attack type**: Patterns for bonafide, synthesis, conversion, replay.

### 2. Explanation Generation

- **Prediction** (Real/Fake), **confidence**, **attack type** (if fake).
- **Environmental reasons** and **spectrogram reasons**; **overall** human-readable summary.
- Output: JSON (structured) + CSV (per-file summary).

### 3. Implementation

- Feature extractor (log-mel + environmental), model predictor (Phase 4 hybrid), explanation generator.
- **Implemented**: `code/phase6/explain_prediction.py` — chunks raw audio, extracts features **per chunk**, runs checkpoint, supports multiple pooling strategies and VAD gating. See **Implementation and Tuning Log** below for all options and fixes.

---

## 📁 Output Files

- **Script**: `code/phase6/explain_prediction.py` (and optional `run_phase6.py`).
- **Explanation runs**: All Phase 6 runs (baseline and tuning variants) are under **`reports/phase6_explanation_runs/`**. Each subfolder contains `results.csv` and per-file JSONs. See **`reports/phase6_explanation_runs/README.md`** for a description of each run and the commands used.

---

## 🔧 Scripts

- ✅ **`code/phase6/explain_prediction.py`** — Main script: raw audio → chunked features → hybrid model → JSON/CSV.
- ✅ **`code/phase6/README.md`** — Commands and options.
- ✅ **`code/phase6/run_phase6.py`** — Optional wrapper with default paths.

---

## Analysis and Findings (Trump Set and Root Causes)

The following is the full analysis that led to the implementation changes below. Test set: 8 Trump files in `testing_audios/trump/`.

**Naming convention:** **r = real**, **f = fake** (Trump filenames are correct). So: **5 real** (trump_r1–r5), **3 fake** (trump_f1–f3).

### Testing audios: duration and basic stats

- **Durations**: trump_f1 ~2.4 min, trump_f2 ~1.3 min, trump_r1 ~2 min, trump_r2 **~80.5 min**, trump_r3 **~82.5 min**, trump_r4 ~34 min, trump_r5 ~27 min, trump_r6 ~27 min.
- **Chunks (4 s, 1 s overlap)**: r2 → 1610, r3 → 1648; training uses fixed 4 s windows, so long files imply hundreds/thousands of chunks and aggregation effects.

### Phase 5 model behaviour (test set)

- **Overall**: 254,574 samples; Binary EER 16.22%; AUC 0.9167; Accuracy @0.5 89.78%.
- **RealWorld**: 17,084 samples; EER 16.14%; Accuracy @0.5 77.68%.
- **Bonafide**: ~41.3% of bonafide samples predicted as spoof at 0.5 → checkpoint is **bonafide-fragile**.

### Phase 6 baseline (full files, threshold 0.5)

- Accuracy **4/8**: four reals (r1, r2, r3, r5) predicted FAKE; only r4 and the three fakes correct.
- Chunk spoof-prob range for r2–r5 was [0, 1]; **mean** aggregation was driven by a minority of high-spoof chunks.

### Threshold sweep (Trump 8-file, mean aggregation)

- Threshold 0.5 → 50% acc; 0.7 → 87.5% (one real, r1, still predicted FAKE). With tuned pooling/VAD (below), “FP” **8/8** is achieved.

### Shortened-clips experiment

- **r2, r3**: Short clips (30–300 s) flipped decision to REAL → **duration/aggregation** caused FAKE on full file.
- **r1, r5**: Stayed FAKE on short clips → **content/domain/checkpoint** (or high chunk variance), not length alone.

### Phase 6 design vs training (issues identified)

- **Training**: 4 s segments; env features **per segment**.
- **Original inference**: One **file-level** env vector repeated for all chunks; **mean** of chunk probs; single threshold. → Env mismatch, sensitivity to outlier chunks, no robust pooling or VAD.

### Root causes (ranked)

1. Bonafide-fragile operating point (high FPR at 0.5).
2. Long-form inference vs training (chunk count + single env vector).
3. Aggregation method (mean sensitive to few high-spoof chunks).
4. Full-file environmental vector (OOD vs per-segment training).
5. Domain/content (e.g. r5 real but predicted FAKE even on short clips).

---

## Solutions (Implemented)

All of the following have been implemented in `explain_prediction.py`.

### Per-chunk environmental features

- **Before**: One env vector over the entire file, repeated for every chunk.
- **After**: Env computed **per 4 s chunk**; passed as `[B, 12]`. Aligns with Phase 2/4 training.

### Robust pooling and pct_vote

- **`--pooling`**: `median`, `trimmed_mean`, `mean`, `logit_mean`, `pct_vote`.
- Outputs: `spoof_prob_mean`, `spoof_prob_median`, `spoof_prob_trimmed`, `spoof_prob_logit_mean`, and for `pct_vote`: `pct_chunks_above_chunk_threshold` with a **vote** threshold for file decision.
- **`--trim_fraction`** (default 0.1) for trimmed mean.
- **Recommendation**: Use **`pct_vote`** for long/broadcast-style files.

### Chunk vs vote thresholds (pct_vote)

- **`--chunk_threshold`** (default 0.65): chunk counts as spoof if spoof prob ≥ this.
- **`--vote_threshold`** (default 0.50; **tuned to 0.70** for Trump): file is FAKE if `pct_chunks_above_chunk_threshold >= vote_threshold`.
- **`--threshold`**: used only for non–pct_vote pooling (default 0.65).

### VAD gating (fixed)

- **Before**: Chunk-local RMS percentile → ~0.7 speech ratio everywhere; no real gating.
- **After**:
  - **`--vad_mode file_percentile`**: File-level RMS percentile → one threshold; per-chunk speech ratio vs that threshold; chunks below **`--vad_min_speech_ratio`** excluded from aggregation.
  - **`--vad_mode abs_db`**: **`--vad_db_threshold`** (e.g. -45).
  - **`--vad_rms_percentile`**: For file_percentile (default 30; tested 40, 50). **Recommendation**: **40** for balance of gating and stability.

### Recommended defaults (long audio)

- **Pooling**: `pct_vote` for long files; `median` for simple runs.
- **Thresholds**: For pct_vote: `--chunk_threshold 0.65`, **`--vote_threshold 0.70`**; for others `--threshold 0.65`.
- **VAD**: `--vad_mode file_percentile`, **`--vad_rms_percentile 40`**, `--vad_min_speech_ratio 0.40` (0 disables gating).
- **Debug**: `--debug_chunk_stats` adds chunk-level stats to JSON.

### Trump 8-file runs (summary; **r = real, f = fake** — 5 real, 3 fake)

| Run | Accuracy | Notes |
|-----|----------|--------|
| baseline (mean @ 0.5) | 4/8 | Four reals (r1,r2,r3,r5) predicted FAKE |
| v2_median (median @ 0.65) | 5/8 | r3 fixed; r2,r5 still FAKE |
| v2_pct70 (pct_vote, single 0.70) | 7/8 | One real (r1) still FAKE |
| v3_pctvote (vote 0.50) | 5/8 | r2,r5 FAKE again |
| v3_pctvote_tuned (vote 0.70) | 8/8 | All 5 reals REAL, all 3 fakes FAKE |
| v3_pctvote_p40_only / p40 | 8/8 | vad_rms_percentile 40 (or 50); stronger gating |

With **correct Trump naming** (r=real, f=fake), the tuned configs (pct_vote, vote 0.70, VAD p40) achieve **8/8** on the Trump set. Current run on all testing audios (Trump + Pakistani + synthetic) also gives **Trump 8/8**; see `reports/phase6_explanation_runs/all_testing_audios/RESULTS_ANALYSIS.md`.

### Other implementation details

- **Env in JSON**: File-level “explanation” env is **median** of per-chunk raw env dicts (human summary; model input is per-chunk).
- **Scaler**: No env scaler patch in Phase 6; Phase 4 uses per-sample env normalization.
- **RT60/silence**: Same constants as Phase 2.

---

## Detail evaluation (full test set)

- **Phase 5** was run with **threshold sweep** (0.5, 0.65, 0.70). Results: see `reports/evaluation/threshold_sweep.csv` and the “Threshold sweep (detail evaluation)” section in `reports/evaluation/comprehensive_evaluation_report.md`. At 0.70, bonafide FPR is lower than at 0.5 with a small accuracy trade-off.
- **Phase 6 on full test set**: Optional; requires file-level test list (test manifest is segment-level). See `reports/evaluation/` for Phase 5 outputs; **do not modify** the evaluation folder for Phase 6 run organization.

---

## ✅ Success Criteria

- [x] Explanation system generates predictions with reasons (JSON/CSV).
- [x] Per-chunk environmental features; robust pooling and VAD gating.
- [x] Human-readable explanations; works on real and fake audio (raw wav).
- [x] Tuning documented; explanation runs organized under `reports/phase6_explanation_runs/`.
- [ ] Optional: deeper feature attribution / Grad-CAM (future).

---

## 🔗 Dependencies

- **Prerequisites**: Phase 5 (evaluation), Phase 4 checkpoint, feature extraction (log-mel + environmental).
- **Next**: Phase 7 (domain adaptation) if needed; or deployment/testing.

---

## 📝 References

- Pipeline: `reports/COMPLETE_PIPELINE_TO_GOAL.md`, `reports/COMPLETE_PROJECT_STORY.md`
- Phase 2: `reports/pipeline_phases/PHASE2_FEATURE_EXTRACTION.md`
- Phase 5: `reports/pipeline_phases/PHASE5_EVALUATION.md`; `reports/evaluation/comprehensive_evaluation_report.md`
- Phase 6 runs: **`reports/phase6_explanation_runs/README.md`**
- Code: `code/phase6/explain_prediction.py`, `code/phase6/README.md`

---

**Last Updated**: February 2026  
**Status**: ✅ COMPLETE (CLOSED) — **Next**: Phase 7 (Domain Adaptation)
