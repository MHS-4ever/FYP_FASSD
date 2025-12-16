import os
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset


class StreamingFeatureDataset(Dataset):
    """
    Streaming feature loader with HDF5 acceleration.
    ✅ Safe for Windows multiprocessing (each worker opens its own handle).
    ✅ Supports 'filepath', 'lfcc_path', or 'mel_path' columns.
    ✅ Automatically falls back to .npy files if HDF5 not found.
    """

    def __init__(self, df, feature_type="lfcc", max_frames=400, shuffle=True):
        self.df = df.reset_index(drop=True)
        self.feature_type = feature_type
        self.max_frames = max_frames
        self.shuffle = shuffle

        # Detect which column contains feature paths
        if "filepath" in df.columns:
            self.path_col = "filepath"
        elif "lfcc_path" in df.columns:
            self.path_col = "lfcc_path"
        elif "mel_path" in df.columns:
            self.path_col = "mel_path"
        else:
            raise KeyError("No valid feature path column found (expected 'filepath', 'lfcc_path', or 'mel_path').")

        example_path = df[self.path_col].iloc[0]

        # Determine base folder and possible HDF5 file
        if "features_augmented" in example_path.lower():
            self.base_dir = r"E:\FYP\data\features_augmented"
        else:
            self.base_dir = r"E:\FYP\data\features"

        # Map feature_type to actual HDF5 filename (mel -> logmel)
        h5_feature_name = "logmel" if feature_type == "mel" else feature_type
        self.h5_path = os.path.join(self.base_dir, f"{h5_feature_name}_packed.h5")
        self.h5_mode = os.path.exists(self.h5_path)
        self.h5_path_to_open = self.h5_path if self.h5_mode else None

        # Important: do NOT open the file here (causes pickle error)
        self.h5_file = None

        if self.h5_mode:
            print(f"[HDF5] HDF5 mode enabled -> {self.h5_path}")
        else:
            print(f"[NPY] Using .npy loader (no HDF5 found).")

    def __len__(self):
        return len(self.df)

    def _ensure_h5_open(self):
        """Open HDF5 file lazily (safe inside each worker)."""
        if self.h5_mode and self.h5_file is None:
            self.h5_file = h5py.File(self.h5_path_to_open, "r")

    def _load_feature(self, file_path):
        """Load a feature from HDF5 or .npy fallback."""
        key = os.path.basename(file_path).replace(".npy", "")

        # HDF5 fast path
        if self.h5_mode:
            self._ensure_h5_open()
            if key in self.h5_file:
                return np.array(self.h5_file[key])

        # fallback: load from .npy
        if os.path.exists(file_path):
            return np.load(file_path, allow_pickle=False)

        raise FileNotFoundError(f"Feature not found: {file_path}")

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        file_path = row[self.path_col]
        x = self._load_feature(file_path)

        # Crop or pad to max_frames
        T = x.shape[1]
        if T > self.max_frames:
            start = np.random.randint(0, T - self.max_frames)
            x = x[:, start:start + self.max_frames]
        elif T < self.max_frames:
            pad = np.zeros((x.shape[0], self.max_frames - T), dtype=np.float32)
            x = np.concatenate([x, pad], axis=1)

        # Normalize
        x = (x - np.mean(x)) / (np.std(x) + 1e-5)

        label = 1 if row["label"] == "spoof" else 0
        x = torch.from_numpy(x.copy()).unsqueeze(0).float()
        y = torch.tensor(label, dtype=torch.long)
        return x, y

    def close(self):
        """Safely close HDF5 file."""
        if self.h5_file is not None:
            self.h5_file.close()
