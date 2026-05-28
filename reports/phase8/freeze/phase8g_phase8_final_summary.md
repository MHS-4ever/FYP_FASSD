# Phase 8 Final Summary (Phase 8G)

## What Phase 8 Did
Phase 8 built a multi-axis forensic evidence engine for audio analysis.
It focuses on evidence indicators instead of a single fake/real score.

## Why No Binary Fake/Real
- replay indicators can happen for human or AI-origin audio
- mixer/channel processing can happen for human or AI-origin audio
- partial fabrication can be local inside a file
- one score would hide important forensic context

## Phase-by-Phase Achievements
- Phase 8B: evidence table builder complete
- Phase 8C / 8C-A1: acoustic features and audit complete
- Phase 8D / 8D-A1: frozen SSL embeddings and audit complete
- Phase 8E-0: dataset assembly and leakage audit complete
- Phase 8E-1 / 8E-1A: file-level evidence models + threshold review complete
- Phase 8E-2 / 8E-3: timestamp-based partial localization + segment model complete
- Phase 8F: multi-axis fusion layer complete and accepted

## Evidence Axes
- origin evidence
- replay/rerecording evidence
- mixer/channel evidence
- partial fabrication segment evidence

## What Fusion Does
Fusion combines available axis evidence, assigns an experimental status, and triggers manual review when needed.
Missing retrospective axes are treated as `not_evaluated`, not suspicious.

## What Phase 8 Does Not Claim
- no final court-proof verdict
- no guaranteed perfect detection
- no single fake/real final score

## Why Phase 9 Is Separate
Phase 8 is the research/evidence engine.
Phase 9 is the release/integration phase for local inference, API, and demo packaging.
