# Complete Project Story: FASSD - Forensic Acoustic Synthetic Speech Detector

**Project Goal**: Build a system that detects AI-generated (fake) audio by analyzing environmental acoustics, not just synthetic artifacts.

**Current Status**: Models work well on training data but fail on real-world audio due to domain mismatch.

---

## 📋 Executive Summary (Simple Version)

### The Real Goal

Build a **generalized model** that works on **ANY audio** from **ANY voice**, not just training data. The model should detect real vs fake for any speaker, any recording condition.

### What We Did

- Processed 400GB+ of audio data (800,000+ files)
- Built 2 types of models (ResNet CNN + Environmental Classifier)
- Trained on **only 2 out of 3 datasets** (ASVspoof_LA + DF, missing PA)
- Tested on ASVspoof dataset (works well)
- Tested on real-world audio (complete failure)

### What Works

- ✅ Models work perfectly on ASVspoof dataset (2.61% error rate)
- ✅ Feature extraction pipeline works
- ✅ Data augmentation system works

### What Doesn't Work

- ❌ **Not using all three datasets** (missing ASVspoof_PA for replay attacks)
- ❌ **No speaker-independent evaluation** (same speakers in train/test)
- ❌ **No generalization strategy** (model only works on training data)
- ❌ Models fail on real-world broadcast audio
- ❌ Cannot distinguish real from fake in processed audio
- ❌ Domain mismatch problem

### Why It Failed

1. **Missing Dataset**: Only used 2 out of 3 ASVspoof datasets (missing PA)
2. **No Generalization**: Model learns patterns specific to training data
3. **Speaker Overlap**: Same speakers in train and test (not true generalization)
4. **Domain Mismatch**: Trained on studio recordings, tested on broadcast audio
5. **No Proper Pipeline**: No strategy for building a generalized model

### What's Needed

1. **Use all three datasets** (LA + DF + PA)
2. **Speaker-independent split** (no speaker overlap between train/test)
3. **Multi-task learning** (detect all attack types: synthesis, conversion, replay)
4. **Cross-domain evaluation** (test on real-world audio)
5. **Domain adaptation** (fine-tune on real-world data if needed)

**Bottom Line**: We built models that work on training data, but we don't have a proper pipeline for building a **generalized model** that works on any audio. We need to start over with a proper generalization strategy.

---

## 📖 The Complete Story

### What We Wanted to Build

A SaaS product that:

- Takes an audio file as input
- Analyzes environmental acoustic features (room acoustics, background noise, etc.)
- Determines if the audio is REAL (human) or FAKE (AI-generated)
- Provides a detailed explanation of WHY it's real or fake

**Key Idea**: AI can mimic voices perfectly, but it struggles to replicate natural environmental acoustics (room reverb, background noise, microphone characteristics, etc.)

---

## 🎯 Phase 1: Setting Up the Foundation (Week 1-2)

### What We Did

1. **Set up the environment**

   - Installed Python, PyTorch, CUDA for GPU
   - Set up conda environment
   - Configured RTX 3050 GPU

2. **Got the dataset**

   - ASVspoof 2021 dataset (400GB+)
   - 181,566 real audio files
   - 611,829 fake audio files
   - Total: ~800,000 audio files

3. **Extracted features**
   - LFCC (Linear Frequency Cepstral Coefficients) - 20 features
   - Log-Mel Spectrograms - 64 features
   - Saved features as .npy files, then packed into HDF5 for efficiency

**Why**: Features are easier for models to learn from than raw audio.

**Result**: ✅ Successfully extracted features from all audio files

---

## 🎯 Phase 2: Data Augmentation (Week 2-3)

### What We Did

Added variations to training data to make models more robust:

- Added background noise (MUSAN dataset)
- Added room reverb (RIR - Room Impulse Response)
- Simulated codec compression (downsample/upsample)
- Random gain and clipping

**Why**: Real-world audio has noise, reverb, compression. Training on clean studio data only makes models fail on real-world audio.

**Result**: ✅ Created augmented dataset with 611,829 additional samples

---

## 🎯 Phase 3: Baseline Model Training (Week 3-4)

### What We Did

1. **Built a simple CNN model (LCNN)**

   - Lightweight Convolutional Neural Network
   - Small model (~5,000 parameters)
   - Trained on LFCC features

2. **Fixed critical bugs**

   - Class weight bug (model was learning wrong)
   - Unicode console issues
   - Data loading problems

3. **Trained and evaluated**
   - Trained on clean data: 9.68% error rate
   - Trained on augmented data: 15.71% error rate
   - Tested on both clean and augmented test sets

**Why**: Start simple, then improve. Baseline gives us something to compare against.

