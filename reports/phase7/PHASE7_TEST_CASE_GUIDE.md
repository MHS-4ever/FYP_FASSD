# Phase 7 Test Case Guide

**Phase:** 7A (controlled forensic testing)  
**Manifest:** [../phase7_forensic_tests/forensic_test_manifest_template.csv](../phase7_forensic_tests/forensic_test_manifest_template.csv)  
**Labels:** [PHASE7_LABEL_SCHEMA.md](PHASE7_LABEL_SCHEMA.md)

---

## Recommended audio length

| Use case | Length |
|----------|--------|
| **Default** (T1–T4 P0) | **20–30 seconds** of speech |
| **Minimum** | **≥ 8 seconds** — do not submit shorter clips |
| **Edited / spliced / partial fabrication** | **30–45 seconds** (or specific case length) |
| **Long evidence simulation** | **60–120 seconds** — later batches, not default P0 |
| **Silence** | **~0.5–1 s** at start and end of each clip |

---

## Test groups (first cycle: T1–T5 only)

Only **T1–T5** are required for the **first** 7A cycle. This is enough to measure baseline behavior before fine-tuning.

### T1 — Clean / direct origin tests

| ID pattern | Description |
|------------|-------------|
| Clean human | Mobile mic and/or USB mic, direct recording |
| Direct AI | TTS or voice clone, **no** replay chain |

**Learn:** False positive rate on normal human; true positive on obvious AI.

### T2 — Replay tests

| Chain | Description |
|-------|-------------|
| Human replay | Human voice → laptop speaker → mobile recording |
| AI replay | AI voice → laptop speaker → mobile recording |

**Learn:** Origin vs manipulation confusion (human replay may stay REAL).

### T3 — Mixer / channel processed tests

| Variant | Description |
|---------|-------------|
| Human + mixer | Human through mixer/EQ/PA then record |
| AI + mixer | AI through same chain |

**Learn:** `channel_processed` vs false FAKE on human.

### T4 — Compression / platform / broadcast tests

| Variant | Description |
|---------|-------------|
| WhatsApp | Forward human and/or AI through WhatsApp |
| YouTube / broadcast | If available in first cycle |

**Learn:** Platform compression score drift vs origin.

### T5 — Fabricated / partial insertion tests

| Variant | Description |
|---------|-------------|
| Partial AI insert | Mostly real audio + short AI segment |
| Reference case | `T5_FAB_001` — see below |

**Learn:** Segment-level detection when whole-file is REAL.

---

## Fabricated test case — `T5_FAB_001`

| Property | Value |
|----------|--------|
| **test_id** | `T5_FAB_001` |
| **Total duration** | **34 seconds** |
| **Fake region** | **14.0 s – 21.0 s** (~7 s, ~**20.6%** of file) |
| **Rest** | Real (human) audio |
| **Path (example)** | `testing_audios/fabricated/fabricated_001.wav` |
| **manipulation_type** | `partial_ai_insert` |
| **partial_fabrication_detected** | `true` (ground truth) |

### Evaluation rules

1. **Do not** judge pass/fail on whole-file REAL/FAKE alone.  
2. Compare chunk spoof scores **inside 14–21 s** vs **outside**.  
3. Record `partial_region_detected` per [PARTIAL_FABRICATION_CHUNK_ANALYSIS.md](../phase7_forensic_tests/PARTIAL_FABRICATION_CHUNK_ANALYSIS.md).  
4. Document chunk timeline in results CSV and analysis report.  

### Extended partial cases (later P1)

PF1–PF5 in legacy 7A spec: 120 s + 10 s insert, 60 s + 5 s, cloned sentence, human splice, WhatsApp + insert — add after core T5 passes.

---

## Paired sample recommendation

Use the **same script or content** across a set where possible:

| Pair member | Condition |
|-------------|-----------|
| `human_001_clean` | Clean human direct |
| `human_001_laptop_replay_mobile` | Human replay |
| `human_001_mixer_processed` | Human + mixer |
| `human_001_whatsapp` | Human compressed |
| `ai_001_direct` | AI direct |
| `ai_001_laptop_replay_mobile` | AI replay |
| `ai_001_mixer_processed` | AI + mixer |
| `ai_001_whatsapp` | AI compressed |

Record `pair_id` in manifest `notes` (e.g. `pair_id=human_001`).

---

## Naming recommendation

```
human_001_clean.wav
human_001_laptop_replay_mobile.wav
human_001_mixer_processed.wav
human_001_whatsapp.wav
ai_001_direct.wav
ai_001_laptop_replay_mobile.wav
ai_001_mixer_processed.wav
fabricated_001_real_with_ai_14s_21s.wav
```

**test_id** in manifest should stay unique (e.g. `T1_HUMAN_001`, `T5_FAB_001`).

---

## Storage layout

```
testing_audios/
├── forensic_p0/
│   ├── human_clean_mobile/
│   ├── human_clean_usb/
│   ├── ai_direct/
│   ├── human_replay_laptop_to_phone/
│   ├── ai_replay_laptop_to_phone/
│   ├── human_mixer/
│   ├── ai_mixer/
│   └── whatsapp_compressed/
└── fabricated/
    └── fabricated_001.wav
```

---

## Minimum P0 batch (legacy count)

~40 files across clean human, AI, replay, mixer, WhatsApp — see [PHASE7A_CONTROLLED_TEST_SUITE.md](PHASE7A_CONTROLLED_TEST_SUITE.md). T5 partial-fabrication is **in addition** to core P0 where possible.
