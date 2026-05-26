# Phase 7C1 — Labeling Guide (8 variants)

Reuse [Phase 7B label schema](../phase7/PHASE7_LABEL_SCHEMA.md). Round-1 uses **fixed labels per variant**.

---

## 1. human_001_clean.wav

| Field | Value |
|-------|--------|
| source_origin | human |
| manipulation_type | clean_direct |
| ground_truth_origin | human |
| ground_truth_manipulation | clean |
| origin_label | human_likely |
| manipulation_label | clean_original |
| attack_hint | bonafide |
| risk_level | low |
| partial_fabrication_binary | 0 |

---

## 2. human_001_replay_laptop_mobile.wav

| Field | Value |
|-------|--------|
| manipulation_type | human_replay |
| ground_truth_manipulation | replayed |
| origin_label | human_likely |
| manipulation_label | replayed_or_re_recorded |
| attack_hint | replay |
| risk_level | medium |
| partial_fabrication_binary | 0 |

---

## 3. human_001_mixer_processed.wav

| Field | Value |
|-------|--------|
| manipulation_type | mixer_processed |
| device_chain | **laptop_mixer_mobile_recording** |
| recording_condition | mixer_changed_during_playback_and_mobile_recording |
| ground_truth_manipulation | processed |
| origin_label | human_likely |
| manipulation_label | channel_processed |
| attack_hint | **unknown** |
| risk_level | medium |
| partial_fabrication_binary | 0 |
| notes | Human played from laptop; mixer/EQ changed during playback; recorded on mobile |

**Critical:** Human mixer/EQ must **NOT** use `attack_hint=voice_conversion`.

---

## 4. human_001_fabricated.wav

| Field | Value |
|-------|--------|
| source_origin | mixed |
| manipulation_type | partial_ai_insert |
| ground_truth_origin | mixed |
| ground_truth_manipulation | mixed |
| origin_label | mixed_or_partial_ai |
| manipulation_label | edited_or_spliced |
| attack_hint | synthesis |
| risk_level | high |
| partial_fabrication_binary | **1** |
| suspicious_start_time | **REQUIRED** |
| suspicious_end_time | **REQUIRED** |

Mostly **human** audio with **AI-generated segment** inserted/replaced.

---

## 5. ai_001_direct.wav

| Field | Value |
|-------|--------|
| source_origin | ai |
| manipulation_type | clean_direct |
| ground_truth_origin | ai |
| ground_truth_manipulation | clean |
| origin_label | ai_likely |
| manipulation_label | clean_original |
| attack_hint | synthesis |
| risk_level | high |
| partial_fabrication_binary | 0 |

---

## 6. ai_001_replay_laptop_mobile.wav

| Field | Value |
|-------|--------|
| manipulation_type | ai_replay |
| ground_truth_manipulation | replayed |
| origin_label | ai_likely |
| manipulation_label | replayed_or_re_recorded |
| attack_hint | replay |
| risk_level | high |
| partial_fabrication_binary | 0 |

---

## 7. ai_001_mixer_processed.wav

| Field | Value |
|-------|--------|
| manipulation_type | mixer_processed |
| device_chain | **laptop_mixer_mobile_recording** |
| recording_condition | mixer_changed_during_playback_and_mobile_recording |
| ground_truth_manipulation | processed |
| origin_label | ai_likely |
| manipulation_label | channel_processed |
| attack_hint | synthesis |
| risk_level | high |
| partial_fabrication_binary | 0 |
| notes | AI played from laptop; mixer/EQ changed during playback; recorded on mobile |

---

## 8. ai_001_fabricated.wav

| Field | Value |
|-------|--------|
| source_origin | mixed |
| manipulation_type | partial_ai_insert |
| origin_label | mixed_or_partial_ai |
| manipulation_label | edited_or_spliced |
| attack_hint | synthesis |
| risk_level | high |
| partial_fabrication_binary | **1** |
| suspicious_start_time | **REQUIRED** |
| suspicious_end_time | **REQUIRED** |

If mostly **AI with human insert**, keep `partial_ai_insert` / `mixed_or_partial_ai` for now and add to `notes`:

```text
mostly_ai_with_human_insert
```

A separate `partial_human_insert` class may be added later.

---

## Validation

```text
python code/phase7/build_phase7c1_manifest_from_audio.py ^
  --audio_dir data/phase7c1/raw ^
  --output_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --timestamp_template reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv

python code/phase7/validate_phase7c1_collection_manifest.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --output_dir reports/phase7/phase7c1_collection/validation ^
  --allow_missing_audio --allow_warnings
```
