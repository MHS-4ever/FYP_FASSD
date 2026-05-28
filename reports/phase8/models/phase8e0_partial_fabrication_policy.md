# Phase 8E-0 Partial Fabrication Policy

## Core Policy
Inherited file-level `partial_fabrication` labels are not true segment labels. They only indicate that a file contains partial fabrication somewhere, not where it occurs.

## Prohibited Action
Do not train a segment classifier directly using inherited partial-fabrication labels as if each segment were truly labeled.
This remains prohibited even when file-level partial labels are confident.

## Required Evidence for Segment-Level Partial Detection
Before supervised segment training, the dataset must include:
- known fabricated timestamp annotations
- inside/outside comparison windows
- splice/transition evidence around suspicious boundaries
- manual-review rules for uncertain transitions

## Phase 8E-0 Output Intent
Current Phase 8E-0 output for partial fabrication is localization preparation only:
- segment context table
- inherited labels clearly marked
- explicit `segment_label_source`
- `eligible_partial_segment_training=false` for inherited labels
- reason field documenting why training is blocked

This policy prevents label-noise leakage and avoids false confidence in weakly supervised segment targets.
Phase 8E-0 remains dataset preparation only and does not start Phase 8E-1 training.
