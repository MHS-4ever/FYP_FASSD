import numpy as np
import torch
from torch.utils.data import Dataset

class FeatureDataset(Dataset):
    def __init__(self, df, feature_type="lfcc", max_frames=200):
        
        #Args:
        #    df: Pandas DataFrame with feature paths + labels
        #    feature_type: "lfcc" or "mel"
        #    max_frames: Number of frames to pad/trim each sample to
        
        self.df = df
        self.feature_type = feature_type
        self.max_frames = max_frames
        self.label_map = {"bonafide": 1, "spoof": 0}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        feat_path = row[f"{self.feature_type}_path"]
        x = np.load(feat_path)  # shape [n_features, time]
        x = self._pad_or_trim(x)
        x = torch.tensor(x).unsqueeze(0).float()  # shape [1, F, T]

        y = self.label_map.get(row["label"], -1)
        return x, torch.tensor(y).long()

    def _pad_or_trim(self, x):
        """Pad or trim feature to fixed frame length"""
        F, T = x.shape
        if T < self.max_frames:
            pad_width = self.max_frames - T
            x = np.pad(x, ((0, 0), (0, pad_width)), mode="constant")
        elif T > self.max_frames:
            x = x[:, :self.max_frames]
        return x
