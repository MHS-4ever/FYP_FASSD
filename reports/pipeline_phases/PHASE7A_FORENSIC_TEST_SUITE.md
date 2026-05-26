# Phase 7A — Controlled Forensic Test Suite

> **Note:** Phase 7 planning has been reorganized. The canonical Phase 7 documentation now lives in `reports/phase7/`. This file is retained for reference/backward compatibility. Canonical 7A spec: [phase7/PHASE7A_CONTROLLED_TEST_SUITE.md](../phase7/PHASE7A_CONTROLLED_TEST_SUITE.md).

**Status:** 🟡 **NEXT** (documentation + templates ready; audio files not yet recorded)  
**Priority:** 🔴 CRITICAL (before any fine-tuning)  
**Dependencies:** Phase 6 complete, baseline checkpoint available  
**Training:** **None** in this phase

---

## 1. Objective

Run the **existing Phase 6 inference pipeline** (`code/phase6/explain_prediction.py`) on a **controlled forensic test suite** to measure where the **current baseline model** fails and succeeds.

Conditions to cover:

| Condition | What we learn |
|-----------|----------------|
| Clean human (mobile / USB) | False positive rate on normal recordings |
| Direct AI | True positive on obvious synthetics |
| Human replay (speaker → phone) | Origin vs manipulation confusion |
| AI replay (speaker → phone) | AI + channel artifact interaction |
| Mixer / EQ processed | Channel_processed vs fake confusion |
| WhatsApp / social compression | Platform_compressed score drift |
| YouTube / broadcast | Long-form + broadcast processing |
| Edited / spliced | Segment inconsistency (baseline probe) |
| Partial AI insertion | Mixed-origin behavior (future) |
| Urdu / Pakistani local audio | Language/domain gap |

**Deliverable:** Evidence-backed failure patterns **before** any Phase 7C fine-tuning.

---

## 2. Why We Are Not Training Yet

1. **Failure types must be measured**, not assumed (e.g. Urdu FPs, human-replay REAL calls).
2. **Fine-tuning without controlled tests** can improve one domain while breaking ASVspoof/studio performance (catastrophic forgetting).
3. **Threshold and pooling** choices need per-condition stats, not anecdotal Trump-only tuning.
4. **New labels** (origin vs manipulation) require a test harness before new training targets exist.

Phase 7A produces **forensic_test_results.csv** and **FORENSIC_TEST_ANALYSIS.md** as the gate for Phase 7B–7C.

---

## 3. Folder Structure

Create and use this layout (templates provided; audio files added by you later):

```
reports/phase7/phase7_forensic_tests/
├── README.md                              # How to fill manifest and run tests
├── forensic_test_manifest_template.csv      # Column template + allowed values
├── forensic_test_manifest.csv             # Your filled manifest (create when ready)
├── results/
│   ├── forensic_test_results.csv          # Aggregated results (after runs)
│   ├── FORENSIC_TEST_ANALYSIS.md          # Human analysis by condition group
│   └── json_outputs/                      # Per-file Phase 6 JSON (one per test_id)
└── notes/
    └── recording_protocols.md               # Optional: how each condition was captured

code/phase7/                               # Planned automation (not implemented yet)
├── README.md                              # Points to Phase 7A doc; script stubs described
├── run_forensic_test_suite.py             # (planned) batch Phase 6 over manifest
└── analyze_forensic_test_results.py       # (planned) merge JSON → CSV + analysis skeleton
```

**Note:** `code/phase7/*.py` scripts are **planned** only. Until implemented, run Phase 6 **per file** or via a manual batch loop you control.

---

## 4. Manifest Columns

File: `forensic_test_manifest.csv` (copy from `forensic_test_manifest_template.csv`).

| Column | Required | Description |
|--------|----------|-------------|
| `test_id` | Yes | Unique ID, e.g. `P0_HUMAN_MOBILE_01` |
| `priority` | Yes | `P0`, `P1`, or `P2` |
| `audio_path` | Yes | Path to wav/mp3 (relative to repo or absolute) |
| `source_origin` | Yes | Intended **content** origin (see allowed values) |
| `manipulation_type` | Yes | How audio was produced (see allowed values) |
| `language` | Yes | `english`, `urdu`, etc. |
| `speaker_type` | Yes | `known_public`, `local_speaker`, `self_recorded`, `unknown` |
| `device_chain` | No | Free text, e.g. `iPhone14_direct`, `laptop_USB_mic` |
| `platform` | Yes | `none`, `whatsapp`, `youtube`, etc. |
| `ground_truth_origin` | Yes | Labeler truth for origin |
| `ground_truth_manipulation` | Yes | Labeler truth for manipulation |
| `expected_forensic_result` | No | Short expected narrative for reviewer |
| `notes` | No | Recording date, mic model, `pair_id`, etc. |