**Result**: ✅ Baseline model works, but error rate is high (15.71%)

---

## 🎯 Phase 4.1: Trying Better Features (Week 4-5)

### What We Did

1. **Switched from LFCC to Log-Mel Spectrograms**

   - Mel features are better for speech tasks
   - 64 frequency bins instead of 20 coefficients

2. **Trained new models**
   - Clean model: 8.57% error rate (better!)
   - Robust model: 15.25% error rate (slightly better than LFCC)

**Why**: Different features capture different information. Mel spectrograms are better for speech.

**Result**: ✅ Mel features are better than LFCC (15.25% vs 15.71% error rate)

---

## 🎯 Phase 4.2: Building a Deeper Model (Week 5-6)

### What We Did

1. **Built Deep ResNet CNN**

   - Much deeper network (8 residual blocks)
   - 2.8 million parameters (vs 5,000 in baseline)
   - Skip connections (ResNet architecture)

2. **Trained with optimizations**

   - Mixed precision training (faster)
   - Quick evaluation during training (saves time)
   - Class weighting for imbalanced data

3. **Results**
   - Clean test: 0.57% error rate ⭐ (EXCELLENT!)
   - Augmented test: 2.61% error rate ⭐ (EXCELLENT!)
   - 83% improvement over baseline!

**Why**: Deeper models can learn more complex patterns. ResNet architecture prevents overfitting.

**Result**: ✅ **OUTSTANDING SUCCESS** - Model works perfectly on ASVspoof dataset

---

## 🚨 Phase 4.3: The Big Problem Discovered (Week 6-7)

### What Happened

**We tested on real-world audio (Trump recordings)**:

- 6 real audio files
- 2 fake audio files
- **Result: ALL 8 predicted as FAKE (100% wrong!)**

### Why This Happened

1. **Domain Mismatch**

   - Model trained on: ASVspoof studio recordings (clean, controlled)
   - Tested on: Broadcast/processed audio (compressed, noisy, different characteristics)
   - Model learned patterns specific to ASVspoof, not general audio

2. **What the Model Learned**

   - ResNet CNN: Detects synthetic vocoder artifacts (works on ASVspoof)
   - Doesn't analyze: Environmental acoustics (room, background, etc.)
   - Fails on: Real-world processed audio (looks "synthetic" to the model)

3. **The Real Problem**
   - Project goal: Detect fakes using **environmental acoustics**
   - What we built: Detects fakes using **synthetic artifacts**
   - These are different things!

**Result**: ❌ Model fails completely on real-world audio

---

## 🎯 Phase 4.3: Building Environmental Detector (Week 7-8)

### What We Did

1. **Built Environmental Feature Extractor**

   - RT60 (reverberation time)
   - SNR (signal-to-noise ratio)
   - Spectral characteristics
   - Background noise analysis
   - "Too clean" detection
   - 12 environmental features total

2. **Tried Anomaly Detection**

   - Train on real audio only
   - Learn what "normal" looks like
   - Flag anything unusual as fake
   - **Result**: 25% accuracy (terrible)

3. **Switched to Supervised Learning**
   - Train on BOTH real and fake audio
   - Learn differences between them
   - **Result**: 81.69% accuracy on ASVspoof test set ✅

**Why**: Environmental features should capture room acoustics, background noise, etc. that AI struggles to replicate.

**Result**: ✅ Works on ASVspoof (81.69%), but still fails on real-world audio

---

## 🚨 The Final Problem: Domain Mismatch

### What We Discovered

**Environmental Classifier Results on Trump Audio**:

- Real audio scores: 0.500 - 0.746 (mean: 0.660)
- Fake audio scores: 0.669 - 0.674 (mean: 0.672)
- **Scores are nearly identical!**

### Why This Happens

1. **Broadcast Processing**

   - Real broadcast audio is heavily processed (compression, EQ, noise reduction)
   - This makes it look "unnatural" to models trained on clean studio data
   - Environmental features become similar to synthetic audio

2. **AI-Generated Audio**

   - Modern AI can add realistic processing
   - Can simulate broadcast characteristics
   - Can mimic compression artifacts

3. **Feature Overlap**
   - After processing, real and fake audio have similar:
     - Spectral characteristics
     - Environmental features
     - Acoustic properties
   - Model trained on studio data can't distinguish them

**Result**: ❌ Cannot distinguish real from fake broadcast audio

---

## 📊 Summary: What Works and What Doesn't

### ✅ What Works

1. **ResNet CNN on ASVspoof**

   - 0.57% error rate on clean test
   - 2.61% error rate on augmented test
   - Excellent performance on training data

