# Phase 4.3: Environmental Feature Detection

**Duration**: Week 6-8  
**Status**: ⚠️ Partial - Domain Mismatch Discovered

## What We Did

1. **Built Environmental Feature Extractor**
   - RT60 (reverberation time)
   - SNR (signal-to-noise ratio)
   - Spectral characteristics
   - Background noise analysis
   - 12 environmental features total

2. **Tried Anomaly Detection**
   - Isolation Forest trained on real audio only
   - **Result**: 24.5% accuracy (poor)

3. **Switched to Supervised Learning**
   - Random Forest trained on both real and fake
   - **Result**: 81.69% accuracy on ASVspoof

4. **Real-World Testing**
   - Tested on Trump audio (broadcast/processed)
   - **Result**: Complete failure - cannot distinguish real vs fake

## Critical Discovery

❌ **Domain Mismatch Problem**:
- Models work on ASVspoof (studio recordings)
- Fail on real-world audio (broadcast/processed)
- Environmental features overlap between real and fake after processing

## Results

✅ Environmental feature extractor working  
✅ Works on ASVspoof (81.69% accuracy)  
❌ Fails on real-world audio (domain mismatch)

## Files Created

- `Code/features/environmental_features.py`
- `Code/train_environment_classifier.py`
- `Code/predict_hybrid.py`
- Model: `models_saved/environment_classifier.pkl`
- Reports: Multiple analysis documents

