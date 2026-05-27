# Phase 8A — Evidence Table Schema (Frozen for Phase 8B)

**Status:** CANDIDATE FROZEN — schema `phase8a_v1_1`; pending human sign-off  
**Schema version:** `phase8a_v1_1`  
**Formats:** CSV (primary for analysis) + JSON (optional nested export per file)

---

## 1. Purpose

The evidence table is the **central artifact** of Phase 8. Phase 8B will populate these columns from existing Phase 7 outputs and metadata — without new model training in the first 8B pass.

**Anti-collapse rule:** There is **no** single `evidence_origin_score` or `origin_score` column. Origin is always stored as **four parallel scores** (human, AI, mixed, unknown). Fusion derives `calibrated_origin_label` — never treat one scalar as fake/real.

Two logical tables:

1. **`evidence_files.csv`** — one row per audio file  
2. **`evidence_segments.csv`** — one row per segment/window  

---

## 2. File-level schema (`evidence_files.csv`)

### 2.1 Identity and metadata

| Field | Data type | Allowed values / range | Required | Description |
|-------|-----------|------------------------|----------|-------------|
| `schema_version` | string | `phase8a_v1_1` | yes | Schema version for builder validation |
| `file_id` | string | Unique ID (e.g. 7C1 role prefix + hash) | yes | Stable primary key |
| `audio_path` | string | Valid repo-relative or absolute path | yes | Location of WAV/audio |
| `duration_sec` | float | > 0 | yes | File duration in seconds |
| `sample_rate` | int | e.g. 16000, 44100, 48000 | yes | Hz after preprocessing standard |
| `source_dataset` | string | `phase7c1`, `phase7a`, `user_upload`, … | yes | Provenance |
| `split` | enum string | `train`, `val`, `test`, `holdout`, `eval_only`, `none` | yes | Split discipline (7C2 groups) |
| `known_origin_label` | enum string | `human`, `ai_synthetic`, `mixed`, `unknown`, `na` | yes | Ground truth when available; `na` for blind |
| `known_manipulation_labels` | string | Semicolon-list of manipulation enums; `na` | yes | Ground truth multi-label |
| `known_segment_labels_available` | bool | `true`, `false` | yes | Whether per-segment GT exists |

### 2.2 Origin evidence (explicit — required)

| Field | Data type | Range | Required | Description |
|-------|-----------|-------|----------|-------------|
| `evidence_origin_human_score` | float | [0, 1] | yes | Support for human-produced speech |
| `evidence_origin_ai_score` | float | [0, 1] | yes | Support for AI/synthetic speech |
| `evidence_origin_mixed_score` | float | [0, 1] | yes | Support for mixed origin over file/time |
| `evidence_origin_unknown_score` | float | [0, 1] | yes | Insufficient/conflicting origin evidence |

**Deprecated (do not emit in 8B):** `evidence_origin_score` — any single scalar origin field.

### 2.3 Manipulation evidence (required)

| Field | Data type | Range | Required | Description |
|-------|-----------|-------|----------|-------------|
| `evidence_replay_score` | float | [0, 1] | yes | Replay/rerecording evidence strength |
| `evidence_mixer_channel_score` | float | [0, 1] | yes | Mixer/channel processing evidence |
| `evidence_partial_fabrication_score` | float | [0, 1] | yes | Partial fabrication evidence |
| `evidence_splice_score` | float | [0, 1] | yes | Edit/splice evidence |
| `evidence_quality_score` | float | [0, 1] | yes | Compression/low-quality stress (high = worse quality / more artifact) |

### 2.4 Calibrated labels and decision (required)

| Field | Data type | Allowed values | Required | Description |
|-------|-----------|----------------|----------|-------------|
| `calibrated_origin_label` | enum string | `human`, `ai_synthetic`, `mixed`, `unknown` | yes | Single post-fusion origin label |
| `calibrated_manipulation_labels` | string | Semicolon-list; `clean` alone or multi | yes | Post-calibration manipulation set |
| `final_forensic_status` | enum string | See label schema decision labels | yes | User-facing fused status |
| `manual_review_required` | bool | `true`, `false` | yes | Human review flag |
| `forensic_summary` | string | Free text, max ~500 chars recommended | yes | Forensic-safe short summary for report |

