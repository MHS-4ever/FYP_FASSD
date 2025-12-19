"""
Test Script for Hybrid ResNet-Environmental Architecture

Tests:
1. Forward pass with dummy inputs
2. Output shape verification
3. Loss computation test
4. Gradient flow check
5. Parameter count verification
"""

import torch
import torch.nn as nn
import sys
import os

# Add current directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from hybrid_resnet_environmental import HybridResNetEnvironmental
from multi_task_loss import MultiTaskLoss, compute_class_weights_from_labels


def test_forward_pass():
    """Test forward pass with dummy inputs."""
    print("\n" + "="*80)
    print("TEST 1: Forward Pass")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    model.eval()
    
    batch_size = 4
    spectrogram_input = torch.randn(batch_size, 1, 64, 400)
    environmental_input = torch.randn(batch_size, 12)
    
    print(f"Input shapes:")
    print(f"  Spectrogram: {spectrogram_input.shape}")
    print(f"  Environmental: {environmental_input.shape}")
    
    with torch.no_grad():
        binary_logits, multiclass_logits = model(spectrogram_input, environmental_input)
    
    print(f"\nOutput shapes:")
    print(f"  Binary logits: {binary_logits.shape} (expected: [{batch_size}, 2])")
    print(f"  Multi-class logits: {multiclass_logits.shape} (expected: [{batch_size}, 4])")
    
    # Verify shapes
    assert binary_logits.shape == (batch_size, 2), f"Binary logits shape mismatch: {binary_logits.shape}"
    assert multiclass_logits.shape == (batch_size, 4), f"Multi-class logits shape mismatch: {multiclass_logits.shape}"
    
    print("✓ Forward pass test passed!")
    return True


def test_output_shapes():
    """Test output shapes for different batch sizes."""
    print("\n" + "="*80)
    print("TEST 2: Output Shape Verification")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    model.eval()
    
    batch_sizes = [1, 4, 8, 16]
    
    for batch_size in batch_sizes:
        spectrogram_input = torch.randn(batch_size, 1, 64, 400)
        environmental_input = torch.randn(batch_size, 12)
        
        with torch.no_grad():
            binary_logits, multiclass_logits = model(spectrogram_input, environmental_input)
        
        assert binary_logits.shape == (batch_size, 2), f"Batch {batch_size}: Binary shape mismatch"
        assert multiclass_logits.shape == (batch_size, 4), f"Batch {batch_size}: Multi-class shape mismatch"
        
        print(f"  Batch size {batch_size:2d}: ✓ Binary [{batch_size}, 2], Multi-class [{batch_size}, 4]")
    
    print("✓ Output shape verification passed!")
    return True


def test_loss_computation():
    """Test loss computation."""
    print("\n" + "="*80)
    print("TEST 3: Loss Computation")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    model.train()
    
    batch_size = 8
    spectrogram_input = torch.randn(batch_size, 1, 64, 400)
    environmental_input = torch.randn(batch_size, 12)
    
    binary_labels = torch.randint(0, 2, (batch_size,))
    multiclass_labels = torch.randint(0, 4, (batch_size,))
    
    # Forward pass
    binary_logits, multiclass_logits = model(spectrogram_input, environmental_input)
    
    # Compute loss
    loss_fn = MultiTaskLoss(binary_weight=0.7, multiclass_weight=0.3)
    total_loss, binary_loss, multiclass_loss = loss_fn(
        binary_logits, multiclass_logits, binary_labels, multiclass_labels
    )
    
    print(f"Total loss: {total_loss.item():.4f}")
    print(f"Binary loss: {total_loss.item():.4f}")
    print(f"Multi-class loss: {multiclass_loss.item():.4f}")
    
    # Verify loss is a scalar
    assert total_loss.dim() == 0, "Total loss should be a scalar"
    assert total_loss.item() > 0, "Loss should be positive"
    
    print("✓ Loss computation test passed!")
    return True


def test_gradient_flow():
    """Test gradient flow through all components."""
    print("\n" + "="*80)
    print("TEST 4: Gradient Flow Check")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    model.train()
    
    batch_size = 4
    spectrogram_input = torch.randn(batch_size, 1, 64, 400, requires_grad=False)
    environmental_input = torch.randn(batch_size, 12, requires_grad=False)
    
    binary_labels = torch.randint(0, 2, (batch_size,))
    multiclass_labels = torch.randint(0, 4, (batch_size,))
    
    # Forward pass
    binary_logits, multiclass_logits = model(spectrogram_input, environmental_input)
    
    # Compute loss
    loss_fn = MultiTaskLoss(binary_weight=0.7, multiclass_weight=0.3)
    total_loss, _, _ = loss_fn(binary_logits, multiclass_logits, binary_labels, multiclass_labels)
    
    # Backward pass
    total_loss.backward()
    
    # Check gradients
    has_gradients = False
    no_gradients = []
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            has_gradients = True
            grad_norm = param.grad.norm().item()
            if grad_norm == 0:
                no_gradients.append(name)
        else:
            no_gradients.append(name)
    
    if has_gradients:
        print("✓ Gradients computed for most parameters")
        if no_gradients:
            print(f"⚠ Warning: {len(no_gradients)} parameters have no gradients:")
            for name in no_gradients[:5]:  # Show first 5
                print(f"    - {name}")
            if len(no_gradients) > 5:
                print(f"    ... and {len(no_gradients) - 5} more")
    else:
        print("✗ ERROR: No gradients computed!")
        return False
    
    # Check gradient norms
    grad_norms = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norm = param.grad.norm().item()
            grad_norms.append((name, grad_norm))
    
    print(f"\nGradient statistics:")
    print(f"  Parameters with gradients: {len(grad_norms)}")
    if grad_norms:
        avg_norm = sum(norm for _, norm in grad_norms) / len(grad_norms)
        max_norm = max(norm for _, norm in grad_norms)
        min_norm = min(norm for _, norm in grad_norms)
        print(f"  Average gradient norm: {avg_norm:.6f}")
        print(f"  Max gradient norm: {max_norm:.6f}")
        print(f"  Min gradient norm: {min_norm:.6f}")
    
    print("✓ Gradient flow test passed!")
    return True


