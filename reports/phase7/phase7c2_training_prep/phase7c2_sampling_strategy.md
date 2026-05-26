# Phase 7C2 — Sampling Strategy

## Old dataset (balanced subset)

- **Source manifests:** `data/manifests/train_speaker_independent.csv`, `val_speaker_independent.csv`, `test_speaker_independent.csv`
- **Method:** Streaming reservoir sampling per attack group (`bonafide`, `synthesis`, `conversion`, `replay`)
- **Seed:** `42` (offset per split)
- **No audio copying** — manifest rows only
- **Approved caps:** train **250** per attack (1000 old), val/test **50** each (200 old)

## Phase 7C1

- Use existing **`split`** column (`train` / `val` / `test`)
- Keep **`split_group_id`** = `base_id` grouping intact
- Expected counts: **128 / 24 / 32** train/val/test

## Combined manifests

```
phase7c2_train_manifest.csv = old_balanced_train + phase7c1_train
phase7c2_val_manifest.csv   = old_balanced_val   + phase7c1_val
phase7c2_test_manifest.csv  = old_balanced_test  + phase7c1_test
```

Do **not** use 1000/200/200 per attack for first fine-tune (~97% old rows). Use approved 250/50/50 unless a later experiment explicitly needs more anti-forgetting mass.
