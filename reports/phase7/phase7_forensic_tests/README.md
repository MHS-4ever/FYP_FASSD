# Phase 7A — Forensic Test Suite (Workspace)

**Status:** Templates ready — **test audio not yet recorded**  
**Spec:** `reports/phase7/PHASE7A_CONTROLLED_TEST_SUITE.md`  
**Scope:** `reports/UPDATED_PROJECT_SCOPE.md` (includes partial-fabrication / Scope 3)

---

## What this folder is for

Controlled forensic test cases for the **baseline** model (`hybrid_resnet_environmental_best.pth`) **before** any fine-tuning.

You will:

1. Copy `forensic_test_manifest_template.csv` → `forensic_test_manifest.csv`
2. Record or collect ~40 P0 audio files (see spec Section 5) — **20–30 s** each, **≥ 8 s** minimum, paired same-script sets ([recording_protocols.md](notes/recording_protocols.md))
3. Fill manifest rows with paths and ground-truth labels
4. Run Phase 6 inference (per file or via future `code/phase7/run_forensic_test_suite.py`)
5. Aggregate into `results/forensic_test_results.csv`
6. Write `results/FORENSIC_TEST_ANALYSIS.md`

---

## Files

| File | Purpose |
|------|---------|
| `forensic_test_manifest_template.csv` | Column headers + **`T5_FAB_001`** partial-fabrication example |
| `PARTIAL_FABRICATION_CHUNK_ANALYSIS.md` | Inside/outside region metrics + `partial_region_detected` rules |
| `forensic_test_manifest.csv` | **You create** — filled manifest |
| `results/json_outputs/` | One Phase 6 JSON per test |
| `results/forensic_test_results.csv` | Merged manifest + scores |
| `results/FORENSIC_TEST_ANALYSIS.md` | Analysis by condition group |
| `results/FORENSIC_TEST_ANALYSIS_TEMPLATE.md` | Empty analysis skeleton |
| `notes/recording_protocols.md` | How each condition was captured |

---

## Suggested audio storage (when you record)

```
testing_audios/
└── forensic_p0/
    ├── human_clean_mobile/
    ├── human_clean_usb/
    ├── ai_direct/
    ├── human_replay_laptop_to_phone/
    ├── ai_replay_laptop_to_phone/
    ├── human_mixer/
    ├── ai_mixer/
    └── whatsapp_compressed/
└── fabricated/
    └── fabricated_001.wav   # T5_FAB_001 — 34 s, AI insert 14–21 s
```

Paths in the manifest should point to actual files under `E:/FYP/testing_audios/...` or similar.

**Partial-fabrication P0:** See `T5_FAB_001` in the manifest template and [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](PARTIAL_FABRICATION_CHUNK_ANALYSIS.md).

---

## Inference command (baseline)

```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py ^
  --ckpt models_saved/hybrid_resnet_environmental_best.pth ^
  --audio_path <AUDIO_PATH> ^
  --output_dir reports/phase7/phase7_forensic_tests/results/json_outputs ^
  --pooling pct_vote ^
  --chunk_threshold 0.65 ^
  --vote_threshold 0.70 ^
  --vad_mode file_percentile ^
  --vad_rms_percentile 40 ^
  --vad_min_speech_ratio 0.40 ^
  --batch_size 32
```

---

## Rules

- **No training** in Phase 7A
- Do not treat `REAL`/`FAKE` as final forensic verdict — see `reports/FORENSIC_PRODUCT_ROADMAP.md`
- Complete analysis before Phase 7C fine-tuning
