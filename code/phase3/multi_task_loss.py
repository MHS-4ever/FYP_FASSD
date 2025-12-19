"""
Multi-Task Loss Function for Hybrid Model

Combines binary classification loss (real vs fake) and multi-class classification loss (attack type).
Supports class weighting for imbalanced datasets.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiTaskLoss(nn.Module):
    """
    Multi-task loss combining binary and multi-class classification.
    
    Loss = α × binary_loss + β × multiclass_loss
    
    Where:
    - binary_loss = CrossEntropy(binary_pred, binary_label)
    - multiclass_loss = CrossEntropy(multiclass_pred, attack_type_label)
    - α = binary_weight (default: 0.7)
    - β = multiclass_weight (default: 0.3)
    """
    def __init__(self, 
                 binary_weight=0.7, 
                 multiclass_weight=0.3,
                 binary_class_weights=None,
                 multiclass_class_weights=None,
                 reduction='mean'):
        """
        Initialize multi-task loss.
        
        Args:
            binary_weight: Weight for binary classification task (default: 0.7)
            multiclass_weight: Weight for multi-class classification task (default: 0.3)
            binary_class_weights: Class weights for binary task [real_weight, fake_weight]
            multiclass_class_weights: Class weights for multi-class task [bonafide, synthesis, conversion, replay]
            reduction: 'mean' or 'sum' (default: 'mean')
        """
        super().__init__()
        
        self.binary_weight = binary_weight
        self.multiclass_weight = multiclass_weight
        self.reduction = reduction
        
        # Binary classification loss
        if binary_class_weights is not None:
            binary_class_weights = torch.tensor(binary_class_weights, dtype=torch.float32)
        self.binary_criterion = nn.CrossEntropyLoss(weight=binary_class_weights, reduction=reduction)
        
        # Multi-class classification loss
        if multiclass_class_weights is not None:
            multiclass_class_weights = torch.tensor(multiclass_class_weights, dtype=torch.float32)
        self.multiclass_criterion = nn.CrossEntropyLoss(weight=multiclass_class_weights, reduction=reduction)
    
    def forward(self, binary_logits, multiclass_logits, binary_labels, multiclass_labels):
        """
        Compute multi-task loss.
        
        Args:
            binary_logits: [B, 2] - Binary classification logits (real, fake)
            multiclass_logits: [B, 4] - Multi-class classification logits (bonafide, synthesis, conversion, replay)
            binary_labels: [B] - Binary labels (0=real, 1=fake)
            multiclass_labels: [B] - Multi-class labels (0=bonafide, 1=synthesis, 2=conversion, 3=replay)
        
        Returns:
            total_loss: Scalar loss value
            binary_loss: Binary classification loss
            multiclass_loss: Multi-class classification loss
        """
        # Compute individual losses
        binary_loss = self.binary_criterion(binary_logits, binary_labels)
        multiclass_loss = self.multiclass_criterion(multiclass_logits, multiclass_labels)
        
        # Combine losses
        total_loss = self.binary_weight * binary_loss + self.multiclass_weight * multiclass_loss
        
        return total_loss, binary_loss, multiclass_loss


def compute_class_weights_from_labels(labels, n_classes):
    """
    Compute class weights from label distribution (inverse frequency weighting).
    
    Args:
        labels: [N] - Label array
        n_classes: Number of classes
    
    Returns:
        weights: [n_classes] - Class weights (normalized)
    """
    import numpy as np
    
    # Count class frequencies
    unique, counts = np.unique(labels, return_counts=True)
    class_counts = np.zeros(n_classes)
    for u, c in zip(unique, counts):
        class_counts[u] = c
    
    # Avoid division by zero
    class_counts = np.maximum(class_counts, 1)
    
    # Inverse frequency weighting
    total = class_counts.sum()
    weights = total / (n_classes * class_counts)
    
    # Normalize to sum to n_classes
    weights = weights / weights.sum() * n_classes
    
    return weights.tolist()


def create_loss_function(binary_class_weights=None,
                        multiclass_class_weights=None,
                        binary_weight=0.7,
                        multiclass_weight=0.3):
    """
    Create a multi-task loss function with optional class weighting.
    
    Args:
        binary_class_weights: [real_weight, fake_weight] or None
        multiclass_class_weights: [bonafide, synthesis, conversion, replay] or None
        binary_weight: Weight for binary task (default: 0.7)
        multiclass_weight: Weight for multi-class task (default: 0.3)
    
    Returns:
        loss_fn: MultiTaskLoss instance
    """
    return MultiTaskLoss(
        binary_weight=binary_weight,
        multiclass_weight=multiclass_weight,
        binary_class_weights=binary_class_weights,
        multiclass_class_weights=multiclass_class_weights
    )


if __name__ == "__main__":
    # Test the loss function
    print("="*80)
    print("Testing Multi-Task Loss Function")
    print("="*80)
    
    batch_size = 8
    n_attack_types = 4
    
    # Create dummy predictions and labels
    binary_logits = torch.randn(batch_size, 2)
    multiclass_logits = torch.randn(batch_size, n_attack_types)
    
    binary_labels = torch.randint(0, 2, (batch_size,))
    multiclass_labels = torch.randint(0, n_attack_types, (batch_size,))
    
    print(f"\nInput shapes:")
    print(f"  Binary logits: {binary_logits.shape}")
    print(f"  Multi-class logits: {multiclass_logits.shape}")
    print(f"  Binary labels: {binary_labels.shape}")
    print(f"  Multi-class labels: {multiclass_labels.shape}")
    
    # Test without class weights
    print("\n" + "-"*80)
    print("Test 1: Without class weights")
    print("-"*80)
    loss_fn = MultiTaskLoss(binary_weight=0.7, multiclass_weight=0.3)
    total_loss, binary_loss, multiclass_loss = loss_fn(
        binary_logits, multiclass_logits, binary_labels, multiclass_labels
    )
    
    print(f"Total loss: {total_loss.item():.4f}")
    print(f"Binary loss: {binary_loss.item():.4f}")
    print(f"Multi-class loss: {multiclass_loss.item():.4f}")
    
    # Test with class weights
    print("\n" + "-"*80)
    print("Test 2: With class weights (imbalanced data)")
    print("-"*80)
    
    # Simulate imbalanced data: 95% fake, 5% real
    binary_weights = [10.0, 0.5]  # Higher weight for real (minority class)
    
    # Simulate imbalanced attack types: 40% bonafide, 30% synthesis, 20% conversion, 10% replay
    multiclass_weights = [0.5, 0.67, 1.0, 2.0]  # Higher weights for minority classes
    
    loss_fn_weighted = MultiTaskLoss(
        binary_weight=0.7,
        multiclass_weight=0.3,
        binary_class_weights=binary_weights,
        multiclass_class_weights=multiclass_weights
    )
    
    total_loss_w, binary_loss_w, multiclass_loss_w = loss_fn_weighted(
        binary_logits, multiclass_logits, binary_labels, multiclass_labels
    )
    
    print(f"Total loss (weighted): {total_loss_w.item():.4f}")
    print(f"Binary loss (weighted): {binary_loss_w.item():.4f}")
    print(f"Multi-class loss (weighted): {multiclass_loss_w.item():.4f}")
    
    # Test class weight computation
    print("\n" + "-"*80)
    print("Test 3: Compute class weights from labels")
    print("-"*80)
    
    # Simulate imbalanced labels
    import numpy as np
    binary_labels_imbalanced = np.array([0] * 1 + [1] * 7)  # 1 real, 7 fake
    multiclass_labels_imbalanced = np.array([0] * 4 + [1] * 3 + [2] * 1)  # 4 bonafide, 3 synthesis, 1 conversion
    
    binary_weights_computed = compute_class_weights_from_labels(binary_labels_imbalanced, 2)
    multiclass_weights_computed = compute_class_weights_from_labels(multiclass_labels_imbalanced, 4)
    
    print(f"Binary class weights (computed): {binary_weights_computed}")
    print(f"Multi-class class weights (computed): {multiclass_weights_computed}")
    
    print("\n" + "="*80)
    print("✓ Loss function test completed successfully!")
    print("="*80)

