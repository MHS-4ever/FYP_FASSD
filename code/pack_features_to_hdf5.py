import os
import h5py
import numpy as np
from tqdm import tqdm
import glob
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


def pack_folder_to_hdf5(src_dir, dst_path, compression="gzip", delete_source=False, num_workers=None, batch_size=500):
    """
    Pack all .npy files from a folder into one HDF5 file with optimized batch processing.
    
    Args:
        src_dir: Source directory containing .npy files
        dst_path: Destination HDF5 file path
        compression: Compression type (default: "gzip")
        delete_source: If True, delete source directory after successful packing
        num_workers: Number of parallel workers for file I/O (default: auto-detect)
        batch_size: Batch size for processing files (default: 500)
    """
    print(f"\n[PACK] Packing folder: {src_dir}")
    files = sorted(glob.glob(os.path.join(src_dir, "*.npy")))
    print(f"[INFO] Found {len(files)} .npy files to pack")

    if not files:
        print(f"[WARN] No .npy files found in {src_dir}")
        return False

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    # Load first file to determine shape
    try:
        sample = np.load(files[0], allow_pickle=False)
        expected_shape = sample.shape
        print(f"[INFO] Expected shape: {expected_shape}")
    except Exception as e:
        print(f"[ERROR] Failed to load sample file {files[0]}: {e}")
        return False

    # Calculate optimal chunk size (~100MB per chunk)
    feature_size = np.prod(expected_shape) * 4  # 4 bytes per float32
    chunk_size = max(1, min(1000, int(100 * 1024 * 1024 / feature_size)))  # ~100MB chunks
    
    # Determine number of workers
    if num_workers is None:
        num_workers = min(multiprocessing.cpu_count(), 32)  # Cap at 32 to avoid overhead
    print(f"[INFO] Using {num_workers} parallel workers for file I/O")
    print(f"[INFO] Batch size: {batch_size} files per batch")

    def load_and_process_file(file_path):
        """Load and process a single .npy file."""
        try:
            arr = np.load(file_path, allow_pickle=False)
            if arr.shape != expected_shape:
                # Handle shape mismatches
                if arr.ndim == len(expected_shape):
                    # Try to pad/truncate if dimensions match
                    if arr.size < np.prod(expected_shape):
                        # Pad
                        arr_padded = np.zeros(expected_shape, dtype=arr.dtype)
                        slices = tuple(slice(0, min(s1, s2)) for s1, s2 in zip(arr.shape, expected_shape))
                        arr_padded[slices] = arr[slices]
                        arr = arr_padded
                    else:
                        # Truncate
                        slices = tuple(slice(0, s) for s in expected_shape)
                        arr = arr[slices]
                else:
                    # Shape mismatch - fill with zeros
                    arr = np.zeros(expected_shape, dtype=np.float32)
            return arr, None, os.path.basename(file_path).replace(".npy", "")
        except Exception as e:
            return np.zeros(expected_shape, dtype=np.float32), str(e), os.path.basename(file_path).replace(".npy", "")

    try:
        with h5py.File(dst_path, "w") as h5f:
            # Create a group for all features
            features_group = h5f.create_group('features')
            
            # Process files in batches with parallel loading
            num_batches = (len(files) + batch_size - 1) // batch_size
            errors = []
            
            for batch_idx in tqdm(range(num_batches), desc=f"Packing -> {os.path.basename(dst_path)}"):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(files))
                batch_files = files[start_idx:end_idx]
                
                # Load batch in parallel using ThreadPoolExecutor (better for I/O)
                batch_data = {}
                
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    # Submit all tasks
                    future_to_file = {
                        executor.submit(load_and_process_file, file_path): file_path
                        for file_path in batch_files
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            arr, error, key = future.result()
                            batch_data[key] = arr
                            if error:
                                errors.append((file_path, error))
                        except Exception as e:
                            errors.append((file_path, str(e)))
                            key = os.path.basename(file_path).replace(".npy", "")
                            batch_data[key] = np.zeros(expected_shape, dtype=np.float32)
                
                # Write batch to HDF5
                for key, arr in batch_data.items():
                    try:
                        features_group.create_dataset(
                            key, 
                            data=arr, 
                            compression=compression,
                            compression_opts=1  # Lower compression for faster writes
                        )
                    except Exception as e:
                        errors.append((key, f"HDF5 write error: {e}"))
            
            # Report errors
            if errors:
                print(f"\n[WARN] {len(errors)} files had errors (showing first 10):")
                for file_path, error_msg in errors[:10]:
                    tqdm.write(f"  - {os.path.basename(file_path)}: {error_msg}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            
            # Store metadata
            metadata_group = h5f.create_group('metadata')
            metadata_group.attrs['num_files'] = len(files)
            metadata_group.attrs['feature_shape'] = expected_shape
            metadata_group.attrs['source_directory'] = src_dir

        size_gb = os.path.getsize(dst_path) / 1e9
        print(f"[OK] Done! Packed file saved -> {dst_path}")
        print(f"[SIZE] Approx. size: {size_gb:.2f} GB")
        
        # Delete source directory if requested and packing succeeded
        if delete_source:
            print(f"\n[DELETE] Deleting source directory: {src_dir}")
            try:
                shutil.rmtree(src_dir)
                print(f"[OK] Source directory deleted successfully")
            except Exception as e:
                print(f"[ERROR] Failed to delete source directory: {e}")
                return False
        
        print()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to pack files: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pack .npy feature files to HDF5 format")
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
    parser.add_argument(
        '--compression',
        type=str,
        default='gzip',
        choices=['gzip', 'lzf', 'szip', 'none'],
        help='Compression type (default: gzip)'
    )
    
    args = parser.parse_args()
    
    # -------- Folders to process --------
    base_paths = [
        # Clean features
        (r"E:\FYP\data\features\lfcc", r"E:\FYP\data\features\lfcc_packed.h5", False),
        (r"E:\FYP\data\features\logmel", r"E:\FYP\data\features\logmel_packed.h5", False),

        # Augmented features
        (r"E:\FYP\data\features_augmented\lfcc", r"E:\FYP\data\features_augmented\lfcc_packed.h5", False),
        (r"E:\FYP\data\features_augmented\logmel", r"E:\FYP\data\features_augmented\logmel_packed.h5", False),
        
        # Previous pipeline - pack and delete source
        (r"E:\FYP\data\features\logmel_previous_pipeline", r"E:\FYP\data\features\logmel_packed_previous_pipeline.h5", True),
    ]

    print("="*80)
    print("PACKING FEATURES TO HDF5")
    print("="*80)
    print(f"[INFO] Using {args.num_workers or min(multiprocessing.cpu_count(), 32)} workers")
    print(f"[INFO] Batch size: {args.batch_size}")
    print(f"[INFO] Compression: {args.compression}")
    print()

    success_count = 0
    skip_count = 0
    error_count = 0

    for src, dst, delete_source in base_paths:
        if not os.path.exists(src):
            print(f"[WARN] Source folder not found: {src}")
            skip_count += 1
            continue
        if os.path.exists(dst):
            print(f"[SKIP] HDF5 file already exists: {dst}")
            skip_count += 1
            continue
        
        success = pack_folder_to_hdf5(
            src, dst, 
            compression=args.compression,
            delete_source=delete_source,
            num_workers=args.num_workers,
            batch_size=args.batch_size
        )
        
        if success:
            success_count += 1
        else:
            error_count += 1
            print(f"[ERROR] Failed to pack {src} -> {dst}")
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Successfully packed: {success_count}")
    print(f"Skipped (already exists): {skip_count}")
    print(f"Errors: {error_count}")
    print("="*80)