2. **Environmental Classifier on ASVspoof**

   - 81.69% accuracy on test set
   - Good discrimination between real and fake studio recordings

3. **Feature Extraction Pipeline**

   - Successfully extracts features from 800,000+ audio files
   - Efficient HDF5 storage system

4. **Data Augmentation**
   - Creates diverse training data
   - Improves model robustness

### ❌ What Doesn't Work

1. **Real-World Audio Detection**

   - ResNet CNN: 100% false positives (all real audio predicted as fake)
   - Environmental Classifier: Cannot distinguish real from fake broadcast audio
   - Scores overlap completely (0.660 vs 0.672)

2. **Domain Generalization**

   - Models trained on studio data don't work on broadcast/processed audio
   - Different recording conditions, processing, compression

3. **Environmental Analysis for Broadcast Audio**
   - Broadcast processing makes real audio look synthetic
   - AI can simulate broadcast characteristics
   - Features trained on studio data don't transfer

---

## 🎯 What Was the Original Plan?

### Project Scope

**Goal**: Build a system that detects AI-generated audio by analyzing environmental acoustics.

**Method**:

- Extract environmental features (room acoustics, background noise, etc.)
- Train model to detect unnatural environmental patterns
- Provide explanations based on environmental analysis

**Why This Approach**:

- AI can mimic voices perfectly
- AI struggles to replicate natural environmental acoustics
- This is the competitive advantage

### What We Actually Built

1. **Synthetic Artifact Detector (ResNet CNN)**

   - Detects vocoder artifacts in spectrograms
   - Works on ASVspoof studio recordings
   - Fails on real-world processed audio

2. **Environmental Feature Extractor**

   - Extracts 12 environmental features
   - Works on ASVspoof studio recordings
   - Fails on real-world broadcast audio

3. **Hybrid System**
   - Combines both approaches
   - Still fails on real-world audio

---

## 🔍 Why Did We Fail?

### Root Cause: Domain Mismatch

**Training Data**: ASVspoof studio recordings

- Clean, controlled environment
- High-quality audio
- Consistent recording conditions

**Test Data**: Real-world broadcast audio

- Heavily processed (compression, EQ, noise reduction)
- Different acoustic environments
- Transmission artifacts
- Different processing pipelines

**The Problem**: Models learn patterns specific to training data. When test data is different, models fail.

### Specific Issues

1. **ResNet CNN**

   - Learned to detect synthetic vocoder artifacts
   - Real broadcast audio (after processing) looks "synthetic"
   - Result: All real audio predicted as fake

2. **Environmental Classifier**
   - Learned environmental patterns from studio recordings
   - Broadcast audio has different environmental characteristics
   - Real and fake broadcast audio look similar after processing
   - Result: Cannot distinguish them

---

## 💡 What We Learned

### Technical Lessons

1. **Domain Mismatch is Critical**

   - Models trained on one domain don't work on another
   - Need diverse training data from the start

2. **Feature Engineering Matters**

   - Different features capture different information
   - Need features specific to the target domain

3. **Model Architecture Helps**

   - Deeper models (ResNet) perform better
   - But architecture alone can't solve domain mismatch

4. **Data Augmentation is Important**
   - Helps with robustness
   - But doesn't solve fundamental domain differences

### Project Lessons

1. **Scope Clarification Needed Earlier**

   - Should have clarified "environmental analysis" vs "synthetic artifact detection"
   - Should have tested on real-world audio earlier

2. **Data Collection is Critical**

   - Need diverse real-world data from the start
   - 400GB of ASVspoof data isn't enough if it's all studio recordings

3. **Testing Strategy**
   - Should test on target domain early
   - Don't wait until the end

---

## 🛠️ What Needs to Be Done

### Immediate Solutions (Temporary)

1. **Use Threshold 0.75**

   - For broadcast audio, use higher threshold
   - Gets 75% accuracy by predicting all as REAL
   - **Limitation**: Can't detect fake samples

2. **Document Limitations**
   - Clearly state: Works on studio recordings, not broadcast
   - Explain domain mismatch issue

### Real Solutions (Long-Term)

1. **Collect Diverse Real-World Data**

   - Broadcast recordings (TV, radio)
   - Podcasts
   - Phone calls
   - Social media audio
   - Video calls
   - Need 10,000+ samples of each type

2. **Retrain Models**

   - Include 50% real-world data in training
   - Mix with ASVspoof data
   - Expected: Better generalization

3. **Feature Engineering**

   - Add broadcast-specific features
   - Compression artifact detection
   - Codec identification
   - Processing chain analysis

4. **Domain Adaptation**
   - Fine-tune on real-world data
   - Use transfer learning techniques
   - Implement domain adaptation methods

---

