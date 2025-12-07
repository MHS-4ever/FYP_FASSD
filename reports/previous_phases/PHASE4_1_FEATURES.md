# Phase 4.1: Feature Comparison (Mel vs LFCC)

**Duration**: Week 4-5  
**Status**: ✅ Complete

## What We Did

1. **Switched from LFCC to Log-Mel Spectrograms**
   - Mel features better for speech tasks
   - 64 frequency bins vs 20 coefficients

2. **Trained New Models**
   - Clean model: 8.57% EER
   - Robust model: 15.25% EER

## Results

✅ Mel features outperform LFCC (15.25% vs 15.71% EER)  
✅ Identified best feature type for future work  
✅ Models: `baseline_cnn_mel.pth`, `baseline_cnn_mel_robust.pth`

## Files Created

- Models trained with Mel features
- `reports/PHASE4_1_RESULTS.md`

