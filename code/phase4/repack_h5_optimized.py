"""
Re-pack HDF5 files with optimized chunking and compression for fast batch loading.

The original file has chunks=(1, 64, 400) which requires one disk read per sample.
This script re-packs with chunks=(64, 64, 400) so 64 samples are read together.

Expected improvement:
- File size: 180GB -> ~40-60GB (with compression)
- Batch read speed: 64x faster (read 64 samples per disk access instead of 1)

Usage:
    python repack_h5_optimized.py --input C:/FYP/data/features/logmel_packed.h5 --output C:/FYP/data/features/logmel_packed_fast.h5
"""

import argparse
import h5py
import numpy as np
from tqdm import tqdm
import os


def repack_h5(input_path, output_path, chunk_samples=64, compression='gzip', compression_opts=4):
    """
    Re-pack HDF5 with optimized settings.
    
    Args:
        input_path: Original HDF5 file
        output_path: Output optimized HDF5 file
        chunk_samples: Number of samples per chunk (default: 64)
        compression: Compression algorithm ('gzip', 'lzf', or None)
        compression_opts: Compression level (1-9 for gzip)
    """
    print(f"[INPUT] Reading: {input_path}")
    print(f"[OUTPUT] Writing: {output_path}")
    
    with h5py.File(input_path, 'r') as f_in:
        # Get original info
        features = f_in['features']
        n_samples, height, width = features.shape
        dtype = features.dtype
        
        print(f"\n[ORIGINAL]")
        print(f"  Shape: {features.shape}")
        print(f"  Dtype: {dtype}")
        print(f"  Chunks: {features.chunks}")
        print(f"  Compression: {features.compression}")
        print(f"  File size: {os.path.getsize(input_path) / 1e9:.2f} GB")
        
        # Calculate optimal chunk size
        chunk_shape = (chunk_samples, height, width)
        print(f"\n[NEW SETTINGS]")
        print(f"  Chunks: {chunk_shape}")
        print(f"  Compression: {compression} (level {compression_opts})")
        
        # Create output file
        with h5py.File(output_path, 'w') as f_out:
            # Create dataset with optimized settings
            out_features = f_out.create_dataset(
                'features',
                shape=(n_samples, height, width),
                dtype=dtype,
                chunks=chunk_shape,
                compression=compression,
                compression_opts=compression_opts if compression == 'gzip' else None,
                shuffle=True  # Helps compression
            )
            
            # Copy in chunks for memory efficiency
            batch_size = chunk_samples * 16  # Read 16 chunks at a time
            print(f"\n[COPYING] {n_samples} samples in batches of {batch_size}...")
            
            for start in tqdm(range(0, n_samples, batch_size), desc="Re-packing"):
                end = min(start + batch_size, n_samples)
                out_features[start:end] = features[start:end]
            
            # Copy indices if they exist
            if 'indices' in f_in:
                print("\n[COPYING] Index mappings...")
                f_out.copy(f_in['indices'], 'indices')
            
            # Copy metadata if it exists
            if 'metadata' in f_in:
                print("[COPYING] Metadata...")
                f_out.copy(f_in['metadata'], 'metadata')
    
    # Check output size
    output_size = os.path.getsize(output_path) / 1e9
    input_size = os.path.getsize(input_path) / 1e9
    compression_ratio = input_size / output_size
    
    print(f"\n[COMPLETE]")
    print(f"  Original size: {input_size:.2f} GB")
    print(f"  New size: {output_size:.2f} GB")
    print(f"  Compression ratio: {compression_ratio:.1f}x")
    print(f"  Space saved: {input_size - output_size:.2f} GB")


def main():
    parser = argparse.ArgumentParser(description='Re-pack HDF5 for fast batch loading')
    parser.add_argument('--input', type=str, required=True, help='Input HDF5 file')
    parser.add_argument('--output', type=str, required=True, help='Output HDF5 file')
    parser.add_argument('--chunk_samples', type=int, default=64, 
                       help='Samples per chunk (default: 64)')
    parser.add_argument('--compression', type=str, default='gzip', 
                       choices=['gzip', 'lzf', 'none'],
                       help='Compression type (default: gzip)')
    parser.add_argument('--compression_level', type=int, default=4,
                       help='Compression level 1-9 for gzip (default: 4)')
    
    args = parser.parse_args()
    
    compression = None if args.compression == 'none' else args.compression
    
    repack_h5(
        args.input, 
        args.output, 
        chunk_samples=args.chunk_samples,
        compression=compression,
        compression_opts=args.compression_level
    )


if __name__ == '__main__':
    main()


