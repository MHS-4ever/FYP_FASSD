# FYP — Deepfake Audio Detection (FASSD)

## Current scope (what this project delivers)

See `FASSD - Scope.md`. The project focuses on:

- **AI vs Human Voice Detection**: classify whether a full recording is genuine human speech or AI-generated.
- **AI-Replaced Voices in Real Recordings**: detect voice swapping/replacement by finding environmental/acoustic inconsistencies.
- **Replay Detection of AI Voices**: detect AI audio played through a device and re-recorded (replay artifacts).

## Current status (latest verified)

- **Best model checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth`
- **Latest evaluation report**: `reports/evaluation/comprehensive_evaluation_report.md`
- **Key result (RealWorld test set)**: **EER = 16.14%** ✅ (target < 20%)
- **Overall test EER**: **16.22%**

## First-time setup (Windows / PowerShell)

Create and activate the environment:

```powershell
conda create -n fassd python=3.10 -y
```

```powershell
conda activate fassd
```

Install PyTorch (CUDA 12.1 wheels):

```powershell
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
```

Install project dependencies:

```powershell
cd E:\FYP
pip install -r requirements.txt
```

Verify CUDA:

```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

## Most common actions

### Evaluate the best model on the test set (Phase 5)

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_chunked.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

### Run demo audio folder (current scripts)

Trump demo audios are in `testing_audios/`.

- **Note**: current demo scripts are from the previous pipeline (`code/test_audio_simple.py`, `code/predict_hybrid.py`).  
  Phase 6 will add a unified demo that uses the **trained hybrid checkpoint** and produces explanations.

## Repo navigation (where to look)

| Path | Purpose |
|---|---|
| `FASSD - Scope.md` | Final scope statement |
| `reports/pipeline_phases/` | Phase design/planning docs |
| `code/phase0` … `code/phase5` | Phase implementations |
| `models_saved/` | Checkpoints + training logs |
| `reports/evaluation/` | Phase 5 evaluation outputs (CSVs + report + figures) |
| `testing_audios/` | Trump real/fake test audios |
| `release/README.md` | Planned local demo app packaging (Gradio) |

## What’s next (Phase 6)

- **Phase 6 doc**: `reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`
- Goal: build an explanation system and (after it’s stable) package a local demo UI under `release/`.

