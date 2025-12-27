"""
Repack HDF5 with LARGER CHUNKS for fast batch loading.

PROBLEM:
- Current chunks: (1, 64, 400) = 1 sample per chunk = 256 disk reads per batch
- Training speed: 6+ seconds per batch → 10+ hours per epoch

SOLUTION:
- New chunks: (256, 64, 400) = 256 samples per chunk = 1 disk read per batch
- NO compression (we proved gzip causes 470ms/sample decompression overhead)

Expected speedup: 100-256x (from 6s/batch to 0.02-0.05s/batch)

Usage:
    python code/phase4/repack_h5_chunked.py --input C:/FYP/data/features/logmel_packed.h5 --output C:/FYP/data/features/logmel_chunked.h5
"""

import argparse
import h5py
import numpy as np
from tqdm import tqdm
import os
import time


def repack_h5_chunked(input_path, output_path, chunk_samples=256):
    """
    Repack HDF5 with larger chunks for batch-aligned reads.
    
    Args:
        input_path: Original HDF5 file (chunks=1,64,400)
        output_path: Output HDF5 file (chunks=256,64,400)
        chunk_samples: Samples per chunk (should match batch size)
    """
    print("=" * 80)
    print("REPACK HDF5 WITH LARGER CHUNKS (NO COMPRESSION)")
    print("=" * 80)
    
    # Check input file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    input_size_gb = os.path.getsize(input_path) / 1e9
    print(f"\nInput: {input_path}")
    print(f"Input size: {input_size_gb:.2f} GB")
    
    # Check available disk space
    output_dir = os.path.dirname(output_path) or '.'
    import shutil
    free_space_gb = shutil.disk_usage(output_dir).free / 1e9
    print(f"Free space on output drive: {free_space_gb:.1f} GB")
    
    if free_space_gb < input_size_gb * 1.1:
        print(f"\n[ERROR] Not enough disk space!")
        print(f"Need at least {input_size_gb * 1.1:.1f} GB, have {free_space_gb:.1f} GB")
        return False
    
    print(f"\nOutput: {output_path}")
    
    with h5py.File(input_path, 'r') as f_in:
        features = f_in['features']
        n_samples, height, width = features.shape
        dtype = features.dtype
        
        print(f"\n[ORIGINAL FILE]")
        print(f"  Shape: {features.shape}")
        print(f"  Dtype: {dtype}")
        print(f"  Chunks: {features.chunks}")
        print(f"  Compression: {features.compression}")
        
        if features.chunks[0] >= chunk_samples:
            print(f"\n[INFO] File already has chunks >= {chunk_samples}. No repack needed!")
            return True
        
        # New chunk shape
        new_chunks = (chunk_samples, height, width)
        chunk_size_mb = (chunk_samples * height * width * 4) / 1e6
        
        print(f"\n[NEW SETTINGS]")
        print(f"  Chunks: {new_chunks}")
        print(f"  Chunk size: {chunk_size_mb:.1f} MB")
        print(f"  Compression: None (fastest reads)")
        print(f"  Expected disk reads per batch: 1 (was 256)")
        
        # Delete existing output if exists
        if os.path.exists(output_path):
            print(f"\n[CLEANUP] Deleting existing output file...")
            os.remove(output_path)
        
        # Create output file
        print(f"\n[REPACKING] This will take 15-30 minutes...")
        start_time = time.time()
        
        with h5py.File(output_path, 'w') as f_out:
            # Create dataset with new chunks
            out_features = f_out.create_dataset(
                'features',
                shape=(n_samples, height, width),
                dtype=dtype,
                chunks=new_chunks,
                compression=None,  # NO compression!
                shuffle=False
            )
            
            # Copy in batches (read multiple chunks at once for efficiency)
            copy_batch_size = chunk_samples * 4  # Read 4 output chunks at a time
            n_batches = (n_samples + copy_batch_size - 1) // copy_batch_size
            
            for i in tqdm(range(n_batches), desc="Repacking"):
                start_idx = i * copy_batch_size
                end_idx = min(start_idx + copy_batch_size, n_samples)
                out_features[start_idx:end_idx] = features[start_idx:end_idx]
            
            # Copy indices
            if 'indices' in f_in:
                print("\n[COPYING] Index mappings...")
                f_out.copy(f_in['indices'], 'indices')
            
            # Copy metadata
            if 'metadata' in f_in:
                print("[COPYING] Metadata...")
                f_out.copy(f_in['metadata'], 'metadata')
    
    elapsed = time.time() - start_time
    output_size_gb = os.path.getsize(output_path) / 1e9
    
    print(f"\n" + "=" * 80)
    print("REPACK COMPLETE!")
    print("=" * 80)
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Input size: {input_size_gb:.2f} GB")
    print(f"Output size: {output_size_gb:.2f} GB")
    
    # Verify the new file
    print(f"\n[VERIFY] Checking output file...")
    with h5py.File(output_path, 'r') as f:
        print(f"  Shape: {f['features'].shape}")
        print(f"  Chunks: {f['features'].chunks}")
        print(f"  Compression: {f['features'].compression}")
        
        # Speed test
        print(f"\n[SPEED TEST] Reading 256 random samples...")
        indices = np.random.choice(n_samples, 256, replace=False)
        indices.sort()  # Sorted access (like training)
        
        start = time.time()
        for idx in indices:
            _ = f['features'][idx]
        elapsed_256 = time.time() - start
        
        print(f"  256 sorted samples: {elapsed_256*1000:.1f} ms")
        print(f"  Per sample: {elapsed_256/256*1000:.2f} ms")
        
        # Compare: read 256 contiguous samples (should be much faster)
        start = time.time()
        _ = f['features'][0:256]
        elapsed_contiguous = time.time() - start
        print(f"  256 contiguous samples (batch read): {elapsed_contiguous*1000:.1f} ms")
    
    print(f"\n" + "=" * 80)
    print("TRAINING COMMAND (use the new file):")
    print("-" * 80)
    print(f"python code/phase4/train_hybrid_fast.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 {output_path} --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 256 --epochs 20")
    print("-" * 80)
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Repack HDF5 with larger chunks')
    parser.add_argument('--input', type=str, required=True, help='Input HDF5 file')
    parser.add_argument('--output', type=str, required=True, help='Output HDF5 file')
    parser.add_argument('--chunk_samples', type=int, default=256,
                       help='Samples per chunk (default: 256, matches batch size)')
    
    args = parser.parse_args()
    
    repack_h5_chunked(args.input, args.output, args.chunk_samples)


if __name__ == '__main__':
    main()

