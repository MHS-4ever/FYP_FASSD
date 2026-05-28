# Phase 8B — Expected Outputs

**Schema version (builder default):** `phase8b_v1`  
**Generated files (after user runs builder):**

- `reports/phase8/evidence_table/phase8b_file_evidence_table.csv`
- `reports/phase8/evidence_table/phase8b_segment_evidence_table.csv`
- `reports/phase8/evidence_table/phase8b_build_report.md`
- `reports/phase8/validation/phase8b_evidence_table_validation_report.md` (after validator)

---

## Placeholder / null policy (Phase 8B)

| Column type | Phase 8B value |
|-------------|----------------|
| Evidence scores | **Empty string** (not 0.0, not copied from labels) |
| Fusion / calibration placeholders | **Empty string** |
| `manual_review_required` | **Empty** (not `false`) |
| `suspicious_segment_flag` | **Empty**, except ground-truth partial region overlap → `true` |
| `known_origin_label` | Populated from manifest when available, else `na` |
| `duration_sec` / `sample_rate` | From manifest or WAV; empty if missing and `--allow_missing_audio` |

---

## File-level columns

| Column | Type | Allowed / notes |
|--------|------|----------------|
| `schema_version` | string | `phase8b_v1` |
| `file_id` | string | Unique, non-empty |
| `audio_path` | string | As in manifest |
| `original_manifest_path` | string | Repo-relative manifest path |
| `original_row_index` | int | 0-based CSV row index |
| `duration_sec` | float or empty | Seconds |
| `sample_rate` | int or empty | Hz |
| `source_dataset` | string | e.g. `phase7c1`, `phase7c2` |
| `split` | enum | `train`, `val`, `test`, `holdout`, `eval_only`, `none` |
| `known_origin_label` | enum | `human`, `ai_synthetic`, `mixed`, `unknown`, `na` |
| `known_manipulation_labels` | string | Semicolon-list of frozen manipulation labels, or `na` |
| `known_segment_labels_available` | bool string | `true` / `false` |
| `evidence_origin_human_score` | float or empty | [0, 1] when filled later |
| `evidence_origin_ai_score` | float or empty | |
| `evidence_origin_mixed_score` | float or empty | |
| `evidence_origin_unknown_score` | float or empty | |
| `evidence_replay_score` | float or empty | |
| `evidence_mixer_channel_score` | float or empty | |
| `evidence_partial_fabrication_score` | float or empty | |
| `evidence_splice_score` | float or empty | |
| `evidence_quality_score` | float or empty | |
| `calibrated_origin_label` | enum or empty | Filled in 8F |
| `calibrated_manipulation_labels` | string or empty | |
| `final_forensic_status` | enum or empty | See allowed statuses below |
| `forensic_risk_level` | enum or empty | `low`, `medium`, `high`, `inconclusive` |
| `manual_review_required` | bool or empty | |
| `manual_review_reason` | enum or empty | See 8A schema |
| `fusion_trace` | string or empty | JSON/text in 8F |
| `evidence_source_paths` | string | Manifest path(s) used |
| `forensic_summary` | string or empty | 8G |

**Forbidden columns:** `evidence_origin_score`, `origin_score`

---

## Segment-level columns

| Column | Type | Notes |
|--------|------|-------|
| `schema_version` | string | `phase8b_v1` |
| `file_id` | string | FK to file table |
| `segment_id` | string | e.g. `{file_id}_w0000` |
| `audio_path` | string | Parent file path |
| `start_sec` | float | ≥ 0 |
| `end_sec` | float | > start |
| `segment_duration_sec` | float | end − start |
| `segment_origin_human_score` | float or empty | |
| `segment_origin_ai_score` | float or empty | |
| `segment_origin_mixed_score` | float or empty | |
| `segment_origin_unknown_score` | float or empty | |
| `replay_score` | float or empty | |
| `mixer_channel_score` | float or empty | |
| `partial_fabrication_score` | float or empty | |
| `splice_score` | float or empty | |
| `quality_score` | float or empty | |
| `suspicious_segment_flag` | bool or empty | GT overlap only in 8B |
| `segment_reason` | string or empty | e.g. `ground_truth_partial_region` |
| `segment_evidence_source` | string or empty | Filled when scores added |

---

## Allowed labels (frozen)

**Origin:** `human`, `ai_synthetic`, `mixed`, `unknown`, `na`

**Manipulation:** `clean`, `replay_rerecorded`, `mixer_channel_processed`, `partial_fabrication`, `edited_spliced`, `compressed_low_quality`, `unknown_manipulation`

**Final forensic status (when populated in 8F):**  
`accept_human_clean`, `suspicious_origin`, `suspicious_manipulation`, `suspicious_mixed`, `inconclusive_manual_review`

---

## Example row descriptions (no fake scores)

### File row — clean human (7C1-style)

- `known_origin_label`: `human`  
- `known_manipulation_labels`: `clean`  
- All `evidence_*_score`: empty  
- `final_forensic_status`: empty  

### File row — human replay

- `known_origin_label`: `human`  
- `known_manipulation_labels`: `replay_rerecorded`  
- Evidence scores: empty (replay score filled later by 8C/8E)  

### File row — direct AI

- `known_origin_label`: `ai_synthetic`  
- `known_manipulation_labels`: `clean` (valid: no replay/mixer manipulation)  
- Evidence scores: empty until models run  

### Segment row — default

- `start_sec` / `end_sec`: window bounds  
- All score columns: empty  
- `suspicious_segment_flag`: empty unless GT partial region overlaps window  

---

## Alignment with Phase 8A schema

Phase 8B uses `phase8b_v1` as builder schema version. Column names match [phase8a_evidence_table_schema.md](phase8a_evidence_table_schema.md) with these additions for traceability:

- `original_manifest_path`
- `original_row_index`

Future merge to `phase8a_v1_1` may rename outputs to `evidence_files.csv` / `evidence_segments.csv` after sign-off.
