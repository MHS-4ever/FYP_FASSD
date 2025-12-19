# Phase 3: Hybrid Model Architecture

**Status**: ⏳ IN PROGRESS  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3  
**Dependencies**: Phase 2 (Feature Extraction) ✅ COMPLETE

---

## 🎯 Objective

Design and implement a hybrid deep learning model with two branches (spectrogram + environmental) that work together to detect deepfake audio, trained end-to-end. This phase focuses on architecture design and implementation, not training.

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

**Base Model:** Use existing `code/models/resnet_cnn.py` as starting point

**Purpose:** Detect synthetic artifacts in spectrogram representation

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

**Purpose:** Analyze environmental consistency (real recordings have natural acoustics, AI-generated audio often lacks this)

### Fusion Layer

**Option 1: Concatenation** (Initial Implementation)

```
Concat: [spectrogram_emb, env_emb] → [B, 256]
FC: 256 → 128
ReLU
Dropout: 0.2
```

**Option 2: Attention-Based Fusion** (Future Enhancement)

```
Attention mechanism to weight spectrogram vs environmental
Weighted combination → [B, 128]
```

**Initial Choice:** Concatenation (simpler, can upgrade later)

**Purpose:** Combine information from both branches

### Output Heads

**Head 1: Binary Classification (Real vs Fake)**

```
FC: 128 → 64
ReLU
Dropout: 0.2
FC: 64 → 2
```

**Output:** `[B, 2]` - Logits for (real, fake)

**Head 2: Multi-Class Classification (Attack Type)**

```
FC: 128 → 64
ReLU
Dropout: 0.2
FC: 64 → 4
```

**Output:** `[B, 4]` - Logits for (bonafide, synthesis, conversion, replay)

---

## 📋 Tasks

### 1. Implement Hybrid Architecture

**File to Create:** `code/phase3/hybrid_resnet_environmental.py`

**Components to Implement:**

- `ResNetBranch` - Spectrogram processing branch
- `EnvironmentalBranch` - Environmental feature processing branch
- `FusionLayer` - Combine both branches
- `BinaryHead` - Real/fake classification head
- `MultiClassHead` - Attack type classification head
- `HybridResNetEnvironmental` - Complete model combining all components

**Requirements:**

- Modular design (each component as separate class)
- Proper weight initialization
- Support for different batch sizes
- Embedding extraction method for analysis

### 2. Implement Multi-Task Loss

**File to Create:** `code/phase3/multi_task_loss.py`

**Loss Function Design:**

```python
total_loss = α × binary_loss + β × multiclass_loss

Where:
- binary_loss = CrossEntropy(binary_pred, binary_label)
- multiclass_loss = CrossEntropy(multiclass_pred, attack_type_label)
- α = 0.7 (weight for binary task - primary objective)
- β = 0.3 (weight for multiclass task - secondary objective)
```

**Class Weighting:**

- Support for class weights to handle imbalanced data
- Expected imbalance: ~95% fake, ~5% real
- Use inverse frequency weighting
- Configurable weights for both binary and multiclass tasks

**Requirements:**

- Flexible loss weights (α, β)
- Class weight support
- Separate loss tracking (binary, multiclass, total)
- Proper reduction (mean/sum)

### 3. Test Architecture

**File to Create:** `code/phase3/test_hybrid_architecture.py`

**Tests to Implement:**

1. Forward pass with dummy inputs
2. Output shape verification (different batch sizes)
3. Loss computation test
4. Gradient flow check
5. Parameter count verification
6. Embedding extraction test
7. Model save/load test

**Requirements:**

- Comprehensive test coverage
- Clear error messages
- Test summary report
- Exit code 0 on success, 1 on failure

### 4. Create Orchestrator Script

**File to Create:** `code/phase3/run_phase3.py`

**Purpose:** Run all Phase 3 steps in sequence

**Features:**

- Run all tests automatically
- Skip options for individual steps
- Clear progress reporting
- Error handling

---

## 📁 Expected Output Files

```
code/phase3/
├── hybrid_resnet_environmental.py    # Model architecture
├── multi_task_loss.py                # Loss function
├── test_hybrid_architecture.py        # Architecture tests
├── run_phase3.py                     # Orchestrator script
└── README.md                          # Usage documentation
```

**Note:** These files are created in Phase 3, but the model will be used in Phase 4 (Training).

---

## ✅ Success Criteria

**Phase 3 is considered complete when:**

