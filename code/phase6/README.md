# Phase 6: Explanation System

Generate explanations for the Phase 4 hybrid model on raw audio (e.g. `testing_audios/` Trump set). The script chunks long audio, extracts **per-chunk** log-mel and environmental features, runs the trained hybrid checkpoint, and saves per-file JSON/CSV with configurable pooling and VAD gating.

**Outputs**: All Phase 6 runs are organized under **`reports/phase6_explanation_runs/`**. See **`reports/phase6_explanation_runs/README.md`** for what each subfolder contains and the full Phase 6 doc at **`reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`**.

## Quick start (median pooling)

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_dir E:/FYP/testing_audios --output_dir reports/phase6_explanation_runs/my_run --batch_size 32 --pooling median --threshold 0.65 --vad_mode file_percentile --vad_rms_percentile 40 --vad_min_speech_ratio 0.40
```

## Long-audio robust voting (recommended for long/broadcast-style files)

Use **pct_vote** with **vote_threshold 0.70** and **vad_rms_percentile 40** for best balance on long files (e.g. Trump 8-file set: 8/8 correct with corrected labels — trump_r1 is actually FAKE).

```powershell
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_dir E:/FYP/testing_audios --output_dir reports/phase6_explanation_runs/my_run --batch_size 32 --pooling pct_vote --chunk_threshold 0.65 --vote_threshold 0.70 --vad_mode file_percentile --vad_rms_percentile 40 --vad_min_speech_ratio 0.40
```

## Run on the test manifest (validation)

```powershell
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --output_dir reports/phase6_explanation_runs/test_manifest --batch_size 32 --pooling median --threshold 0.65 --vad_mode file_percentile --vad_min_speech_ratio 0.40 --max_files 100
```

## Options (summary)

| Option | Default | Description |
|--------|---------|-------------|
| `--audio_dir` / `--audio_path` | — | Folder or single file |
| `--ckpt` | required | Phase 4 best checkpoint |
| `--test_manifest` | — | CSV with `filepath` for bulk run |
| `--output_dir` | `reports/explanation_examples` | Prefer `reports/phase6_explanation_runs/<name>` |
| `--chunk_duration`, `--overlap` | 4s, 1s | Match Phase 4 training window |
| `--pooling` | `median` | `median`, `trimmed_mean`, `mean`, `logit_mean`, `pct_vote` |
| `--threshold` | `0.65` | For non–pct_vote pooling |
| `--chunk_threshold` | `0.65` | Chunk spoof threshold for pct_vote |
| `--vote_threshold` | `0.50` | Vote-ratio for pct_vote; **0.70** recommended for long audio |
| `--trim_fraction` | `0.10` | For trimmed_mean |
| `--vad_mode` | `file_percentile` | `file_percentile` or `abs_db` |
| `--vad_min_speech_ratio` | `0.40` | Min speech ratio to keep chunk; `0` = no gating |
| `--vad_rms_percentile` | `30` | For file_percentile; **40** recommended |
| `--vad_db_threshold` | `-45` | For abs_db |
| `--debug_chunk_stats` | off | Add chunk stats to JSON/CSV |
| `--batch_size` | 32 | Chunk batch size |

## Notes

- **Per-chunk env**: Environmental features are computed **per 4 s chunk** (aligned with Phase 2/4 training).
- **VAD**: Uses **file-level** RMS percentile (or absolute dB), not chunk-local percentile.
- Outputs include `spoof_prob_mean/median/trimmed`, `pct_chunks_above_chunk_threshold` (for pct_vote), and VAD info.
- Log-mel params match Phase 2 (`n_fft=512, hop=160, win=400`).

