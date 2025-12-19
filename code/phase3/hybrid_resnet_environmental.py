"""
Hybrid ResNet-Environmental Model for Deepfake Audio Detection

Architecture:
- Branch 1: ResNet CNN (spectrogram input) → synthetic artifact detection
- Branch 2: MLP (environmental features) → environmental consistency analysis
- Fusion Layer: Concatenate branches
- Output Heads:
  - Binary: Real vs Fake
  - Multi-class: Attack Type (bonafide, synthesis, conversion, replay)
"""

import torch
import torch.nn as nn
import sys
import os

# Add parent directory to path to import ResNet components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models.resnet_cnn import ResidualBlock


class ResNetBranch(nn.Module):
    """
    ResNet branch for processing spectrogram features.
    
    Input: [B, 1, 64, 400] - Log-Mel Spectrogram
    Output: [B, 128] - Spectrogram embedding
    """
    def __init__(self, dropout=0.3):
        super().__init__()
        
        # Initial convolution
        self.conv_init = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )
        
        # Residual blocks with downsampling
        self.layer1 = self._make_layer(32, 32, stride=1)    # No downsample
        self.layer2 = self._make_layer(32, 64, stride=2)    # Downsample 2x
        self.layer3 = self._make_layer(64, 128, stride=2)   # Downsample 2x
        self.layer4 = self._make_layer(128, 256, stride=2)  # Downsample 2x
        
        # Global pooling and embedding
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(256, 128)
        
        # Initialize weights
        self._initialize_weights()
    
    def _make_layer(self, in_channels, out_channels, stride):
        """Create a residual layer with 2 residual blocks."""
        return nn.Sequential(
            ResidualBlock(in_channels, out_channels, stride),
            ResidualBlock(out_channels, out_channels, 1)
        )
    
    def _initialize_weights(self):
        """Initialize weights with He initialization."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # Input: [B, 1, 64, 400]
        x = self.conv_init(x)      # [B, 32, 64, 400]
        
        x = self.layer1(x)         # [B, 32, 64, 400]
        x = self.layer2(x)         # [B, 64, 32, 200]
        x = self.layer3(x)         # [B, 128, 16, 100]
        x = self.layer4(x)         # [B, 256, 8, 50]
        
        x = self.gap(x)            # [B, 256, 1, 1]
        x = x.view(x.size(0), -1)  # [B, 256]
        x = self.dropout(x)
        x = self.fc(x)             # [B, 128]
        
        return x


class EnvironmentalBranch(nn.Module):
    """
    MLP branch for processing environmental features.
    
    Input: [B, 12] - Environmental features
    Output: [B, 128] - Environmental embedding
    """
    def __init__(self, input_dim=12, dropout=0.2):
        super().__init__()
        
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(128, 128)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # Input: [B, 12]
        x = self.mlp(x)  # [B, 128]
        return x


class FusionLayer(nn.Module):
    """
    Fusion layer to combine spectrogram and environmental embeddings.
    
    Input: [B, 128] (spectrogram) + [B, 128] (environmental) = [B, 256]
    Output: [B, 128] - Fused representation
    """
    def __init__(self, dropout=0.2):
        super().__init__()
        
        # Concatenation-based fusion
        self.fusion = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, spectrogram_emb, environmental_emb):
        # Concatenate embeddings
        fused = torch.cat([spectrogram_emb, environmental_emb], dim=1)  # [B, 256]
        fused = self.fusion(fused)  # [B, 128]
        return fused


class BinaryHead(nn.Module):
    """
    Binary classification head: Real vs Fake.
    
    Input: [B, 128] - Fused representation
    Output: [B, 2] - Binary logits (real, fake)
    """
    def __init__(self, input_dim=128, dropout=0.2):
        super().__init__()
        
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 2)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # Input: [B, 128]
        x = self.classifier(x)  # [B, 2]
        return x


class MultiClassHead(nn.Module):
    """
    Multi-class classification head: Attack Type.
    
    Input: [B, 128] - Fused representation
    Output: [B, 4] - Multi-class logits (bonafide, synthesis, conversion, replay)
    """
    def __init__(self, input_dim=128, n_classes=4, dropout=0.2):
        super().__init__()
        
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_classes)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # Input: [B, 128]
        x = self.classifier(x)  # [B, 4]
        return x


class HybridResNetEnvironmental(nn.Module):
    """
    Hybrid model combining ResNet CNN (spectrogram) and MLP (environmental features).
    
    Architecture:
    1. ResNet Branch: [B, 1, 64, 400] → [B, 128]
    2. Environmental Branch: [B, 12] → [B, 128]
    3. Fusion Layer: [B, 256] → [B, 128]
    4. Binary Head: [B, 128] → [B, 2]
    5. MultiClass Head: [B, 128] → [B, 4]
    
    Inputs:
        spectrogram: [B, 1, 64, 400] - Log-Mel Spectrogram
        environmental: [B, 12] - Environmental features
    
    Outputs:
        binary_logits: [B, 2] - Real vs Fake
        multiclass_logits: [B, 4] - Attack Type
    """
    def __init__(self, n_attack_types=4, dropout=0.3):
        super().__init__()
        
        # Two branches
        self.resnet_branch = ResNetBranch(dropout=dropout)
        self.environmental_branch = EnvironmentalBranch(input_dim=12, dropout=0.2)
        
        # Fusion layer
        self.fusion = FusionLayer(dropout=0.2)
        
        # Output heads
        self.binary_head = BinaryHead(input_dim=128, dropout=0.2)
        self.multiclass_head = MultiClassHead(input_dim=128, n_classes=n_attack_types, dropout=0.2)
    
    def forward(self, spectrogram, environmental):
        """
        Forward pass.
        
        Args:
            spectrogram: [B, 1, 64, 400] - Log-Mel Spectrogram
            environmental: [B, 12] - Environmental features
        
        Returns:
            binary_logits: [B, 2] - Real vs Fake logits
            multiclass_logits: [B, 4] - Attack Type logits
        """
        # Process through branches
        spectrogram_emb = self.resnet_branch(spectrogram)  # [B, 128]
        environmental_emb = self.environmental_branch(environmental)  # [B, 128]
        
        # Fuse branches
        fused = self.fusion(spectrogram_emb, environmental_emb)  # [B, 128]
        
        # Generate outputs
        binary_logits = self.binary_head(fused)  # [B, 2]
        multiclass_logits = self.multiclass_head(fused)  # [B, 4]
        
        return binary_logits, multiclass_logits
    
    def get_embeddings(self, spectrogram, environmental):
        """
        Get intermediate embeddings (useful for analysis/visualization).
        
        Returns:
            spectrogram_emb: [B, 128]
            environmental_emb: [B, 128]
            fused_emb: [B, 128]
        """
        spectrogram_emb = self.resnet_branch(spectrogram)
        environmental_emb = self.environmental_branch(environmental)
        fused_emb = self.fusion(spectrogram_emb, environmental_emb)
        
        return spectrogram_emb, environmental_emb, fused_emb


if __name__ == "__main__":
    # Test the model
    print("="*80)
    print("Testing Hybrid ResNet-Environmental Model")
    print("="*80)
    
    model = HybridResNetEnvironmental(n_attack_types=4)
    
    print("\nModel Architecture:")
    print(model)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nTotal parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Test forward pass
    batch_size = 4
    spectrogram_input = torch.randn(batch_size, 1, 64, 400)
    environmental_input = torch.randn(batch_size, 12)
    
    print(f"\nInput shapes:")
    print(f"  Spectrogram: {spectrogram_input.shape}")
    print(f"  Environmental: {environmental_input.shape}")
    
    with torch.no_grad():
        binary_logits, multiclass_logits = model(spectrogram_input, environmental_input)
    
    print(f"\nOutput shapes:")
    print(f"  Binary logits: {binary_logits.shape}")
    print(f"  Multi-class logits: {multiclass_logits.shape}")
    
    # Test embeddings
    spec_emb, env_emb, fused_emb = model.get_embeddings(spectrogram_input, environmental_input)
    print(f"\nEmbedding shapes:")
    print(f"  Spectrogram embedding: {spec_emb.shape}")
    print(f"  Environmental embedding: {env_emb.shape}")
    print(f"  Fused embedding: {fused_emb.shape}")
    
    print("\n" + "="*80)
    print("✓ Model test completed successfully!")
    print("="*80)