- [ ] Hybrid architecture implemented (`hybrid_resnet_environmental.py`)
- [ ] Multi-task loss implemented (`multi_task_loss.py`)
- [ ] Test suite created (`test_hybrid_architecture.py`)
- [ ] Orchestrator script created (`run_phase3.py`)
- [ ] All 7 tests pass successfully
- [ ] Model processes inputs correctly (spectrogram + environmental)
- [ ] Output shapes are correct (binary: [B, 2], multiclass: [B, 4])
- [ ] Loss computation works correctly
- [ ] Gradients flow to all parameters
- [ ] Parameter count is reasonable (~2.9M parameters)
- [ ] Model can be saved and loaded
- [ ] No errors in test execution
- [ ] Documentation complete (README.md)

**Once all criteria are met, update status to ✅ COMPLETE**

---

## 📊 Expected Model Specifications

### Parameter Breakdown

```
Component              | Parameters | Percentage | Purpose
-----------------------|------------|------------|------------------
ResNet Branch          | ~2.8M      | ~70%       | Spectrogram processing
Environmental Branch   | ~20K       | <1%        | Environmental features
Fusion Layer           | ~50K       | ~1%        | Combine branches
Binary Head            | ~10K       | <1%        | Real/fake classification
MultiClass Head        | ~10K       | <1%        | Attack type classification
-------------------------------------------
Total                  | ~2.9M      | 100%       |
```

**Model Size:** ~12 MB (with FP32 weights)

### Input/Output Specifications

**Inputs:**

- Spectrogram: `[B, 1, 64, 400]` - Log-Mel Spectrogram
- Environmental: `[B, 12]` - Environmental features

**Outputs:**

- Binary logits: `[B, 2]` - (real, fake)
- Multi-class logits: `[B, 4]` - (bonafide, synthesis, conversion, replay)

**Embeddings:**

- Spectrogram embedding: `[B, 128]`
- Environmental embedding: `[B, 128]`
- Fused embedding: `[B, 128]`

---

## ⚠️ Limitations & Challenges

### Challenge 1: Branch Integration

**Problem:** Combining two different feature types (spectrogram vs environmental) with different scales and characteristics.

**Potential Issues:**

- Feature scale mismatch (spectrogram values vs environmental values)
- One branch dominating the other during training
- Fusion layer not learning effective combination

**Solutions:**

- Use proper normalization (environmental features will be normalized in Phase 4)
- Start with concatenation fusion (simpler)
- Monitor both branch outputs during training
- Consider attention-based fusion if needed

### Challenge 2: Multi-Task Learning

**Problem:** Balancing binary classification (real vs fake) and multi-class classification (attack type) tasks.

**Potential Issues:**

- One task learning faster than the other
- Loss weights (α, β) may need adjustment
- Need to monitor both metrics separately

**Solutions:**

- Use weighted loss (α=0.7 for binary, β=0.3 for multiclass)
- Monitor both tasks during training (Phase 4)
- Adjust weights if one task dominates
- Consider task-specific learning rates

### Challenge 3: Gradient Flow

**Problem:** Ensuring gradients flow properly to both branches during backpropagation.

**Potential Issues:**

- Vanishing gradients in one branch
- Exploding gradients
- One branch not updating (gradient flow blocked)

**Solutions:**

- Proper weight initialization (He initialization for ResNet, normal for MLP)
- Gradient clipping if needed
- Monitor gradient norms during training
- Check for disconnected computational graph

### Challenge 4: Parameter Count

**Problem:** Model size may exceed expectations or be too small.

**Potential Issues:**

- More parameters than expected (memory issues, overfitting risk)
- Fewer parameters than expected (underfitting risk)

**Solutions:**

- Verify architecture matches design document
- Check for unexpected layers or connections
- Compare with expected breakdown
- Adjust architecture if needed

### Challenge 5: Class Imbalance

**Problem:** Dataset is heavily imbalanced (~95% fake, ~5% real).

**Potential Issues:**

- Model biased toward majority class
- Poor performance on minority class (real samples)

**Solutions:**

- Use class weights in loss function
- Monitor per-class metrics
- Consider focal loss if needed
- Use appropriate evaluation metrics (EER, not just accuracy)

---

## 🐛 Possible Errors & Solutions

### Error 1: ImportError: No module named 'models.resnet_cnn'

**Cause:** Python path not set correctly or file doesn't exist.

**Solution:**

