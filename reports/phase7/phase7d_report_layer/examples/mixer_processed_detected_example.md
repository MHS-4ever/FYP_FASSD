# Example Report — Mixer / Channel Processed

**Illustrative only.**  
**Typical status:** `human_mixer_manipulation_detected` or `ai_mixer_detected`

---

## Executive Summary

Overall risk is assessed as **medium** or **high** depending on evidence strength. The system detected indicators of **channel processing or mixer-like artifacts**. Origin assessment depends on source context: **likely human** vs **ai_suspicious** must be reported separately from channel manipulation.

## Final Risk Assessment (human-origin example)

| Field | Value |
|-------|-------|
| Overall risk level | medium |
| Overall status | channel_processing_or_mixer_artifacts_detected |
| Manual review required | **true** |
| Origin hint | likely_human |
| Manipulation hint | channel_processed |

## Evidence Summary

Baseline model retains mixer detection on Phase 7C1 tests. R2 may modulate clean-human branches but baseline manipulation sensitivity is retained in 7C4-v2 fusion for mixer categories.

## Recommended Action

Listen for EQ/compression/PA artifacts. If `source_origin=ai`, add technical note that AI speech may exhibit additional synthesis indicators beyond channel processing.

## What this example must NOT say

- “Mixer proves AI.”  
- “Clean original recording.”  