**Note on `clean`:** `calibrated_manipulation_labels` = `clean` means **no replay/mixer/splice/partial manipulation detected** — not “human-safe” and not “non-AI.” Direct AI may be `ai_synthetic` + `clean`.

### 2.5 Trace and explainability (required)

| Field | Data type | Allowed values | Required | Description |
|-------|-----------|----------------|----------|-------------|
| `forensic_risk_level` | enum string | `low`, `medium`, `high`, `inconclusive` | yes | Fused risk band for UI/report |
| `manual_review_reason` | enum string | See list below | yes | Why review flagged; use `none` if not required |
| `fusion_trace` | string | JSON string or short text | yes | Which fusion rules fired (explainability) |
| `evidence_source_paths` | string | Semicolon-separated paths | yes | Source CSV/JSONL/reports used to build row |

#### `manual_review_reason` allowed values

`none`, `weak_origin_evidence`, `conflicting_origin_evidence`, `strong_manipulation_weak_origin`, `quality_limited`, `suspicious_segment_file_conflict`, `borderline_scores`, `unknown_domain`

### Optional file-level columns (Phase 8B+)

| Field | Data type | Notes |
|-------|-----------|-------|
| `split_group_id` | string | 7C2 leakage control |
| `role_id` | string | 7C1 controlled role identifier |
| `hybrid_file_score` | float | Legacy Hybrid file-level score — manipulation/risk only |
| `c4v2_decision` | string | 7C4-v2 prototype output |
| `aasist_score` | float | Optional archived column |
| `risk_positive_legacy` | bool | Phase 7 `risk_target` — not origin |

---

## 3. Segment-level schema (`evidence_segments.csv`)

| Field | Data type | Allowed values / range | Required | Description |
|-------|-----------|------------------------|----------|-------------|
| `schema_version` | string | `phase8a_v1_1` | yes | Must match file table |
| `file_id` | string | Must exist in file table | yes | Foreign key |
| `segment_id` | string | Unique per file (e.g. `file_id_w0003`) | yes | Segment key |
| `start_sec` | float | ≥ 0 | yes | Window start |
| `end_sec` | float | > `start_sec` | yes | Window end |
| `segment_duration_sec` | float | > 0 | yes | `end_sec - start_sec` |

### 3.1 Segment origin evidence (explicit — required)

| Field | Data type | Range | Required | Description |
|-------|-----------|-------|----------|-------------|
| `segment_origin_human_score` | float | [0, 1] | yes | Window human origin support |
| `segment_origin_ai_score` | float | [0, 1] | yes | Window AI/synthetic origin support |
| `segment_origin_mixed_score` | float | [0, 1] | yes | Window mixed-origin support |
| `segment_origin_unknown_score` | float | [0, 1] | yes | Window unknown/abstain support |

**Deprecated (do not emit in 8B):** `origin_score` — any single scalar segment origin field.

### 3.2 Segment manipulation evidence (required)

| Field | Data type | Range | Required | Description |
|-------|-----------|-------|----------|-------------|
| `replay_score` | float | [0, 1] | yes | Window replay evidence |
| `mixer_channel_score` | float | [0, 1] | yes | Window mixer/channel evidence |
| `partial_fabrication_score` | float | [0, 1] | yes | Window partial-fabrication evidence |
| `splice_score` | float | [0, 1] | yes | Window splice evidence |
| `quality_score` | float | [0, 1] | yes | Window quality stress |

### 3.3 Segment flags and trace (required)

| Field | Data type | Allowed values | Required | Description |
|-------|-----------|----------------|----------|-------------|
| `suspicious_segment_flag` | bool | `true`, `false` | yes | Exceeds segment suspicion threshold |
| `segment_reason` | string | Controlled vocabulary below | yes | Why flagged or quiet |
| `segment_evidence_source` | string | Path to JSONL/CSV/model output | yes | Provenance for this segment row |

### `segment_reason` allowed tokens (extensible in 8F)

`none`, `high_replay`, `high_mixer`, `high_partial`, `high_splice`, `origin_ai_local`, `origin_mixed_local`, `region_delta`, `quality_limited`, `borderline`, `conflict_origin_manipulation`

