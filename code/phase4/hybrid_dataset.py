"""
Hybrid Dataset for Loading Both Spectrogram and Environmental Features

This dataset class loads both spectrogram features (from logmel_packed.h5) and 
environmental features (from environmental_packed.h5) for training the hybrid model.
"""

import os
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset
import pandas as pd


class HybridFeatureDataset(Dataset):
    """
    Dataset class for loading both spectrogram and environmental features from HDF5.
    
    Features:
    - Loads spectrogram features from logmel_packed.h5
    - Loads environmental features from environmental_packed.h5
    - Returns both features along with binary and multiclass labels
    - Supports Windows multiprocessing (each worker opens its own HDF5 handle)
    """
    
    def __init__(self, df, spectrogram_h5_path, environmental_h5_path, 
                 environmental_scaler=None, max_frames=400, shuffle=True):
        """
        Initialize hybrid dataset.
        
        Args:
            df: DataFrame with columns: spectrogram_idx, environmental_idx, label, attack_type
            spectrogram_h5_path: Path to logmel_packed.h5 file
            environmental_h5_path: Path to environmental_packed.h5 file
            environmental_scaler: StandardScaler for environmental features (optional)
            max_frames: Maximum number of time frames for spectrogram (default: 400)
            shuffle: Whether to shuffle (for training) - not used here, but kept for consistency
        """
        self.df = df.reset_index(drop=True)
        self.max_frames = max_frames
        self.shuffle = shuffle
        self.environmental_scaler = environmental_scaler
        
        # Verify required columns exist
        required_cols = ['spectrogram_idx', 'environmental_idx', 'label']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {missing_cols}")
        
        # Filter samples that have both features
        valid_mask = (self.df['spectrogram_idx'] >= 0) & (self.df['environmental_idx'] >= 0)
        self.df = self.df[valid_mask].reset_index(drop=True)
        
        if len(self.df) == 0:
            raise ValueError("No valid samples with both spectrogram and environmental features!")
        
        # Store HDF5 paths (don't open here - causes pickle errors with multiprocessing)
        self.spectrogram_h5_path = spectrogram_h5_path
        self.environmental_h5_path = environmental_h5_path
        
        # Lazy HDF5 file handles (opened per worker)
        self.spectrogram_h5_file = None
        self.environmental_h5_file = None
        
        # Verify HDF5 files exist
        if not os.path.exists(self.spectrogram_h5_path):
            raise FileNotFoundError(f"Spectrogram HDF5 not found: {self.spectrogram_h5_path}")
        if not os.path.exists(self.environmental_h5_path):
            raise FileNotFoundError(f"Environmental HDF5 not found: {self.environmental_h5_path}")
        
        print(f"[HYBRID DATASET] Initialized with {len(self.df)} samples")
        print(f"[HYBRID DATASET] Spectrogram HDF5: {self.spectrogram_h5_path}")
        print(f"[HYBRID DATASET] Environmental HDF5: {self.environmental_h5_path}")
        if self.environmental_scaler is not None:
            print(f"[HYBRID DATASET] Using environmental scaler")
    
    def _ensure_h5_open(self):
        """Open HDF5 files lazily (safe inside each worker)."""
        if self.spectrogram_h5_file is None:
            self.spectrogram_h5_file = h5py.File(self.spectrogram_h5_path, 'r')
        if self.environmental_h5_file is None:
            self.environmental_h5_file = h5py.File(self.environmental_h5_path, 'r')
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        """
        Get a single sample.
        
        Returns:
            spectrogram: torch.Tensor of shape [1, 64, max_frames] - Log-Mel spectrogram
            environmental: torch.Tensor of shape [12] - Environmental features
            binary_label: torch.Tensor (0=bonafide, 1=spoof)
            multiclass_label: torch.Tensor (0=bonafide, 1=synthesis, 2=conversion, 3=replay)
        """
        row = self.df.iloc[idx]
        
        # Open HDF5 files if needed
        self._ensure_h5_open()
        
        # Load spectrogram feature
        spec_idx = int(row['spectrogram_idx'])
        spectrogram = np.array(self.spectrogram_h5_file['features'][spec_idx], dtype=np.float32)
        
        # Load environmental feature
        env_idx = int(row['environmental_idx'])
        environmental = np.array(self.environmental_h5_file['features'][env_idx], dtype=np.float32)
        
        # Process spectrogram: ensure correct shape [64, 400]
        if spectrogram.shape != (64, self.max_frames):
            # Handle shape mismatches
            if spectrogram.shape[1] > self.max_frames:
                # Crop if too long
                start = np.random.randint(0, spectrogram.shape[1] - self.max_frames) if self.shuffle else 0
                spectrogram = spectrogram[:, start:start + self.max_frames]
            elif spectrogram.shape[1] < self.max_frames:
                # Pad if too short
                pad_width = ((0, 0), (0, self.max_frames - spectrogram.shape[1]))
                spectrogram = np.pad(spectrogram, pad_width, mode='constant')
        
        # Normalize spectrogram (per-sample normalization)
        spectrogram = (spectrogram - np.mean(spectrogram)) / (np.std(spectrogram) + 1e-5)
        
        # Scale environmental features if scaler provided
        if self.environmental_scaler is not None:
            environmental = self.environmental_scaler.transform([environmental])[0]
        
        # Convert to tensors
        spectrogram_tensor = torch.from_numpy(spectrogram.copy()).unsqueeze(0).float()  # [1, 64, 400]
        environmental_tensor = torch.from_numpy(environmental.copy()).float()  # [12]
        
        # Get labels
        # Binary label: 0=bonafide, 1=spoof
        binary_label = 1 if row['label'] == 'spoof' else 0
        
        # Multiclass label: 0=bonafide, 1=synthesis, 2=conversion, 3=replay
        attack_type = row.get('attack_type', 'bonafide')
        attack_type_lower = str(attack_type).lower()
        if attack_type_lower == 'bonafide':
            multiclass_label = 0
        elif attack_type_lower == 'synthesis':
            multiclass_label = 1
        elif attack_type_lower == 'conversion':
            multiclass_label = 2
        elif attack_type_lower == 'replay':
            multiclass_label = 3
        else:
            # Default to bonafide if unknown
            multiclass_label = 0
        
        binary_label_tensor = torch.tensor(binary_label, dtype=torch.long)
        multiclass_label_tensor = torch.tensor(multiclass_label, dtype=torch.long)
        
        return spectrogram_tensor, environmental_tensor, binary_label_tensor, multiclass_label_tensor
    
    def close(self):
        """Safely close HDF5 files."""
        if self.spectrogram_h5_file is not None:
            self.spectrogram_h5_file.close()
            self.spectrogram_h5_file = None
        if self.environmental_h5_file is not None:
            self.environmental_h5_file.close()
            self.environmental_h5_file = None


