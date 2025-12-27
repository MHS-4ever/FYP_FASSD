# FYP — Deepfake Audio Detection (FASSD)

## Project scope

See `FASSD - Scope.md`. This project targets:
- **AI vs Human voice detection**
- **AI-replaced voices in real recordings** (environment/acoustic mismatch)
- **Replay detection of AI voices** (device + re-recording artifacts)

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

- **Phase code**: `code/phase0` … `code/phase5`
- **Phase plans / design docs**: `reports/pipeline_phases/PHASE*.md`
- **Trained models / checkpoints**: `models_saved/`
- **Evaluation outputs (Phase 5)**: `reports/evaluation/`
- **Demo audios (Trump)**: `testing_audios/`

## Current best model (Phase 4 → Phase 5)

- **Checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth`
- **Phase 5 test summary** (see `reports/evaluation/comprehensive_evaluation_report.md`):
  - Overall test EER: **16.22%**
  - RealWorld test EER: **16.14%** (meets MVP target < 20%)

## Quick commands

Run commands from the repo root:

```powershell
cd E:\FYP
conda activate fassd
```

### Phase 0

```powershell
python code/phase0/run_phase0.py
```

### Phase 1

```powershell
python code/phase1/run_phase1.py
```

### Phase 2

```powershell
python code/phase2/run_phase2.py
```

### Phase 3

```powershell
python code/phase3/run_phase3.py
```

### Phase 4 training (already completed)

See `code/phase4/README.md`.

### Phase 5 evaluation (completed)

See `code/phase5/README.md` and `reports/pipeline_phases/PHASE5_EVALUATION.md`.

### Phase 6 (next): Explanation system + demo UI

Planned in `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`.

## Release packaging (planned)

When Phase 6 is complete, a self-contained local demo folder will be created:
- `release/README.md` explains the final structure and workflow.

### Demo (after Phase 6 is implemented)

The demo will run as a local Gradio web app:

```powershell
cd E:\FYP
conda activate fassd
python release/app.py
```