- Verify `code/models/resnet_cnn.py` exists
- Check import path in `hybrid_resnet_environmental.py`
- Ensure running from project root directory
- Add parent directory to Python path if needed

### Error 2: Shape Mismatch in Forward Pass

**Cause:** Input shapes don't match expected dimensions.

**Solution:**

- Verify spectrogram shape: `[B, 1, 64, 400]`
- Verify environmental shape: `[B, 12]`
- Check batch dimension consistency
- Ensure inputs are tensors, not numpy arrays

### Error 3: Gradient Flow Issues

**Cause:** Disconnected computational graph or requires_grad=False.

**Solution:**

- Check all parameters have `requires_grad=True`
- Verify loss computation includes all model outputs
- Check for `detach()` calls in forward pass
- Ensure model is in training mode (`model.train()`)

### Error 4: Out of Memory

**Cause:** Batch size too large or model too big.

**Solution:**

- Reduce batch size in test scripts
- Use gradient checkpointing (future enhancement)
- Check for memory leaks
- Use CPU instead of GPU for testing

### Error 5: Parameter Count Mismatch

**Cause:** Architecture doesn't match design document.

**Solution:**

- Verify all layers match design document
- Check for unexpected layers or connections
- Compare with expected breakdown
- Review architecture implementation

### Error 6: Test Failures

**Cause:** Various (see specific test error messages).

**Solution:**

- Read error messages carefully
- Verify all dependencies installed (`pip install -r requirements.txt`)
- Check model architecture matches design
- Ensure input shapes are correct
- Verify PyTorch version compatibility

### Error 7: Loss Computation Errors

**Cause:** Label shapes don't match logits or invalid values.

**Solution:**

- Verify binary labels: `[B]` with values 0 or 1
- Verify multiclass labels: `[B]` with values 0-3
- Check loss function input shapes
- Ensure labels are LongTensor type
- Check for NaN or Inf values in inputs

---

## 🔍 Architecture Verification Checklist

**Before marking Phase 3 as complete, verify:**

- [ ] Input shapes match expected (spectrogram: [B, 1, 64, 400], environmental: [B, 12])
- [ ] Output shapes correct (binary: [B, 2], multiclass: [B, 4])
- [ ] Loss decreases with dummy data (not NaN or Inf)
- [ ] Gradients computed for all parameters
- [ ] Model can be saved and loaded successfully
- [ ] Parameter count within expected range (~2.9M)
- [ ] All 7 test suite tests pass
- [ ] No errors or warnings in test output
- [ ] Model architecture matches design document
- [ ] Embeddings have correct shapes ([B, 128] each)
- [ ] Model can be imported in other scripts

**Status Update:** Only mark as ✅ COMPLETE after all checks pass

---

## 🔗 Dependencies

**Prerequisites:**

- ✅ Phase 2: Feature Extraction (need features to test)
- ✅ Existing ResNet CNN code (`code/models/resnet_cnn.py`)

**Required Python Packages:**

- `torch` - PyTorch deep learning framework
- `numpy` - Numerical operations
- All dependencies listed in `requirements.txt`

**Next Phase:**

- Phase 4: Training (requires architecture from Phase 3)

---

## 📝 Design Decisions

### Fusion Method: Concatenation vs Attention

**Decision:** Start with concatenation, can upgrade to attention later.

**Rationale:**

- Simpler to implement and debug
- Faster to train
- Can upgrade if needed based on results
- Attention adds complexity and parameters

### Loss Weights: α=0.7, β=0.3

**Decision:** Binary task gets higher weight (0.7) than multiclass (0.3).

**Rationale:**

- Binary classification is primary objective
- Multi-class is secondary (attack type identification)
- Weights can be adjusted during training if needed

### Model Size: ~2.9M Parameters

**Decision:** Keep model relatively small for efficiency.

**Rationale:**

- Balance between capacity and efficiency
- Most parameters in ResNet branch (spectrogram processing)
- Environmental branch is lightweight (MLP)
- Suitable for deployment

---

## 🚀 Implementation Notes

- **Modularity:** Each component (branch, fusion, head) is a separate class for flexibility
- **Extensibility:** Easy to add attention fusion, different heads, etc.
- **Testability:** Comprehensive test suite ensures correctness
- **Documentation:** Clear code comments and README for usage

---

**Last Updated**: December 2025  
**Status**: ⏳ IN PROGRESS

**Note**: This document will be updated to ✅ COMPLETE status only after all tests pass, all files are created, and success criteria are met.
