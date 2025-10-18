import numpy as np
import torch
from torch.utils.data import Dataset

def _to_1ft(x: np.ndarray):
    """
    Ensure [1, F, T] float32 tensor.
    Expects x as [F, T].
    """
    if x.ndim != 2:
        raise ValueError(f"Expected feature with shape [F,T], got {x.shape}")
    x = x.astype(np.float32)
    x = (x - x.mean()) / (x.std() + 1e-6)  # per-utterance norm
    return torch.from_numpy(x).unsqueeze(0)

def _pad_or_crop(x: torch.Tensor, target_T: int):
    """
    x: [1,F,T]  -> pad with zeros or center-crop to target_T
    """
    _, _, T = x.shape
    if T == target_T:
        return x
    if T < target_T:
        pad = target_T - T
        return torch.nn.functional.pad(x, (0, pad))
    # crop (center)
    start = max((T - target_T) // 2, 0)
    return x[:, :, start:start+target_T]

class FeatureDataset(Dataset):
    """
    feature_type: "lfcc" or "mel"
    target_T: frames after pad/crop (e.g. 400 ~ about 4s @ hop 10ms)
    """
    def __init__(self, df, feature_type="lfcc", target_T=400):
        self.df = df.reset_index(drop=True)
        self.feature_type = feature_type
        self.target_T = target_T

        # choose the column
        if feature_type == "lfcc":
            self.col = "lfcc_path"
        else:
            # allow either 'mel_path' or 'logmel_path'
            self.col = "mel_path" if "mel_path" in df.columns else "logmel_path"

        # map labels
        self.labels = self.df["label"].map({"bonafide": 1, "spoof": 0}).astype(int)

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        path = row[self.col]
        feat = np.load(path)              # [F,T]
        x = _to_1ft(feat)                 # [1,F,T]
        x = _pad_or_crop(x, self.target_T)
        y = self.labels.iloc[idx]
        return x, torch.tensor(y, dtype=torch.long)
