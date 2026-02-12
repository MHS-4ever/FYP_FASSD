# Phase 5: Comprehensive Evaluation

**Status**: ✅ **COMPLETED (TEST EVALUATED + REPORTS GENERATED)**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 4  
**Dependencies**: Phase 4 (Training)

---

## 🎯 Objective

Comprehensively evaluate the trained hybrid model on all domains and attack types to verify generalization and identify areas for improvement.

---

## ✅ Final Result (Dec 27, 2025)

Evaluation completed on the **speaker-independent test set** using:
- Checkpoint: `models_saved/hybrid_resnet_environmental_best.pth`
- Test manifest: `data/manifests/test_speaker_independent.csv`

**Key outcome (MVP / scope-critical):**
- ✅ **RealWorld test EER = 16.14%** (**< 20% target met**)

### Test Metrics Summary

| Split | Samples | Binary EER (↓) | Binary AUC (↑) | Binary Acc @0.5 | Multiclass Acc |
|---|---:|---:|---:|---:|---:|
| **Overall** | 254,574 | **16.22%** | **0.9167** | 89.78% | 64.36% |
| **ASVspoof** | 237,490 | 18.15% | 0.8947 | 90.65% | 63.39% |
| **RealWorld** | 17,084 | **16.14%** | **0.9236** | 77.68% | 77.90% |

### Per-Dataset (Test)

| Dataset | Samples | EER (↓) | AUC (↑) |
|---|---:|---:|---:|
| LA | 24,388 | 6.30% | 0.9847 |
| DF | 94,032 | 8.33% | 0.9763 |
| PA | 119,070 | 16.23% | 0.9095 |
| RealWorld | 17,084 | 16.14% | 0.9236 |

---

## 📋 Tasks

### 1. In-Domain Evaluation (ASVspoof)

**Test Sets:**
- ASVspoof LA test set
- ASVspoof DF test set
- ASVspoof PA test set
- Combined ASVspoof test set

**Metrics Per Dataset:**
- EER (Equal Error Rate)
- AUC (Area Under ROC Curve)
- Accuracy (binary classification)
- Confusion matrix
- Per-attack-type breakdown

**Attack Type Analysis:**
- Bonafide detection rate
- Synthesis detection rate (LA)
- Conversion detection rate (DF)
- Replay detection rate (PA)

### 2. Cross-Domain Evaluation (Real-World)

**Test Sets:**
- Broadcast audio test set
- Phone audio test set
- Podcast audio test set
- Social media audio test set
- Combined Real-world test set

**Metrics Per Domain:**
- EER (Equal Error Rate)
- AUC (Area Under ROC Curve)
- Accuracy (binary classification)
- Confusion matrix
- False positive/negative rates

**Domain Comparison:**
- Compare Real-world performance vs ASVspoof performance
- Identify which domains perform best/worst
- Analyze domain-specific challenges

### 3. Speaker-Independent Evaluation

**Verification:**
- Confirm no speaker overlap between train/test
- Evaluate per-speaker performance (if possible)
- Analyze speaker generalization

**Metrics:**
- Per-speaker accuracy
- Speaker-level EER
- Generalization analysis

### 4. Multi-Task Evaluation

**Binary Task (Real vs Fake):**
- EER, AUC, Accuracy
- Confusion matrix
- Per-domain breakdown

**Multiclass Task (Attack Type):**
- Accuracy (4-class: bonafide, synthesis, conversion, replay)
- Per-class precision/recall
- Confusion matrix
- Attack type detection rates

**Task Correlation:**
- Analyze relationship between binary and multiclass predictions
- Check if binary confidence correlates with multiclass accuracy

### 5. Comprehensive Metrics Report

**Generate Report With:**
- Overall performance summary
- Per-domain performance tables
- Per-attack-type performance tables
- Confusion matrices
- ROC curves
- Performance comparison (ASVspoof vs Real-world)
- Failure case analysis

---

## 📁 Output Files

```
reports/
├── evaluation/
│   ├── comprehensive_evaluation_report.md    # Main report (includes Threshold sweep section)
│   ├── overall_metrics.csv                    # Overall metrics (overall split)
│   ├── threshold_sweep.csv                     # Detail evaluation: accuracy & bonafide FPR at 0.5, 0.65, 0.70
│   ├── asvspoof_evaluation.csv                 # ASVspoof metrics
│   ├── realworld_evaluation.csv                # Real-world metrics
│   ├── per_domain_metrics.csv                  # Domain breakdown
│   ├── per_attack_metrics.csv                  # Attack type breakdown
│   └── confusion_matrices/
│       ├── overall_binary_cm.png
│       └── overall_multiclass_cm.png
└── evaluation/figures/
    ├── roc_overall.png
    ├── roc_asvspoof.png
    └── roc_realworld.png
```

---

## 🔧 Scripts Needed

### Implemented (Phase 5):
- ✅ `code/phase5/evaluate_hybrid_model.py` - Main evaluation script (overall + per-domain + per-attack + figures + markdown report)
- ✅ `code/phase5/run_phase5.py` - Convenience runner with defaults
- ✅ `code/phase5/README.md` - Practical guide / commands

### Existing (Reuse):
- ✅ `code/utils_metrics.py` - EER, AUC, confusion matrix

---

## ✅ Success Criteria

- [x] Comprehensive evaluation completed on the test set
- [x] All metrics calculated (EER, AUC, Accuracy)
- [x] Per-domain performance analyzed
- [x] Per-attack-type performance analyzed
- [x] Speaker-independent verification passed (train/test overlap count = 0)
- [x] Evaluation report generated
- [x] **KEY**: Real-world EER < 20% (MVP requirement) ✅

