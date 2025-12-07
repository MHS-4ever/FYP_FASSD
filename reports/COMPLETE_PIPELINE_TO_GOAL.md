# Complete Pipeline to Achieve Goal

**Goal**: Build a model that works on **ANY audio** from **ANY voice**, detecting real vs fake using environmental factors as core component.

---

## 🎯 Goal Breakdown

1. ✅ Takes **ANY audio file** as input (any voice, any speaker, any recording condition)
2. ✅ Determines if it's **REAL** (human) or **FAKE** (AI-generated)
3. ✅ Works on **unseen speakers** (generalization)
4. ✅ Works on **different recording conditions** (broadcast, phone, studio, etc.)
5. ✅ Provides **explanation** of why it's real or fake
6. ✅ Use **environmental factors** as core of the model

---

## 📋 Complete Pipeline

### Phase 0: Real-World Data Collection (CRITICAL - Week 1-2)

**Why**: ASVspoof alone is NOT enough. Need real-world data to learn real-world patterns.

**Tasks**:

1. **Collect Real-World Audio**
   - Broadcast recordings (TV, radio): 5,000+ samples
   - Phone recordings: 3,000+ samples
   - Podcasts: 3,000+ samples
   - Social media audio: 2,000+ samples
   - **Total: 10,000+ samples minimum**

2. **Label Real-World Audio**
   - Use known real audio (easier to get)
   - Or manually label real vs fake
   - Create manifest with domain labels (broadcast/phone/podcast/social)

3. **Verify Data Quality**
   - Check audio quality
   - Verify labels
   - Report statistics

**Output**: `data/realworld/manifest_realworld.csv`

**Scripts Needed**:
- Data collection scripts (manual or automated)
- Labeling tools

---

### Phase 1: Unified Dataset Preparation (Week 2)

**Why**: Combine all datasets (ASVspoof + Real-world) with proper labels.

**Tasks**:

1. **Create Unified Manifest**
   - Combine ASVspoof_LA (real + fake)
   - Combine ASVspoof_DF (real + fake)
   - Combine ASVspoof_PA (real + fake)
   - **Add real-world data** (from Phase 0)
   - Add dataset labels (LA/DF/PA/RealWorld)
   - Add attack type labels (synthesis/conversion/replay/bonafide)
   - Add domain labels (studio/broadcast/phone/podcast/social)
   - Extract speaker IDs

2. **Speaker-Independent Split**
   - Split by speaker (not sample)
   - Ensure no speaker overlap between train/test
   - Balance real/fake distribution in each split
   - Ensure both domains (ASVspoof + Real-world) in train and test

**Output**:
- `data/manifests/unified_asvspoof_manifest.csv`
- `data/manifests/train_speaker_independent.csv`
- `data/manifests/test_speaker_independent.csv`

**Scripts Needed**:
- `Code/create_unified_manifest.py` ✅ (created)
- `Code/create_speaker_independent_split.py` (to create)

---

### Phase 2: Feature Extraction (Week 2-3)

**Why**: Extract both spectrogram and environmental features for hybrid model.

**Tasks**:

1. **Extract Spectrogram Features**
   - Log-Mel spectrograms (64 bins)
   - For ResNet CNN branch
   - Extract from all audio files (ASVspoof + Real-world)

2. **Extract Environmental Features**
   - 12 environmental features (RT60, SNR, spectral, etc.)
   - For Environmental MLP branch
   - Extract from all audio files (ASVspoof + Real-world)

3. **Pack Features**
   - Pack spectrogram features into HDF5
   - Pack environmental features into HDF5 (or CSV)
   - Include dataset and domain labels

**Output**:
- `data/features/logmel_packed.h5` (spectrogram features)
- `data/features/environmental_packed.h5` (environmental features)
- `data/features/features_manifest_unified.csv`

**Scripts Needed**:
- `Code/features/feature_extraction.py` (modify to extract both)
- `Code/pack_features_to_hdf5.py` (modify to pack both)

---

### Phase 3: Hybrid Model Architecture (Week 3)

**Why**: Single model with two branches (spectrogram + environmental) trained end-to-end.

**Tasks**:

1. **Design Hybrid Architecture**
   - **Branch 1**: ResNet CNN (spectrogram input → synthetic artifact detection)
   - **Branch 2**: MLP/FCN (environmental features input → environmental consistency)
   - **Fusion Layer**: Concatenate or attention-based fusion
   - **Output Heads**:
     - Binary: Real vs Fake
     - Multi-class: Bonafide, Synthesis, Conversion, Replay

2. **Implement Multi-Task Loss**
   - Binary cross-entropy for real/fake
   - Cross-entropy for attack type
   - Weighted combination

3. **Test Architecture**
   - Forward pass test
   - Output shape verification
   - Loss computation test

**Output**: Model architecture code

**Scripts Needed**:
- `Code/models/hybrid_resnet_environmental.py` (to create)
- `Code/utils/multi_task_loss.py` (to create)

---

### Phase 4: Training (Week 3-4)

**Why**: Train hybrid model on mixed data (ASVspoof + Real-world) for domain generalization.

**Tasks**:

1. **Prepare Training Data**
   - Use unified manifest with speaker-independent split
   - Mix: 50% ASVspoof + 50% Real-world
   - Stratify by domain (ensure both domains in train/test)

2. **Train Hybrid Model**
   - Use both spectrogram and environmental features
   - Train end-to-end (both branches together)
   - Monitor:
     - Binary accuracy (real/fake)
     - Attack type accuracy (synthesis/conversion/replay)
     - Per-domain performance (ASVspoof vs Real-world)
   - Save best checkpoint based on validation EER (both domains)

