# Example Report — Direct AI (Segment Suspicious)

**Illustrative only.**  
**Typical status:** `direct_ai_file_level_missed_but_segment_suspicious`

---

## Executive Summary

Overall risk is assessed as **high**. File-level pooled scores did not reach the detection threshold under current settings, but **segment-level evidence indicates** possible synthetic or AI-generated speech in one or more regions. Manual review is required.

## Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | high |
| Overall status | segment_level_ai_suspicion |
| Manual review required | **true** |
| Origin hint | ai_suspicious |
| Manipulation hint | synthetic_segment_indicators |

## Evidence Summary

Baseline segment timeline shows concentrated high spoof-like scores. R2 checkpoints may show lower file-level pooled votes. Phase 7C4-v2 applies baseline segment evidence combined with R2 score checks for direct-AI cases.

## Suspicious Segment Analysis

| Start (s) | End (s) | Score | Source | Explanation |
|-----------|---------|-------|--------|-------------|
| 4.0 | 8.0 | 0.91 | baseline | Elevated spoof-like scores consistent with synthetic segment indicators. |
| 16.0 | 20.0 | 0.87 | baseline | Secondary suspicious window; review priority high. |

## Recommended Action

Priority manual review of listed segments. Obtain recording context (generation method, device chain). Do not use as sole proof of AI origin.

## What this example must NOT say

- “AI proven at file level.”  
- “Definitely deepfake.”  
