# Phase 7E1 — AASIST Expected I/O Inspection

**Generated:** 2026-05-26T19:35:38.345343+00:00  
**Verdict:** `PASS`  
**Source:** `E:\FYP\code\phase7\aasist\vendor\AASIST`  

## Aggregated hints (heuristic)

### sample_rate
- _(none detected)_

### input_length
- _(none detected)_

### n_fft
- _(none detected)_

### labels
- `spoof`
- `Spoof`

### checkpoint_keys
- _(none detected)_

## Unknowns / manual confirmation

- Exact tensor layout (waveform vs spectrogram) without running upstream code
- Official checkpoint key names without loading a real checkpoint
- Training label CSV format for FASSD until Phase 7E2 adapter
- sample_rate not found in configs — confirm from upstream README (often 16 kHz)

## Notes for Phase 7E2

- Build adapter to emit audio paths + binary risk_target per PHASE7E0_AASIST_LABEL_STRATEGY.md
- Map FASSD manifests using phase7e0_selected_paths.json canonical paths
- Align sample rate / clip length with values found in config (if any)
- Support partial-fabrication suspicious windows from 7C1 manifest
- Never include Phase 7A holdout in train/val

