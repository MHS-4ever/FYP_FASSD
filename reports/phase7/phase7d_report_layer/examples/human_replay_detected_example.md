# Example Report — Human Replay Detected

**Illustrative only.**  
**Typical status:** `human_replay_manipulation_detected`

---

## Executive Summary

Overall risk is assessed as **medium** (may be **high** if suspicious chunk ratio is elevated). Speech content appears **consistent with human origin**, while the system detected indicators of **replay or re-recording**. This does not by itself indicate AI-generated speech.

## Final Risk Assessment

| Field | Value |
|-------|-------|
| Overall risk level | medium |
| Overall status | replay_or_rerecording_indicators_detected |
| Manual review required | **true** |
| Origin hint | likely_human |
| Manipulation hint | replayed_or_rerecorded |

## Evidence Summary

Baseline checkpoint sensitivity drives replay detection on Phase 7C1 controlled tests. File-level prediction may remain REAL while manipulation-like chunk patterns and attack hints support replay assessment.

## Recommended Action

Expert listen for double-hop recording artifacts (speaker → phone, room change). Report to stakeholders as **human-origin with manipulation risk**, not as synthetic speech alone.

## What this example must NOT say

- “The speaker is AI.”  
- “Original studio recording confirmed.”  
