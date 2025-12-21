# Phase 3: Hybrid Model Architecture

**Status**: ✅ **COMPLETE**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3  
**Dependencies**: Phase 2 (Feature Extraction) ✅ COMPLETE  
**Completion Date**: December 2025

---

## 🎯 Quick Start

This folder contains scripts for implementing and testing the hybrid ResNet-Environmental model architecture.

**To test the architecture:**

```bash
python code/phase3/test_hybrid_architecture.py
```

**To run all Phase 3 steps:**

```bash
python code/phase3/run_phase3.py
```

---

## 📁 Scripts in This Folder

| Script                           | Purpose                   | When to Use                          |
| -------------------------------- | ------------------------- | ------------------------------------ |
| `hybrid_resnet_environmental.py` | Hybrid model architecture | Import in training scripts (Phase 4) |
| `multi_task_loss.py`             | Multi-task loss function  | Import in training scripts (Phase 4) |
| `test_hybrid_architecture.py`    | Architecture tests        | Run to verify model works correctly  |
| `run_phase3.py`                  | Run all Phase 3 steps     | Run to execute all tests in sequence |
| `README.md`                      | This documentation        | Reference for using Phase 3 scripts  |

---

## 🔧 Step-by-Step Usage

### Step 1: Test Model Architecture Directly

Test the hybrid model with dummy inputs to verify it works:

```bash
python code/phase3/hybrid_resnet_environmental.py
```

**What it does:**

- Creates the hybrid model
- Prints model architecture
- Counts parameters
- Tests forward pass with dummy data
- Verifies output shapes

**Expected Output:**

```
================================================================================
Testing Hybrid ResNet-Environmental Model
================================================================================

Model Architecture:
HybridResNetEnvironmental(...)

Total parameters: 2,XXX,XXX
Trainable parameters: 2,XXX,XXX

Input shapes:
  Spectrogram: torch.Size([4, 1, 64, 400])
  Environmental: torch.Size([4, 12])

Output shapes:
  Binary logits: torch.Size([4, 2])
  Multi-class logits: torch.Size([4, 4])

Embedding shapes:
  Spectrogram embedding: torch.Size([4, 128])
  Environmental embedding: torch.Size([4, 128])
  Fused embedding: torch.Size([4, 128])

================================================================================
✓ Model test completed successfully!
================================================================================
```

**If you see errors:**

- Check that `code/models/resnet_cnn.py` exists
- Verify PyTorch is installed: `pip install torch`
- Check import paths are correct

---

### Step 2: Test Loss Function

Test the multi-task loss function:

```bash
python code/phase3/multi_task_loss.py
```

**What it does:**

- Tests loss computation without class weights
- Tests loss computation with class weights
- Tests class weight computation from labels

**Expected Output:**

```
================================================================================
Testing Multi-Task Loss Function
================================================================================

Input shapes:
  Binary logits: torch.Size([8, 2])
  Multi-class logits: torch.Size([8, 4])
  Binary labels: torch.Size([8])
  Multi-class labels: torch.Size([8])

--------------------------------------------------------------------------------
Test 1: Without class weights
--------------------------------------------------------------------------------
Total loss: X.XXXX
Binary loss: X.XXXX
Multi-class loss: X.XXXX

--------------------------------------------------------------------------------
Test 2: With class weights (imbalanced data)
--------------------------------------------------------------------------------
Total loss (weighted): X.XXXX
Binary loss (weighted): X.XXXX
Multi-class loss (weighted): X.XXXX

================================================================================
✓ Loss function test completed successfully!
================================================================================
```

**If you see errors:**

- Verify PyTorch is installed correctly
- Check that input shapes match expected

---

### Step 3: Run Full Architecture Test Suite

Run comprehensive tests to verify everything works:

```bash
python code/phase3/test_hybrid_architecture.py
```

**What it does:**

- Tests forward pass with different batch sizes
- Verifies output shapes
- Tests loss computation
- Checks gradient flow
- Verifies parameter count
- Tests embedding extraction
- Tests model save/load

**Expected Output:**

