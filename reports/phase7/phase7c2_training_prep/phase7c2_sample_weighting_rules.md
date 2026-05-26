# Phase 7C2 — Sample Weighting Rules

Column: **`sample_weight`** (float, cap **4.0**, floor **0.1**)  
Column: **`weight_reason`** (audit trail)

## Old subset

| Group | Weight | Notes |
|-------|--------|-------|
| bonafide | 1.0 | |
| synthesis | 1.0 | |
| conversion | 1.0 | |
| replay | 0.7 | Origin loss masked |

## Phase 7C1 base weights

| Variant | Weight |
|---------|--------|
| Clean human (`clean_direct` + human) | 2.5 |
| Direct AI (`clean_direct` + ai) | 2.5 |
| Human replay | 2.5 |
| AI replay | 2.0 |
| Human mixer | 2.5 |
| AI mixer | 2.0 |
| Partial fabrication | 3.0 |

## Baseline bonuses (from 7C1 baseline results)

| baseline_status | Bonus |
|-----------------|-------|
| clean_human_false_alarm | +0.5 |
| direct_ai_file_level_missed_but_segment_suspicious | +0.5 |
| direct_ai_missed | +0.75 |
| partial_fabrication_missed | +0.75 |

Final weight = min(4.0, base + bonuses).
