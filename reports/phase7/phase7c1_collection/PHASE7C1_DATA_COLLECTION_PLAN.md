# Phase 7C1 — Data Collection Plan (Round-1 operational)

**Status:** Active — **184 files collected** (manifest build next)  
**Training:** None in this phase  
**Canonical summary:** [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](../phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md)

---

## Round-1 collected dataset (actual)

| Item | Value |
|------|--------|
| Base IDs | **23** (`base_001` … `base_023`) |
| Variants per base | **8** |
| **Total audio files** | **184** (23 × 8) |
| Purpose | First **domain-adaptation / fine-tuning** experiment |

### Eight variants per base_id

1. `human_{NNN}_clean.wav`  
2. `human_{NNN}_replay_laptop_mobile.wav`  
3. `human_{NNN}_mixer_processed.wav` — laptop playback, **mixer/EQ changed during playback**, recorded on mobile  
4. `human_{NNN}_fabricated.wav` — partial AI insert; **timestamps required**  
5. `ai_{NNN}_direct.wav`  
6. `ai_{NNN}_replay_laptop_mobile.wav`  
7. `ai_{NNN}_mixer_processed.wav` — same mixer protocol as human  
8. `ai_{NNN}_fabricated.wav` — partial insert; **timestamps required**  

**Mixer labeling:** `device_chain=laptop_mixer_mobile_recording`, `manipulation_label=channel_processed`, human `attack_hint=unknown` (never `voice_conversion`).

---

## Split plan (fixed by base number)

| Split | Base IDs |
|-------|----------|
| **train** | `base_001` – `base_016` |
| **val** | `base_017` – `base_019` |
| **test** | `base_020` – `base_023` |

All **8 variants** share the same `split_group_id` and `split`.

Phase **7A T1–T5** remain **`controlled_holdout`** — not in this manifest.

---

## Folder layout

```text
data/phase7c1/raw/                    # audio (human_001_clean.wav, …)

reports/phase7/phase7c1_collection/
  phase7c1_collection_manifest.csv
  phase7c1_fabricated_timestamps_to_fill.csv
  phase7c1_collection_status.md
  validation/
    phase7c1_manifest_build_report.md
    phase7c1_validation_report.md
```

---

## Workflow (after audio recorded)

### 1. Build manifest from audio folder

```text
python code/phase7/build_phase7c1_manifest_from_audio.py ^
  --audio_dir data/phase7c1/raw ^
  --output_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --timestamp_template reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv
```

### 2. Fill fabricated timestamps

Edit `phase7c1_fabricated_timestamps_to_fill.csv` (46 rows: human + ai fabricated per base), then merge into manifest.

### 3. Validate

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --target_counts reports/phase7/phase7c1_collection/phase7c1_target_counts.csv ^
  --output_dir reports/phase7/phase7c1_collection/validation ^
  --allow_missing_audio ^
  --allow_warnings
```

Use `--strict` only after all fabricated timestamps are filled.

### 4. Summary

```text
python code/phase7/summarize_phase7c1_collection.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --target_counts reports/phase7/phase7c1_collection/phase7c1_target_counts.csv ^
  --output_md reports/phase7/phase7c1_collection/phase7c1_collection_status.md
```

---

## Target counts

[phase7c1_target_counts.csv](phase7c1_target_counts.csv): **184** Round-1 actual; higher counts are **future ideal** only.

---

## Not in Round-1

- WhatsApp / social mandatory  
- YouTube / TikTok / Facebook mandatory  
- 300+ files before first experiment  

---

## Related code

| Script | Role |
|--------|------|
| [build_phase7c1_manifest_from_audio.py](../../code/phase7/build_phase7c1_manifest_from_audio.py) | Scan audio → manifest + timestamp template |
| [validate_phase7c1_collection_manifest.py](../../code/phase7/validate_phase7c1_collection_manifest.py) | Manifest QA |
| [summarize_phase7c1_collection.py](../../code/phase7/summarize_phase7c1_collection.py) | Status markdown |
