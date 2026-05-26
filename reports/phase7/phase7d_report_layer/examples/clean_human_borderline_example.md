# Example Report — Clean Human Borderline

**Illustrative only** — not generated from live inference.  
**Typical status:** `clean_human_borderline`  
**Phase 7C1 context:** ~15/23 clean-human files fall in this category.

---

## Executive Summary

Overall risk is assessed as **medium**. The recording should not be treated as free of concern without expert review. Conflicting evidence between lower R2 file-level scores and baseline segment-level indicators prevents an automatic low-risk conclusion.

## Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | medium |
| Overall status | inconclusive_manual_review_recommended |
| Manual review required | **true** |
| Origin hint | likely_human_or_uncertain |
| Manipulation hint | uncertain |

## Evidence Summary

R2 `best_product` and `best_loss` outputs suggest lower pooled spoof scores, consistent with cautious clean-human handling. Baseline chunk timeline shows one or more windows with elevated spoof-like scores. Phase 7C4-v2 fusion assigned **borderline** rather than false alarm or acceptance.

## Suspicious Segment Analysis

| Start (s) | End (s) | Score | Source | Explanation |
|-----------|---------|-------|--------|-------------|
| 8.0 | 12.0 | 0.88 | baseline | Segment-level evidence indicates elevated spoof-like scores; manual listen recommended. |

## Recommended Action

Manual listen to flagged segments and full file. Do not label as synthetic or AI-generated without expert review. Document reviewer notes and chain of custody.

## What this example must NOT say

- “This recording is fake.”  
- “100% real / authentic.”  
- “No review needed.”  