---

## 4. JSON export shape (optional)

```json
{
  "schema_version": "phase8a_v1_1",
  "file_id": "string",
  "audio_path": "string",
  "metadata": {
    "duration_sec": 0.0,
    "sample_rate": 16000,
    "source_dataset": "phase7c1",
    "split": "test"
  },
  "known_labels": {
    "origin": "human",
    "manipulation": ["replay_rerecorded"],
    "segment_labels_available": true
  },
  "evidence": {
    "origin": {
      "human": 0.0,
      "ai_synthetic": 0.0,
      "mixed": 0.0,
      "unknown": 0.0
    },
    "replay": 0.0,
    "mixer_channel": 0.0,
    "partial_fabrication": 0.0,
    "splice": 0.0,
    "quality": 0.0
  },
  "calibrated": {
    "origin_label": "human",
    "manipulation_labels": ["replay_rerecorded"]
  },
  "decision": {
    "final_forensic_status": "suspicious_manipulation",
    "forensic_risk_level": "medium",
    "manual_review_required": false,
    "manual_review_reason": "none",
    "forensic_summary": "string",
    "fusion_trace": "{}"
  },
  "provenance": {
    "evidence_source_paths": "path1;path2"
  },
  "segments": [
    {
      "segment_id": "string",
      "start_sec": 0.0,
      "end_sec": 0.0,
      "origin": {
        "human": 0.0,
        "ai_synthetic": 0.0,
        "mixed": 0.0,
        "unknown": 0.0
      },
      "manipulation": { },
      "suspicious_segment_flag": false,
      "segment_reason": "none",
      "segment_evidence_source": "string"
    }
  ]
}
```

---

## 5. Validation rules (8B loader must enforce)

1. `schema_version` = `phase8a_v1_1` on every row.  
2. `file_id` unique in `evidence_files.csv`.  
3. Every `evidence_segments.file_id` exists in file table.  
4. `end_sec` ≤ file `duration_sec` (tolerance 50 ms).  
5. All origin score columns present; **reject** rows containing `evidence_origin_score` or `origin_score`.  
6. Origin scores in [0, 1] (warn if all four are near-zero without `unknown` calibration plan).  
7. `calibrated_manipulation_labels` if contains `clean`, must not contain other labels.  
8. `manual_review_required` = `true` when `final_forensic_status` = `inconclusive_manual_review`.  
9. `manual_review_reason` = `none` only when `manual_review_required` = `false`.  
10. Enum fields reject typos (fail build on unknown label).  
11. `evidence_source_paths` non-empty for 7C1-populated rows.

---

## 6. Phase 8B population plan (reference only)

| Column group | Initial 8B source (no new training) |
|--------------|--------------------------------------|
| Identity / metadata | 7C1 manifests, 7C2 splits |
| Manipulation `evidence_*` (replay, mixer, partial, …) | Hybrid chunk timelines + file scores |
| Origin four-tuple | Stub: high `unknown` until 8E; **never** map Hybrid spoof score to `evidence_origin_ai_score` alone |
| Calibrated / final / trace | Fusion dry-run per 8A rules or placeholder with `fusion_trace` documenting stub |
| Segments | Parse existing `*_chunk_timeline.jsonl`; map manipulation to segment columns; origin four-tuple per window |
| `evidence_source_paths` | List each Phase 7 CSV/JSONL path used |

---

## 7. Storage locations (planned, not created in 8A)

| Artifact | Path |
|----------|------|
| File table | `reports/phase8/evidence_table/evidence_files.csv` |
| Segment table | `reports/phase8/evidence_table/evidence_segments.csv` |
| JSON exports | `reports/phase8/evidence_table/json/{file_id}.json` |

**Phase 8B status:** NOT STARTED — directories may contain only `.gitkeep` until builder runs.

---

## Related documents

- [phase8a_multi_axis_label_schema.md](../label_schema/phase8a_multi_axis_label_schema.md) — authoritative labels  
- [phase8a_fusion_and_abstention_rules.md](../fusion/phase8a_fusion_and_abstention_rules.md)  
- [phase8a_architecture_freeze.md](../architecture/phase8a_architecture_freeze.md)
