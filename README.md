# FASSD — Forensic Acoustics for Synthetic Speech Detection

FASSD is a Final Year Project focused on **deepfake audio detection and forensic audio analysis**. The system is designed to analyze a given audio recording and identify whether it is authentic human speech, AI-generated speech, AI-replaced speech, or a replayed AI voice recording.

The project is not limited to simple binary deepfake detection. Its main goal is to move toward a **forensic audio product** that can process an input audio file, extract acoustic and environmental evidence, generate model predictions, visualize suspicious regions, and prepare a structured forensic-style report.

---

## Project Scope

The final scope of FASSD contains three main detection tasks:

1. **AI vs Human Voice Detection**
   - Detect whether a complete audio recording is natural human speech or AI-generated synthetic speech.

2. **Detection of AI-Replaced Voices in Real Recordings**
   - Identify cases where a real human recording has been manipulated by replacing or swapping the original voice with an AI-generated voice.
   - This uses acoustic mismatches and environmental inconsistencies such as background noise, room tone, reverberation, and channel artifacts.

3. **Replay Detection of AI Voices**
   - Detect AI-generated speech that has been played through a speaker or mobile device and then re-recorded.
   - This focuses on replay artifacts such as double reverberation, device frequency response, compression traces, and background mismatch.

---

## Core Idea

Most deepfake audio detectors focus only on speech content or spectral patterns. FASSD also considers **forensic acoustic evidence**, especially:

- Background noise consistency
- Reverberation and room acoustics
- Channel/device artifacts
- Spectrogram-based traces
- Segment-level manipulation patterns
- Model confidence and forensic explanation

This helps the system support more realistic forensic cases, where only part of the audio may be manipulated or where synthetic speech is replayed through a physical device.

---

## Current Project Direction

The project started with baseline CNN models trained on MFCC/LFCC spectrogram-style features. Later, the approach was expanded to include environmental and acoustic features because the main project goal is forensic authenticity verification, not only simple AI-vs-human classification.

The system direction is now:

```text
Input audio
   ↓
Preprocessing and normalization
   ↓
Feature extraction
   ├── Spectrogram/acoustic features
   ├── Environmental features
   ├── Replay/channel artifacts
   └── Segment-level evidence
   ↓
Model inference
   ├── File-level decision
   └── Segment-level suspicious-region analysis
   ↓
Visualization and report generation
   ↓
Forensic-style output report
```

---

## Repository Structure

```text
E:\FYP
│
├── Code/                         # Main source code
│   ├── data_loading/              # Dataset loaders and manifest utilities
│   ├── features/                  # Feature extraction scripts
│   ├── models/                    # Model architecture files
│   ├── train_baseline.py          # Baseline CNN training script
│   ├── evaluate_baseline.py       # Baseline evaluation script
│   ├── data_augmentation.py       # Audio augmentation pipeline
│   └── utils_metrics.py           # Evaluation metrics utilities
│
├── data/                          # Processed data, features, manifests, and raw links
│   ├── features/                  # Extracted feature manifests
│   ├── features_augmented/        # Augmentation outputs/checkpoints
│   ├── features_merged/           # Merged feature manifests
│   ├── manifests/                 # Dataset metadata and missing-file reports
│   ├── noise_rir/                 # Noise and room impulse response resources
│   └── raw/                       # Raw dataset shortcuts or audio references
│
├── DataSet/                       # ASVspoof and related dataset files
│   └── English/
│       ├── DeepFake (DF)/
│       ├── Logical Access (LA)/
│       └── keys/
│
├── images/                        # Project workflow and phase images
├── models_saved/                  # Trained model checkpoints
├── notebooks/                     # Experiment notebooks
├── reports/                       # Logs, figures, validation reports, and outputs
├── Research Article/              # Research papers used for study
├── Title Defence/                 # Title defence presentation
├── FASSD - Scope.md               # Final project scope
├── requirements.txt               # Python dependencies
└── README.md                      # Root project documentation
```

---

## Datasets Used

The project uses a combination of public and custom datasets:

