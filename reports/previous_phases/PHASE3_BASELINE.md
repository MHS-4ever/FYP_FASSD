# Phase 3: Baseline Model Training

**Duration**: Week 3-4  
**Status**: ✅ Complete

## What We Did

1. **Built LCNN Baseline Model**
   - Lightweight Convolutional Neural Network
   - ~5,000 parameters
   - Trained on LFCC features

2. **Fixed Critical Bugs**
   - Class weight bug (model was learning wrong)
   - Unicode console issues
   - Data loading problems

3. **Trained and Evaluated**
   - Clean data: 9.68% EER
   - Augmented data: 15.71% EER

## Results

✅ Baseline model working  
✅ Identified Mel features as better than LFCC  
✅ Established baseline for comparison

## Files Created

- `Code/models/baseline_cnn.py`
- `Code/train_baseline.py`
- `Code/evaluate_model.py`
- Models: `baseline_cnn_lfcc.pth`, `baseline_cnn_lfcc_robust.pth`

