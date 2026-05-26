# Phase 7C2 Dataset Balance Report

Fine-tuning preparation manifests — **no training performed**.

## Totals by split

| split | total_rows | old_rows | phase7c1_rows | avg_sample_weight | partial_fabrication_rows | use_origin_loss_false |
| --- | --- | --- | --- | --- | --- | --- |
| train | 1128 | 1000 | 128 | 1.1172429078014185 | 32 | 250 |
| val | 224 | 200 | 24 | 1.1049107142857142 | 6 | 50 |
| test | 232 | 200 | 32 | 1.165948275862069 | 8 | 50 |


## Rows by data_source

| split | data_source | count |
| --- | --- | --- |
| test | old | 200 |
| test | phase7c1 | 32 |
| train | old | 1000 |
| train | phase7c1 | 128 |
| val | old | 200 |
| val | phase7c1 | 24 |


## Rows by origin_label

| split | origin_label | count |
| --- | --- | --- |
| test | ai_likely | 112 |
| test | human_likely | 62 |
| test | mixed_or_partial_ai | 8 |
| test | uncertain | 50 |
| train | ai_likely | 548 |
| train | human_likely | 298 |
| train | mixed_or_partial_ai | 32 |
| train | uncertain | 250 |
| val | ai_likely | 109 |
| val | human_likely | 59 |
| val | mixed_or_partial_ai | 6 |
| val | uncertain | 50 |


## Rows by manipulation_label

| split | manipulation_label | count |
| --- | --- | --- |
| test | channel_processed | 8 |
| test | clean_original | 158 |
| test | edited_or_spliced | 8 |
| test | replayed_or_re_recorded | 58 |
| train | channel_processed | 32 |
| train | clean_original | 782 |
| train | edited_or_spliced | 32 |
| train | replayed_or_re_recorded | 282 |
| val | channel_processed | 6 |
| val | clean_original | 156 |
| val | edited_or_spliced | 6 |
| val | replayed_or_re_recorded | 56 |


## Rows by attack_hint

| split | attack_hint | count |
| --- | --- | --- |
| test | bonafide | 54 |
| test | replay | 58 |
| test | synthesis | 66 |
| test | unknown | 4 |
| test | voice_conversion | 50 |
| train | bonafide | 266 |
| train | replay | 282 |
| train | synthesis | 314 |
| train | unknown | 16 |
| train | voice_conversion | 250 |
| val | bonafide | 53 |
| val | replay | 56 |
| val | synthesis | 62 |
| val | unknown | 3 |
| val | voice_conversion | 50 |


## Partial fabrication (binary=1)

| split | count |
| --- | --- |
| test | 8 |
| train | 32 |
| val | 6 |


## Average sample_weight by data_source

| split | data_source | mean_weight |
| --- | --- | --- |
| train | old | 0.925 |
| train | phase7c1 | 2.6191 |
| val | old | 0.925 |
| val | phase7c1 | 2.6042 |
| test | old | 0.925 |
| test | phase7c1 | 2.6719 |


## Loss mask counts (train)

- `use_origin_loss` true: 878, false: 250
- `use_manipulation_loss` true: 1128, false: 0
- `use_attack_loss` true: 1128, false: 0
- `use_partial_loss` true: 1128, false: 0

## Phase 7C1 contribution

- Train: **128** / expected ~128
- Val: **24** / expected ~24
- Test: **32** / expected ~32

## Old balanced subset contribution

- Train: **1000** (max ~4000 = 4×1000 per attack group)
- Val: **200** (max ~800)
- Test: **200** (max ~800)

## Readiness verdict

**READY FOR REVIEW** — Manifests combine balanced old subset + weighted Phase 7C1. Run validation, review holdout report, then sign off before Phase 7C3 fine-tuning script work.
