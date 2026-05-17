# Forensic Dataset Validation Report — Phase 7B

**Input rows:** 25  
**Critical errors:** 0  
**Warnings:** 0  

---

## 1. Summary counts

| Metric | Count |
|--------|------:|
| Total files | 25 |
| Approved | 23 |
| Needs review | 2 |
| Rejected | 0 |
| dataset_role=controlled_holdout | 25 |
| use_for_training=true | 0 |

## 2. Count by origin_label

- `human_likely`: 13
- `ai_likely`: 10
- `mixed_or_partial_ai`: 2

## 3. Count by manipulation_label

- `clean_original`: 8
- `replayed_or_re_recorded`: 7
- `edited_or_spliced`: 7
- `channel_processed`: 2
- `platform_compressed`: 1

## 4. Count by attack_hint

- `replay`: 7
- `unknown`: 6
- `voice_conversion`: 5
- `synthesis`: 4
- `bonafide`: 3

## 5. Count by risk_level

- `high`: 11
- `medium`: 11
- `inconclusive`: 2
- `low`: 1

## 6. Count by language

- `english`: 13
- `urdu`: 12

## 7. Count by platform

- `none`: 24
- `whatsapp`: 1

## 8. Partial fabrication timestamps

- partial_ai_insert rows: 2
- Missing suspicious timestamps: 0

## 9. Training readiness verdict

**Phase 7A/T1–T5 is `controlled_holdout` — NOT used for training.**

- All rows must have `use_for_training=false` (current: **0** with true — must be **0**).
- `forensic_training_manifest_preview.csv` is a **future CSV format preview** only.
- Approved rows may use `use_for_validation=true` and `use_for_testing=true`.

Phase 7C fine-tuning requires a **larger collected dataset** (see gap analysis).

---

## 10. Errors

- None

## 11. Warnings

- None
