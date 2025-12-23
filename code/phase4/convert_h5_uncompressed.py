"""
Convert gzip-compressed HDF5 files to uncompressed format for FAST training.

Steps:
1. Delete existing .h5 files from D: drive (duplicates)
2. Convert E: drive .h5 files to uncompressed format on D: drive

This fixes the 470ms/sample bottleneck caused by gzip decompression.
Expected speedup: ~100x faster data loading.

Usage:
    python convert_h5_uncompressed.py
"""

import os
import sys
import h5py
import numpy as np
from tqdm import tqdm
import time
import shutil


def delete_d_drive_files():
    """Delete duplicate .h5 files from D: drive to free space."""
    print("\n" + "=" * 80)
    print("STEP 1: Delete duplicate .h5 files from D: drive")
    print("=" * 80)
    
    files_to_delete = [
        'D:/FYP/data/features/logmel_packed.h5',
        'D:/FYP/data/features/environmental_packed.h5'
    ]
    
    freed_space = 0
    for filepath in files_to_delete:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  Deleting: {filepath} ({size/1e9:.2f} GB)")
            os.remove(filepath)
            freed_space += size
            print(f"  [DELETED]")
        else:
            print(f"  Not found: {filepath}")
    
    print(f"\n  Freed: {freed_space/1e9:.2f} GB")
    
    # Check new free space
    _, _, free = shutil.disk_usage('D:/')
    print(f"  D: drive free space now: {free/1e9:.1f} GB")
    
    return free


def convert_to_uncompressed(src_path, dst_path, batch_size=1000):
    """
    Convert compressed HDF5 to uncompressed format.
    
    Args:
        src_path: Source (gzip compressed) HDF5 on E: drive
        dst_path: Destination (uncompressed) HDF5 on D: drive
        batch_size: Samples to process at once
    """
    print(f"\n  Converting: {src_path}")
    print(f"  Output: {dst_path}")
    
    # Create output directory
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    
    with h5py.File(src_path, 'r') as src:
        shape = src['features'].shape
        dtype = src['features'].dtype
        
        print(f"  Shape: {shape}")
        print(f"  Dtype: {dtype}")
        print(f"  Source compression: {src['features'].compression}")
        
        # Calculate uncompressed size
        uncompressed_gb = np.prod(shape) * 4 / 1e9
        print(f"  Uncompressed size: {uncompressed_gb:.2f} GB")
        
        with h5py.File(dst_path, 'w') as dst:
            # Create uncompressed dataset
            # Use chunk size of 1 sample for optimal random access
            if len(shape) == 3:  # Spectrograms [N, 64, 400]
                chunks = (1, shape[1], shape[2])
            else:  # Environmental [N, 12]
                chunks = (100, shape[1])  # Small features, larger chunks OK
            
            dst_features = dst.create_dataset(
                'features',
                shape=shape,
                dtype=dtype,
                compression=None,  # NO COMPRESSION!
                chunks=chunks
            )
            
            print(f"  Output chunks: {chunks}")
            print(f"  Output compression: None (uncompressed)")
            
            # Copy in batches with progress bar
            n_samples = shape[0]
            n_batches = (n_samples + batch_size - 1) // batch_size
            
            start_time = time.time()
            for i in tqdm(range(n_batches), desc="  Converting"):
                start_idx = i * batch_size
                end_idx = min(start_idx + batch_size, n_samples)
                
                # Read from source (triggers decompression)
                batch = src['features'][start_idx:end_idx]
                
                # Write to destination (no compression)
                dst_features[start_idx:end_idx] = batch
            
            elapsed = time.time() - start_time
            speed = n_samples / elapsed
            print(f"  Converted {n_samples:,} samples in {elapsed/60:.1f} minutes ({speed:.0f} samples/sec)")
            
            # Copy indices
            if 'indices' in src:
                print("  Copying indices...")
                dst.create_group('indices')
                for key in src['indices'].keys():
                    dst['indices'].create_dataset(key, data=src['indices'][key][:])
            
            # Copy metadata
            if 'metadata' in src:
                print("  Copying metadata...")
                dst.create_group('metadata')
                for key in src['metadata'].attrs.keys():
                    dst['metadata'].attrs[key] = src['metadata'].attrs[key]
    
    # Verify
    print("  Verifying...")
    with h5py.File(dst_path, 'r') as f:
        print(f"  Output compression: {f['features'].compression}")
        
        # Speed test
        start = time.time()
        _ = f['features'][0]
        single_ms = (time.time() - start) * 1000
        
        start = time.time()
        _ = f['features'][0:100]
        batch_ms = (time.time() - start) * 1000
        
        print(f"  Read 1 sample: {single_ms:.1f}ms (was ~470ms)")
        print(f"  Read 100 samples: {batch_ms:.1f}ms")
    
    file_size = os.path.getsize(dst_path) / 1e9
    print(f"  File size: {file_size:.2f} GB")
    
    return True


def main():
    print("=" * 80)
    print("CONVERT HDF5 FILES TO UNCOMPRESSED FORMAT")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Delete duplicate .h5 files from D: drive (~103 GB freed)")
    print("  2. Convert E: drive .h5 files to uncompressed on D: drive")
    print()
    print("Expected result: ~100x faster data loading!")
    print()
    
    # Source files on E: drive
    src_spec = 'E:/FYP/data/features/logmel_packed.h5'
    src_env = 'E:/FYP/data/features/environmental_packed.h5'
    
    # Destination files on D: drive (fast drive)
    dst_spec = 'D:/FYP/data/features/logmel_packed.h5'
    dst_env = 'D:/FYP/data/features/environmental_packed.h5'
    
    # Check source files exist
    if not os.path.exists(src_spec):
        print(f"[ERROR] Source not found: {src_spec}")
        return 1
    if not os.path.exists(src_env):
        print(f"[ERROR] Source not found: {src_env}")
        return 1
    
    print(f"Source files:")
    print(f"  Spectrograms: {src_spec} ({os.path.getsize(src_spec)/1e9:.2f} GB)")
    print(f"  Environmental: {src_env} ({os.path.getsize(src_env)/1e9:.2f} GB)")
    
    # Step 1: Delete D: drive files
    free_space = delete_d_drive_files()
    
    # Check if we have enough space
    needed_gb = 200  # ~193GB + buffer
    if free_space / 1e9 < needed_gb:
        print(f"[ERROR] Not enough space! Need {needed_gb}GB, have {free_space/1e9:.1f}GB")
        return 1
    
    # Step 2: Convert spectrograms (large file)
    print("\n" + "=" * 80)
    print("STEP 2: Convert spectrogram HDF5 (this will take ~30-60 minutes)")
    print("=" * 80)
    
    success = convert_to_uncompressed(src_spec, dst_spec, batch_size=1000)
    if not success:
        return 1
    
    # Step 3: Convert environmental features (small file)
    print("\n" + "=" * 80)
    print("STEP 3: Convert environmental HDF5 (fast)")
    print("=" * 80)
    
    success = convert_to_uncompressed(src_env, dst_env, batch_size=10000)
    if not success:
        return 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("CONVERSION COMPLETE!")
    print("=" * 80)
    print()
    print("Uncompressed files created on D: drive:")
    print(f"  {dst_spec} ({os.path.getsize(dst_spec)/1e9:.2f} GB)")
    print(f"  {dst_env} ({os.path.getsize(dst_env)/1e9:.2f} GB)")
    print()
    print("Training command (same paths, now FAST):")
    print("-" * 80)
    print(f"python code/phase4/train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 64 --epochs 20 --num_workers 8")
    print("-" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

