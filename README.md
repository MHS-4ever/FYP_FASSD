# FYP — Deepfake Audio Detection (FASSD)

## Project scope

See `FASSD - Scope.md`. This project targets:
- **AI vs Human voice detection**
- **AI-replaced voices in real recordings** (environment/acoustic mismatch)
- **Replay detection of AI voices** (device + re-recording artifacts)

## Current working phase

- **Phase 6**: Explanation system + demo UI (`reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`)

## First-time setup (Windows / PowerShell)

### 1) Create the conda environment (if you don’t already have it)

```powershell
conda create -n fassd python=3.10 -y
```

### 2) Activate the environment

```powershell
conda activate fassd
```

### 3) Install PyTorch (CUDA)

If you have an NVIDIA GPU and CUDA 12.1, install the CUDA wheels:

```powershell
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
```

### 4) Install project dependencies

From the repo root:

```powershell
cd E:\FYP
pip install -r requirements.txt
```

### 5) Verify CUDA is working

```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

## Where things are

| Location | What it contains |
|---|---|
| `code/phase0` … `code/phase5` | Phase implementation scripts |
| `reports/pipeline_phases/` | Phase planning/design documents (`PHASE0`…`PHASE7`) |
| `models_saved/` | Checkpoints / pickles / training logs |
| `reports/evaluation/` | Phase 5 evaluation outputs (CSVs + report + figures) |
| `testing_audios/` | Demo audios (Trump real/fake) |
| `release/` | Planned local demo app packaging (Gradio) |

## Current best model (Phase 4 → Phase 5)

- **Checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth`
- **Phase 5 test summary** (see `reports/evaluation/comprehensive_evaluation_report.md`):
  - Overall test EER: **16.22%**
  - RealWorld test EER: **16.14%** (meets MVP target < 20%)

## Project phases (map + status)

| Phase | Description |
|---|---|
| **[Phase 0](code/phase0/)** + [`PHASE0_DATA_COLLECTION.md`](reports/pipeline_phases/PHASE0_DATA_COLLECTION.md) | Data collection + preprocessing + real-world dataset creation |
| **[Phase 1](code/phase1/)** + [`PHASE1_UNIFIED_DATASET.md`](reports/pipeline_phases/PHASE1_UNIFIED_DATASET.md) | Unified manifest + speaker-independent splits |
| **[Phase 2](code/phase2/)** + [`PHASE2_FEATURE_EXTRACTION.md`](reports/pipeline_phases/PHASE2_FEATURE_EXTRACTION.md) | Feature extraction (log-mel + environmental) + HDF5 packing |
| **[Phase 3](code/phase3/)** + [`PHASE3_HYBRID_ARCHITECTURE.md`](reports/pipeline_phases/PHASE3_HYBRID_ARCHITECTURE.md) | Hybrid architecture (ResNet + environmental branch) + multi-task loss |
| **[Phase 4](code/phase4/)** + [`PHASE4_TRAINING.md`](reports/pipeline_phases/PHASE4_TRAINING.md) | Training + bottleneck fixes (HDF5 uncompressed + chunked fast loader) |
| **[Phase 5](code/phase5/)** + [`PHASE5_EVALUATION.md`](reports/pipeline_phases/PHASE5_EVALUATION.md) | Test evaluation + report generation (overall + ASVspoof + RealWorld + per-attack) |
| **Phase 6** + [`PHASE6_EXPLANATION_SYSTEM.md`](reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md) | **Current**: explanation system + demo UI (Gradio) |
| **Phase 7** + [`PHASE7_DOMAIN_ADAPTATION.md`](reports/pipeline_phases/PHASE7_DOMAIN_ADAPTATION.md) | Optional: only if RealWorld EER > 20% |

## Quick run commands (per phase)

Run commands from the repo root:

```powershell
cd E:\FYP
conda activate fassd
```

| Phase | Command |
|---|---|
| Phase 0 | `python code/phase0/run_phase0.py` |
| Phase 1 | `python code/phase1/run_phase1.py` |
| Phase 2 | `python code/phase2/run_phase2.py` |
| Phase 3 | `python code/phase3/run_phase3.py` |
| Phase 4 | See `code/phase4/README.md` |
| Phase 5 | See `code/phase5/README.md` |

## Demo (after Phase 6 is implemented)

The demo will run as a local Gradio web app:

```powershell
cd E:\FYP
conda activate fassd
python release/app.py
```

See `release/README.md` for the planned release structure and model-swap workflow.

