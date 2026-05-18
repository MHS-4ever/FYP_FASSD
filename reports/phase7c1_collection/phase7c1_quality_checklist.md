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

## Validation script

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --input reports/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --output reports/phase7c1_collection/phase7c1_validation_report.md ^
  --allow_warnings
```

---

## Round-1 scope (do not block on)

- WhatsApp / social compression rows  
- YouTube / long evidence files  
- 300+ total files  
- Future ideal counts (50–100 per category) — track separately in `phase7c1_target_counts.csv`