### Forensic label columns (planning / expected outputs)

Use for test design and results merge (populated after inference + rule mapping in 7D):

| Column | Description |
|--------|-------------|
| `origin_label` | Expected or derived: human_likely, ai_likely, mixed_or_partial_ai, uncertain |
| `manipulation_label` | Expected or derived: clean_original, replayed_or_re_recorded, channel_processed, etc. |
| `attack_hint` | bonafide, synthesis, voice_conversion, replay, unknown |
| `risk_level` | low, medium, high, inconclusive |
| `partial_fabrication_detected` | true / false (ground truth for Scope 3 tests) |
| `suspicious_start_time` | Ground truth or detected start (seconds) |
| `suspicious_end_time` | Ground truth or detected end (seconds) |
| `expected_report_wording` | Short template case ID (A–K from Phase 7D) |
| `expected_forensic_interpretation` | One-line expected narrative for reviewer |

### Allowed values

**`priority`:** `P0` | `P1` | `P2`

**`source_origin`:** `human` | `ai` | `mixed` | `unknown`

**`manipulation_type`:**

`clean_direct` | `human_replay` | `ai_replay` | `mixer_processed` | `whatsapp_compressed` | `youtube_broadcast` | `phone_recorded` | `edited_spliced` | `partial_ai_insert` | `noisy_room` | `unknown`

**`language`:** `english` | `urdu` | `punjabi` | `hindi` | `mixed` | `unknown`

**`speaker_type`:** `known_public` | `local_speaker` | `self_recorded` | `unknown`

**`platform`:** `none` | `whatsapp` | `youtube` | `facebook` | `tiktok` | `screen_recording` | `unknown`

**`ground_truth_origin`:** `human` | `ai` | `mixed` | `unknown`

**`ground_truth_manipulation`:** `clean` | `replayed` | `processed` | `compressed` | `edited` | `mixed` | `unknown`

---

## 5. Required First Batch (P0)

Minimum **~40 P0 files** before Phase 7A is considered complete:

| # | Condition | Count | `manipulation_type` (typical) |
|---|-----------|------:|-------------------------------|
| 1 | Clean human, mobile mic | 5 | `clean_direct` / `phone_recorded` |
| 2 | Clean human, laptop/USB mic | 5 | `clean_direct` |
| 3 | Direct AI (TTS/clone, no replay) | 5 | `clean_direct` |
| 4 | Human voice → laptop speaker → mobile record | 5 | `human_replay` |
| 5 | AI voice → laptop speaker → mobile record | 5 | `ai_replay` |
| 6 | Human → mixer/EQ → record | 5 | `mixer_processed` |
| 7 | AI → mixer/EQ → record | 5 | `mixer_processed` |
| 8 | WhatsApp-forwarded human and/or AI | 5 | `whatsapp_compressed` |

**Total: 40 files** (expand with P1: YouTube, edited, Urdu, partial AI, etc.)

Store audio under a dedicated tree, e.g. `testing_audios/forensic_p0/` (create when recording).

### 5.1 Recording duration and pairing (required)

Full detail: `reports/phase7/phase7_forensic_tests/notes/recording_protocols.md`

| Rule | Value |
|------|--------|
| **Default P0 length** | **20–30 seconds** of speech per file |
| **Minimum** | **≥ 8 seconds** — do not submit shorter clips to 7A |
| **Edited / partial AI** (P1+) | **30–45 seconds** |
| **Long-evidence tests** | **60–120 seconds** — later batches only, not default P0 |
| **Silence** | **~0.5–1 s** at start and end |
| **Paired samples** | Same script/content across clean, direct AI, replay, mixer, WhatsApp, and AI variants where possible; use `pair_id` in manifest `notes` |

### 5.2 Partial fabrication tests (required in 7A plan)

