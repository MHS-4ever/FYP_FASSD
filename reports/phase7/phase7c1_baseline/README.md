# Phase 7C1 — Baseline Evaluation (Pre Fine-Tuning)

**Purpose:** Run the **current** hybrid checkpoint on all **184** Phase 7C1 collection files and record a **before training** benchmark. No model training or fine-tuning in this step.

**Checkpoint:** `models_saved/hybrid_resnet_environmental_best.pth`  
**Manifest:** `reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv`

---

## Commands (run from repo root, `fassd` env)

### 1. Run baseline inference

```text
python code/phase7/run_phase7c1_baseline.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --output_dir reports/phase7/phase7c1_baseline/results ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32 ^
  --save_chunk_timeline
```

### 2. Analyze results

```text
python code/phase7/analyze_phase7c1_baseline.py ^
  --results_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv ^
  --output_md reports/phase7/phase7c1_baseline/results/PHASE7C1_BASELINE_ANALYSIS.md ^
  --category_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_category_summary.csv ^
  --error_csv reports/phase7/phase7c1_baseline/results/phase7c1_baseline_error_cases.csv ^
  --partial_csv reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv
```

---

## Output layout

```text
reports/phase7/phase7c1_baseline/
├── README.md
├── results/
│   ├── phase7c1_baseline_results.csv
│   ├── PHASE7C1_BASELINE_ANALYSIS.md
│   ├── phase7c1_baseline_category_summary.csv
│   ├── phase7c1_baseline_error_cases.csv
│   ├── phase7c1_partial_fabrication_analysis.csv
│   ├── chunk_timelines/
│   └── json_outputs/
└── logs/
```

---

## Interpretation (product-level)

Evaluation uses **`baseline_status`**, not simple REAL/FAKE accuracy alone.

| Category | Key statuses |
|----------|----------------|
| Clean human | `clean_human_accepted`, `clean_human_false_alarm`, `clean_human_borderline` |
| Direct AI | `direct_ai_detected`, `direct_ai_missed`, `direct_ai_file_level_missed_but_segment_suspicious` |
| Human replay | `human_replay_manipulation_detected`, `human_replay_missed` |
| AI replay | `ai_replay_detected`, `ai_replay_missed`, `ai_replay_file_level_missed_but_segment_suspicious` |
| Human mixer | `human_mixer_manipulation_detected`, `human_mixer_missed` |
| AI mixer | `ai_mixer_detected`, `ai_mixer_missed`, `ai_mixer_file_level_missed_but_segment_suspicious` |
| Partial fabrication | `partial_fabrication_detected`, `partial_fabrication_missed`, `partial_fabrication_not_evaluable` |

**Partial fabrication:** Compare spoof scores **inside** vs **outside** the manifest suspicious region (`suspicious_start_time` / `suspicious_end_time`). File-level REAL/FAKE is secondary.

**Segment-suspicious miss:** File predicted REAL but `max_chunk_spoof >= 0.95` or `suspicious_chunk_ratio >= 0.30`.

**Manipulation detected (replay/mixer):** `prediction == FAKE` OR `decision_score >= 0.65`.

---

## Review files after run

1. `results/PHASE7C1_BASELINE_ANALYSIS.md`
2. `results/phase7c1_baseline_results.csv` (under `reports/phase7/phase7c1_baseline/`)
3. `results/phase7c1_baseline_category_summary.csv`
4. `results/phase7c1_baseline_error_cases.csv`
5. `results/phase7c1_partial_fabrication_analysis.csv`

---

## Scope limits

- Reuses `code/phase6/explain_prediction.py` — **no** Phase 6 logic changes.
- **No** Phase 7C fine-tuning in this phase.
- Phase 7A controlled holdout (T1–T5) is **not** part of this 184-file set.