```
================================================================================
HYBRID RESNET-ENVIRONMENTAL ARCHITECTURE TEST SUITE
================================================================================

================================================================================
TEST 1: Forward Pass
================================================================================
Input shapes:
  Spectrogram: torch.Size([4, 1, 64, 400])
  Environmental: torch.Size([4, 12])

Output shapes:
  Binary logits: torch.Size([4, 2]) (expected: [4, 2])
  Multi-class logits: torch.Size([4, 4]) (expected: [4, 4])
✓ Forward pass test passed!

================================================================================
TEST 2: Output Shape Verification
================================================================================
  Batch size  1: ✓ Binary [1, 2], Multi-class [1, 4]
  Batch size  4: ✓ Binary [4, 2], Multi-class [4, 4]
  Batch size  8: ✓ Binary [8, 2], Multi-class [8, 4]
  Batch size 16: ✓ Binary [16, 2], Multi-class [16, 4]
✓ Output shape verification passed!

[... more tests ...]

================================================================================
TEST SUMMARY
================================================================================
  Forward Pass                    : ✓ PASSED
  Output Shapes                   : ✓ PASSED
  Loss Computation                : ✓ PASSED
  Gradient Flow                   : ✓ PASSED
  Parameter Count                 : ✓ PASSED
  Embedding Extraction            : ✓ PASSED
  Model Save/Load                 : ✓ PASSED
--------------------------------------------------------------------------------
Total: 7/7 tests passed
================================================================================

✓ All tests passed! Architecture is ready for training.
```

**If tests fail:**

- Read the error message carefully
- Check the troubleshooting section below
- Verify all dependencies are installed

---

### Step 4: Run All Phase 3 Steps (Orchestrator)

Run all steps in sequence using the orchestrator:

```bash
python code/phase3/run_phase3.py
```

**What it does:**

- Runs all Phase 3 tests automatically
- Provides summary of results

**Options:**

```bash
# Skip tests (if already verified)
python code/phase3/run_phase3.py --skip-tests

# Run only tests
python code/phase3/run_phase3.py --test-only
```

**Expected Output:**

```
================================================================================
PHASE 3: HYBRID MODEL ARCHITECTURE
================================================================================

[INFO] This script will run all Phase 3 steps:
  1. Test hybrid architecture (forward pass, shapes, gradients, etc.)

================================================================================
STEP: Test Hybrid Architecture
================================================================================
[INFO] Running: python code/phase3/test_hybrid_architecture.py

[... test output ...]

[OK] Test Hybrid Architecture completed successfully

================================================================================
✓ PHASE 3 COMPLETED SUCCESSFULLY
================================================================================

[INFO] Phase 3 outputs:
  - Hybrid model architecture: code/phase3/hybrid_resnet_environmental.py
  - Multi-task loss: code/phase3/multi_task_loss.py
  - Test results: See output above

[INFO] Next steps:
  - Phase 4: Training (requires architecture from Phase 3)
  - Use the hybrid model for end-to-end training
```

---

## ✅ Success Criteria Checklist

After running all tests, verify:

- [x] Model architecture test passes (Step 1) ✅
- [x] Loss function test passes (Step 2) ✅
- [x] All 7 architecture tests pass (Step 3) ✅
- [x] Orchestrator completes successfully (Step 4) ✅
- [x] Parameter count is ~2.9M (within expected range) ✅
- [x] No errors or warnings in test output ✅
- [x] Model can be imported in other scripts ✅

**✅ Phase 3 is complete and ready for Phase 4 (Training).**

---

## 📊 Expected Results

### Model Parameters

**Expected Parameter Count:** ~2.9M parameters

**Breakdown:**

- ResNet Branch: ~2.8M (~70%)
- Environmental Branch: ~20K (<1%)
- Fusion Layer: ~50K (~1%)
- Binary Head: ~10K (<1%)
- Multi-class Head: ~10K (<1%)

### Test Results

**All 7 tests should pass:**