These cases test **Scope 3**: mostly real audio with a short inserted suspicious segment. Record when ready; document in manifest with `manipulation_type=partial_ai_insert` and `partial_fabrication_detected=true` in ground-truth columns.

| Test case | Description | Suggested duration |
|-----------|-------------|-------------------|
| PF1 | **120 s** real audio + **~10 s** AI/cloned insert | ~120–130 s total |
| PF2 | **60 s** real audio + **~5 s** AI insert | ~60–65 s total |
| PF3 | Real audio + **one cloned/converted sentence** inserted | 30–45 s or per script |
| PF4 | Real audio + **human sentence** inserted from **different room** (splice, not AI) | 30–45 s |
| PF5 | **WhatsApp-compressed** real audio with **inserted AI segment** | After compression pipeline |

**7A research question:** When whole-file `prediction` is **REAL**, do high spoof-probability **chunks** appear only in the inserted region? If not, document gap for 7C/7D.

Priority: include at least **PF1–PF2** in first partial-fabrication batch (P1 if P0 is already full).

### 5.3 Canonical example: `T5_FAB_001` (34 s, fake insert 14–21 s)

**Reference file:** `testing_audios/fabricated/fabricated_001.wav`  
**Full chunk-analysis spec:** [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7/phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md)

| Property | Value |
|----------|--------|
| Duration | 34 s total |
| Suspicious region (ground truth) | **14.0 – 21.0 s** (AI insert) |
| `partial_fabrication_detected` (GT) | `true` |
| Expected whole-file | Often **REAL** — **do not use as sole pass/fail** |

**Chunk rules:**

- Mark chunk **inside** if its `[start, end]` **overlaps** 14.0–21.0 s.  
- Compare **inside** vs **outside** spoof scores and attack hints.  
- Compute `partial_region_detected` = true if any of:
  - `inside_region_avg_spoof >= outside_region_avg_spoof + 0.15`, OR  
  - `inside_region_max_spoof >= 0.65`, OR  
  - inside dominant attack is synthesis/conversion while outside is mostly bonafide.

**Manifest row (copy-ready):**

```csv
test_id,priority,audio_path,source_origin,manipulation_type,language,speaker_type,device_chain,platform,ground_truth_origin,ground_truth_manipulation,partial_fabrication_detected,suspicious_start_time,suspicious_end_time,expected_forensic_result,notes
T5_FAB_001,P0,E:/FYP/testing_audios/fabricated/fabricated_001.wav,mixed,partial_ai_insert,urdu,known_public,edited_real_plus_ai,none,mixed,mixed,true,14.0,21.0,Mostly real audio with inserted AI-generated segment from 14s to 21s,Total duration 34 seconds. Fake inserted region is 14s to 21s.
```

---

## 6. Current Inference Command

Use **unchanged** Phase 6 settings (baseline). Per file:

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

Optional: `--debug_chunk_stats` for borderline cases.

When `run_forensic_test_suite.py` exists, it will loop over `forensic_test_manifest.csv` with this configuration.

---

## 7. Result CSV Columns

Aggregated file: `reports/phase7/phase7_forensic_tests/results/forensic_test_results.csv`

