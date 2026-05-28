# Phase 8D — Frozen SSL Embedding Extraction Design

**Status:** Script created — **NOT YET EXECUTED**  
**Primary model:** `microsoft/wavlm-base-plus`  
**Fallback models:** `microsoft/wavlm-base`, `facebook/wav2vec2-base`

---

## Purpose

Phase 8D adds **frozen pretrained speech embeddings** for each file and segment in Phase 8B tables.  
These embeddings complement Phase 8C handcrafted acoustic features and are intended for **later** Phase 8E lightweight modeling.

Phase 8D itself is extraction only:

- no training
- no fine-tuning
- no classifier
- no predictions
- no evidence score filling

---

## Why after Phase 8C

Phase 8C provides interpretable acoustic/channel indicators that were useful for replay/mixer cues.  
Phase 8D adds richer representation features (SSL embeddings) that may better support origin/mixed/partial patterns in later phases.

---

## Frozen model rules

The extractor enforces frozen usage:

- `model.eval()`
- `requires_grad_(False)` on parameters
- inference under `torch.no_grad()`

No optimizer, no loss, no backward pass, no checkpoint writes.

---

## Extraction flow

1. Load Phase 8B file and segment tables.
2. Load SSL audio extractor + model via `transformers` (`AutoFeatureExtractor`, `AutoModel`).
3. Audio preprocessing:
   - resolve path
   - mono conversion
   - resample to 16 kHz (default)
4. File embedding extraction.
5. Segment embedding extraction using `start_sec` / `end_sec`.
6. Pooling:
   - `mean` (default)
   - `mean_std` (concat of mean and std vectors)
7. Save:
   - file embeddings CSV
   - segment embeddings CSV
   - file metadata CSV
   - segment metadata CSV
   - extraction report

Model load safety policy:

- Default: `use_safetensors=True`
- `.bin` weights are allowed only with explicit user override (`--allow_bin_weights`)

Pooling/mask correctness rule:

- WavLM/wav2vec2 hidden states are frame-level (`[batch, frames, hidden]`) and typically much shorter than raw waveform sample length.
- Raw audio attention masks may not match hidden frame length.
- Phase 8D applies attention masking only when mask length matches hidden frame length; otherwise it safely falls back to unmasked mean/std pooling.

---

## GPU / memory safety (RTX 3050 6GB)

- default `batch_size=1`
- one sample at a time processing
- no hidden-state accumulation across dataset
- optional `torch.cuda.empty_cache()` during loops
- resume + chunked flush for interruption safety

---

## Progress / resume behavior

Supported CLI controls:

- `--resume`: skip already extracted `file_id` / `segment_id`
- `--flush_every_files` / `--flush_every_segments`: append periodically
- `--no_progress` and `--progress_every`: progress fallback controls
- tqdm auto-used when available

---

## Limitations

- Embeddings are dense latent vectors and not directly human-interpretable like Phase 8C scalar features.
- Extraction status can be non-`ok` for missing/unreadable/too-short/silent audio.
- Model loading may fail due to cache/network/auth issues; script reports model-specific guidance.
- Some checkpoints include ASR/tokenizer assets that are irrelevant here; Phase 8D intentionally avoids tokenizer loading by using `AutoFeatureExtractor`.
- `pytorch_model.bin` loading may be blocked on older torch versions due to security restrictions.
- Torch upgrade is optional and should be planned carefully for CUDA compatibility.
- Validation is configured to fail when extraction outputs are 100% blank or all rows are `model_error/error`.

---

## Not in scope (Phase 8D)

- Any model training or fine-tuning
- Any fake/real decision logic
- Any origin/manipulation prediction output
- Any Phase 8E classifier setup

---

## Related

- `code/phase8/embeddings/extract_phase8d_ssl_embeddings.py`
- `code/phase8/embeddings/phase8d_ssl_utils.py`
- `code/phase8/validation/validate_phase8d_embeddings.py`