- **ASVspoof 2021 Logical Access (LA)**
- **ASVspoof 2021 DeepFake (DF)**
- **Replay / Physical Access style audio scenarios**
- **Custom collected audio data** from sources such as broadcast, YouTube, and other real-world audio material
- **Augmented datasets** using noise, reverberation, compression, and replay-style transformations
- **Partial fabrication test cases** for evaluating segment-level manipulation detection

Dataset files are not necessarily stored directly in Git because of size and licensing restrictions. Local dataset paths and generated manifests are stored under `data/` and `DataSet/`.

---

## Setup

### 1. Clone or open the project

```powershell
cd E:\FYP
```

### 2. Create and activate environment

Recommended environment name:

```powershell
conda create -n fassd python=3.10 -y
conda activate fassd
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Verify project files

```powershell
dir
```

Expected important files/folders:

```text
Code/
data/
DataSet/
models_saved/
reports/
requirements.txt
FASSD - Scope.md
README.md
```

---

## Common Commands

### Train baseline model

```powershell
python Code\train_baseline.py
```

### Evaluate baseline model

```powershell
python Code\evaluate_baseline.py
```

### Extract features

```powershell
python Code\features\feature_extraction.py
```

### Run data augmentation

```powershell
python Code\data_augmentation.py
```

### Check dataset or manifest issues

```powershell
python Code\check_dataset_df.py
```

> Note: Some commands may require path arguments depending on the current phase script being used.

---

## Outputs

Typical outputs generated by the system include:

- Trained model checkpoints in `models_saved/`
- Feature manifests in `data/features/` and `data/features_merged/`
- Evaluation logs and figures in `reports/`
- Learning curves and validation plots in `reports/figures/`
- Forensic report outputs in later product/demo phases

---

## Hardware Used

The project has been developed and tested on a local Windows machine with:

- Windows 11
- Intel Core i5-13420H
- 16 GB RAM
- NVIDIA GeForce RTX 3050 Laptop GPU

Because the GPU memory is limited, model choices and batch sizes should be selected carefully. Lightweight or base-size models are preferred over very large transformer models unless training is optimized with small batches, mixed precision, gradient accumulation, or feature caching.

---

## Forensic Report Goal

The final product should not only return a label such as `real` or `fake`. It should provide forensic-style evidence, including:

- File-level authenticity decision
- Confidence score
- Segment-level suspicious timestamps
- Spectrogram or waveform visualization
- Environmental mismatch indicators
- Replay/channel artifact indicators
- Explanation of model findings
- Exportable forensic-style PDF report

This makes the system more useful for investigation, presentation, and evidence review.

---

## Project Status

FASSD has evolved through multiple phases:

- Baseline CNN detection using MFCC/LFCC-style features
- Augmentation and dataset expansion
- Environmental/acoustic feature integration
- Hybrid model experimentation
- Transformer/AASIST-style model exploration
- Product-oriented forensic report and UI direction
- Partial fabrication and segment-level manipulation analysis

The current direction is focused on making the system practical as a forensic audio analysis tool rather than only a benchmark classification model.

---

## Notes for Contributors / Teammates

When adding new code or experiments:

1. Keep phase-specific scripts organized inside `Code/` or a clearly named subfolder.
2. Save generated reports under `reports/`.
3. Save trained models under `models_saved/` or a phase-specific model registry.
4. Do not commit large dataset files unless required and allowed.
5. Keep manifests, validation reports, and result summaries updated.
6. Use clear filenames for test cases, especially for partial fabrication experiments.
7. Document every new model with its input features, checkpoint path, and expected output format.

---

## Suggested Git Ignore Rules

Large files and generated artifacts should usually be excluded from Git:

```gitignore
__pycache__/
*.pyc
*.pth
*.pt
*.ckpt
*.wav
*.flac
*.mp3
*.npy
*.npz
.env
.venv/
fassd/
reports/temp/
data/raw/
DataSet/
```

Model checkpoints, datasets, and generated audio files should be stored locally or in an external drive/cloud storage if they are too large for Git.

---

## Project Name

**FASSD** stands for:

```text
Forensic Acoustics for Synthetic Speech Detection
```

It is a forensic deepfake audio detection system designed to support authenticity verification of speech evidence.
