import torch
import numpy as np
from torch.utils.data import IterableDataset

class StreamingFeatureDataset(IterableDataset):
    """
    Streams features directly from disk instead of keeping them in memory.
    Works with huge datasets of pre-extracted .npy feature files.
    """

    def __init__(self, df, feature_type="lfcc", max_frames=200, shuffle=False):
        self.paths = df[f"{feature_type}_path"].tolist()
        self.labels = df["label"].map({"bonafide": 1, "spoof": 0}).tolist()
        self.max_frames = max_frames
        self.shuffle = shuffle

    def _pad_or_trim(self, x):
        F, T = x.shape
        if T < self.max_frames:
            pad = self.max_frames - T
            x = np.pad(x, ((0, 0), (0, pad)), mode="constant")
        elif T > self.max_frames:
            x = x[:, :self.max_frames]
        return x

    def __iter__(self):
        index_order = np.arange(len(self.paths))
        if self.shuffle:
            np.random.shuffle(index_order)

        for i in index_order:
            feat_path = self.paths[i]
            label = self.labels[i]
            # mmap_mode="r" → loads from disk lazily
            x = np.load(feat_path, mmap_mode="r")
            x = self._pad_or_trim(x)
            x = torch.from_numpy(np.copy(x)).unsqueeze(0).float()
            y = torch.tensor(label).long()
            yield x, y
