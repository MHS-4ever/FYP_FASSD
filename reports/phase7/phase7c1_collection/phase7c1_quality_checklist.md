# Phase 7C1 — Quality Checklist (Round-1)

Use before marking `quality_status=approved` and before Phase 7C fine-tuning.

---

## Recording

- [ ] Duration **≥ 8 s** (target **30–60 s**)
- [ ] **0.5–1 s** silence at start/end
- [ ] Correct script read (matches `script_id` / language)
- [ ] Variant matches recording chain (clean vs replay vs mixer vs fabricated)

---

## Manifest

- [ ] All **required columns** filled (see template)
- [ ] **8 variants** per `base_id` (or document missing with reason)
- [ ] `split_group_id` consistent; **same `split`** for all variants in group
- [ ] No duplicate `audio_path`
- [ ] `speaker_gender` ∈ {male, female, unknown}
- [ ] `language` ∈ {english, urdu, mixed, unknown}

---

## Labels

- [ ] Human mixer: `attack_hint` **not** `voice_conversion`
- [ ] Human replay: `origin_label=human_likely`
- [ ] Fabricated: `partial_fabrication_binary=1` + valid timestamps
- [ ] `suspicious_end_time` > `suspicious_start_time`

---

## Files

- [ ] Audio exists at `audio_path`
- [ ] `duration` / `sample_rate` / `channels` updated after export

---

## Holdout

- [ ] No Phase **7A** T1–T5 files in 7C1 training manifest
- [ ] No `controlled_holdout` rows marked for training

---

## Manifest build (from 184 audio files)

```text
python code/phase7/build_phase7c1_manifest_from_audio.py ^
  --audio_dir data/phase7c1/raw ^
  --output_manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --timestamp_template reports/phase7/phase7c1_collection/phase7c1_fabricated_timestamps_to_fill.csv
```

## Validation script

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --manifest reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --output_dir reports/phase7/phase7c1_collection/validation ^
  --allow_missing_audio --allow_warnings
```

Fabricated rows: fill `phase7c1_fabricated_timestamps_to_fill.csv` before `--strict`.

---

## Round-1 scope (do not block on)

- WhatsApp / social compression rows  
- YouTube / long evidence files  
- 300+ total files  
- Future ideal counts (50–100 per category) — track separately in `phase7c1_target_counts.csv`
