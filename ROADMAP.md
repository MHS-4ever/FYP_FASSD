# FASSD Project Roadmap

## Current Status: Phase 4 - Advanced Models & Features

---

## ✅ Completed Phases

### Phase 0: Environment Setup

- ✅ Miniconda + CUDA environment
- ✅ Python 3.10.18 + PyTorch 2.5.1
- ✅ RTX 3050 6GB GPU configured
- ✅ Dependencies installed

### Phase 1: Feature Extraction

- ✅ LFCC features extracted (20 coefficients × frames)
- ✅ Log-Mel spectrograms extracted (64 bins × frames)
- ✅ Manifests created with label mapping
- ✅ 611,829 clean features + 611,829 augmented features

### Phase 2: Data Augmentation

- ✅ MUSAN noise augmentation
- ✅ RIR (room impulse response) convolution
- ✅ Codec simulation (downsample/upsample)
- ✅ Random gain and clipping
- ✅ Augmented features packed in HDF5

### Phase 3: Baseline Model Training & Debugging

- ✅ LCNN architecture implemented
- ✅ Streaming HDF5 dataset loader
- ✅ **Fixed critical class weight bug** (Nov 1, 2025)
- ✅ **Fixed Unicode console issues** (Nov 1, 2025)
- ✅ **LFCC models trained & evaluated** (Nov 3, 2025)
  - Clean: EER 9.68%, AUC 0.965
  - Robust: EER 15.71% (augmented test)

### Phase 4.1: Log-Mel Feature Experiments ✅

- ✅ **Mel models trained & evaluated** (Nov 5, 2025)
  - Mel Robust (WINNER): EER 9.69% (clean), 15.25% (augmented)
  - Mel Clean: EER 8.57% (clean), 36.33% (augmented) - overfitted
- ✅ **Key Finding**: Mel features outperform LFCC by 0.46% on augmented test
- ✅ **Best model selected**: `baseline_cnn_mel_robust.pth`

---

## 🔄 Current Phase: Phase 4 - Advanced Models & Features

### 4.1: Experiment with Different Features ✅ COMPLETE

**Completed:**

1. ✅ **Log-Mel Spectrograms**
   - Trained LCNN on mel features (clean + robust models)
   - **Result**: Mel outperforms LFCC (15.25% vs 15.71% EER on augmented test)
   - **Winner**: `baseline_cnn_mel_robust.pth`

**Future Options:**

2. **Feature Fusion** (optional)

   - Combine LFCC + Log-Mel in dual-stream architecture
   - Concat or attention-based fusion

3. **Additional Features** (optional)
   - MFCC (Mel-frequency cepstral coefficients)
   - Constant-Q Transform (CQT)
   - Raw waveform with learnable front-end

**Decision**: Proceed with Mel features for advanced architectures

### 4.2: Advanced Architectures ⏳ NEXT

**Priority: Deeper CNN with ResNet-style architecture**

1. **Deeper CNN** ← START HERE

   - Implement ResNet-style skip connections
   - Increase model capacity (more layers)
   - Goal: Improve on 15.25% EER baseline

2. **RNN/LSTM**

   - Capture temporal dependencies
   - BiLSTM on top of CNN features

3. **Transformer**

   - Self-attention for long-range patterns
   - Audio Transformer (Conformer)

4. **State-of-the-Art**
   - AASIST (End-to-end attention-based model)
   - RawNet2 (Raw waveform CNN)
   - Wav2Vec 2.0 fine-tuning

### 4.3: Environmental Feature Detection

**For Scope Goal #2 & #3:**

**Voice Replacement Detection:**

- Extract environmental acoustic features:
  - Background noise patterns
  - Reverb characteristics (RT60)
  - Frequency response differences

**Replay Detection:**

- Detect replay artifacts:
  - Double reverberation
  - Speaker frequency response
  - Channel mismatch indicators

**Implementation:**

1. Extract environment-specific features
2. Train binary classifier: genuine vs replaced/replayed
3. Combine with deepfake detector for multi-task model

### 4.4: Multi-Task Learning (Advanced)

