# 🎙️ FASSD — Forensic Acoustic Synthetic Speech Detector

> **Detecting AI-generated audio through environmental acoustic analysis**

---

## 🎯 Project Scope

> 📄 Full scope document: [`FASSD - Scope.md`](FASSD%20-%20Scope.md)

---

## 📊 Project Status

**Active Working Scope**: Currently working on **Scope 1 (AI vs Human Voice Detection)** — enhancing with explanation system (Phase 6).

| Component | Status | Details |
|-----------|--------|---------|
| **Model Training** | ✅ Complete | Hybrid ResNet-Environmental model trained |
| **Best Checkpoint** | ✅ Available | `models_saved/hybrid_resnet_environmental_best.pth` |
| **Evaluation** | ✅ Complete | RealWorld EER: **16.14%** (target < 20% ✅) |
| **Explanation System** | 🚧 In Progress | Phase 6 development |
| **Demo App** | 📋 Planned | Gradio web interface (after Phase 6) |

**Latest Results**: Overall test EER = **16.22%**, AUC = **0.9167** | See full report: `reports/evaluation/comprehensive_evaluation_report.md`

---

## 🚀 Quick Start

### First-Time Setup

**1. Create conda environment:**
```powershell
conda create -n fassd python=3.10 -y
conda activate fassd
```

**2. Install PyTorch (CUDA 12.1):**
```powershell
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
```

**3. Install project dependencies:**
```powershell
cd E:\FYP
pip install -r requirements.txt
```

**4. Verify CUDA:**
```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

---


### Run Demo (Current Scripts)

**Note**: Current demo scripts (`code/test_audio_simple.py`, `code/predict_hybrid.py`) use the previous pipeline.  
**Phase 6** will add a unified demo using the trained hybrid checkpoint with explanations.

**Demo audio files**: Located in `testing_audios/` (Trump real/fake test audios)

---

## 🔄 Pipeline Evolution

**Previous Pipeline** (4 phases): ResNet CNN model achieved 2.61% EER on ASVspoof but failed on real-world audio due to domain mismatch. Documentation: [`reports/previous_phases/`](reports/previous_phases/)

**Current Pipeline** (Phase 0-6): Complete redesign with hybrid ResNet-Environmental architecture, mixed training data (ASVspoof + Real-world), and speaker-independent evaluation. Achieves **16.14% EER on RealWorld** (target < 20% ✅).

**Note**: Previous demo scripts (`code/test_audio_simple.py`, `code/predict_hybrid.py`) are deprecated. Phase 6 will provide a unified demo using the trained hybrid checkpoint.

---

## 🎨 Demo Application (Planned)

After Phase 6 completion, a **local Gradio web app** will be available in the `release/` folder.

### Features (Planned)
- 📤 Upload audio files (`.wav` format)
- 🎯 Real-time prediction (REAL/FAKE)
- 📊 Confidence scores and attack type classification
- 🔍 **Explanation system**: Environmental feature contributions + spectrogram visualizations
- 💾 Export prediction reports (JSON)

### Quick Run (After Phase 6)
```powershell
cd E:\FYP
conda activate fassd
python release/app.py
```

> 📖 Full demo documentation: [`release/README.md`](release/README.md)

---

## 📁 Project Structure

| Path | Description |
|------|-------------|
| **`FASSD - Scope.md`** | Project scope definition |
| **`reports/pipeline_phases/`** | Phase design & planning documents |
| **`code/phase0/`** ... **`code/phase5/`** | Phase implementation code |
| **`code/phase6/`** | Explanation system (in progress) |
| **`models_saved/`** | Model checkpoints & training logs |
| **`reports/evaluation/`** | Phase 5 evaluation outputs (CSVs, reports, figures) |
| **`testing_audios/`** | Test audio files (Trump real/fake) |
| **`release/`** | Demo app folder (Gradio web interface) |
| **`data/`** | Datasets, manifests, extracted features |

---

## 🔄 Development Phases

| Phase | Status | Description | Documentation |
|-------|--------|-------------|---------------|
| **Phase 0** | ✅ Complete | Data collection & preparation | [`reports/pipeline_phases/PHASE0_*.md`](reports/pipeline_phases/) |
| **Phase 1** | ✅ Complete | Unified dataset preparation | [`reports/pipeline_phases/PHASE1_*.md`](reports/pipeline_phases/) |
| **Phase 2** | ✅ Complete | Feature extraction | [`reports/pipeline_phases/PHASE2_*.md`](reports/pipeline_phases/) |
| **Phase 3** | ✅ Complete | Data augmentation | [`reports/pipeline_phases/PHASE3_*.md`](reports/pipeline_phases/) |
| **Phase 4** | ✅ Complete | Hybrid model training | [`reports/pipeline_phases/PHASE4_TRAINING.md`](reports/pipeline_phases/PHASE4_TRAINING.md) |
| **Phase 5** | ✅ Complete | Comprehensive evaluation | [`reports/pipeline_phases/PHASE5_EVALUATION.md`](reports/pipeline_phases/PHASE5_EVALUATION.md) |
| **Phase 6** | 🚧 In Progress | Explanation system | [`reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md`](reports/pipeline_phases/PHASE6_EXPLANATION_SYSTEM.md) |

---

## 📚 Documentation

- **Scope**: [`FASSD - Scope.md`](FASSD%20-%20Scope.md)
- **Phase Documentation**: [`reports/pipeline_phases/`](reports/pipeline_phases/)
- **Evaluation Report**: [`reports/evaluation/comprehensive_evaluation_report.md`](reports/evaluation/comprehensive_evaluation_report.md)
- **Demo App Guide**: [`release/README.md`](release/README.md)

---

## 🔧 System Requirements

- **OS**: Windows 10/11
- **Python**: 3.10
- **GPU**: NVIDIA GPU with CUDA support (tested on RTX 3050 6GB, RTX 3070)
- **RAM**: 16GB+ recommended
- **Storage**: 200GB+ for datasets and features

---

## 📝 License & Notes

This is a Final Year Project (FYP) implementation.  
For questions or issues, refer to the phase-specific documentation in `reports/pipeline_phases/`.

---

**Last Updated**: Phase 6 in progress | Best model: `hybrid_resnet_environmental_best.pth` (EER: 16.22%)