1. ✓ Forward Pass
2. ✓ Output Shapes
3. ✓ Loss Computation
4. ✓ Gradient Flow
5. ✓ Parameter Count
6. ✓ Embedding Extraction
7. ✓ Model Save/Load

---

## 🐛 Troubleshooting

### Issue: ImportError: No module named 'models.resnet_cnn'

**Error Message:**

```
ModuleNotFoundError: No module named 'models.resnet_cnn'
```

**Solution:**

1. Verify `code/models/resnet_cnn.py` exists
2. Check you're running from the project root (`E:\FYP`)
3. The import path should be correct in the script

**Fix:**

```python
# In hybrid_resnet_environmental.py, this should work:
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models.resnet_cnn import ResidualBlock
```

---

### Issue: Shape Mismatch Errors

**Error Message:**

```
RuntimeError: Expected input batch_size (...) to match target batch_size (...)
```

**Solution:**

- Verify input shapes:
  - Spectrogram: `[B, 1, 64, 400]`
  - Environmental: `[B, 12]`
- Ensure batch sizes match for both inputs

---

### Issue: Gradient Flow Problems

**Error Message:**

```
Warning: No gradients computed for some parameters
```

**Solution:**

1. Check all parameters have `requires_grad=True`
2. Verify loss computation includes all model outputs
3. Check for `detach()` calls in forward pass

---

### Issue: Out of Memory

**Error Message:**

```
RuntimeError: CUDA out of memory
```

**Solution:**

1. Reduce batch size in test scripts
2. Use CPU instead of GPU for testing
3. Close other applications using GPU

---

### Issue: Tests Failing

**What to do:**

1. Read the error message carefully
2. Check which specific test failed
3. Verify all dependencies are installed: `pip install -r requirements.txt`
4. Check that model architecture matches design
5. Ensure input shapes are correct

**Common causes:**

- Missing dependencies
- Incorrect import paths
- Shape mismatches
- Version incompatibilities

---

### Issue: Parameter Count Mismatch

**Expected:** ~2.9M parameters  
**If different:**

**Solution:**

1. Verify model architecture matches design document
2. Check for unexpected layers
3. Compare with expected breakdown above
4. If significantly different, review architecture implementation

---

## 📝 Notes

- **Model files** (`hybrid_resnet_environmental.py`, `multi_task_loss.py`) are meant to be imported in Phase 4 training scripts
- **Test files** (`test_hybrid_architecture.py`) are for verification only
- All scripts should be run from the project root directory (`E:\FYP`)
- If tests pass, the architecture is ready for training in Phase 4

---

## 🔗 Next Steps

**After Phase 3 is complete:**

1. **Phase 4: Training** - Use the hybrid model for end-to-end training
   - Import `HybridResNetEnvironmental` from `code.phase3.hybrid_resnet_environmental`
   - Import `MultiTaskLoss` from `code.phase3.multi_task_loss`
   - Train on unified dataset with both spectrogram and environmental features

---

**Last Updated**: December 2025  
**Status**: ✅ **COMPLETE**

---

## ✅ Phase 3 Completion Summary

**All Steps Completed Successfully:**

- ✅ Step 1: Model architecture implemented (`hybrid_resnet_environmental.py`)
- ✅ Step 2: Multi-task loss implemented (`multi_task_loss.py`)
- ✅ Step 3: Test suite created and all tests passing (`test_hybrid_architecture.py`)
- ✅ Step 4: Orchestrator script working (`run_phase3.py`)
- ✅ All 7 architecture tests passed
- ✅ Parameter count verified (2,902,822 parameters)
- ✅ Model can be saved and loaded
- ✅ Documentation complete

**Output Files Ready for Phase 4:**

- `code/phase3/hybrid_resnet_environmental.py` - Hybrid model architecture
- `code/phase3/multi_task_loss.py` - Multi-task loss function
- `code/phase3/test_hybrid_architecture.py` - Architecture tests (all passing)
- `code/phase3/run_phase3.py` - Orchestrator script
- `code/phase3/README.md` - This documentation

**Next Phase**: Phase 4 - Training (use hybrid model for end-to-end training)
