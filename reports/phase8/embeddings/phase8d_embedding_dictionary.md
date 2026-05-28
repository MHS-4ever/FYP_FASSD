# Phase 8D — SSL Embedding Dictionary

**Schema version:** `phase8d_v1`  
**Scope:** Frozen SSL embedding extraction outputs only (no predictions)

---

## File embedding CSV fields

### Identity fields

- `schema_version`: embedding export schema tag
- `file_id`: joins to Phase 8B file table
- `audio_path`: source audio path
- `source_dataset`: source dataset label
- `split`: train/val/test/...
- `known_origin_label`: known label context only
- `known_manipulation_labels`: known label context only

### Provenance fields

- `embedding_model_name`: pretrained model used (e.g., `microsoft/wavlm-base-plus`)
- `embedding_layer`: currently `last_hidden_state`
- `pooling`: `mean` or `mean_std`
- `target_sample_rate`: extraction sample rate (default 16000)
- `embedding_dim`: actual embedding vector length
- `extraction_status`: extraction outcome
- `warning_message`: non-fatal issue details

### Embedding vector fields

- `ssl_emb_000 ... ssl_emb_NNN`: dense numeric vector values
- N depends on model hidden size and pooling:
  - `mean`: usually hidden size (e.g., 768)
  - `mean_std`: usually 2 * hidden size

---

## Segment embedding CSV fields

### Identity fields

- `schema_version`
- `file_id`
- `segment_id`
- `audio_path`
- `start_sec`
- `end_sec`
- `segment_duration_sec`

### Provenance fields

- `embedding_model_name`
- `embedding_layer`
- `pooling`
- `target_sample_rate`
- `embedding_dim`
- `extraction_status`
- `warning_message`

### Embedding vector fields

- `ssl_emb_000 ... ssl_emb_NNN` (same embedding policy as file-level)

---

## Metadata CSV fields

### File metadata

- `file_id`, `audio_path`
- `known_origin_label`, `known_manipulation_labels`
- `duration_sec`, `sample_rate`
- `embedding_model_name`, `pooling`
- `extraction_status`, `warning_message`

### Segment metadata

- `file_id`, `segment_id`, `audio_path`
- `start_sec`, `end_sec`, `segment_duration_sec`
- `embedding_model_name`, `pooling`
- `extraction_status`, `warning_message`

---

## `extraction_status` values

- `ok`
- `missing_audio`
- `unreadable_audio`
- `too_short`
- `silent_or_invalid`
- `model_error`
- `error`

---

## How to interpret embeddings

- SSL embeddings are pretrained representation vectors (latent features).
- They capture broad speech structure and context in a compact numeric form.
- They are **not** directly interpretable as explicit acoustic statistics.
- They are **not** proof of authenticity/manipulation by themselves.
- They are intended as inputs for later, separate modeling phases (Phase 8E+).

### Loader note

- Phase 8D loads `AutoFeatureExtractor + AutoModel`.
- No tokenizer is used.
- No ASR decoding or text transcription is performed.

---

## Not included

- No fake/real scores
- No replay/mixer decisions
- No final forensic status
- No evidence score column filling in Phase 8B tables

