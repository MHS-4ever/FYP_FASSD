import os
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset


class StreamingFeatureDataset(Dataset):
    """
    Streaming feature loader with HDF5 acceleration.
    Supports automatic fallback to .npy files if .h5 not found.
    """

    def __init__(self, df, feature_type="lfcc", max_frames=400, shuffle=True):
        self.df = df.reset_index(drop=True)
        self.feature_type = feature_type
        self.max_frames = max_frames
        self.shuffle = shuffle

        # detect source folders
        if len(df) == 0:
            raise ValueError("Empty dataframe provided to StreamingFeatureDataset.")

        # infer dataset root path from first file
        example_path = df["filepath"].iloc[0]
        if "features_augmented" in example_path.lower():
            self.base_dir = r"E:\FYP\data\features_augmented"
        else:
            self.base_dir = r"E:\FYP\data\features"

        # try to find packed .h5 file
        self.h5_path = os.path.join(self.base_dir, f"{feature_type}_packed.h5")
        if os.path.exists(self.h5_path):
            print(f"⚡ Using HDF5-accelerated loader → {self.h5_path}")
            self.h5_mode = True
            self.h5_file = h5py.File(self.h5_path, "r")
        else:
            print(f"📂 Using standard .npy loader (no HDF5 found)")
            self.h5_mode = False
            self.h5_file = None

    def __len__(self):
        return len(self.df)

    def _load_feature(self, file_path):
        """Load feature from .h5 if available, otherwise from .npy."""
        key = os.path.basename(file_path).replace(".npy", "")
        if self.h5_mode:
            try:
                arr = np.array(self.h5_file[key])
                return arr
            except KeyError:
                # if not found in .h5, fallback to .npy
                pass

        # fallback: load from .npy
        if os.path.exists(file_path):
            arr = np.load(file_path, allow_pickle=False)
            return arr
        else:
            raise FileNotFoundError(f"Feature file not found: {file_path}")

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        x = self._load_feature(row["filepath"])

        # crop or pad to fixed frame length
        T = x.shape[1]
        if T > self.max_frames:
            start = np.random.randint(0, T - self.max_frames)
            x = x[:, start:start + self.max_frames]
        elif T < self.max_frames:
            pad = np.zeros((x.shape[0], self.max_frames - T), dtype=np.float32)
            x = np.concatenate([x, pad], axis=1)

        # normalization (optional, helps stability)
        x = (x - np.mean(x)) / (np.std(x) + 1e-5)

        label = 1 if row["label"] == "spoof" else 0

        # convert to tensor
        x = torch.from_numpy(x.copy()).unsqueeze(0).float()
        y = torch.tensor(label, dtype=torch.long)
        return x, y

    def close(self):
        """Safely close the HDF5 file."""
        if self.h5_file is not None:
            self.h5_file.close()
