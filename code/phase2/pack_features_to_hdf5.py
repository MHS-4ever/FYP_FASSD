"""
Pack Features to HDF5 for Phase 2

Packs extracted spectrogram and environmental features into HDF5 format for efficient loading.
Creates two HDF5 files:
1. logmel_packed.h5 - Spectrogram features [N, 64, 400]
2. environmental_packed.h5 - Environmental features [N, 12]

Also creates an updated manifest with feature indices linking audio files to feature locations.

Usage:
    python pack_features_to_hdf5.py --manifest data/manifests/unified_manifest.csv --spectrogram_dir data/features/spectrograms --environmental_dir data/features/environmental --output_dir data/features
"""

import argparse
import os
import sys
import h5py
import numpy as np
import pandas as pd
from tqdm import tqdm
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


def pack_spectrograms(manifest_df, spectrogram_dir, output_path, num_workers=None, batch_size=500):
    """
    Pack spectrogram features into HDF5.
    
    Args:
        manifest_df: DataFrame with filepath column
        spectrogram_dir: Directory containing .npy spectrogram files
        output_path: Path to output HDF5 file
    
    Returns:
        indices: Dictionary mapping manifest row indices to HDF5 indices
        metadata: Metadata dictionary
    """
    print(f"\n[PACK] Packing spectrograms to: {output_path}")
    
    # Collect all feature files
    feature_files = []
    indices = {}
    valid_indices = []
    
    for idx, row in tqdm(manifest_df.iterrows(), total=len(manifest_df), desc="Collecting spectrograms"):
        audio_path = row['filepath']
        audio_basename = os.path.basename(audio_path)
        audio_name = os.path.splitext(audio_basename)[0]
        # Match the naming convention from extraction (index prefix)
        feature_path = os.path.join(spectrogram_dir, f"{idx:08d}_{audio_name}_logmel.npy")
        
        if os.path.exists(feature_path):
            feature_files.append(feature_path)
            indices[idx] = len(valid_indices)
            valid_indices.append(idx)
        else:
            indices[idx] = -1  # Missing feature
    
    print(f"[INFO] Found {len(feature_files)} spectrogram files")
    
    if len(feature_files) == 0:
        print("[ERROR] No spectrogram files found!")
        return None, None
    
    # Load first file to get shape
    sample = np.load(feature_files[0])
    expected_shape = sample.shape
    print(f"[INFO] Expected shape: {expected_shape}")
    
    # Create HDF5 file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Calculate optimal chunk size (balance between memory and I/O efficiency)
    # Chunk size: ~100MB per chunk (adjust based on feature size)
    feature_size = np.prod(expected_shape) * 4  # 4 bytes per float32
    chunk_size = max(1, min(1000, int(100 * 1024 * 1024 / feature_size)))  # ~100MB chunks
    
    # Determine number of workers (use all available CPU cores)
    if num_workers is None:
        num_workers = min(multiprocessing.cpu_count(), 32)  # Cap at 32 to avoid overhead
    print(f"[INFO] Using {num_workers} parallel workers for file I/O")
    
    def load_and_process_feature(feature_path):
        """Load and process a single feature file."""
        try:
            feature = np.load(feature_path)
            if feature.shape != expected_shape:
                # Pad or truncate if needed
                if feature.shape[0] == expected_shape[0]:
                    if feature.shape[1] < expected_shape[1]:
                        feature = np.pad(feature, ((0, 0), (0, expected_shape[1] - feature.shape[1])), mode='constant')
                    else:
                        feature = feature[:, :expected_shape[1]]
                else:
                    # Shape mismatch - fill with zeros
                    feature = np.zeros(expected_shape, dtype=np.float32)
            return feature, None
        except Exception as e:
            return np.zeros(expected_shape, dtype=np.float32), str(e)
    
    with h5py.File(output_path, 'w') as h5f:
        # Create dataset with chunking for better performance
        dataset = h5f.create_dataset(
            'features',
            shape=(len(feature_files), *expected_shape),
            dtype=np.float32,
            compression='gzip',
            compression_opts=1,  # Lower compression for faster writes (1-9, 1 is fastest)
            chunks=(chunk_size, *expected_shape)  # Enable chunking
        )
        
        # Batch processing with parallel file loading
        num_batches = (len(feature_files) + batch_size - 1) // batch_size
        
        for batch_idx in tqdm(range(num_batches), desc="Packing spectrograms"):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(feature_files))
            batch_files = feature_files[start_idx:end_idx]
            
            # Load batch in parallel using ThreadPoolExecutor (better for I/O)
            batch_data = [None] * len(batch_files)
            errors = []
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks
                future_to_idx = {
                    executor.submit(load_and_process_feature, feature_path): i
                    for i, feature_path in enumerate(batch_files)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        feature, error = future.result()
                        batch_data[idx] = feature
                        if error:
                            errors.append((batch_files[idx], error))
                    except Exception as e:
                        batch_data[idx] = np.zeros(expected_shape, dtype=np.float32)
                        errors.append((batch_files[idx], str(e)))
            
            # Report errors
            for file_path, error_msg in errors:
                tqdm.write(f"[ERROR] Failed to load {file_path}: {error_msg}")
            
            # Write batch to HDF5
            if batch_data:
                batch_array = np.stack(batch_data, axis=0)
                dataset[start_idx:end_idx] = batch_array
        
        # Store indices mapping as a single array (much more efficient)
        # Create arrays for manifest indices and HDF5 indices
        manifest_indices = np.array(list(indices.keys()), dtype=np.int64)
        h5_indices = np.array([indices[idx] for idx in manifest_indices], dtype=np.int32)
        
        indices_group = h5f.create_group('indices')
        indices_group.create_dataset('manifest_idx', data=manifest_indices, compression='gzip', compression_opts=1)
        indices_group.create_dataset('h5_idx', data=h5_indices, compression='gzip', compression_opts=1)
        
        # Store metadata
        metadata_group = h5f.create_group('metadata')
        metadata_group.attrs['num_samples'] = len(feature_files)
        metadata_group.attrs['feature_shape'] = expected_shape
        metadata_group.attrs['feature_type'] = 'logmel_spectrogram'
        metadata_group.attrs['sample_rate'] = 16000
        metadata_group.attrs['n_mels'] = 64
        metadata_group.attrs['n_frames'] = 400
    
    file_size_gb = os.path.getsize(output_path) / 1e9
    print(f"[OK] Packed {len(feature_files)} spectrograms")
    print(f"[SIZE] File size: {file_size_gb:.2f} GB")
    
    return indices, {
        'num_samples': len(feature_files),
        'feature_shape': expected_shape,
        'file_size_gb': file_size_gb
    }


def pack_environmental(manifest_df, environmental_dir, output_path, num_workers=None, batch_size=500):
    """
    Pack environmental features into HDF5.
    
    Args:
        manifest_df: DataFrame with filepath column
        environmental_dir: Directory containing .npy environmental feature files
        output_path: Path to output HDF5 file
    
    Returns:
        indices: Dictionary mapping manifest row indices to HDF5 indices
        metadata: Metadata dictionary
    """
    print(f"\n[PACK] Packing environmental features to: {output_path}")
    
    # Collect all feature files
    feature_files = []
    indices = {}
    valid_indices = []
    
    for idx, row in tqdm(manifest_df.iterrows(), total=len(manifest_df), desc="Collecting environmental features"):
        audio_path = row['filepath']
        audio_basename = os.path.basename(audio_path)
        audio_name = os.path.splitext(audio_basename)[0]
        # Match the naming convention from extraction (index prefix)
        feature_path = os.path.join(environmental_dir, f"{idx:08d}_{audio_name}_env.npy")
        
        if os.path.exists(feature_path):
            feature_files.append(feature_path)
            indices[idx] = len(valid_indices)
            valid_indices.append(idx)
        else:
            indices[idx] = -1  # Missing feature
    
    print(f"[INFO] Found {len(feature_files)} environmental feature files")
    
    if len(feature_files) == 0:
        print("[ERROR] No environmental feature files found!")
        return None, None
    
    # Load first file to get shape
    sample = np.load(feature_files[0])
    expected_shape = sample.shape
    print(f"[INFO] Expected shape: {expected_shape}")
    
    # Create HDF5 file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    feature_names = [
        'rt60', 'drr', 'snr', 'background_level', 'silence_ratio',
        'spectral_tilt', 'spectral_flatness', 'spectral_rolloff',
        'cleanliness_score', 'high_freq_content', 'background_consistency',
        'env_stability'
    ]
    
    # Calculate optimal chunk size
    feature_size = np.prod(expected_shape) * 4  # 4 bytes per float32
    chunk_size = max(1, min(1000, int(100 * 1024 * 1024 / feature_size)))  # ~100MB chunks
    
    # Determine number of workers (use all available CPU cores)
    if num_workers is None:
        num_workers = min(multiprocessing.cpu_count(), 32)  # Cap at 32 to avoid overhead
    print(f"[INFO] Using {num_workers} parallel workers for file I/O")
    
    def load_and_process_feature(feature_path):
        """Load and process a single environmental feature file."""
        try:
            feature = np.load(feature_path)
            if feature.shape != expected_shape:
                # Pad or truncate if needed
                if len(feature) < len(expected_shape):
                    feature = np.pad(feature, (0, len(expected_shape) - len(feature)), mode='constant')
                else:
                    feature = feature[:len(expected_shape)]
            return feature, None
        except Exception as e:
            return np.zeros(expected_shape, dtype=np.float32), str(e)
    
    with h5py.File(output_path, 'w') as h5f:
        # Create dataset with chunking for better performance
        dataset = h5f.create_dataset(
            'features',
            shape=(len(feature_files), *expected_shape),
            dtype=np.float32,
            compression='gzip',
            compression_opts=1,  # Lower compression for faster writes
            chunks=(chunk_size, *expected_shape)  # Enable chunking
        )
        
        # Batch processing with parallel file loading
        num_batches = (len(feature_files) + batch_size - 1) // batch_size
        
        for batch_idx in tqdm(range(num_batches), desc="Packing environmental features"):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(feature_files))
            batch_files = feature_files[start_idx:end_idx]
            
            # Load batch in parallel using ThreadPoolExecutor (better for I/O)
            batch_data = [None] * len(batch_files)
            errors = []
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks
                future_to_idx = {
                    executor.submit(load_and_process_feature, feature_path): i
                    for i, feature_path in enumerate(batch_files)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        feature, error = future.result()
                        batch_data[idx] = feature
                        if error:
                            errors.append((batch_files[idx], error))
                    except Exception as e:
                        batch_data[idx] = np.zeros(expected_shape, dtype=np.float32)
                        errors.append((batch_files[idx], str(e)))
            
            # Report errors
            for file_path, error_msg in errors:
                tqdm.write(f"[ERROR] Failed to load {file_path}: {error_msg}")
            
            # Write batch to HDF5
            if batch_data:
                batch_array = np.stack(batch_data, axis=0)
                dataset[start_idx:end_idx] = batch_array
        
        # Store indices mapping as a single array (much more efficient)
        manifest_indices = np.array(list(indices.keys()), dtype=np.int64)
        h5_indices = np.array([indices[idx] for idx in manifest_indices], dtype=np.int32)
        
        indices_group = h5f.create_group('indices')
        indices_group.create_dataset('manifest_idx', data=manifest_indices, compression='gzip', compression_opts=1)
        indices_group.create_dataset('h5_idx', data=h5_indices, compression='gzip', compression_opts=1)
        
        # Store metadata
        metadata_group = h5f.create_group('metadata')
        metadata_group.attrs['num_samples'] = len(feature_files)
        metadata_group.attrs['feature_shape'] = expected_shape
        metadata_group.attrs['feature_type'] = 'environmental'
        metadata_group.attrs['num_features'] = len(feature_names)
        # Store feature names as a dataset (HDF5 doesn't support list attributes well)
        metadata_group.create_dataset('feature_names', data=[n.encode('utf-8') for n in feature_names])
    
    file_size_gb = os.path.getsize(output_path) / 1e9
    print(f"[OK] Packed {len(feature_files)} environmental features")
    print(f"[SIZE] File size: {file_size_gb:.2f} GB")
    
    return indices, {
        'num_samples': len(feature_files),
        'feature_shape': expected_shape,
        'feature_names': feature_names,
        'file_size_gb': file_size_gb
    }


def create_updated_manifest(manifest_df, spectrogram_indices, environmental_indices, output_path):
    """
    Create updated manifest with feature indices.
    
    Args:
        manifest_df: Original manifest DataFrame
        spectrogram_indices: Dictionary mapping manifest indices to HDF5 indices
        environmental_indices: Dictionary mapping manifest indices to HDF5 indices
        output_path: Path to save updated manifest
    """
    print(f"\n[MANIFEST] Creating updated manifest with feature indices...")
    
    # Create copy of manifest
    updated_df = manifest_df.copy()
    
    # Add feature indices
    updated_df['spectrogram_idx'] = updated_df.index.map(lambda x: spectrogram_indices.get(x, -1))
    updated_df['environmental_idx'] = updated_df.index.map(lambda x: environmental_indices.get(x, -1))
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    updated_df.to_csv(output_path, index=False)
    
    # Statistics
    has_spectrogram = (updated_df['spectrogram_idx'] >= 0).sum()
    has_environmental = (updated_df['environmental_idx'] >= 0).sum()
    has_both = ((updated_df['spectrogram_idx'] >= 0) & (updated_df['environmental_idx'] >= 0)).sum()
    
    print(f"[INFO] Samples with spectrogram features: {has_spectrogram}/{len(updated_df)}")
    print(f"[INFO] Samples with environmental features: {has_environmental}/{len(updated_df)}")
    print(f"[INFO] Samples with both features: {has_both}/{len(updated_df)}")
    print(f"[OK] Updated manifest saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Pack features to HDF5")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--spectrogram_dir',
        type=str,
        default=r'E:\FYP\data\features\spectrograms',
        help='Directory containing spectrogram .npy files'
    )
    parser.add_argument(
        '--environmental_dir',
        type=str,
        default=r'E:\FYP\data\features\environmental',
        help='Directory containing environmental .npy files'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=r'E:\FYP\data\features',
        help='Output directory for HDF5 files'
    )
    parser.add_argument(
        '--spectrogram_only',
        action='store_true',
        help='Only pack spectrogram features'
    )
    parser.add_argument(
        '--environmental_only',
        action='store_true',
        help='Only pack environmental features'
    )
    parser.add_argument(
        '--num_workers',
        type=int,
        default=None,
        help='Number of parallel workers for file I/O (default: auto-detect CPU count, max 32)'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=500,
        help='Batch size for processing files (default: 500)'
    )
    
    args = parser.parse_args()
    
    # Load manifest
    print(f"[INFO] Loading manifest: {args.manifest}")
    if not os.path.exists(args.manifest):
        print(f"[ERROR] Manifest not found: {args.manifest}")
        return 1
    
    df = pd.read_csv(args.manifest, low_memory=False)
    print(f"[INFO] Loaded {len(df)} samples from manifest")
    
    # Pack spectrograms
    spectrogram_indices = None
    spectrogram_metadata = None
    
    if not args.environmental_only:
        spectrogram_output = os.path.join(args.output_dir, 'logmel_packed.h5')
        spectrogram_indices, spectrogram_metadata = pack_spectrograms(
            df, args.spectrogram_dir, spectrogram_output, 
            num_workers=args.num_workers, batch_size=args.batch_size
        )
        if spectrogram_indices is None:
            print("[ERROR] Failed to pack spectrograms")
            if not args.spectrogram_only:
                return 1
    
    # Pack environmental features
    environmental_indices = None
    environmental_metadata = None
    
    if not args.spectrogram_only:
        environmental_output = os.path.join(args.output_dir, 'environmental_packed.h5')
        environmental_indices, environmental_metadata = pack_environmental(
            df, args.environmental_dir, environmental_output,
            num_workers=args.num_workers, batch_size=args.batch_size
        )
        if environmental_indices is None:
            print("[ERROR] Failed to pack environmental features")
            if not args.environmental_only:
                return 1
    
    # Create updated manifest
    if spectrogram_indices is not None and environmental_indices is not None:
        updated_manifest_path = os.path.join(args.output_dir, 'features_manifest_unified.csv')
        create_updated_manifest(df, spectrogram_indices, environmental_indices, updated_manifest_path)
    
    # Save packing statistics
    stats = {
        'spectrogram': spectrogram_metadata,
        'environmental': environmental_metadata
    }
    stats_path = os.path.join(args.output_dir, 'packing_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\n[INFO] Packing statistics saved to: {stats_path}")
    
    print("\n" + "="*80)
    print("PACKING COMPLETE")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

