# Environmental Acoustic Detection - Implementation Plan

**Project:** Forensic Acoustic for Synthetic Speech Detector (FASSD)  
**Goal:** Detect deepfakes by analyzing environmental acoustic consistency  
**Date:** November 8, 2025

---

## 🎯 Project Objective (Clarified)

### SaaS Product Requirements:

**Input:** Audio clip from user  
**Output:** Real or AI-generated + Detailed explanation  
**Detection Method:** **Environmental acoustic analysis** (not just synthetic artifacts)

### Why Environmental Analysis?

> "AI can now mimic voices and emotions perfectly, but it CANNOT perfectly replicate:
> - Natural room acoustics
> - Consistent background environment
> - Real-world recording imperfections
> - Microphone/channel characteristics"

**This is your competitive advantage!**

---

## 🚨 Current Problem Identified

### What Went Wrong with Trump Test:

**Current Model (ResNet CNN):**
- Detects: Synthetic vocoder artifacts
- Trained on: ASVspoof studio recordings
- Works on: ASVspoof test set (2.61% EER ✅)
- Fails on: Real-world recordings (100% false positives ❌)

**Why it failed:**
- ❌ Only looks at voice synthesis artifacts
- ❌ Doesn't analyze environmental acoustics
- ❌ Trained on studio data, fails on broadcast/media audio
- ❌ No environmental consistency checking

---

## 🏗️ New Architecture Required

### Multi-Modal Detection System

```
                        Audio Input
                            │
            ┌───────────────┴────────────────┐
            │                                │
    Spectral Features            Environmental Features
    (What we have)                   (Need to build)
            │                                │
            │                                │
    ┌───────▼────────┐            ┌─────────▼──────────┐
    │  ResNet CNN    │            │   Environment      │
    │  (Synthetic    │            │   Analyzer         │
    │   Artifacts)   │            │  (Acoustics)       │
    └───────┬────────┘            └─────────┬──────────┘
            │                                │
      Synthetic Score                  Env Score
         (0-1)                            (0-1)
            │                                │
            └───────────────┬────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Fusion Model  │
                    │   (Combine)    │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  Final Output  │
                    │  + Explanation │
                    └────────────────┘
```

---

## 📋 Implementation Plan - Phase 4.3

### Module 1: Environmental Feature Extractor (Week 1)

**File:** `Code/features/environmental_features.py`

**Features to extract:**

1. **Room Acoustics:**
   ```python
   - Reverberation time (RT60)
   - Room size estimation
   - Early reflections
   - Direct-to-reverberant ratio (DRR)
   ```

2. **Background Noise Analysis:**
   ```python
   - Background noise level (SNR)
   - Noise spectral profile
   - Noise consistency across time
   - Silence detection
   ```

3. **Channel Characteristics:**
   ```python
   - Frequency response
   - Bandwidth estimation
   - Compression artifacts (MP3, AAC)
   - Microphone characteristics
   ```

4. **Temporal Consistency:**
   ```python
   - Acoustic environment stability
   - Background changes detection
   - Segment-wise consistency
   ```

**Implementation:**
```python
class EnvironmentalFeatureExtractor:
    def extract(self, audio_path):
        features = {
            'rt60': self.compute_rt60(),
            'snr': self.compute_snr(),
            'spectral_tilt': self.compute_spectral_tilt(),
            'background_consistency': self.check_background_consistency(),
            'reverb_quality': self.analyze_reverb(),
            'channel_quality': self.analyze_channel()
        }
        return features
```

---

### Module 2: Anomaly Detection System (Week 1)

**File:** `Code/models/environment_detector.py`

**Approach:** One-Class Classification or Anomaly Detection

**Strategy:**
```python
Train on: Real recordings (bonafide samples)
Learn: What "natural" environmental acoustics look like
Detect: Anything that deviates from natural patterns

Models to try:
1. Isolation Forest
2. One-Class SVM  
3. Autoencoder (reconstruction error)
4. Deep SVDD (Deep Support Vector Data Description)
```

**Why this works:**
- Don't need fake samples to train
- Learn distribution of "real" acoustic environments
- Flag anything unusual/synthetic/too clean

---

### Module 3: Combined Detection System (Week 2)

**File:** `Code/models/hybrid_detector.py`

**Combines:**
1. **Synthetic Detector** (existing ResNet CNN)
   - Score: Probability of synthetic artifacts
   
2. **Environmental Detector** (new)
   - Score: Probability of unnatural acoustics
   
