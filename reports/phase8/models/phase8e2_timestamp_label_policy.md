# Phase 8E-2 Timestamp Label Policy

## What Counts as a True Timestamp Label
Reliable labels for supervised segment training should include at least one of:
- per-segment ground-truth fabricated/non-fabricated labels
- explicit suspicious/fabricated start/end timestamps with clear source metadata
- splice boundary timestamps with validated annotation source
- external timestamp annotations aligned to file/segment windows with sufficient overlap

## What Does Not Count
- inherited file-level partial-fabrication labels alone
- empty placeholder columns without usable values
- ambiguous or incomplete timestamp fragments

## When Supervised Partial Segment Training Is Allowed
Allowed only when:
- true timestamp/per-segment labels are available and consistent
- positive/negative segment counts are sufficient
- leakage-aware grouping is feasible

## When It Is Blocked
Blocked when:
- only inherited file-level labels exist
- timestamp labels are incomplete or unreliable
- segment class counts are insufficient

## How to Collect Better Labels Later
- annotate suspicious/fabricated intervals with clear reviewer protocol
- include outside/clean neighboring intervals
- store annotation source and confidence
- version timestamp labels for auditability
- maintain stable file path/id references (e.g., `output_file`) for reliable matching

## Safe Wording Policy
Use:
- candidate segment
- localized anomaly indicator
- manual review candidate
- timestamp-aligned preparation label (not final forensic proof)
- inside/outside baseline comparison indicator

Avoid:
- confirmed fabricated segment (unless verified ground truth exists)
- final forensic decision language
