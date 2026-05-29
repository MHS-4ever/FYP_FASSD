# Phase 9D Testing Design

## Purpose

Phase 9D verifies the **Phase 9C live inference architecture** on a **controlled subset** of Phase 7C1 testing audios. This is **architecture verification** and **expected-axis behavior checking**, not a claim of forensic accuracy or court-ready proof.

Testing is needed after Phase 9B model packaging because:

- packaged active models must load and predict in the release layout,
- feature alignment and SSL extraction must work on new files,
- fusion and reporting must remain multi-axis and experimental,
- partial fabrication behavior must be measured across more examples than the four manual smoke cases.

## Scope and safety

- **Active models only:** `release/models/{origin,replay,mixer,partial_segment}/`
- **Reference models inactive:** AASIST / HybridResNet are not used in inference
- **No single binary authenticity score** and **no final fake/real decision** (evidence axes remain separate)
- All outputs: `experimental_forensic_prototype`
- Default sample size: **5 files per detected category** (not full dataset)

## Controlled manifest scan (Phase 9D-P1)

The manifest builder **does not** recursively walk the entire `data/` tree by default.

- **Default `--scan_mode`:** `controlled_folders`
- Scans only named Phase 7C1 raw subfolders (e.g. `ai_direct`, `human_clean`, `ai_mixer_processed`, …)
- **Shallow scan:** files in each folder plus one subdirectory level (no deep `rglob`)
- **Early stopping:** up to `max_per_category × 3` candidates per category, then sample `max_per_category`
- **Limits:** `--max_scan_files` (default 5000), `--max_files_per_folder_scan` (default 200)
- **Skips** paths containing: `augmented`, `rir`, `noise`, `features`, `embeddings`, `cache`, `reports`, etc.
- **No symlink following**
- Writes `reports/phase9/testing/phase9d_manifest_build_report.md` after each build

**Excluded by default:** augmented datasets, RIR/noise corpora, feature caches, and other massive generated trees (e.g. millions of files). Large-scale stress testing is a **later phase** after the local pipeline is stable.

Optional `--scan_mode recursive_limited` exists for small trees only (depth-capped walk with the same skip rules).

## Test categories

| Category | Typical source folders / names | Expected primary axis | Expected fusion (behavior check) |
|---|---|---|---|
| `human_direct` | `human_clean`, `human_direct` | clean_human | `accept_human_clean_experimental` or inconclusive |
| `ai_direct` | `ai_direct` | origin | `suspicious_origin_experimental` |
| `ai_replay` / `human_replay` | replay, repeat, rerecord | replay | `suspicious_replay_experimental` |
| `ai_mixer` / `human_mixer` | mixer, channel, processed | mixer_channel | `suspicious_mixer_channel_experimental` |
| `ai_fabricated` / `human_fabricated` | fabricated | partial review | partial fusion or documented broad activation |
| `bad_audio_*` | synthetic short/silent/invalid | error_or_manual_review | safe error / inconclusive without crash |

Category detection is **heuristic** from paths. Uncertain files are labeled `unknown` and expect manual review.

## Scripts (manual run only)

### 1. Build manifest

```bat
python code/phase9/testing/build_phase9d_test_manifest.py ^
  --audio_root data/phase7c1/raw ^
  --scan_mode controlled_folders ^
  --max_per_category 5 ^
  --include_bad_audio_tests
```

Review `reports/phase9/testing/phase9d_manifest_build_report.md` after the build.

Run from the repository root (`E:\FYP`) so relative paths resolve correctly:

- `data/phase7c1/raw` → audio input folders
- `reports/phase9/testing/phase9d_test_manifest.csv` → manifest output
- `reports/phase9/testing/bad_audio_samples` → synthetic bad-audio output (not project root)

Optional bad-audio synthesis requires `numpy` and `soundfile` or `scipy`.

### 2. Batch inference

```bat
python code/phase9/testing/run_phase9d_batch_inference.py ^
  --manifest reports/phase9/testing/phase9d_test_manifest.csv ^
  --output_dir reports/phase9/testing/phase9d_outputs ^
  --device auto
```

Uses `release.src.inference_pipeline.analyze_audio_file` directly (no training, no apps).

### 3. Summarize results

```bat
python code/phase9/testing/summarize_phase9d_results.py ^
  --manifest reports/phase9/testing/phase9d_test_manifest.csv ^
  --batch_results reports/phase9/testing/phase9d_batch_results.csv ^
  --outputs_dir reports/phase9/testing/phase9d_outputs ^
  --make_plots
```

### 4. Validate artifacts

```bat
python code/phase9/testing/validate_phase9d_end_to_end_tests.py
```

## How to interpret results

Use wording:

- **behavior check**
- **architecture verification**
- **expected-axis consistency**
- **limitation observed**

Do **not** report final accuracy unless category labels are independently validated.

### Partial fabrication limitation

Partial fabrication localization remains a known limitation:

- broad activation (`high_segment_fraction >= 0.60`) is **not** localized partial proof,
- fabricated cases often require review because the live partial model frequently reports broad activation,
- replay/mixer context can block `partial_fusion_eligible` under strict criteria,
- `phase9d_partial_behavior_review.csv` documents per-case gates and block reasons.

This conservative behavior is safer than overclaiming localized fabrication. Phase 9E apps can proceed after the limitation is documented; optional Phase 9D-P4 can tune partial handling later.

### Bad audio

Short/silent/invalid samples should complete without unhandled crashes. Errors should be captured in batch results and JSON.

## Outputs

| File | Description |
|---|---|
| `phase9d_test_manifest.csv` | Controlled case list |
| `phase9d_outputs/<case>_analysis.json` | Per-case forensic JSON |
| `phase9d_outputs/<case>_report.md` | Per-case safe markdown report |
| `phase9d_batch_results.csv` | Batch run summary |
| `phase9d_test_summary.csv` | Expected vs actual consistency |
| `phase9d_category_behavior_summary.csv` | Per-category counts |
| `phase9d_partial_behavior_review.csv` | Partial gate / arbitration review |
| `phase9d_failure_cases.csv` | Errors and unexpected fusion |
| `phase9d_end_to_end_test_report.md` | Human-readable summary |

## Recommendation before Phase 9E

After manual review of batch outputs and partial behavior:

1. Confirm mixer/replay cases are not `suspicious_mixed` solely due to partial overfire.
2. Confirm direct AI/human cases match expected-axis behavior at a high level.
3. Document partial limitations clearly in reports.
4. Proceed to FastAPI/Gradio (Phase 9E) only after this review.
