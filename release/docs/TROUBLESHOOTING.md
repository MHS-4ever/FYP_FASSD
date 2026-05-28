# Troubleshooting (Skeleton)

## Common Issues

- Missing model artifacts: expected in Phase 9A, resolved in Phase 9B.
- Missing transformers: install dependencies from `requirements_release.txt`.
- WavLM download/cache issue: verify internet/cache path during Phase 9C integration.
- torch/safetensors issue: install compatible torch build for local CPU/CUDA.
- CUDA memory issue: fall back to CPU during local testing.
- audio load failure: verify format/path and decoding libraries.
- API not starting: verify environment and dependency installation.
- Gradio not starting: verify environment and dependency installation.
