# Example Report — Partial Fabrication Detected

**Illustrative only.**  
**Typical status:** `partial_fabrication_detected`

---

## Executive Summary

Overall risk is assessed as **high**. Segment-level evidence suggests possible **partial fabrication or inserted synthetic content** within a recording that may appear human-like overall. Manual review of flagged time ranges is required.

## Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | high |
| Overall status | partial_fabrication_or_splice_indicators_detected |
| Manual review required | **true** |
| Origin hint | mixed_or_uncertain |
| Manipulation hint | edited_or_partially_synthetic |

## Segment-level evidence

| Field | Value |
|-------|-------|
| Labeled suspicious region | 14.0 – 21.0 s |
| Inside-region max spoof | 0.82 |
| Outside-region max spoof | 0.41 |
| Partial region delta | 0.41 |
| Partial region detected | true |

## Suspicious Segment Analysis

| Start (s) | End (s) | Type | Explanation |
|-----------|---------|------|-------------|
| 14.0 | 21.0 | labeled_partial_region | Labeled insertion window; inside-region scores exceed outside baseline. |
| 15.0 | 19.0 | high_spoof_chunk | Peak chunk spoof within labeled region. |

## Recommended Action

Expert review of 14–21 s vs rest of file. Do not conclude entire file is synthetic if pooled vote is REAL. Compare with `phase7c1_partial_fabrication_analysis.csv` metrics when available.

## What this example must NOT say

- “The whole file is fake.”  
- “Partial AI proven.” (use “indicators suggest”)  