3. **Fusion Logic:**
   ```python
   if synthetic_score > 0.8:
       return "FAKE", "High synthetic artifact score"
   elif env_score > 0.7:
       return "FAKE", "Unnatural environmental acoustics"
   elif synthetic_score > 0.6 and env_score > 0.5:
       return "FAKE", "Both indicators suggest fake"
   else:
       return "REAL", "Natural voice and environment"
   ```

---

### Module 4: Explainable AI Component (Week 2)

**File:** `Code/utils/explainer.py`

**Provides detailed reasoning:**

```python
class DetectionExplainer:
    def explain(self, audio, prediction):
        report = {
            "prediction": "FAKE",
            "overall_confidence": 0.92,
            "indicators": [
                {
                    "feature": "Room Acoustics",
                    "status": "SUSPICIOUS",
                    "score": 0.85,
                    "explanation": "No natural reverberation detected. Audio appears too clean for claimed environment."
                },
                {
                    "feature": "Background Noise",
                    "status": "SUSPICIOUS", 
                    "score": 0.78,
                    "explanation": "Unnatural silence. Real recordings typically have ambient noise."
                },
                {
                    "feature": "Synthetic Artifacts",
                    "status": "OK",
                    "score": 0.32,
                    "explanation": "No obvious TTS artifacts detected."
                }
            ]
        }
        return report
```

---

## 📊 Implementation Timeline

### Week 1: Environmental Feature Extraction

**Days 1-2:** Research & Design
- Research environmental acoustic features
- Design feature extraction pipeline
- Create test cases

**Days 3-5:** Implementation
- Build `environmental_features.py`
- Extract features from ASVspoof dataset
- Validate feature quality

**Days 6-7:** Testing
- Test on ASVspoof bonafide samples
- Verify features make sense
- Document feature distributions

---

### Week 2: Anomaly Detection Training

**Days 1-3:** Model Development
- Implement anomaly detection models
- Train on bonafide environmental features
- Validate on held-out bonafide data

**Days 4-5:** Integration
- Combine with existing ResNet CNN
- Build fusion module
- Create unified inference pipeline

**Days 6-7:** Testing & Tuning
- Test on ASVspoof spoof samples
- Test on real-world recordings (Trump)
- Tune decision thresholds

---

### Week 3: Explainability & Polish

**Days 1-3:** Explainer Development
- Build explanation generator
- Map features to human-readable reasons
- Create detailed reports

**Days 4-5:** End-to-End Testing
- Test complete system
- Validate on diverse audio sources
- Benchmark performance

**Days 6-7:** Documentation
- Document all features
- Write usage guides
- Prepare for web integration

---

## 🎯 Expected Performance

### Target Metrics:

| Test Scenario | Current Model | Target with Env Detection |
|---------------|---------------|---------------------------|
| ASVspoof synthetic | 2.61% EER ✅ | 2-3% EER ✅ |
| Real-world broadcast | 100% FP ❌ | < 5% FP ✅ |
| Studio recordings | 0.57% EER ✅ | 1-2% EER ✅ |
| **Trump recordings** | **100% FP** ❌ | **Correct detection** ✅ |

---

## 📁 File Structure (Cleaned)

### Keep (Essential):
```
E:\FYP\
├── Code\
│   ├── models\
│   │   ├── baseline_cnn.py
│   │   └── resnet_cnn.py
│   ├── train_baseline.py
│   ├── train_resnet.py
│   ├── evaluate_model.py
│   └── test_audio_simple.py
├── models_saved\
│   └── resnet_cnn_mel_robust.pth (2.8M params, 2.61% EER)
└── reports\
    ├── PHASE4_1_RESULTS.md
    ├── PHASE4_2_RESULTS.md
    └── ROADMAP.md
```

### Build (New):
```
E:\FYP\
├── Code\
│   ├── features\
│   │   └── environmental_features.py    # NEW - Extract env features
│   ├── models\
│   │   ├── environment_detector.py      # NEW - Anomaly detection
│   │   └── hybrid_detector.py           # NEW - Combined system
│   ├── utils\
│   │   └── explainer.py                 # NEW - Generate explanations
│   ├── train_environment_detector.py    # NEW - Train env model
│   └── predict_hybrid.py                # NEW - Full system inference
└── reports\
    └── ENVIRONMENTAL_DETECTION_PLAN.md  # This file
```

---

## 🚀 Phase 4.3 Roadmap

