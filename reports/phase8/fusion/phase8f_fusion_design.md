# Phase 8F Fusion Design

## Purpose
Phase 8F creates an experimental multi-axis forensic fusion layer that combines:
- origin evidence
- replay evidence
- mixer/channel evidence
- partial fabrication segment evidence
- abstention and manual-review logic

The objective is structured evidence synthesis, not a final verdict.

## Why No Single Fake/Real Score
Phase 8F explicitly avoids collapsing outputs into one fake/real number or absolute label.  
Each evidence axis stays separate because replay and mixer/channel indicators can occur on both human and AI-origin recordings.

## Input Sources
- Phase 8E-1 OOF file predictions and task metrics
- Phase 8E-1A threshold recommendations
- Phase 8E-3 OOF segment predictions and file localization summary
- Phase 8E-2 top candidate segment table
- Phase 8E-0 file/segment master metadata for identity/context joins

## Selected Evidence Models
- origin: `origin_file_model` with `ssl` feature set
- replay: `replay_file_model` with `acoustic` feature set
- mixer/channel: `mixer_file_model` with `acoustic` feature set
- partial fabrication: `partial_fabrication_segment_model` with `combined` feature set

## Fusion Record Structure
Phase 8F writes:
- file-level fusion records (`phase8f_file_fusion_records.csv`)
- segment-level partial evidence records (`phase8f_segment_fusion_records.csv`)
- manual-review queue (`phase8f_manual_review_queue.csv`)
- safe report outputs (`.jsonl` and `.md`)
- fusion summary and fusion report

## Missing Evidence Handling
Missing axis outputs are represented as:
- `*_model_available=false`
- `*_feature_set=not_evaluated`
- evidence strength `not_evaluated`

Missing axes are never converted to zero-risk or zero-probability assumptions.
In retrospective OOF fusion, missing axes are expected because each model is evaluated on task-specific datasets rather than all files.

## Manual Review Behavior
Manual review is required when:
- evidence is borderline
- multiple axes conflict or co-fire
- partial fabrication evidence is moderate/high
- status is inconclusive

Manual review is not automatically required for every missing axis in retrospective OOF records.

## Partial Segment Summarization
Partial evidence is segment/timestamp based and summarized as:
- max segment probability per file
- top segment ranges
- candidate counts and predicted candidate counts
- segment-level candidate records for review context

## Limitations
- outputs are experimental model outputs
- thresholds are candidate thresholds for review use
- fusion status is a forensic evidence indicator, not final proof
- domain shift and annotation noise can affect reliability
- retrospective OOF fusion can contain `not_evaluated` axes due to dataset coverage
- future live inference (Phase 9) is expected to evaluate all deployed axes per uploaded audio