## 📈 Current Performance Summary

### ASVspoof Dataset (Training Domain)

| Model                    | Clean Test | Augmented Test | Status       |
| ------------------------ | ---------- | -------------- | ------------ |
| ResNet CNN               | 0.57% EER  | 2.61% EER      | ✅ Excellent |
| Environmental Classifier | 81.69% Acc | -              | ✅ Good      |

### Real-World Audio (Target Domain)

| Model                    | Accuracy                        | Status              |
| ------------------------ | ------------------------------- | ------------------- |
| ResNet CNN               | 0% (all predicted as fake)      | ❌ Complete failure |
| Environmental Classifier | 25-75% (depending on threshold) | ⚠️ Poor             |
| Hybrid System            | 0-75% (depending on threshold)  | ⚠️ Poor             |

**Note**: 75% accuracy is misleading - it works by predicting all as REAL, which happens to be correct for 6/8 samples.

---

## 🎓 For Your FYP Report

### What to Include

1. **What You Built**

   - ResNet CNN: Excellent on ASVspoof (2.61% EER)
   - Environmental Classifier: Good on ASVspoof (81.69% accuracy)
   - Feature extraction pipeline: Works perfectly
   - Data augmentation system: Improves robustness

2. **What You Learned**

   - Domain mismatch is a critical problem
   - Models need diverse training data
   - Testing on target domain early is important
   - Feature engineering matters

3. **Challenges Faced**

   - Domain mismatch between training and test data
   - Real-world audio has different characteristics
   - Broadcast processing makes real audio look synthetic
   - Need diverse real-world training data

4. **Future Work**

   - Collect diverse real-world audio dataset
   - Retrain models with mixed data
   - Add broadcast-specific features
   - Implement domain adaptation techniques

5. **Contributions**
   - Built working models for ASVspoof dataset
   - Identified domain mismatch problem
   - Analyzed why models fail on real-world audio
   - Provided path forward for future work

---

## 📝 Simple Summary

### What We Did

1. Set up environment and got 400GB dataset ✅
2. Extracted features from all audio files ✅
3. Built data augmentation system ✅
4. Trained baseline model ✅
5. Improved to ResNet CNN (excellent on ASVspoof) ✅
6. Built environmental feature extractor ✅
7. Trained environmental classifier ✅
8. Tested on real-world audio ❌

### What Works

- Everything works perfectly on ASVspoof dataset
- ResNet CNN: 2.61% error rate
- Environmental Classifier: 81.69% accuracy

### What Doesn't Work

- Real-world broadcast audio detection
- Models fail due to domain mismatch
- Real and fake broadcast audio look similar after processing

### Why It Failed

- Trained on studio recordings (ASVspoof)
- Tested on broadcast/processed audio (different domain)
- Models learned patterns specific to training data
- Need diverse real-world training data

### What's Needed

- Collect diverse real-world audio (broadcast, podcasts, phone calls, etc.)
- Retrain models with mixed data (50% real-world + 50% ASVspoof)
- Add broadcast-specific features
- Implement domain adaptation

---

## 🎯 Conclusion

**We built excellent models that work perfectly on the training data (ASVspoof), but they fail on real-world audio due to domain mismatch.**

This is a common problem in machine learning - models need to be trained on data similar to what they'll encounter in production.

**The work is not wasted** - we have:

- Working models for ASVspoof dataset
- Complete feature extraction pipeline
- Understanding of the problem
- Clear path forward

**Next step**: Collect diverse real-world audio and retrain models.

---

---

## 🎯 The Real Goal (Clarified)

### What We Actually Need to Build

A **generalized model** that:

1. Works on **ANY audio** from **ANY voice**
2. Detects real vs fake for **unseen speakers**
3. Works on **different recording conditions** (broadcast, phone, studio, etc.)
4. Uses **all three ASVspoof datasets** (LA + DF + PA)
5. Provides explanations for predictions

### What We Have Now

- ✅ Models that work on ASVspoof dataset (2.61% EER)
- ❌ **Only using 2 out of 3 datasets** (missing PA for replay attacks)
- ❌ **No speaker-independent evaluation** (same speakers in train/test)
- ❌ **No generalization strategy** (model only works on training data)
- ❌ Models fail on real-world audio (100% false positives)

### What We Need to Do

1. **Use all three datasets** (LA + DF + PA)
2. **Speaker-independent split** (no speaker overlap)
3. **Multi-task learning** (detect all attack types)
4. **Cross-domain evaluation** (test on real-world audio)
5. **Domain adaptation** (fine-tune if needed)

**See**: `reports/GENERALIZED_MODEL_PLAN.md` for the complete plan.

---

**End of Complete Project Story**
