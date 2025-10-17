import torch.nn as nn

class LCNNBaseline(nn.Module):
    def __init__(self, n_classes=2):
        super().__init__()
        self.feature = nn.Sequential(
            nn.Conv2d(1,16,3,1,1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d((2,2)),
            nn.Conv2d(16,32,3,1,1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d((2,2)),
            nn.Conv2d(32,64,3,1,1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1))
        )
        self.fc = nn.Linear(64, n_classes)
    def forward(self, x):
        x = self.feature(x).flatten(1)
        return self.fc(x)
