import torch.nn as nn

class LCNNBaseline(nn.Module):
    """
    Lightweight CNN for spectro features: input [B,1,F,T]
    """
    def __init__(self, n_classes=2):
        super().__init__()
        self.feat = nn.Sequential(
            nn.Conv2d(1, 16, 3, 1, 1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d((2,2)),
            nn.Conv2d(16, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d((2,2)),
            nn.Conv2d(32, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1))
        )
        self.fc = nn.Linear(64, n_classes)

    def forward(self, x):
        x = self.feat(x)      # [B,64,1,1]
        x = x.view(x.size(0), -1)
        return self.fc(x)