**Three-Way Classification:**

1. Bonafide (real human voice)
2. Synthetic (AI-generated)
3. Replayed (recorded and re-played)

**Architecture:**

- Shared backbone (CNN/Transformer)
- Multiple classification heads
- Joint training with weighted losses

---

## 🎯 Scope Alignment

### Scope 1: AI vs Human Voice Detection ✅

**Status:** Strong baseline achieved  
**Best Model:** LCNN on Mel features (`baseline_cnn_mel_robust.pth`)  
**Performance:** EER 9.69% (clean), 15.25% (augmented)  
**Next:** Implement deeper CNN to improve further

### Scope 2: Voice Replacement Detection 🔄

**Status:** Not yet implemented  
**Requirements:**

- Environmental feature extraction
- Acoustic mismatch detection
- Dataset with replaced voices

### Scope 3: Replay Detection 🔄

**Status:** Not yet implemented  
**Requirements:**

- Replay artifact features
- Dataset with replayed samples
- ASVspoof 2021 PA (Physical Access) track

---

## 📊 Milestones & Timeline

| Phase | Task                      | Est. Time | Status         |
| ----- | ------------------------- | --------- | -------------- |
| 3.1   | Retrain LFCC models       | 1-2 hours | ✅ Complete    |
| 3.2   | Validate LFCC models      | 30 min    | ✅ Complete    |
| 4.1   | Train & eval Mel models   | 2 hours   | ✅ Complete    |
| 4.2   | Implement deeper CNN      | 2-3 hours | ⏳ Next        |
| 4.3   | Environmental features    | 4-6 hours | ❌ Not started |
| 4.4   | Multi-task learning       | 6-8 hours | ❌ Not started |
| 5.0   | Final evaluation & report | 3-4 hours | ❌ Not started |

---

## 🔧 Recommended Next Steps (Priority Order)

### Immediate (Today)

1. ✅ Review `ISSUE_RESOLVED.md`
2. ✅ Retrain baseline models with fixed code
3. ✅ Validate model performance

### Short-term (This Week)

4. ✅ Train Log-Mel baseline for comparison
5. ⏳ Implement ResNet-style deeper CNN ← CURRENT
6. ⏳ Analyze error cases (false positives/negatives)

### Medium-term (Next 2 Weeks)

7. Research environmental feature extraction
8. Implement voice replacement detector
9. Collect/prepare replay detection dataset

### Long-term (Next Month)

10. Implement advanced architecture (Transformer/AASIST)
11. Multi-task learning for all 3 scopes
12. Final evaluation and thesis writing

---

## 📚 Resources & References

### ASVspoof Challenge

- ASVspoof 2021 DF (DeepFake) - Currently using ✅
- ASVspoof 2021 LA (Logical Access) - Currently using ✅
- ASVspoof 2021 PA (Physical Access) - For replay detection ❌

### Papers to Review

1. "AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks" (2021)
2. "RawNet2: End-to-End Speech Synthesis for Anti-Spoofing" (2020)
3. "Replay Attack Detection with Complementary High-Resolution Information" (2019)
4. "Voice Liveness Detection Based on Pop Noise Modeling" (2017)

### Code Repositories

- ASVspoof 2021 Baseline: https://github.com/asvspoof-challenge/2021
- AASIST: https://github.com/clovaai/aasist
- RawNet2: https://github.com/Jungjee/RawNet

---

## 🎓 Final Year Project Deliverables

### Required Outputs

1. ✅ Working codebase (97% complete)
2. ✅ Trained baseline models (LFCC + Mel, 4 models total)
3. ✅ Evaluation metrics & comparison complete
4. ❌ Project report/thesis
5. ❌ Presentation slides
6. ❌ Demo application (optional)

### Evaluation Criteria

- AI vs Human detection: EER < 10%, AUC > 0.95
- Voice replacement detection: Accuracy > 80%
- Replay detection: EER < 15%
- Code quality and documentation
- Innovation and technical depth

---

**Last Updated:** November 5, 2025  
**Next Review:** After ResNet-style deeper CNN implementation