### Milestone 1: Feature Extraction ✅
**Deliverable:** Working environmental feature extractor  
**Test:** Extract features from 100 samples, verify they make sense  
**Files:** `environmental_features.py`

### Milestone 2: Anomaly Detector 🔄
**Deliverable:** Trained environmental anomaly detector  
**Test:** Achieves >90% detection on ASVspoof  
**Files:** `environment_detector.py`, `train_environment_detector.py`

### Milestone 3: Hybrid System 🔄
**Deliverable:** Combined synthetic + environmental detection  
**Test:** Works on both ASVspoof and real-world audio  
**Files:** `hybrid_detector.py`, `predict_hybrid.py`

### Milestone 4: Explainability 🔄
**Deliverable:** Detailed explanations for predictions  
**Test:** Clear, understandable reasons for each decision  
**Files:** `explainer.py`

### Milestone 5: Trump Test Pass 🔄
**Deliverable:** Correctly classifies Trump audio files  
**Test:** 6 real detected as real, 2 fake detected as fake  
**Success Criteria:** >80% accuracy on Trump test set

---

## 📊 Success Criteria

Phase 4.3 is successful when:

1. ✅ Environmental features extracted from audio
2. ✅ Anomaly detector trained on bonafide samples
3. ✅ Hybrid system combines synthetic + environmental detection
4. ✅ **Trump test passes** (6 real → REAL, 2 fake → FAKE)
5. ✅ Explainable outputs generated
6. ✅ System works on diverse audio sources

---

## 🎓 Technical Approach

### Environmental Features (Python Libraries)

```python
import librosa          # Audio analysis
import scipy.signal     # Signal processing
import pyroomacoustics  # Room acoustics (RT60)
import noisereduce      # Noise analysis
```

### Key Features to Implement:

1. **RT60 (Reverberation Time)**
```python
def compute_rt60(audio, sr):
    # Measure how long sound takes to decay
    # Real rooms: 0.2-2.0 seconds
    # Synthetic: Often 0 or unnatural
```

2. **SNR (Signal-to-Noise Ratio)**
```python
def compute_snr(audio):
    # Real recordings: 15-40 dB
    # AI-generated: Often >50 dB (too clean)
```

3. **Spectral Tilt**
```python
def compute_spectral_tilt(audio):
    # Natural voices have characteristic frequency roll-off
    # Synthetic may lack natural tilt
```

4. **Background Consistency**
```python
def check_background_consistency(audio):
    # Real audio: Consistent background throughout
    # Edited/fake: Inconsistent or too perfect
```

---

## 💡 Research Insights

### Why Environmental Detection Works:

**AI Voice Generators (ElevenLabs, etc.):**
1. Generate clean audio (no background noise)
2. No natural room acoustics
3. Perfect signal-to-noise ratio
4. Studio-quality output

**Real Recordings:**
1. Always have some background noise
2. Room reverberation present
3. Microphone imperfections
4. Environmental consistency

**Detection Strategy:**
- If audio is "too perfect" → Likely AI-generated
- If environment inconsistent → Likely edited/fake
- If natural imperfections present → Likely real

---

## 📋 Detailed Implementation Steps

### Step 1: Environmental Feature Engineering (3-4 days)

**File:** `Code/features/environmental_features.py`

**Tasks:**
1. Implement RT60 computation
2. Implement SNR analysis
3. Implement spectral tilt
4. Implement background consistency check
5. Create feature vector (10-20 dimensions)
6. Test on sample audio files

**Output:** Feature extraction working on any audio file

---

### Step 2: Feature Analysis (2-3 days)

**Tasks:**
1. Extract environmental features from ASVspoof bonafide samples
2. Extract from ASVspoof spoof samples
3. Analyze feature distributions
4. Identify discriminative features
5. Document findings

**Output:** Understanding which features separate real from fake

---

### Step 3: Anomaly Detector Training (3-4 days)

**File:** `Code/models/environment_detector.py`

**Approach:** One-Class SVM or Isolation Forest

**Training:**
```python
# Train on ONLY bonafide samples
bonafide_features = extract_env_features(bonafide_audios)
detector = IsolationForest()
detector.fit(bonafide_features)

# Test
test_features = extract_env_features(test_audio)
anomaly_score = detector.score_samples(test_features)
# High score = normal (real)
# Low score = anomaly (fake/synthetic)
```

**Output:** Trained anomaly detector model

---

### Step 4: Hybrid System Integration (2-3 days)

**File:** `Code/models/hybrid_detector.py`

