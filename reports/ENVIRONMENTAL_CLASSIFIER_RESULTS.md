# Environmental Classifier Training Results

## Summary

The supervised environmental classifier was trained on 40,000 samples (20,000 real + 20,000 fake) and shows **significantly better performance** than the anomaly detection approach.

## Performance Metrics

### Test Set (ASVspoof Data)
- **Accuracy**: 81.69% ✅ (vs 25% with anomaly detection)
- **AUC-ROC**: 0.910 ✅ (excellent discrimination)
- **Precision (Fake)**: 77.7%
- **Recall (Fake)**: 88.8%

### Confusion Matrix (Test Set)
- **True Negatives** (Real → Real): 2,982
- **False Positives** (Real → Fake): 1,018 (12.7%)
- **False Negatives** (Fake → Real): 447 (5.6%)
- **True Positives** (Fake → Fake): 3,553

### Trump Audio Test
- **Accuracy**: 37.5% (3/8 correct) ⚠️
- **Results**:
  - ✅ Both fake audios correctly detected
  - ✅ 1 real audio correctly identified
  - ❌ 5 real audios incorrectly flagged as fake

## Key Findings

### 1. Supervised Learning Works Much Better
- **81.69% accuracy** vs 25% with anomaly detection
- **0.910 AUC-ROC** indicates excellent discrimination
- Model successfully learns patterns distinguishing real from fake

### 2. Feature Importance
Top discriminative features:
1. **high_freq_content** (21.19%) - AI struggles with high-frequency details
2. **spectral_tilt** (18.30%) - Natural speech has characteristic spectral slope
3. **spectral_flatness** (11.22%) - Real audio has more spectral variation
4. **spectral_rolloff** (10.29%) - Frequency content distribution
5. **snr** (8.92%) - Signal-to-noise ratio

### 3. Domain Mismatch Issue
- **Test set (ASVspoof)**: 81.69% accuracy ✅
- **Trump audios (real-world)**: 37.5% accuracy ⚠️

**Root Cause**: Trump audios are broadcast/processed audio with different characteristics than ASVspoof training data:
- Different recording conditions
- Different processing pipelines
- Different acoustic environments
- May have compression/encoding artifacts

## Comparison: Anomaly Detection vs Supervised Learning

| Metric | Anomaly Detection | Supervised Classifier |
|--------|------------------|----------------------|
| Test Accuracy | 25.7% | **81.69%** ✅ |
| AUC-ROC | ~0.6 (estimated) | **0.910** ✅ |
| Trump Accuracy | 25.0% | 37.5% |
| Training Data | Real only | Real + Fake |
| Approach | Learn "normal" | Learn differences |

## Recommendations

### 1. Build Hybrid System (CRITICAL)
Combine environmental classifier with ResNet CNN:
- **Environmental Classifier**: Catches environmental anomalies (81.69% on ASVspoof)
- **ResNet CNN**: Catches synthetic artifacts in spectrograms
- **Fusion**: Weighted combination for final decision

**Expected Benefits**:
- ResNet CNN may handle domain mismatch better
- Environmental features provide complementary information
- Combined system should be more robust

### 2. Address Domain Mismatch
Options:
- **Add diverse training data**: Include broadcast/processed audio in training
- **Domain adaptation**: Fine-tune on real-world audio
- **Feature engineering**: Add features specific to broadcast audio
- **Data augmentation**: Simulate broadcast processing during training

### 3. Threshold Tuning
For Trump audios, the model is too sensitive (flagging real as fake). Consider:
- Adjusting decision threshold (currently 0.5)
- Using confidence scores in hybrid system
- Implementing adaptive thresholds based on audio characteristics

## Next Steps

1. **Build Hybrid Detector** (`Code/predict_hybrid.py`):
   - Load both models (environmental classifier + ResNet CNN)
   - Extract features from both
   - Combine scores with weighted fusion
   - Test on Trump audios

2. **Evaluate Hybrid System**:
   - Test on ASVspoof validation set
   - Test on Trump audios
   - Compare with individual models

3. **Optimize Fusion Weights**:
   - Tune weights for best performance
   - Consider different weights for different audio types

## Conclusion

The supervised environmental classifier is a **significant improvement** over anomaly detection:
- ✅ 81.69% accuracy on ASVspoof test set
- ✅ 0.910 AUC-ROC (excellent discrimination)
- ⚠️ Still struggles with domain mismatch (Trump audios)

**Recommendation**: Proceed with hybrid system combining environmental classifier + ResNet CNN for maximum robustness.

