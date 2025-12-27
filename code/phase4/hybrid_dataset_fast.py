"""
FAST Hybrid Dataset for Phase 4 Training

Optimized for HDF5 random access performance:
- Sorted index batching to minimize disk seeks
- Chunked reads (fetch multiple samples per HDF5 access)
- Optional RAM caching for maximum speed
- Single-threaded HDF5 access (avoids multiprocessing overhead)

Usage:
    dataset = FastHybridDataset(manifest_df, spectrogram_h5_path, environmental_h5_path)
"""

import os
import h5py
import numpy as np
import torch
import time
from torch.utils.data import Dataset, Sampler
import pandas as pd
from collections import defaultdict


class FastHybridDataset(Dataset):
    """
    FAST Dataset class optimized for HDF5 access patterns.
    
    Key optimizations:
    - Pre-loads index mappings as contiguous arrays
    - Supports RAM caching for repeated access
    - Works with SortedBatchSampler for sequential HDF5 reads
    """
    
    def __init__(self, manifest_df, spectrogram_h5_path, environmental_h5_path, 
                 transform=None, unified_manifest_path=None, cache_in_ram=False,
                 cache_env_in_ram=True, pin_memory=True):
        self.df = manifest_df.reset_index(drop=True)
        self.spectrogram_h5_path = spectrogram_h5_path
        self.environmental_h5_path = environmental_h5_path
        self.transform = transform
        self.cache_in_ram = cache_in_ram
        self.cache_env_in_ram = cache_env_in_ram
        self.pin_memory = pin_memory
        
        # HDF5 file handles (single-threaded)
        self.spectrogram_h5 = None
        self.environmental_h5 = None
        self._spec_chunk_samples = None
        self._env_chunk_samples = None
        self._spec_n_samples = None
        self._env_n_samples = None
        
        # RAM cache (if enabled)
        self.spec_cache = {} if cache_in_ram else None
        self.env_cache = {} if cache_in_ram else None
        
        # Optional: cache tiny environmental features fully in RAM (fastest + avoids many small HDF5 reads)
        self._env_all = None
        if self.cache_env_in_ram:
            try:
                with h5py.File(self.environmental_h5_path, 'r') as f:
                    self._env_all = f['features'][:].astype(np.float32, copy=False)
                print(f"[DATASET] Cached environmental features in RAM: {self._env_all.shape} ({self._env_all.nbytes/1e9:.2f} GB)")
            except Exception as e:
                self._env_all = None
                print(f"[DATASET][WARN] Failed to cache environmental features in RAM, will read from HDF5. Reason: {e}")
        
        # Pre-compute all index mappings
        self._precompute_index_arrays(unified_manifest_path)
        self._precompute_labels()
        
        # Get sorted order for optimal HDF5 access
        self.sorted_order = np.argsort(self.h5_spec_indices)
        
        print(f"[DATASET] Fast dataset initialized with {len(self.df)} samples")
        print(f"[DATASET] RAM caching: {cache_in_ram}")
    
    def _precompute_index_arrays(self, unified_manifest_path=None):
        """Pre-compute all index mappings as numpy arrays."""
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
        
        # Pre-compute HDF5 indices for ALL samples
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
        """Pre-compute labels as numpy arrays."""
        self.binary_labels = (self.df['label'].values == 'spoof').astype(np.int64)
        attack_type_map = {'bonafide': 0, 'synthesis': 1, 'conversion': 2, 'replay': 3}
        self.multiclass_labels = self.df['attack_type'].map(attack_type_map).fillna(0).astype(np.int64).values
        self.domains = self.df['dataset'].values
    
    def _ensure_h5_open(self):
        """Open HDF5 files with optimized settings."""
        if self.spectrogram_h5 is None:
            self.spectrogram_h5 = h5py.File(
                self.spectrogram_h5_path, 'r',
                rdcc_nbytes=1024*1024*1024,  # 1GB cache
                rdcc_nslots=100003
            )
            spec_ds = self.spectrogram_h5['features']
            self._spec_n_samples = spec_ds.shape[0]
            self._spec_chunk_samples = spec_ds.chunks[0] if spec_ds.chunks is not None else 1
        if self.environmental_h5 is None:
            self.environmental_h5 = h5py.File(
                self.environmental_h5_path, 'r',
                rdcc_nbytes=1024*1024*128
            )
            env_ds = self.environmental_h5['features']
            self._env_n_samples = env_ds.shape[0]
            self._env_chunk_samples = env_ds.chunks[0] if env_ds.chunks is not None else 1
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        """Get a single sample with caching support."""
        self._ensure_h5_open()
        
        spec_h5_idx = self.h5_spec_indices[idx]
        env_h5_idx = self.h5_env_indices[idx]
        
        # Check cache first
        if self.spec_cache is not None and idx in self.spec_cache:
            spectrogram = self.spec_cache[idx]
            environmental = self.env_cache[idx]
        else:
            # Load from HDF5
            spectrogram = self.spectrogram_h5['features'][spec_h5_idx]
            if self._env_all is not None:
                environmental = self._env_all[env_h5_idx]
            else:
                environmental = self.environmental_h5['features'][env_h5_idx]
            
            spectrogram = np.array(spectrogram, dtype=np.float32)[np.newaxis, :, :]
            environmental = np.array(environmental, dtype=np.float32)
            
            # Normalize
            spec_mean = spectrogram.mean()
            spec_std = spectrogram.std() + 1e-5
            spectrogram = (spectrogram - spec_mean) / spec_std
            
            env_mean = environmental.mean()
            env_std = environmental.std() + 1e-5
            environmental = (environmental - env_mean) / env_std
            
            # Cache if enabled
            if self.spec_cache is not None:
                self.spec_cache[idx] = spectrogram
                self.env_cache[idx] = environmental
        
        if self.transform:
            spectrogram = self.transform(spectrogram)
        
        return {
            'spectrogram': torch.from_numpy(spectrogram).float(),
            'environmental': torch.from_numpy(environmental).float(),
            'binary_label': torch.tensor(self.binary_labels[idx], dtype=torch.long),
            'multiclass_label': torch.tensor(self.multiclass_labels[idx], dtype=torch.long),
            'domain': self.domains[idx],
            'manifest_idx': self.unified_indices[idx]
        }
    
    def _read_h5_by_chunks(self, ds, h5_indices, chunk_samples, n_samples_total):
        """
        Read arbitrary HDF5 indices efficiently by grouping them by chunk and doing slice reads.
        
        This avoids h5py fancy indexing (which often degenerates into many small reads).
        For chunked HDF5 (e.g., chunks=(256,64,400)), this makes batches require ~1-2 reads.
        """
        h5_indices = np.asarray(h5_indices, dtype=np.int64)
        b = h5_indices.shape[0]
        
        # Group by chunk id (small number of unique chunks per batch when loader is sorted by H5 index)
        chunk_ids = h5_indices // int(chunk_samples)
        order = np.argsort(chunk_ids, kind='mergesort')
        chunk_ids_sorted = chunk_ids[order]
        h5_sorted = h5_indices[order]
        
        # Allocate output (float32)
        # ds is either [N,64,400] or [N,12]
        out_shape = (b,) + tuple(ds.shape[1:])
        out = np.empty(out_shape, dtype=np.float32)
        
        i = 0
        while i < b:
            cid = int(chunk_ids_sorted[i])
            j = i + 1
            while j < b and int(chunk_ids_sorted[j]) == cid:
                j += 1
            
            chunk_start = cid * int(chunk_samples)
            chunk_end = min(chunk_start + int(chunk_samples), int(n_samples_total))
            
            # Read only the minimal continuous slice that covers needed indices within this chunk.
            # This reduces CPU/memory copying vs always materializing the full chunk.
            local = h5_sorted[i:j] - chunk_start
            local_min = int(local.min())
            local_max = int(local.max())
            read_start = chunk_start + local_min
            read_end = min(chunk_start + local_max + 1, chunk_end)
            
            chunk = np.asarray(ds[read_start:read_end], dtype=np.float32)
            
            # Gather needed rows from the read slice
            local_in_read = local - local_min
            out_pos = order[i:j]
            out[out_pos] = chunk[local_in_read]
            
            i = j
        
        return out
    
    def get_batch_direct(self, indices):
        """
        FAST: Get a batch with chunk-aligned slice reads (works even when indices have gaps).
        
        Key fix:
        - Avoid h5py fancy indexing for batch loads (often becomes N small reads)
        - Instead: group indices by HDF5 chunk and slice-read each chunk once
        """
        self._ensure_h5_open()
        
        indices = np.array(indices)
        batch_size = len(indices)
        
        # Get HDF5 indices for this batch
        h5_spec_indices = self.h5_spec_indices[indices]
        h5_env_indices = self.h5_env_indices[indices]

        # Spectrograms: heavy tensor -> must be chunk-slice read
        spec_ds = self.spectrogram_h5['features']
        spec_chunk = self._spec_chunk_samples or (spec_ds.chunks[0] if spec_ds.chunks is not None else 1)
        spec_n = self._spec_n_samples or spec_ds.shape[0]
        spec_data = self._read_h5_by_chunks(spec_ds, h5_spec_indices, spec_chunk, spec_n)  # [B,64,400]
        spectrograms = spec_data[:, np.newaxis, :, :]  # [B,1,64,400]
        
        # Environmental: tiny. Prefer RAM cache if available, else chunk-slice read too.
        if self._env_all is not None:
            environmentals = self._env_all[h5_env_indices]
        else:
            env_ds = self.environmental_h5['features']
            env_chunk = self._env_chunk_samples or (env_ds.chunks[0] if env_ds.chunks is not None else 1)
            env_n = self._env_n_samples or env_ds.shape[0]
            environmentals = self._read_h5_by_chunks(env_ds, h5_env_indices, env_chunk, env_n)  # [B,12]
        
        # Vectorized normalization (much faster than per-sample loop)
        spec_mean = spectrograms.mean(axis=(2, 3), keepdims=True)
        spec_std = spectrograms.std(axis=(2, 3), keepdims=True) + 1e-5
        spectrograms = (spectrograms - spec_mean) / spec_std
        
        env_mean = environmentals.mean(axis=1, keepdims=True)
        env_std = environmentals.std(axis=1, keepdims=True) + 1e-5
        environmentals = (environmentals - env_mean) / env_std
        
        # Gather labels (already pre-computed as arrays)
        binary_labels = self.binary_labels[indices]
        multiclass_labels = self.multiclass_labels[indices]
        domains = [self.domains[i] for i in indices]
        manifest_indices = self.unified_indices[indices]
        
        return {
            'spectrogram': torch.from_numpy(spectrograms.astype(np.float32, copy=False)).contiguous(),
            'environmental': torch.from_numpy(environmentals.astype(np.float32, copy=False)).contiguous(),
            'binary_label': torch.from_numpy(binary_labels).long(),
            'multiclass_label': torch.from_numpy(multiclass_labels).long(),
            'domain': domains,
            'manifest_idx': manifest_indices.tolist()
        }
    
    def close(self):
        """Close HDF5 files."""
        if self.spectrogram_h5 is not None:
            self.spectrogram_h5.close()
            self.spectrogram_h5 = None
        if self.environmental_h5 is not None:
            self.environmental_h5.close()
            self.environmental_h5 = None
        if self.spec_cache is not None:
            self.spec_cache.clear()
            self.env_cache.clear()
    
    def __del__(self):
        self.close()