**Logic:**
```python
def predict_hybrid(audio):
    # 1. Synthetic detection (existing ResNet)
    synthetic_score = resnet_model(audio)
    
    # 2. Environmental detection (new)
    env_features = extract_env_features(audio)
    env_score = anomaly_detector.score(env_features)
    
    # 3. Fusion decision
    if synthetic_score > 0.8:
        return "FAKE", "High synthetic artifacts"
    elif env_score < -0.5:  # Anomaly
        return "FAKE", "Unnatural acoustics"
    elif is_too_clean(env_features):
        return "FAKE", "Suspiciously clean audio"
    else:
        return "REAL", "Natural voice and environment"
```

**Output:** Working hybrid detection system

---

### Step 5: Explainability (2 days)

**File:** `Code/utils/explainer.py`

**Generate detailed reports:**
```json
{
    "prediction": "FAKE",
    "confidence": 0.87,
    "timestamp": "2025-11-08 18:30:00",
    "analysis": {
        "synthetic_artifacts": {
            "score": 0.45,
            "status": "OK",
            "explanation": "No obvious TTS artifacts"
        },
        "room_acoustics": {
            "score": 0.92,
            "status": "SUSPICIOUS",
            "explanation": "No natural reverberation. Audio too clean for casual recording."
        },
        "background_noise": {
            "score": 0.88,
            "status": "SUSPICIOUS",
            "explanation": "Missing ambient noise. Real recordings have background sound."
        },
        "overall": "Audio characteristics suggest AI generation"
    }
}
```

---

### Step 6: Trump Test Validation (1-2 days)

**Goal:** Correctly classify your 8 Trump audio files

**Process:**
1. Run hybrid detector on Trump audios
2. Analyze environmental features
3. Adjust thresholds if needed
4. Validate explanations make sense

**Success:** 6/8 real detected as real, 2/8 fake detected as fake

---

## 🎯 Quick Win: Immediate Features to Check

### Simple Environmental Checks (Can implement today!)

```python
def quick_env_check(audio_path):
    y, sr = librosa.load(audio_path)
    
    # 1. Check if audio is "too clean" (suspiciously high SNR)
    # 2. Check for presence of room tone
    # 3. Check spectral characteristics
    # 4. Check for natural background noise
    
    # Real audio usually fails "too clean" test
    # AI audio often passes "too clean" test (suspicious!)
```

---

## 💰 For SaaS Product

### User Flow:

1. **Upload Audio** → Web interface
2. **Processing** → Extract features (5-10 seconds)
3. **Analysis** → Run both detectors
4. **Results** → Show:
   - ✅ Prediction (Real/Fake)
   - ✅ Confidence score
   - ✅ Detailed breakdown
   - ✅ Visual indicators (graphs)
   - ✅ Explanation in plain English

### Example Output for User:

```
🟢 REAL AUDIO (87% Confidence)

Analysis Breakdown:
✅ Natural room acoustics detected
✅ Consistent background environment
✅ Realistic recording characteristics
⚠️ Slight compression artifacts (normal for MP3)

Conclusion: This appears to be a genuine recording.
```

---

## 🚀 Next Steps - Start Implementation

### Today: Create Environmental Feature Extractor

**I'll build:**
1. `environmental_features.py` - Feature extraction
2. Test on your Trump audios
3. Show you what features look like for real vs fake

**Then:**
- Train anomaly detector
- Integrate with ResNet CNN
- Create hybrid system
- Fix Trump test

---

## ✅ Action Plan Summary

| Task | Duration | Deliverable |
|------|----------|-------------|
| 1. Env feature extraction | 3-4 days | Working feature extractor |
| 2. Feature analysis | 2-3 days | Feature distribution study |
| 3. Anomaly detector | 3-4 days | Trained env detector |
| 4. Hybrid integration | 2-3 days | Combined system |
| 5. Explainability | 2 days | Report generator |
| 6. Trump validation | 1-2 days | Passing test |
| **TOTAL** | **~2-3 weeks** | **Production system** |

---

## 🎓 Thesis Contribution

This approach is **novel** because:

1. ✅ Most deepfake detectors only look at synthetic artifacts
2. ✅ Environmental analysis is underexplored
3. ✅ Hybrid approach combines both signals
4. ✅ Explainable AI makes it practical
5. ✅ Works on real-world audio (not just datasets)

**This could be a strong research contribution!**

---

## 🚀 Ready to Start?

I'll begin implementing the environmental feature extractor. This is the foundation for everything else.

**Should I start building Module 1: Environmental Feature Extractor?** 🎯

