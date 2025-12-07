# Phase 3: Hybrid Model Architecture

**Status**: ⏳ PENDING  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3  
**Dependencies**: Phase 2 (Feature Extraction)

---

## 🎯 Objective

Design and implement a hybrid deep learning model with two branches (spectrogram + environmental) that work together to detect deepfake audio, trained end-to-end.

---

## 📋 Architecture Design

### Overall Structure

```
Input Audio
    │
    ├─→ Branch 1: ResNet CNN (Spectrogram)
    │   └─→ Synthetic Artifact Detection
    │
    └─→ Branch 2: MLP/FCN (Environmental Features)
        └─→ Environmental Consistency Analysis
            │
            └─→ Fusion Layer
                ├─→ Binary Head: Real vs Fake
                └─→ Multi-Class Head: Attack Type
```

### Branch 1: ResNet CNN (Spectrogram)

**Input:** Log-Mel Spectrogram `[B, 1, 64, 400]`

**Architecture:**
```
Initial Conv: 1 → 32 channels

Layer 1: ResBlock(32→32) × 2    [No downsample]
Layer 2: ResBlock(32→64) × 2    [Downsample 2×]
Layer 3: ResBlock(64→128) × 2   [Downsample 2×]
Layer 4: ResBlock(128→256) × 2  [Downsample 2×]

Global Avg Pool: 256 → [256]
Dropout: 0.3
FC: 256 → 128
```

**Output:** `[B, 128]` - Spectrogram embedding

**Base Model:** Use existing `Code/models/resnet_cnn.py` as starting point

### Branch 2: Environmental MLP

**Input:** Environmental Features `[B, 12]`

**Architecture:**
```
FC: 12 → 64
ReLU
Dropout: 0.2

FC: 64 → 128
ReLU
Dropout: 0.2

FC: 128 → 128
```

**Output:** `[B, 128]` - Environmental embedding

### Fusion Layer

**Option 1: Concatenation**
```
Concat: [spectrogram_emb, env_emb] → [B, 256]
FC: 256 → 128
```

**Option 2: Attention-Based Fusion**
```
Attention mechanism to weight spectrogram vs environmental
Weighted combination → [B, 128]
```

**Initial Choice:** Concatenation (simpler, can upgrade later)

### Output Heads

**Head 1: Binary Classification (Real vs Fake)**
```
FC: 128 → 64
ReLU
Dropout: 0.2
FC: 64 → 2
Softmax
```

**Head 2: Multi-Class Classification (Attack Type)**
```
FC: 128 → 64
ReLU
Dropout: 0.2
FC: 64 → 4  (bonafide, synthesis, conversion, replay)
Softmax
```

---

## 📋 Tasks

### 1. Implement Hybrid Architecture

**File:** `Code/models/hybrid_resnet_environmental.py`

**Components:**
- `ResNetBranch` - Spectrogram processing
- `EnvironmentalBranch` - Environmental feature processing
- `FusionLayer` - Combine branches
- `BinaryHead` - Real/fake classification
- `MultiClassHead` - Attack type classification
- `HybridModel` - Complete model

### 2. Implement Multi-Task Loss

**File:** `Code/utils/multi_task_loss.py`

**Loss Function:**
```python
total_loss = α × binary_loss + β × multiclass_loss

Where:
- binary_loss = CrossEntropy(binary_pred, binary_label)
- multiclass_loss = CrossEntropy(multiclass_pred, attack_type_label)
- α = 0.7 (weight for binary task)
- β = 0.3 (weight for multiclass task)
```

**Class Weighting:**
- Apply class weights for imbalanced data (95% fake, 5% real)
- Use same weighting strategy as previous ResNet training

### 3. Test Architecture

**Tests:**
- Forward pass with dummy inputs
- Output shape verification
- Loss computation test
- Gradient flow check
- Parameter count verification

**Test Script:** `Code/test_hybrid_architecture.py`

---

## 📁 Output Files

```
Code/
├── models/
│   └── hybrid_resnet_environmental.py    # Model architecture
└── utils/
    └── multi_task_loss.py                # Loss function

tests/
└── test_hybrid_architecture.py           # Architecture tests
```

---

## 🔧 Scripts Needed

### To Create:
- `Code/models/hybrid_resnet_environmental.py` - Hybrid model
- `Code/utils/multi_task_loss.py` - Multi-task loss
- `Code/test_hybrid_architecture.py` - Architecture tests

### Existing (Reuse):
- ✅ `Code/models/resnet_cnn.py` - Base for Branch 1

---

## ✅ Success Criteria

- [ ] Hybrid architecture implemented
- [ ] Both branches process inputs correctly
- [ ] Fusion layer combines branches
- [ ] Both output heads produce correct shapes
- [ ] Multi-task loss computes correctly
- [ ] Forward pass works with dummy data
- [ ] Gradient flow verified
- [ ] Parameter count reasonable (~3-5M parameters)

---

## 📊 Expected Model Size

**Parameter Breakdown:**
```
Component              | Parameters | Percentage
-----------------------|------------|------------
ResNet Branch          | ~2.8M      | ~70%
Environmental Branch   | ~20K       | <1%
Fusion Layer           | ~50K       | ~1%
Binary Head            | ~10K       | <1%
MultiClass Head        | ~10K       | <1%
-------------------------------------------
Total                  | ~2.9M      | 100%
```

**Model Size:** ~12 MB (with FP32 weights)

---

## ⚠️ Challenges & Solutions

### Challenge 1: Branch Integration
**Problem**: Combining two different feature types  
**Solution**: Use fusion layer with proper normalization, attention mechanism if needed

### Challenge 2: Multi-Task Learning
**Problem**: Balancing binary and multiclass tasks  
**Solution**: Weighted loss, monitor both tasks during training

### Challenge 3: Gradient Flow
**Problem**: Ensuring gradients flow to both branches  
**Solution**: Proper initialization, gradient clipping if needed

---

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 2: Feature Extraction (need features to test)
- ✅ Existing ResNet CNN code

**Next Phase:**
- Phase 4: Training (requires architecture)

---

## 📝 Notes

- Start with simple concatenation fusion, can upgrade to attention later
- Monitor both tasks during training (separate metrics)
- Consider freezing one branch initially if training is unstable
- Document architecture decisions and rationale

---

## 🔍 Architecture Verification Checklist

- [ ] Input shapes match expected
- [ ] Output shapes correct (binary: [B, 2], multiclass: [B, 4])
- [ ] Loss decreases with dummy data
- [ ] Gradients computed for all parameters
- [ ] Model can be saved/loaded
- [ ] Inference time reasonable (<100ms per sample)

---

**Last Updated**: [Date]  
**Status**: ⏳ PENDING

