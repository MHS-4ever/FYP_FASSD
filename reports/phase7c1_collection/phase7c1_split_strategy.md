# Phase 7C1 — Split Strategy (Round-1)

---

## 1. Unit of split

- Split at **`split_group_id`** (one group = all 8 variants for a `base_id`).
- Example: `split_group_id=base_001` covers all of:
  - `human_001_clean`, `human_001_replay_laptop_mobile`, …
  - `ai_001_direct`, …, `ai_001_fabricated`

**Never** put paired variants in different splits.

---

## 2. Proposed ratios (7C1 corpus only)

| Split | Share |
|-------|------:|
| train | 70% |
| val | 15% |
| test | 15% |

Assign whole `split_group_id` blocks (e.g. 11 train / 2 val / 2 test for 15 bases — adjust as speakers grow).

---

## 3. Speaker-level constraint

- Prefer **no `speaker_id` appearing in more than one split** when possible.
- If one speaker has multiple `base_id` sessions, keep all their `split_group_id` values in the **same** split.

---

## 4. Phase 7A holdout (separate)

| Set | Rule |
|-----|------|
| Phase 7A T1–T5 (25 files) | **`controlled_holdout`** — never in 7C1 train/val/test |
| Phase 7C1 Round-1 (~120 files) | Used for first 7C domain-adaptation experiment |

Do not merge holdout paths into `phase7c1_collection_manifest.csv`.

---

## 5. Chunk-level warning

If features are extracted as **multiple chunks per file** later, split at **file/speaker/group** first — not random chunks (see 7C0 file-level balance audit).

---

## 6. Example manifest fields

```text
base_id=001
split_group_id=base_001
split=train
```

All 8 rows for `base_001` share the same `split` value.
