"""Comprehensive diagnostic to identify issues in FASSD project"""
import os
import sys
import torch
import pandas as pd
import numpy as np
from pathlib import Path

print("="*70)
print(" FASSD PROJECT DIAGNOSTIC ".center(70, "="))
print("="*70)

# 1. Environment Check
print("\n[1] ENVIRONMENT CHECK")
print("-" * 70)
print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")

# 2. Data Files Check
print("\n[2] DATA FILES CHECK")
print("-" * 70)

data_checks = {
    "Manifest (combined)": r"E:\FYP\data\features_merged\features_manifest_combined.csv",
    "LFCC HDF5 (clean)": r"E:\FYP\data\features\lfcc_packed.h5",
    "LogMel HDF5 (clean)": r"E:\FYP\data\features\logmel_packed.h5",
    "LFCC HDF5 (augmented)": r"E:\FYP\data\features_augmented\lfcc_packed.h5",
    "LogMel HDF5 (augmented)": r"E:\FYP\data\features_augmented\logmel_packed.h5",
}

for name, path in data_checks.items():
    exists = os.path.exists(path)
    if exists and path.endswith('.h5'):
        size_mb = os.path.getsize(path) / (1024**2)
        print(f"[OK] {name}: {size_mb:.1f} MB")
    elif exists:
        print(f"[OK] {name}")
    else:
        print(f"[MISSING] {name}")

# 3. Model Checkpoints Check
print("\n[3] MODEL CHECKPOINTS CHECK")
print("-" * 70)

model_checks = {
    "Baseline (clean)": r"E:\FYP\models_saved\baseline_cnn.pth",
    "Baseline (robust)": r"E:\FYP\models_saved\baseline_cnn_robust.pth",
}

for name, path in model_checks.items():
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        try:
            ckpt = torch.load(path, map_location='cpu', weights_only=False)
            has_model = 'model' in ckpt
            num_params = len(ckpt['model']) if has_model else 0
            print(f"[OK] {name}: {size_kb:.1f} KB, {num_params} params")
        except Exception as e:
            print(f"[ERROR] {name}: Cannot load - {e}")
    else:
        print(f"[MISSING] {name}")

# 4. Manifest Analysis
print("\n[4] MANIFEST ANALYSIS")
print("-" * 70)

try:
    manifest_path = r"E:\FYP\data\features_merged\features_manifest_combined.csv"
    df = pd.read_csv(manifest_path)
    
    print(f"Total samples: {len(df):,}")
    print(f"Columns: {', '.join(df.columns)}")
    print(f"\nLabel distribution:")
    for label, count in df['label'].value_counts().items():
        pct = count / len(df) * 100
        print(f"  {label}: {count:,} ({pct:.2f}%)")
    
    if 'source' in df.columns:
        print(f"\nSource distribution:")
        for source, count in df['source'].value_counts().items():
            pct = count / len(df) * 100
            print(f"  {source}: {count:,} ({pct:.2f}%)")
            
    # Check if paths exist
    sample_paths = df[['lfcc_path', 'mel_path']].iloc[0]
    print(f"\nSample feature paths check:")
    for col in ['lfcc_path', 'mel_path']:
        path = sample_paths[col]
        exists = os.path.exists(path)
        print(f"  {col}: {'EXISTS' if exists else 'MISSING'}")
        
except Exception as e:
    print(f"[ERROR] Cannot read manifest: {e}")

# 5. Feature Loading Test
print("\n[5] FEATURE LOADING TEST")
print("-" * 70)

try:
    # Test loading from HDF5
    import h5py
    h5_path = r"E:\FYP\data\features\lfcc_packed.h5"
    
    if os.path.exists(h5_path):
        with h5py.File(h5_path, 'r') as f:
            num_keys = len(f.keys())
            print(f"LFCC HDF5: {num_keys:,} features stored")
            
            # Test loading one feature
            first_key = list(f.keys())[0]
            feature = np.array(f[first_key])
            print(f"Sample feature shape: {feature.shape}")
            print(f"Sample feature dtype: {feature.dtype}")
    else:
        print("[WARNING] LFCC HDF5 not found")
        
    # Test loading from .npy
    if 'lfcc_path' in df.columns:
        sample_npy = df['lfcc_path'].iloc[0]
        if os.path.exists(sample_npy):
            npy_feat = np.load(sample_npy)
            print(f"Sample .npy feature shape: {npy_feat.shape}")
        
except Exception as e:
    print(f"[ERROR] Feature loading test failed: {e}")

# 6. Model Architecture Test
print("\n[6] MODEL ARCHITECTURE TEST")
print("-" * 70)

try:
    sys.path.insert(0, r'E:\FYP\Code')
    from models.baseline_cnn import LCNNBaseline
    
    model = LCNNBaseline(n_classes=2)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Test forward pass
    dummy_input = torch.randn(1, 1, 20, 400)  # [B, C, F, T]
    output = model(dummy_input)
    print(f"Output shape: {output.shape}")
    print(f"Expected: [1, 2]")
    
    # Load checkpoint and test
    ckpt_path = r"E:\FYP\models_saved\baseline_cnn_robust.pth"
    if os.path.exists(ckpt_path):
        ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=False)
        model.load_state_dict(ckpt['model'])
        model.eval()
        with torch.no_grad():
            output = model(dummy_input)
            probs = torch.softmax(output, dim=1)
            print(f"Test inference successful")
            print(f"Probabilities: {probs.numpy()[0]}")
    
except Exception as e:
    print(f"[ERROR] Model test failed: {e}")
    import traceback
    traceback.print_exc()

# 7. Dataset Loader Test
print("\n[7] DATASET LOADER TEST")
print("-" * 70)

try:
    from data_loading.streaming_dataset_loader import StreamingFeatureDataset
    from torch.utils.data import DataLoader
    
    # Create small test dataset
    test_df = df.sample(100, random_state=42).reset_index(drop=True)
    
    dataset = StreamingFeatureDataset(
        test_df, 
        feature_type='lfcc', 
        max_frames=400, 
        shuffle=False
    )
    
    print(f"Dataset length: {len(dataset)}")
    
    # Test single sample
    x, y = dataset[0]
    print(f"Sample shape: {x.shape}")
    print(f"Sample label: {y.item()}")
    
    # Test DataLoader
    loader = DataLoader(dataset, batch_size=8, num_workers=0)
    batch_x, batch_y = next(iter(loader))
    print(f"Batch shape: {batch_x.shape}")
    print(f"Batch labels: {batch_y.numpy()}")
    
    print("[OK] Dataset loader working correctly")
    
except Exception as e:
    print(f"[ERROR] Dataset loader test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print(" DIAGNOSTIC COMPLETE ".center(70, "="))
print("="*70)

