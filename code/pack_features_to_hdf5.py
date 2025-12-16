import os
import h5py
import numpy as np
from tqdm import tqdm
import glob


def pack_folder_to_hdf5(src_dir, dst_path, compression="gzip"):
    """Pack all .npy files from a folder into one HDF5 file."""
    print(f"\n[PACK] Packing folder: {src_dir}")
    files = glob.glob(os.path.join(src_dir, "*.npy"))
    print(f"[INFO] Found {len(files)} .npy files to pack")

    if not files:
        print(f"[WARN] No .npy files found in {src_dir}")
        return

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    with h5py.File(dst_path, "w") as h5f:
        for fp in tqdm(files, desc=f"Packing -> {os.path.basename(dst_path)}", ncols=100):
            try:
                key = os.path.basename(fp).replace(".npy", "")
                arr = np.load(fp, allow_pickle=False)
                h5f.create_dataset(key, data=arr, compression=compression)
            except Exception as e:
                print(f"[SKIP] {fp} -> {e}")
                continue

    size_gb = os.path.getsize(dst_path) / 1e9
    print(f"[OK] Done! Packed file saved -> {dst_path}")
    print(f"[SIZE] Approx. size: {size_gb:.2f} GB\n")


if __name__ == "__main__":
    # -------- Folders to process --------
    base_paths = [
        # Clean features
        (r"E:\FYP\data\features\lfcc", r"E:\FYP\data\features\lfcc_packed.h5"),
        (r"E:\FYP\data\features\logmel", r"E:\FYP\data\features\logmel_packed.h5"),

        # Augmented features
        (r"E:\FYP\data\features_augmented\lfcc", r"E:\FYP\data\features_augmented\lfcc_packed.h5"),
        (r"E:\FYP\data\features_augmented\logmel", r"E:\FYP\data\features_augmented\logmel_packed.h5"),
    ]

    for src, dst in base_paths:
        if not os.path.exists(src):
            print(f"[WARN] Source folder not found: {src}")
            continue
        if os.path.exists(dst):
            print(f"[SKIP] HDF5 file already exists: {dst}")
            continue
        pack_folder_to_hdf5(src, dst)
