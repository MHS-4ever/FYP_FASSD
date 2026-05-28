# Phase 8E-2 Partial Localization Design

## Why Phase 8E-2 Exists
Replay/mixer axes were trainable at file level, but partial fabrication remains weak at segment level when labels are inherited from file-level annotations. Phase 8E-2 therefore prepares localization evidence without supervised segment training.

## Why Partial Fabrication Is Different
For replay/mixer, file-level labels can align with broad file-level evidence patterns. For partial fabrication, only a subset of segments may be affected, so inherited file-level labels are unsafe as segment truth labels.

## Core Preparation Strategy
Phase 8E-2 computes descriptive candidate indicators:
- timestamp label availability audit
- external timestamp annotation normalization/matching (CSV/JSON/JSONL supported)
- within-file deviation indicators (acoustic + SSL)
- neighbor transition indicators
- candidate ranking within each partial file
- Phase 8E-3 readiness review

No model training, no predictions, and no final forensic decisions are produced.

## Inside/Outside Comparison Idea
If true timestamps exist, inside/outside comparisons can be computed for labeled fabricated vs non-fabricated regions. If not available, fallback is unsupervised within-file deviation only.

Current expected annotation sources include:
- `data/phase7c1/raw/ai_fabricated/insertion_stamps.csv`
- `data/phase7c1/raw/human_fabricated/insertion_stamps.csv`

Known supported columns include `output_file`, `insert_start_sec`, `insert_end_sec`, and `label` (auto-detect or explicit CLI mapping).

## Within-File Deviation Idea
Each segment is compared to its file context using robust distance/deviation features:
- acoustic distance from file median profile
- SSL distance from file median profile
- percentile-based combined deviation score

## Neighbor Transition Idea
Each segment is compared to neighboring segments:
- acoustic and SSL deltas to previous/next segments
- combined transition score
- transition rank within file

## How Candidates Are Used
Outputs represent candidate segments for:
- manual review
- future fusion context (Phase 8F candidate signals)

They are not confirmed fabricated-segment labels.

`phase8e2_suspicious_segment_candidates.csv` is the all-segment ranking table.
`phase8e2_top_suspicious_segment_candidates.csv` is the top-candidates-only table.

## Limitations
- inherited labels do not support safe supervised segment training
- candidate indicators can flag unusual segments that are not necessarily fabricated
- timestamp coverage is the key blocker for Phase 8E-3 supervised progression
- inside/outside baseline features support preparation but do not by themselves prove fabrication
