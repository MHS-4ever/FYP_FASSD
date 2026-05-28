# Phase 8D SSL Embedding Extraction Report

**Generated:** 2026-05-28 09:37:24 UTC
**Runtime:** 304.74 sec

## Configuration

- model_name: `microsoft/wavlm-base-plus`
- pooling: `mean`
- segment_mode: `file_and_segments`
- device: `auto`
- use_safetensors: `True`
- allow_bin_weights: `False`
- batch_size: 1 (processed safely one-at-a-time)
- embedding_dim: 768
- progress: `tqdm`

## Runtime summary

- files_processed: 184
- files_skipped_resume: 0
- segments_processed: 4189
- segments_skipped_resume: 0
- warnings_count: 0
- file_ok_count: 184
- file_model_error_count: 0
- file_all_blank_rows: 0
- segment_ok_count: 4189
- segment_model_error_count: 0
- segment_all_blank_rows: 0

## Extraction statuses (files)

- `ok`: 184

## Extraction statuses (segments)

- `ok`: 4189

## Guarantees

- Model frozen: `model.eval()`, `requires_grad_(False)`, `torch.no_grad()`
- Loader uses `AutoFeatureExtractor + AutoModel` (no tokenizer/ASR decoding)
- Raw waveform masks are not applied directly to hidden-state frames.
- No training / no fine-tuning / no classifier / no predictions
- No modification of Phase 8B or Phase 8C files

## Outputs

- `reports/phase8/embeddings/phase8d_file_ssl_embeddings.csv`
- `reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv`
- `reports/phase8/embeddings/phase8d_file_ssl_embedding_metadata.csv`
- `reports/phase8/embeddings/phase8d_segment_ssl_embedding_metadata.csv`
