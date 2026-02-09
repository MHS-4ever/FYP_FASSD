# Phase 6: Explanation System

**Status**: ✅ READY (scripts implemented)  
**Priority**: 🟡 IMPORTANT  
**Duration**: Week 4-5  
**Dependencies**: Phase 5 (Evaluation) - Only if evaluation passes

---

## 🎯 Objective

Build an explanation system that provides human-readable reasons for model predictions, based on environmental features, spectrogram patterns, and attack type classifications.

---

## 📋 Tasks

### 1. Feature Importance Analysis

**Environmental Feature Importance:**
- Analyze which environmental features contribute most to predictions
- Use feature importance from Environmental Branch
- Calculate per-feature contribution to final prediction
- Rank features by importance

**Spectrogram Pattern Analysis:**
- Identify which spectrogram regions are most important
- Use attention maps or gradient-based methods (Grad-CAM)
- Visualize important regions in spectrogram
- Correlate patterns with attack types

**Attack Type Analysis:**
- Analyze which features are important for each attack type
- Identify feature patterns for:
  - Synthesis attacks
  - Conversion attacks
  - Replay attacks
  - Bonafide audio

### 2. Explanation Generation

**Explanation Components:**
1. **Prediction**: Real or Fake
2. **Confidence**: Prediction confidence score
3. **Attack Type**: Detected attack type (if fake)
4. **Environmental Reasons**: Why environmental features suggest real/fake
5. **Spectrogram Reasons**: What patterns were detected
6. **Overall Explanation**: Human-readable summary

**Explanation Format:**

**For FAKE predictions:**
```
Prediction: FAKE
Confidence: 87%
Attack Type: Synthesis

Reasons:
1. Environmental Analysis:
   - RT60 is abnormally low (0.2s) - suggests synthetic environment
   - SNR is too high (45dB) - too clean for natural recording
   - Background consistency is low - indicates artificial processing

2. Spectrogram Analysis:
   - Detected synthesis artifacts in frequency range 2-4 kHz
   - Unnatural spectral patterns in mid-frequencies
   - Missing natural reverberation characteristics

3. Overall:
   This audio appears to be AI-generated speech. The environmental
   characteristics are inconsistent with natural recordings, and
   spectrogram analysis reveals synthetic artifacts.
```

**For REAL predictions:**
```
Prediction: REAL
Confidence: 92%

Reasons:
1. Environmental Analysis:
   - RT60 is natural (0.8s) - consistent with typical room acoustics
   - SNR is typical (25dB) - normal background noise level
   - Environmental features are consistent throughout

2. Spectrogram Analysis:
   - Natural spectral patterns detected
   - Consistent reverberation characteristics
   - No synthetic artifacts found

3. Overall:
   This audio appears to be genuine human speech. Environmental
   characteristics match natural recording conditions, and no
   synthetic artifacts were detected.
```

### 3. Explanation System Implementation

**Components:**
1. **Feature Extractor**: Extract features from audio
2. **Model Predictor**: Get predictions from hybrid model
3. **Feature Analyzer**: Analyze feature contributions
4. **Explanation Generator**: Generate human-readable explanations
5. **Visualization**: Create visualizations (if needed)

**Output Format:**
- Text explanation (human-readable)
- JSON explanation (structured, for API)
- Visualization (spectrogram with highlights, feature importance plots)

---

## 📁 Output Files

```
Code/
└── explain_prediction.py                 # Main explanation script

reports/
└── explanation_examples/
    ├── fake_explanation_example.json
    ├── real_explanation_example.json
    └── explanation_visualizations/
```

---

## 🔧 Scripts Needed

### Implemented (Phase 6):
- ✅ `code/phase6/explain_prediction.py` — chunk raw audio, run Phase 4 hybrid checkpoint, produce per-file JSON + CSV explanations (log-mel + environmental)
- ✅ `code/phase6/run_phase6.py` — convenience wrapper with default laptop paths
- ✅ `code/phase6/README.md` — quick commands and options

### Optional (future):
- `code/utils/feature_importance.py` - deeper feature attributions
- `code/utils/gradcam.py` - gradient-based spectrogram highlights
- `code/utils/explanation_formatter.py` - richer formatting

### Existing (Reuse):
- ✅ `Code/features/environmental_features.py` - Feature extraction
- ✅ Trained hybrid model

---

## ✅ Success Criteria

- [x] Explanation system generates predictions with reasons
- [ ] Environmental feature contributions analyzed
- [ ] Spectrogram patterns identified (if possible)
- [x] Human-readable explanations generated (JSON/text)
- [ ] Explanations are accurate and informative (qualitative check)
- [x] System works on both real and fake audio (raw wav)
- [ ] Examples documented (to be added after first run)

---

## 🚀 Quick Commands

### Laptop / testing_audios (Trump set)
```powershell
cd E:\FYP
conda activate fassd
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_dir E:/FYP/testing_audios --output_dir reports/explanation_examples --batch_size 32 --threshold 0.5
```

### Run via wrapper (defaults to testing_audios)
```powershell
cd E:\FYP
conda activate fassd
python code/phase6/run_phase6.py
```

### (Optional) Use a single file
```powershell
python code/phase6/explain_prediction.py --ckpt models_saved/hybrid_resnet_environmental_best.pth --audio_path E:/FYP/testing_audios/trump_r1.wav --output_dir reports/explanation_examples --batch_size 32 --threshold 0.5
```

---

## 📊 Explanation Quality Metrics

**Evaluation:**
- Explanation accuracy (do reasons match actual features?)
- Explanation clarity (are explanations understandable?)
- User feedback (if possible)

**Test Cases:**
- Real audio → Should explain why it's real
- Fake audio → Should explain why it's fake
- Borderline cases → Should show uncertainty

---

## ⚠️ Challenges & Solutions

### Challenge 1: Feature Attribution
**Problem**: Determining which features contribute to prediction  
**Solution**: 
- Use gradient-based methods (integrated gradients)
- Feature importance from model
- Ablation studies

### Challenge 2: Explanation Accuracy
**Problem**: Explanations may not match actual model reasoning  
**Solution**: 
- Validate explanations with domain experts
- Test on known cases
- Iterate based on feedback

### Challenge 3: Complexity
**Problem**: Too technical explanations  
**Solution**: 
- Use simple language
- Focus on key factors
- Provide both simple and detailed explanations

---

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 5: Evaluation (need evaluated model)
- ✅ Trained hybrid model
- ✅ Feature extraction code

**Next Phase:**
- Phase 7: Domain Adaptation (if needed)
- Or: Deployment/Testing

---

## 📝 Notes

- Explanations should be **interpretable**, not just technical
- Focus on **environmental features** as core (project requirement)
- Provide both **simple** and **detailed** explanations
- Document explanation methodology
- Test explanations on diverse audio samples

---

## 🔍 Explanation System Checklist

- [ ] Feature importance analysis implemented
- [ ] Explanation generation works
- [ ] Explanations are human-readable
- [ ] Both real and fake explanations tested
- [ ] Examples documented
- [ ] System can be integrated into prediction pipeline
- [ ] Visualizations created (if applicable)

---

**Last Updated**: December 27, 2025  
**Status**: ✅ READY