class SortedBatchSampler(Sampler):
    """
    Sampler that yields batches with sorted HDF5 indices to minimize disk seeks.
    
    Within each epoch:
    1. Shuffles at batch level (not sample level)
    2. Each batch contains samples with nearby HDF5 indices
    """
    
    def __init__(self, dataset, batch_size, shuffle=True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        # Sort by HDF5 index
        self.sorted_indices = np.argsort(dataset.h5_spec_indices)
        
        # Create batches of nearby indices
        n_samples = len(dataset)
        self.batches = []
        for i in range(0, n_samples, batch_size):
            batch = self.sorted_indices[i:i+batch_size].tolist()
            self.batches.append(batch)
        
        print(f"[SAMPLER] Created {len(self.batches)} sorted batches")
    
    def __iter__(self):
        if self.shuffle:
            # Shuffle batches, not individual samples
            batch_order = np.random.permutation(len(self.batches))
            for batch_idx in batch_order:
                yield from self.batches[batch_idx]
        else:
            for batch in self.batches:
                yield from batch
    
    def __len__(self):
        return len(self.dataset)


class ChunkedDataLoader:
    """
    Custom data loader that uses chunked HDF5 reads for maximum speed.
    
    Instead of using PyTorch DataLoader (which calls __getitem__ per sample),
    this loads entire batches at once using get_batch_direct().
    """
    
    def __init__(self, dataset, batch_size, shuffle=True, drop_last=False):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_last = drop_last
        
        # Sort indices by HDF5 position
        self.sorted_indices = np.argsort(dataset.h5_spec_indices)
        
        # Create batches
        n_samples = len(dataset)
        self.batches = []
        for i in range(0, n_samples, batch_size):
            batch = self.sorted_indices[i:i+batch_size]
            if len(batch) == batch_size or not drop_last:
                self.batches.append(batch)
    
    def __iter__(self):
        # Shuffle batch order (not sample order within batches)
        if self.shuffle:
            batch_order = np.random.permutation(len(self.batches))
        else:
            batch_order = range(len(self.batches))
        
        for batch_idx in batch_order:
            batch_indices = self.batches[batch_idx]
            t0 = time.perf_counter()
            batch = self.dataset.get_batch_direct(batch_indices)
            batch['_load_ms'] = (time.perf_counter() - t0) * 1000.0
            # Pin memory so .to(device, non_blocking=True) actually overlaps transfer
            if self.dataset.pin_memory and torch.cuda.is_available():
                batch['spectrogram'] = batch['spectrogram'].pin_memory()
                batch['environmental'] = batch['environmental'].pin_memory()
                batch['binary_label'] = batch['binary_label'].pin_memory()
                batch['multiclass_label'] = batch['multiclass_label'].pin_memory()
            yield batch
    
    def __len__(self):
        return len(self.batches)


def collate_fn(batch):
    """Standard collate function for compatibility."""
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

