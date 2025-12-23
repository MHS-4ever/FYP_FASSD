"""
Hybrid Dataset for Phase 4 Training

Loads both spectrogram and environmental features from HDF5 files efficiently.
Optimized for fast data loading with proper Windows multiprocessing support.

OPTIMIZED FOR SPEED:
- Pre-computed unified manifest index lookup (stored as array, not dict per sample)
- Direct HDF5 index access (no filepath lookup per sample)
- Lazy HDF5 file opening (safe for Windows multiprocessing)

Usage:
    dataset = HybridDataset(manifest_df, spectrogram_h5_path, environmental_h5_path)
"""

import os
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset
import pandas as pd


class HybridDataset(Dataset):
    """
    Dataset class for loading hybrid features (spectrogram + environmental) from HDF5.
    
    SPEED OPTIMIZATIONS:
    - Pre-computed index arrays (no dict lookup per sample)
    - Direct HDF5 sequential access where possible
    - Lazy file opening for Windows multiprocessing safety
    - Minimal per-sample computation
    
    Inputs:
        manifest_df: DataFrame with columns: filepath, label, attack_type, dataset, etc.
        spectrogram_h5_path: Path to logmel_packed.h5
        environmental_h5_path: Path to environmental_packed.h5
        transform: Optional transform function
    """
    
    def __init__(self, manifest_df, spectrogram_h5_path, environmental_h5_path, transform=None, unified_manifest_path=None):
        self.df = manifest_df.reset_index(drop=True)
        self.spectrogram_h5_path = spectrogram_h5_path
        self.environmental_h5_path = environmental_h5_path
        self.transform = transform
        
        # Lazy HDF5 file handles (opened per worker)
        self.spectrogram_h5 = None
        self.environmental_h5 = None
        
        # Check if HDF5 files exist
        if not os.path.exists(spectrogram_h5_path):
            raise FileNotFoundError(f"Spectrogram HDF5 not found: {spectrogram_h5_path}")
        if not os.path.exists(environmental_h5_path):
            raise FileNotFoundError(f"Environmental HDF5 not found: {environmental_h5_path}")
        
        # Pre-compute all index mappings as numpy arrays for fast access
        self._precompute_index_arrays(unified_manifest_path)
        
        # Pre-extract labels as numpy arrays (avoid pandas per-sample access)
        self._precompute_labels()
        
        print(f"[DATASET] Initialized with {len(self.df)} samples")
        print(f"[DATASET] Spectrogram HDF5: {spectrogram_h5_path}")
        print(f"[DATASET] Environmental HDF5: {environmental_h5_path}")
    
    def _precompute_index_arrays(self, unified_manifest_path=None):
        """
        Pre-compute all index mappings as numpy arrays for O(1) access.
        This is the key optimization - no dict/filepath lookup per sample.
        """
        # Load unified manifest
        if unified_manifest_path is None:
            unified_manifest_path = 'data/manifests/unified_manifest.csv'
        
        if not os.path.exists(unified_manifest_path):
            raise FileNotFoundError(f"Unified manifest required: {unified_manifest_path}")
        
        # Create filepath -> unified_idx mapping
        unified_df = pd.read_csv(unified_manifest_path, low_memory=False, usecols=['filepath'])
        filepath_to_unified_idx = dict(zip(unified_df['filepath'], range(len(unified_df))))
        
        # Load HDF5 index mappings
        with h5py.File(self.spectrogram_h5_path, 'r') as f:
            if 'indices' in f:
                manifest_indices = f['indices/manifest_idx'][:]
                h5_indices = f['indices/h5_idx'][:]
                unified_to_h5_spec = dict(zip(manifest_indices, h5_indices))
            else:
                unified_to_h5_spec = None
        
        with h5py.File(self.environmental_h5_path, 'r') as f:
            if 'indices' in f:
                manifest_indices = f['indices/manifest_idx'][:]
                h5_indices = f['indices/h5_idx'][:]
                unified_to_h5_env = dict(zip(manifest_indices, h5_indices))
            else:
                unified_to_h5_env = None
        
        # Pre-compute HDF5 indices for ALL samples in this dataset
        n_samples = len(self.df)
        self.h5_spec_indices = np.zeros(n_samples, dtype=np.int64)
        self.h5_env_indices = np.zeros(n_samples, dtype=np.int64)
        self.unified_indices = np.zeros(n_samples, dtype=np.int64)
        
        filepaths = self.df['filepath'].values
        for i, fp in enumerate(filepaths):
            unified_idx = filepath_to_unified_idx.get(fp)
            if unified_idx is None:
                raise ValueError(f"Filepath not found in unified manifest: {fp}")
            
            self.unified_indices[i] = unified_idx
            
            if unified_to_h5_spec is not None:
                self.h5_spec_indices[i] = unified_to_h5_spec.get(unified_idx, unified_idx)
            else:
                self.h5_spec_indices[i] = unified_idx
            
            if unified_to_h5_env is not None:
                self.h5_env_indices[i] = unified_to_h5_env.get(unified_idx, unified_idx)
            else:
                self.h5_env_indices[i] = unified_idx
        
        print(f"[DATASET] Pre-computed {n_samples} index mappings")
    
    def _precompute_labels(self):
        """Pre-compute labels as numpy arrays for fast access."""
        # Binary labels: 0=bonafide, 1=spoof
        self.binary_labels = (self.df['label'].values == 'spoof').astype(np.int64)
        
        # Multi-class labels: 0=bonafide, 1=synthesis, 2=conversion, 3=replay
        attack_type_map = {'bonafide': 0, 'synthesis': 1, 'conversion': 2, 'replay': 3}
        self.multiclass_labels = self.df['attack_type'].map(attack_type_map).fillna(0).astype(np.int64).values
        
        # Domain labels
        self.domains = self.df['dataset'].values
    
    def _ensure_h5_open(self):
        """Open HDF5 files lazily (safe for multiprocessing - each worker opens its own)."""
        if self.spectrogram_h5 is None:
            # Large cache for better chunk reuse (512MB for spectrograms)
            self.spectrogram_h5 = h5py.File(
                self.spectrogram_h5_path, 'r',
                rdcc_nbytes=1024*1024*512,  # 512MB chunk cache
                rdcc_nslots=100003  # Prime number for better hash distribution
            )
        if self.environmental_h5 is None:
            self.environmental_h5 = h5py.File(
                self.environmental_h5_path, 'r',
                rdcc_nbytes=1024*1024*64  # 64MB cache
            )
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        """
        Get a single sample. OPTIMIZED for speed.
        
        Returns:
            spectrogram: [1, 64, 400] - Log-Mel Spectrogram (normalized)
            environmental: [12] - Environmental features (normalized)
            binary_label: int - 0=bonafide, 1=spoof
            multiclass_label: int - 0=bonafide, 1=synthesis, 2=conversion, 3=replay
            domain: str - dataset domain (ASVspoof/RealWorld)
        """
        # Ensure HDF5 files are open
        self._ensure_h5_open()
        
        # Get pre-computed HDF5 indices (O(1) array access, no dict/filepath lookup)
        spec_h5_idx = self.h5_spec_indices[idx]
        env_h5_idx = self.h5_env_indices[idx]
        
        # Load features from HDF5
        spectrogram = self.spectrogram_h5['features'][spec_h5_idx]
        environmental = self.environmental_h5['features'][env_h5_idx]
        
        # Convert to numpy and add channel dimension
        spectrogram = np.array(spectrogram, dtype=np.float32)[np.newaxis, :, :]  # [1, 64, 400]
        environmental = np.array(environmental, dtype=np.float32)  # [12]
        
        # Normalize features (fast vectorized operations)
        spec_mean = spectrogram.mean()
        spec_std = spectrogram.std() + 1e-5
        spectrogram = (spectrogram - spec_mean) / spec_std
        
        env_mean = environmental.mean()
        env_std = environmental.std() + 1e-5
        environmental = (environmental - env_mean) / env_std
        
        # Apply transform if provided
        if self.transform:
            spectrogram = self.transform(spectrogram)
        
        # Get pre-computed labels (O(1) array access)
        binary_label = self.binary_labels[idx]
        multiclass_label = self.multiclass_labels[idx]
        domain = self.domains[idx]
        
        return {
            'spectrogram': torch.from_numpy(spectrogram).float(),
            'environmental': torch.from_numpy(environmental).float(),
            'binary_label': torch.tensor(binary_label, dtype=torch.long),
            'multiclass_label': torch.tensor(multiclass_label, dtype=torch.long),
            'domain': domain,
            'manifest_idx': self.unified_indices[idx]
        }
    
    def close(self):
        """Safely close HDF5 files."""
        if self.spectrogram_h5 is not None:
            self.spectrogram_h5.close()
            self.spectrogram_h5 = None
        if self.environmental_h5 is not None:
            self.environmental_h5.close()
            self.environmental_h5 = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


def collate_fn(batch):
    """
    Custom collate function for HybridDataset.
    
    Combines batch items into tensors, handling variable-length sequences if needed.
    """
    spectrograms = torch.stack([item['spectrogram'] for item in batch])
    environmental = torch.stack([item['environmental'] for item in batch])
    binary_labels = torch.stack([item['binary_label'] for item in batch])
    multiclass_labels = torch.stack([item['multiclass_label'] for item in batch])
    domains = [item['domain'] for item in batch]
    manifest_indices = [item['manifest_idx'] for item in batch]
    
    return {
        'spectrogram': spectrograms,
        'environmental': environmental,
        'binary_label': binary_labels,
        'multiclass_label': multiclass_labels,
        'domain': domains,
        'manifest_idx': manifest_indices
    }

