# Phase 8B — Evidence Table Builder Design

**Status:** Scripts created — **NOT YET EXECUTED** (unless user runs builder)  
**Schema version:** `phase8b_v1`  
**Code:** `code/phase8/evidence_table/build_phase8b_evidence_tables.py`

---

## Purpose

Phase 8B converts existing **manifest CSVs** (Phase 7C1, 7C2, features manifests, etc.) into structured **evidence tables** that later phases populate with real scores and fusion outputs.

Phase 8B is the **scaffold layer**: rows, columns, ground-truth labels, segment windows, and provenance — **not** forensic conclusions.

---

## What Phase 8B builds

| Output | Description |
|--------|-------------|
| File-level CSV | One row per audio file with metadata + empty evidence/fusion columns |
| Segment-level CSV | One row per time window (when `duration_sec` known) |
| Build report | Markdown summary of inputs, counts, warnings |

---

## What Phase 8B does NOT do

- Train or fine-tune models  
- Run model inference (Hybrid, AASIST, SSL, etc.)  
- Modify Phase 7 outputs, checkpoints, or manifests  
- Fill `evidence_*_score` columns from known labels  
- Emit a single `evidence_origin_score` or `origin_score` (forbidden)  
- Treat `manipulation_direct_synthetic` as a manipulation label  
- Decide fake vs real (`final_forensic_status` stays empty until Phase 8F)  

---

## Protection against binary fake/real collapse

1. **Four explicit origin score columns** at file and segment level — all left **empty** in 8B.  
2. **Known labels** (`known_origin_label`, `known_manipulation_labels`) are separate columns from scores.  
3. **No score derivation from labels** — mapping `ai_synthetic` → `evidence_origin_ai_score = 1.0` is explicitly forbidden.  
4. Validator rejects forbidden column names and `manipulation_direct_synthetic` in manipulation fields.

---

## Known labels vs evidence scores

| Column group | Phase 8B | Later phases |
|--------------|----------|--------------|
| `known_origin_label`, `known_manipulation_labels` | From manifest ground truth / experiment design | Unchanged (evaluation reference) |
| `evidence_origin_*_score`, manipulation evidence scores | **Empty** | 8C–8E extractors / classifiers |
| `calibrated_*`, `final_forensic_status`, `fusion_trace` | **Empty** | Phase 8F fusion |

---

## Segment row generation

- Parameters: `--segment_length_sec` (default 4.0), `--segment_hop_sec` (default 2.0).  
- Requires `duration_sec` from manifest or WAV metadata (`wave` stdlib).  
- If duration unknown → **no segment rows** for that file (warning in build report).  
- `suspicious_segment_flag` / `segment_reason` set **only** when manifest provides partial-fabrication time range overlapping the window (ground-truth annotation, not a model score).

---

## Label mapping

Manifest tokens are normalized to frozen Phase 8A vocabulary (see `phase8b_schema_utils.py`). Legacy names such as `origin_ai`, `manipulation_replay` are mapped at read time; they must not appear in output columns.

`manipulation_direct_synthetic` → contributes to **origin** (`ai_synthetic`), never manipulation list.

---

## CLI usage (when ready to run)

```text
python code/phase8/evidence_table/build_phase8b_evidence_tables.py ^
  --input_manifests reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --allow_missing_audio
```

Optional additional manifests via repeated paths in `--input_manifests`.

Validate after build:

```text
python code/phase8/validation/validate_phase8b_evidence_tables.py
```

---

## What later phases fill

| Phase | Fills |
|-------|--------|
| **8C** | Acoustic/channel features → manipulation-related evidence scores |
| **8D** | Frozen SSL embeddings → origin evidence scores |
| **8E** | Lightweight axis classifiers → score columns |
| **8F** | Fusion → calibrated labels, `final_forensic_status`, `fusion_trace` |
| **8G** | `forensic_summary`, UI/report |

---

## Related

- [phase8a_evidence_table_schema.md](phase8a_evidence_table_schema.md) — long-term target schema (`phase8a_v1_1`)  
- [phase8b_expected_outputs.md](phase8b_expected_outputs.md) — column reference  
- [../roadmap/phase8b_status.md](../roadmap/phase8b_status.md) — status tracker  