3. **Training Optimizations**
   - Mixed precision training (FP16)
   - Quick evaluation during training
   - GPU optimizations (TF32, cuDNN)
   - Class weighting for imbalanced data

**Output**: `models_saved/hybrid_resnet_environmental.pth`

**Scripts Needed**:
- `Code/train_hybrid_model.py` (to create)

---

### Phase 5: Evaluation (Week 4)

**Why**: Test model on all domains and attack types to verify generalization.

**Tasks**:

1. **In-Domain Evaluation (ASVspoof)**
   - Test on ASVspoof test set
   - Per-dataset metrics (LA, DF, PA)
   - Per-attack-type metrics (synthesis, conversion, replay)
   - Speaker-independent test

2. **Cross-Domain Evaluation (Real-World)**
   - Test on real-world test set
   - Per-domain metrics (broadcast, phone, podcasts, social media)
   - Compare with in-domain performance

3. **Comprehensive Metrics**
   - EER (Equal Error Rate)
   - AUC (Area Under ROC Curve)
   - Accuracy (binary + multi-class)
   - Confusion matrices
   - Per-domain breakdown

**Output**: Evaluation report with all metrics

**Scripts Needed**:
- `Code/evaluate_hybrid_model.py` (to create)

---

### Phase 6: Explanation System (Week 4-5)

**Why**: Provide detailed explanations for predictions (requirement #5).

**Tasks**:

1. **Feature Importance Analysis**
   - Which environmental features contribute most?
   - Which spectrogram patterns are detected?
   - Per-attack-type analysis

2. **Explanation Generation**
   - Generate human-readable explanations
   - Based on:
     - Environmental feature values (RT60, SNR, etc.)
     - Spectrogram patterns detected
     - Attack type classification
     - Confidence scores

3. **Explanation Format**
   - "This audio is FAKE because:"
     - "RT60 is abnormally low (0.2s) - suggests synthetic environment"
     - "SNR is too high (45dB) - too clean for natural recording"
     - "Detected synthesis attack patterns"
   - "This audio is REAL because:"
     - "RT60 is natural (0.8s)"
     - "SNR is typical (25dB)"
     - "No synthetic artifacts detected"

**Output**: Explanation generation system

**Scripts Needed**:
- `Code/explain_prediction.py` (to create)

---

### Phase 7: Domain Adaptation (If Needed - Week 5)

**Why**: Fine-tune model if cross-domain performance is poor.

**Tasks**:

1. **Collect Additional Real-World Data**
   - If performance < target (EER > 20%)
   - Collect more samples from failing domains
   - Minimum: 1,000+ samples per failing domain

2. **Fine-Tune Model**
   - Use transfer learning (freeze base, train head)
   - Or full fine-tuning on real-world data
   - Monitor per-domain improvement

3. **Evaluate Fine-Tuned Model**
   - Compare before vs after fine-tuning
   - Report improvement in cross-domain performance

**Output**: `models_saved/hybrid_resnet_environmental_finetuned.pth`

**Scripts Needed**:
- `Code/finetune_on_realworld.py` (to create, if needed)

---

## 📊 Success Criteria

### Minimum Viable Product (MVP)

1. ✅ Real-world data collected (10,000+ samples)
2. ✅ Model trained on ASVspoof + Real-world (50/50 mix)
3. ✅ Hybrid architecture (ResNet + Environmental branches)
4. ✅ Speaker-independent evaluation
5. ✅ Works on ASVspoof test set (EER < 5%)
6. ✅ **Works on real-world audio (EER < 20%)** ← KEY
7. ✅ Can detect all three attack types (synthesis, conversion, replay)
8. ✅ Provides explanations for predictions

### Full Success

1. ✅ All MVP criteria met
2. ✅ Works on diverse real-world audio (EER < 15%)
3. ✅ Generalizes to unseen speakers (speaker-independent)
4. ✅ Provides detailed explanations
5. ✅ Ready for deployment

---

## 🔧 Required Scripts Summary

### New Scripts to Create

1. `Code/create_speaker_independent_split.py` - Speaker-based split
2. `Code/models/hybrid_resnet_environmental.py` - Hybrid architecture
3. `Code/utils/multi_task_loss.py` - Multi-task loss
4. `Code/train_hybrid_model.py` - Training script
5. `Code/evaluate_hybrid_model.py` - Evaluation script
6. `Code/explain_prediction.py` - Explanation system
7. `Code/finetune_on_realworld.py` - Fine-tuning (if needed)

### Scripts to Modify

1. `Code/features/feature_extraction.py` - Extract both feature types
2. `Code/pack_features_to_hdf5.py` - Pack both feature types

### Existing Scripts (Keep)

1. `Code/create_unified_manifest.py` ✅ (created)
2. `Code/features/environmental_features.py` ✅ (exists)
3. `Code/models/resnet_cnn.py` ✅ (exists, use as Branch 1 base)

---

## ⏱️ Timeline

- **Week 1-2**: Real-world data collection (CRITICAL)
- **Week 2**: Unified dataset preparation
- **Week 2-3**: Feature extraction
- **Week 3**: Model architecture design
- **Week 3-4**: Training
- **Week 4**: Evaluation
- **Week 4-5**: Explanation system
- **Week 5**: Domain adaptation (if needed)

**Total**: 4-5 weeks

---

## 🚨 Critical Requirements

### Must Have (Non-Negotiable)

1. **Real-World Data Collection** - Cannot skip
2. **Hybrid Architecture** - ResNet + Environmental from start
3. **Mixed Data Training** - 50% ASVspoof + 50% Real-world
4. **Speaker-Independent Split** - No speaker overlap
5. **Environmental Features as Core** - Not optional add-on

---

**End of Complete Pipeline Documentation**