| Column | Source |
|--------|--------|
| `test_id` | manifest |
| `filename` | from JSON |
| `audio_path` | manifest |
| `priority` | manifest |
| `source_origin` | manifest |
| `manipulation_type` | manifest |
| `language` | manifest |
| `ground_truth_origin` | manifest |
| `ground_truth_manipulation` | manifest |
| `prediction` | Phase 6 (`REAL` / `FAKE`) |
| `confidence` | Phase 6 |
| `decision_score` | Phase 6 |
| `effective_threshold` | Phase 6 |
| `attack_type` | Phase 6 multiclass name |
| `attack_type_conf` | Phase 6 |
| `bonafide_prob` | `attack_probs[0]` |
| `synthesis_prob` | `attack_probs[1]` |
| `conversion_prob` | `attack_probs[2]` |
| `replay_prob` | `attack_probs[3]` |
| `n_chunks_used` | Phase 6 |
| `n_chunks_total` | Phase 6 |
| `origin_interpretation` | **Rule-based** (Phase 7A analysis script / manual) |
| `manipulation_interpretation` | **Rule-based** |
| `forensic_summary` | **Rule-based** one-line |
| `correct_origin_basic` | `yes` / `no` / `borderline` vs ground_truth_origin |
| `failure_type` | e.g. `fp_processed_human`, `fn_direct_ai`, `borderline`, `missed_partial_insert` |
| `notes` | reviewer |
| `origin_label` | Derived (7D rules) or expected from manifest |
| `manipulation_label` | Derived or expected |
| `attack_hint` | Derived from `attack_type` / probs |
| `risk_level` | Derived |
| `partial_fabrication_detected` | true/false — **detected** vs ground truth |
| `suspicious_start_time` | Detected segment start (s) |
| `suspicious_end_time` | Detected segment end (s) |
| `expected_report_wording` | Case A–K id (manifest) |
| `expected_forensic_interpretation` | Manifest expected narrative |
| `max_chunk_spoof_prob` | Optional: highest chunk spoof prob |
| `n_suspicious_chunks` | Optional: count of chunks ≥ chunk_threshold |
| `whole_file_prediction` | Phase 6 `prediction` (context only for partial-fab cases) |
| `whole_file_decision_score` | Phase 6 `decision_score` |
| `n_chunks_inside` | Chunks overlapping `suspicious_start_time`–`suspicious_end_time` |
| `n_chunks_outside` | Remaining used chunks |
| `inside_region_avg_spoof` | Mean spoof prob inside region |
| `outside_region_avg_spoof` | Mean spoof prob outside region |
| `inside_region_max_spoof` | Max spoof prob inside region |
| `outside_region_max_spoof` | Max spoof prob outside region |
| `inside_region_dominant_attack` | Mode attack class inside region |
| `outside_region_dominant_attack` | Mode attack class outside region |
| `partial_region_detected` | Computed — see [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7/phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md) |
| `correct_partial_region_detected` | `yes` / `no` vs ground-truth `partial_fabrication_detected` |

Rule mapping for layered labels: `reports/FORENSIC_PRODUCT_ROADMAP.md` and `pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md`.

---

## 8. Analysis Markdown

File: `reports/phase7/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md`

Group results by **manipulation_type** (and language where relevant):

- clean human (direct)
- direct AI
- human replay
- AI replay
- mixer processed
- WhatsApp / compressed
- YouTube / broadcast
- Urdu / Pakistani
- edited / spliced
- partial AI insertion

**Per group, include:**

| Metric | Description |
|--------|-------------|
| Total files | Count in group |
| Correct origin (basic) | `correct_origin_basic == yes` |
| Wrong origin | `no` |
| Borderline | `borderline` |
| Average `decision_score` | Mean spoof vote ratio |
| Common failure pattern | Narrative |
| Recommended next action | e.g. collect more P0, adjust rules, fine-tune in 7C |

Use template: `reports/phase7/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS_TEMPLATE.md` until data exists.

---

## 9. Success Criteria

Phase 7A is **complete** when:

- [ ] `forensic_test_manifest.csv` has **≥ 40 P0** rows with valid `audio_path`
- [ ] Every manifest row has a JSON in `results/json_outputs/`
- [ ] `forensic_test_results.csv` exists and merges manifest + JSON
- [ ] `FORENSIC_TEST_ANALYSIS.md` is filled with per-group tables and failure patterns
- [ ] Team has agreed on **top 3 failure modes** before Phase 7C training
- [ ] **Partial-fabrication cases** run and documented (whole-file vs chunk-level behavior)
- [ ] For each partial-fabrication file: recorded whether **suspicious chunks align** with inserted region when whole-file is REAL
- [ ] Phase 7A answers: **Can current chunking/report logic detect suspicious segments without whole-file FAKE?** (yes/no/partial — with evidence)

---

## 10. Do Not Do Yet

- ❌ Fine-tune or retrain the hybrid model  
- ❌ Permanently change production thresholds without 7A evidence  
- ❌ Replace the model with transformers / AASIST  
- ❌ Modify Phase 6 core inference **except** documented bugfixes  
- ❌ Claim forensic proof from binary `prediction` alone  

---

## Related

- `reports/FORENSIC_PRODUCT_ROADMAP.md`
- `reports/FORENSIC_REPORT_OUTPUT_SPEC.md`
- `reports/AUDIO_TESTING_OUTPUT_GUIDE.md` — interpreting processed human audio
- `reports/phase7/phase7_forensic_tests/README.md`