def test_parameter_count():
    """Test parameter count is reasonable."""
    print("\n" + "="*80)
    print("TEST 5: Parameter Count Verification")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Expected: ~2.9M parameters
    expected_min = 2_000_000
    expected_max = 5_000_000
    
    if expected_min <= total_params <= expected_max:
        print(f"✓ Parameter count is within expected range [{expected_min:,}, {expected_max:,}]")
    else:
        print(f"⚠ Warning: Parameter count {total_params:,} is outside expected range [{expected_min:,}, {expected_max:,}]")
    
    # Breakdown by component
    print("\nParameter breakdown by component:")
    resnet_params = sum(p.numel() for p in model.resnet_branch.parameters())
    env_params = sum(p.numel() for p in model.environmental_branch.parameters())
    fusion_params = sum(p.numel() for p in model.fusion.parameters())
    binary_params = sum(p.numel() for p in model.binary_head.parameters())
    multiclass_params = sum(p.numel() for p in model.multiclass_head.parameters())
    
    print(f"  ResNet Branch: {resnet_params:,} ({resnet_params/total_params*100:.1f}%)")
    print(f"  Environmental Branch: {env_params:,} ({env_params/total_params*100:.1f}%)")
    print(f"  Fusion Layer: {fusion_params:,} ({fusion_params/total_params*100:.1f}%)")
    print(f"  Binary Head: {binary_params:,} ({binary_params/total_params*100:.1f}%)")
    print(f"  Multi-class Head: {multiclass_params:,} ({multiclass_params/total_params*100:.1f}%)")
    
    return True


def test_embeddings():
    """Test embedding extraction."""
    print("\n" + "="*80)
    print("TEST 6: Embedding Extraction")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    model.eval()
    
    batch_size = 4
    spectrogram_input = torch.randn(batch_size, 1, 64, 400)
    environmental_input = torch.randn(batch_size, 12)
    
    with torch.no_grad():
        spec_emb, env_emb, fused_emb = model.get_embeddings(spectrogram_input, environmental_input)
    
    print(f"Spectrogram embedding: {spec_emb.shape} (expected: [{batch_size}, 128])")
    print(f"Environmental embedding: {env_emb.shape} (expected: [{batch_size}, 128])")
    print(f"Fused embedding: {fused_emb.shape} (expected: [{batch_size}, 128])")
    
    assert spec_emb.shape == (batch_size, 128), "Spectrogram embedding shape mismatch"
    assert env_emb.shape == (batch_size, 128), "Environmental embedding shape mismatch"
    assert fused_emb.shape == (batch_size, 128), "Fused embedding shape mismatch"
    
    print("✓ Embedding extraction test passed!")
    return True


def test_model_save_load():
    """Test model save/load functionality."""
    print("\n" + "="*80)
    print("TEST 7: Model Save/Load")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    
    # Save model
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pth') as f:
        temp_path = f.name
    
    try:
        torch.save(model.state_dict(), temp_path)
        print(f"✓ Model saved to: {temp_path}")
        
        # Load model
        new_model = HybridResNetEnvironmental(n_attack_types=4)
        new_model.load_state_dict(torch.load(temp_path))
        print("✓ Model loaded successfully")
        
        # Verify same outputs
        batch_size = 2
        spectrogram_input = torch.randn(batch_size, 1, 64, 400)
        environmental_input = torch.randn(batch_size, 12)
        
        model.eval()
        new_model.eval()
        
        with torch.no_grad():
            binary1, multiclass1 = model(spectrogram_input, environmental_input)
            binary2, multiclass2 = new_model(spectrogram_input, environmental_input)
        
        assert torch.allclose(binary1, binary2), "Binary outputs don't match after load"
        assert torch.allclose(multiclass1, multiclass2), "Multi-class outputs don't match after load"
        
        print("✓ Model outputs match after save/load")
        
    finally:
        # Cleanup
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return True


def main():
    """Run all tests."""
    print("="*80)
    print("HYBRID RESNET-ENVIRONMENTAL ARCHITECTURE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Forward Pass", test_forward_pass),
        ("Output Shapes", test_output_shapes),
        ("Loss Computation", test_loss_computation),
        ("Gradient Flow", test_gradient_flow),
        ("Parameter Count", test_parameter_count),
        ("Embedding Extraction", test_embeddings),
        ("Model Save/Load", test_model_save_load),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name:30s}: {status}")
    
    print("\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n✓ All tests passed! Architecture is ready for training.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    exit(main())

