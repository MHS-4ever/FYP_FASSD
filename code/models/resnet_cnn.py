import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    """
    Residual block with skip connection for audio features.
    """
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, 1, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Skip connection with dimension matching
        self.skip = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.skip = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
    
    def forward(self, x):
        identity = self.skip(x)
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        
        out += identity  # Skip connection
        out = self.relu(out)
        
        return out


class DeepResNetCNN(nn.Module):
    """
    Deeper CNN with ResNet-style skip connections for audio deepfake detection.
    
    Architecture:
    - Input: [B, 1, F, T] where F=64 (mel bins), T=400 (frames)
    - 4 residual blocks with increasing channels: 32->64->128->256
    - Global average pooling + dropout
    - Output: [B, 2] for binary classification
    """
    def __init__(self, n_classes=2, dropout=0.3):
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
        
        # Global pooling and classifier
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(256, n_classes)
        
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
        # Input: [B, 1, F, T]
        x = self.conv_init(x)      # [B, 32, F, T]
        
        x = self.layer1(x)         # [B, 32, F, T]
        x = self.layer2(x)         # [B, 64, F/2, T/2]
        x = self.layer3(x)         # [B, 128, F/4, T/4]
        x = self.layer4(x)         # [B, 256, F/8, T/8]
        
        x = self.gap(x)            # [B, 256, 1, 1]
        x = x.view(x.size(0), -1)  # [B, 256]
        x = self.dropout(x)
        x = self.fc(x)             # [B, 2]
        
        return x


if __name__ == "__main__":
    # Test the model
    model = DeepResNetCNN()
    print("Model Architecture:")
    print(model)
    print(f"\nTotal parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    
    # Test forward pass
    dummy_input = torch.randn(4, 1, 64, 400)  # [batch, channel, mel_bins, frames]
    output = model(dummy_input)
    print(f"\nInput shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")

