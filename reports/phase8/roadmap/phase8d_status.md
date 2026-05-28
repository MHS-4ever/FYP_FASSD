# Phase 8D Status

**Phase 8D status:** SCRIPT CREATED / NOT YET EXECUTED

---

## Phase status snapshot

| Phase | Status |
|---|---|
| Phase 8B | **COMPLETED FOR CONTROLLED PHASE 7C1** |
| Phase 8C | **COMPLETED FOR CONTROLLED PHASE 7C1** |
| Phase 8C-A1 | **COMPLETED** |
| Phase 8D | Script created, pending execution |
| Phase 8E | **NOT STARTED** |

---

## Delivered scripts

- `code/phase8/embeddings/extract_phase8d_ssl_embeddings.py`
- `code/phase8/embeddings/phase8d_ssl_utils.py`
- `code/phase8/validation/validate_phase8d_embeddings.py`

Compatibility patch:

- Uses `AutoFeatureExtractor + AutoModel` (avoids tokenizer/vocab requirement)
- Defaults to safetensors model loading (`use_safetensors=True`)
- `.bin` loading requires explicit `--allow_bin_weights`
- Pooling now handles raw-mask vs hidden-frame length mismatch safely
- Validator now FAILS if embeddings are 100% blank or all rows are `model_error/error`

Docs:

- `reports/phase8/embeddings/phase8d_ssl_embedding_design.md`
- `reports/phase8/embeddings/phase8d_embedding_dictionary.md`

---

## Next action

User runs a controlled extraction test, for example:

```text
python code/phase8/embeddings/extract_phase8d_ssl_embeddings.py --max_files 5 --max_segments 50 --allow_missing_audio
python code/phase8/validation/validate_phase8d_embeddings.py
```

---

## Next review

Assistant reviews:

- embedding dimensions and status counts
- missingness / error distribution
- row alignment with Phase 8B IDs
- validation PASS/FAIL report

---

## Hard constraints

- Frozen model extraction only (no training/fine-tuning)
- No prediction columns
- No evidence score filling
- No Phase 8B/8C table modification
- No checkpoint modification in `models_saved/`
- Phase 8E remains **NOT STARTED**

