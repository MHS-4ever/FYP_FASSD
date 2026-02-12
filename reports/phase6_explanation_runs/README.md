# Phase 6 Explanation Runs

This folder contains all Phase 6 explanation outputs. Each subfolder has a `results.csv` and per-file JSONs. **Do not modify** `reports/evaluation/` (Phase 5 outputs).

**Testing audios layout (current):** `testing_audios/` has subfolders — **pakistani/**, **trump/**, **synthetic_fake/**. All results and this layout are **kept as-is**. Further work focuses **only on Trump testing audios** (`testing_audios/trump/`).

**Naming convention:** **r = real**, **f = fake** for all testing audios.

---

## Subfolders and what each run used

### `baseline/`

- **Source**: Original `reports/explanation_examples/`.
- **Config**: Mean pooling, threshold 0.5, **one file-level environmental vector** repeated for all chunks (pre-fix).
- **Result**: **5/8** correct (corrected labels). Three reals (r2, r3, r5) predicted FAKE; r1 predicted FAKE is correct (r1 is fake). Used to identify root causes (aggregation, env mismatch).

---

### `v2_median/`

- **Config**: **Per-chunk** environmental features; **median** pooling; threshold **0.65**; VAD file_percentile (default).
- **Result**: **6/8** correct (corrected labels); r3 fixed; r2, r5 still FAKE. First run after per-chunk env + robust pooling.

---

### `v2_pct70/`

- **Config**: pct_vote pooling with **single threshold 0.70** (chunk and vote both 0.70).
- **Result**: **8/8** correct (corrected labels). r1 predicted FAKE is correct (r1 is fake). Showed that raising the operating point and vote semantics help.

---

### `v3_pctvote/`

- **Config**: pct_vote with **chunk_threshold 0.65**, **vote_threshold 0.50** (split thresholds).
- **Result**: **6/8** (corrected labels); r2, r5 flipped back to FAKE. Vote 0.50 too low for this set.

---

### `v3_pctvote_tuned/`

- **Config**: pct_vote with **chunk_threshold 0.65**, **vote_threshold 0.70**; VAD file_percentile (e.g. p30).
- **Result**: **8/8** correct (corrected labels); VAD actively filtering (e.g. r2 kept 1552/1610 chunks). **Recommended** for long broadcast-style files.

---

### `v3_pctvote_p40_only/`

- **Config**: Same as tuned but **vad_rms_percentile 40** (stronger gating).
- **Result**: **8/8** correct (corrected labels); e.g. r2 kept 1326/1610 chunks. Good balance of gating and stability.

---

### `v3_pctvote_p40/`

- **Config**: Same as p40_only; this folder was later overwritten by a run with **vad_rms_percentile 50** (same output dir). CSV may show p50; r2 had 922/1610 chunks (strongest gating).
- **Result**: **8/8** correct (corrected labels). p30/p40/p50 all give 8/8 on Trump with corrected labels; **p40** is the recommended default.

---

### `test_manifest/`

- **Source**: Original `reports/explanations_test/`.
- **Config**: Run on **test manifest** (e.g. `data/manifests/test_speaker_independent.csv`) with `--max_files` limit (e.g. 100), median pooling, threshold 0.65, VAD file_percentile. Used to validate explanations on the same distribution as Phase 5.

---

### `all_testing_audios/`

- **Config**: Single run over **all** testing audios: `testing_audios/` (recursive) — pakistani/, trump/, synthetic_fake/. Results kept for reference.
- **Result**: Trump 8/8, Synthetic 1/1, Pakistani 3/8. See **`all_testing_audios/RESULTS_ANALYSIS.md`** for per-file breakdown. Further work uses **Trump only**.

---

## Recommended command (Trump testing audios only)

From project root. Use **Trump folder only** for further work:

```powershell
conda activate fassd
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_dir E:/FYP/testing_audios/trump --output_dir reports/phase6_explanation_runs/trump_run --batch_size 32 --pooling pct_vote --chunk_threshold 0.65 --vote_threshold 0.70 --vad_mode file_percentile --vad_rms_percentile 40 --vad_min_speech_ratio 0.40
```

- **Output**: `reports/phase6_explanation_runs/trump_run/results.csv` and per-file JSONs (8 Trump files). For a new run, use a different subfolder (e.g. `trump_run_v2`) so existing runs are not overwritten.
- To re-run on **all** testing_audios (pakistani + trump + synthetic), use `--audio_dir E:/FYP/testing_audios` and e.g. `--output_dir reports/phase6_explanation_runs/all_testing_audios`.

---

## Full Phase 6 documentation

- **Pipeline phase**: `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md` (objective, analysis, root causes, all implemented options, Trump run summary).
- **Code and options**: `code/phase6/README.md`, `code/phase6/explain_prediction.py`.
