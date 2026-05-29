# Phase 9D-P4 Partial Timestamp Diagnostic Design

## Purpose

Phase 9D-P4 diagnoses **partial fabrication localization** by comparing **live** segment-level partial probabilities against **evaluation-only** true fabricated timestamps from Phase 7C1.

This answers:

1. Do highest-probability segments fall inside the true fabricated region?
2. Is the model high everywhere (broad activation) or peaked near the region?
3. Does `ai_fabricated` differ from `human_fabricated`?
4. Are splice/boundary regions more detectable than full fabricated interiors?
5. Is the issue gate tuning, model design, or missing file-level partial gating?
6. What is the recommended next step?

## Evaluation-only timestamps (critical)

- Timestamp CSVs under `data/phase7c1/raw/{ai,human}_fabricated/insertion_stamps.csv` are **never** passed to models.
- Live inference runs without timestamps (same as Phase 9C production path).
- Timestamps are used **only after** inference to label segments as inside/outside/boundary relative to ground truth.
- No final fake/real decision and no single binary authenticity score.

## Scripts (manual run)

### 1. Run diagnostics

```bat
python code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py --device auto
```

Optional limits:

```bat
python code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py --max_files 10 --overlap_threshold 0.25
```

Uses `analyze_audio_file(..., return_debug=True)` and reads `debug_info.partial_segment_scores`.

### 2. Summarize

```bat
python code/phase9/testing/summarize_phase9d_p4_partial_diagnostics.py --make_plots
```

### 3. Validate

```bat
python code/phase9/testing/validate_phase9d_p4_partial_diagnostics.py
```

## Outputs

| File | Description |
|---|---|
| `phase9d_p4_partial_segment_diagnostics.csv` | Per-segment overlap with true region |
| `phase9d_p4_partial_file_diagnostics.csv` | File-level top-k hit and broad activation metrics |
| `phase9d_p4_boundary_diagnostics.csv` | Splice boundary proximity analysis |
| `phase9d_p4_partial_summary.csv` | Aggregate rates and recommendation |
| `phase9d_p4_partial_diagnostic_report.md` | Human-readable findings |
| `figures/*_timeline.png` | Optional timeline plots |

## Overlap rules

- `inside_fabricated_region`: `overlap_ratio_segment >= overlap_threshold` (default 0.25)
- `boundary_overlap`: overlap > 0 but below threshold
- `outside_fabricated_region`: no overlap

## Diagnostic labels

| Label | Meaning |
|---|---|
| `localized_success` | Top-1 segment inside true region |
| `topk_hits_but_broad_activation` | Top-k hits region but broad activation gate blocks fusion |
| `broad_activation_not_localized` | Broad activation without useful top-k localization |
| `boundary_only_signal` | Top segments near boundaries, not interior |
| `no_timestamp_hit` | Top-k segments miss true region |
| `inference_error` | Pipeline error |

## Interpretation vocabulary

Use:

- timestamp hit rate
- broad activation
- localized contrast
- manual review support
- needs model redesign

Avoid:

- perfect detector
- final fake/real proof
- confirmed fake segment

## Recommendation logic (summary)

The summarizer recommends one of:

- gate tuning only (if localized hits are frequent)
- file-level partial candidate model
- segment retraining with non-partial negatives
- splice/boundary indicator model
- combined approach

Phase 9E apps may proceed after documenting limitations; tuning is optional follow-up (not a blocker for wiring apps).

## Debug API (Phase 9C)

When `return_debug=True`, `debug_info.partial_segment_scores` lists **all** segments with:

- `segment_id`, `start_sec`, `end_sec`
- `partial_probability`, `partial_rank`, `partial_above_threshold`
- `partial_localization_gate` (file-level gate snapshot)

Normal non-debug JSON responses still expose only top candidate segments.

## Safety

- Active models only (Phase 9B packaged)
- AASIST/HybridResNet inactive
- No training/refitting in P4 scripts
- Diagnostic only — does not change fusion behavior