def create_environmental_scaler(df, environmental_h5_path, output_path=None):
    """
    Create and optionally save a StandardScaler for environmental features.
    
    Args:
        df: DataFrame with environmental_idx column
        environmental_h5_path: Path to environmental_packed.h5
        output_path: Optional path to save scaler (if None, just return scaler)
    
    Returns:
        scaler: Fitted StandardScaler
    """
    from sklearn.preprocessing import StandardScaler
    import pickle
    
    print(f"[SCALER] Creating environmental feature scaler from {len(df)} samples...")
    
    # Load all environmental features
    environmental_features = []
    valid_indices = df[df['environmental_idx'] >= 0]['environmental_idx'].tolist()
    
    with h5py.File(environmental_h5_path, 'r') as h5f:
        for idx in valid_indices:
            feature = np.array(h5f['features'][idx], dtype=np.float32)
            environmental_features.append(feature)
    
    environmental_features = np.array(environmental_features)
    print(f"[SCALER] Loaded {len(environmental_features)} environmental features, shape: {environmental_features.shape}")
    
    # Fit scaler
    scaler = StandardScaler()
    scaler.fit(environmental_features)
    
    print(f"[SCALER] Scaler fitted (mean: {scaler.mean_}, std: {scaler.scale_})")
    
    # Save if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"[SCALER] Scaler saved to: {output_path}")
    
    return scaler


if __name__ == "__main__":
    # Test the dataset
    print("="*80)
    print("Testing HybridFeatureDataset")
    print("="*80)
    
    # Example usage (would need actual manifest)
    # df = pd.read_csv('data/features/features_manifest_unified.csv')
    # dataset = HybridFeatureDataset(
    #     df.head(100),
    #     spectrogram_h5_path='data/features/logmel_packed.h5',
    #     environmental_h5_path='data/features/environmental_packed.h5'
    # )
    # 
    # sample = dataset[0]
    # print(f"Spectrogram shape: {sample[0].shape}")
    # print(f"Environmental shape: {sample[1].shape}")
    # print(f"Binary label: {sample[2]}")
    # print(f"Multiclass label: {sample[3]}")
    
    print("\n[INFO] Dataset class ready. Use in training scripts.")