**Notes vs original targets:**
- RealWorld target ✅ met
- Overall EER target (<10%) ❌ not met (overall test EER = 16.22%)
- Multiclass accuracy target (>80%) ❌ not met (overall = 64.36%)

---

## 🚀 How to Run (PC / Laptop)

### PC

```powershell
cd C:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 C:/FYP/data/features/logmel_chunked.h5 --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 256
```

### Laptop

Use `E:/FYP` or `D:/FYP` for the feature H5 paths depending on where your data lives:

```powershell
cd E:\FYP
conda activate fassd
python code/phase5/evaluate_hybrid_model.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --test_manifest data/manifests/test_speaker_independent.csv --train_manifest data/manifests/train_speaker_independent.csv --spectrogram_h5 E:/FYP/data/features/logmel_chunked.h5 --environmental_h5 E:/FYP/data/features/environmental_packed.h5 --output_dir reports/evaluation --batch_size 128
```

Or run the convenience wrapper (PC defaults):

```powershell
cd C:\FYP
conda activate fassd
python code/phase5/run_phase5.py
```

Expected outputs:
- `reports/evaluation/comprehensive_evaluation_report.md` (includes **Threshold sweep (detail evaluation)** table)
- `reports/evaluation/threshold_sweep.csv` — accuracy and bonafide FPR at each threshold (default: 0.5, 0.65, 0.70)
- `reports/evaluation/overall_metrics.csv`, `per_domain_metrics.csv`, `per_attack_metrics.csv`
- `reports/evaluation/confusion_matrices/*.png`
- `reports/evaluation/figures/roc_*.png`

**Detail evaluation (threshold sweep):** The script runs a threshold sweep by default (`--thresholds "0.5 0.65 0.70"`). To use different thresholds: `--thresholds "0.5 0.6 0.65 0.7 0.75"`.

## 📊 Expected Performance

**Minimum Viable Product (MVP) Targets:**
```
Metric                    | Target | Critical
--------------------------|--------|----------
ASVspoof EER              | < 5%   | ✅
Real-world EER            | < 20%  | 🔴 KEY
Overall EER                | < 10%  | ✅
Real-world AUC             | > 0.85 | ✅
Multiclass Accuracy        | > 80%  | ✅
```

**Full Success Targets (updated with test-set results):**
```
Metric                    | Target   | Achieved (test) | Status
--------------------------|----------|-----------------|--------
ASVspoof EER              | < 3%     | 18.15%          | ❌
Real-world EER             | < 15%    | 16.14%          | ❌
Overall EER                | < 8%     | 16.22%          | ❌
Real-world AUC             | > 0.90   | 0.9236          | ✅
Multiclass Accuracy        | > 85%    | 64.36%          | ❌
```

---

## ⚠️ Challenges & Solutions

### Challenge 1: Domain Gap
**Problem**: Large performance gap between ASVspoof and Real-world  
**Solution**: 
- Document gap
- Identify specific failure cases
- Plan Phase 7 (Domain Adaptation) if needed

### Challenge 2: Attack Type Confusion
**Problem**: Model may confuse attack types  
**Solution**: 
- Analyze confusion matrix
- Identify which attacks are confused
- Consider feature engineering or architecture changes

### Challenge 3: False Positives/Negatives
**Problem**: High false positive/negative rates  
**Solution**: 
- Analyze failure cases
- Adjust threshold if needed
- Consider calibration

---

## 🐛 Issue Encountered & Fix

### EER/AUC undefined for single-class slices (FIXED)

**Problem:**
Some evaluation slices (especially per-attack-type) can contain only one class (all bonafide or all spoof). In this case, ROC/EER/AUC are undefined and the evaluation originally crashed with `All-NaN slice encountered`.

**Fix applied:**
- Updated `code/phase5/evaluate_hybrid_model.py` to safely return `NaN` for EER/AUC on single-class subsets and continue generating the rest of the report/CSVs/figures.

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 4: Training (need trained model)

**Next Phase:**
- Phase 6: Explanation System (if evaluation passes)
- Phase 7: Domain Adaptation (only if Real-world EER > 20%)

---

## 📝 Notes

- **CRITICAL**: Real-world EER < 20% is the key success metric
- If Real-world performance is poor, proceed to Phase 7
- Document all failure cases for analysis
- Compare with previous pipeline results
- Generate visualizations for report

---

## 🔍 Evaluation Checklist

- [x] All test sets evaluated (speaker-independent test)
- [x] All metrics calculated
- [x] Per-domain breakdown complete
- [x] Per-attack-type breakdown complete
- [x] Confusion matrices generated
- [x] ROC curves plotted
- [ ] Failure cases identified (optional deep-dive)
- [x] Evaluation report written
- [x] Performance targets checked
- [x] **Detail evaluation**: Threshold sweep (0.5, 0.65, 0.70) run and documented; `threshold_sweep.csv` and report section added

---

## 📊 Detail evaluation (threshold sweep)

The evaluation script now runs a **threshold sweep** by default and reports **accuracy** and **bonafide FPR** at multiple operating points (0.5, 0.65, 0.70) on the full test set. This supports choosing an operating point that reduces false positives on real audio.

- **Output**: `reports/evaluation/threshold_sweep.csv` (columns: `threshold`, `accuracy_pct`, `bonafide_fpr_pct`)
- **Report**: Section **"Threshold sweep (detail evaluation)"** in `comprehensive_evaluation_report.md`
- **Override**: `--thresholds "0.5 0.6 0.65 0.7 0.75"` (space-separated)

---

**Last Updated**: February 2026  
**Status**: ✅ **COMPLETED**

