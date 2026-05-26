# Example Report — AI Replay (Segment Suspicious)

**Illustrative only.**  
**Typical status:** `ai_replay_detected` or `ai_replay_file_level_missed_but_segment_suspicious`

---

## Executive Summary

Overall risk is assessed as **high**. Indicators suggest **AI-related speech content** combined with **replay or re-recording / channel** effects. Manual review is required before any consequential use.

## Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | high |
| Overall status | ai_replay_or_processed_speech_indicators_detected |
| Manual review required | **true** |
| Origin hint | ai_suspicious |
| Manipulation hint | replayed_or_rerecorded |

## Evidence Summary

Fusion uses baseline replay/mixer sensitivity plus R2 scores for AI-origin direct speech variants. Segment timeline may show high spoof windows even when pooled file vote is borderline.

## Suspicious Segment Analysis

| Start (s) | End (s) | Score | Source | Explanation |
|-----------|---------|-------|--------|-------------|
| 6.0 | 10.0 | 0.89 | baseline | Segment-level evidence supports combined AI and replay suspicion. |

## Recommended Action

Priority expert review; document device chain (synthesis → playback → capture). Do not present as guaranteed deepfake.

## What this example must NOT say

- “Guaranteed AI fake.”  
- “Only replay, not AI.” (when origin is ai_suspicious)  
