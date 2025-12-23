"""
Pre-training comprehensive check script.
Verifies all components before training to catch issues early.
"""

import os
import sys
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    print("=" * 80)
    print("PRE-TRAINING COMPREHENSIVE CHECK")
    print("=" * 80)
    
    all_passed = True
    
    # 1. Check files
    print("\n1. FILE CHECKS")
    print("-" * 40)
    files_to_check = {
        'Train manifest': 'data/manifests/train_speaker_independent.csv',
        'Val manifest': 'data/manifests/val_speaker_independent.csv',
        'Unified manifest': 'data/manifests/unified_manifest.csv',
        'Spectrogram HDF5': 'D:/FYP/data/features/logmel_packed.h5',
        'Environmental HDF5': 'D:/FYP/data/features/environmental_packed.h5',
    }
    for name, path in files_to_check.items():
        exists = os.path.exists(path)
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status}")
        if not exists:
            all_passed = False
    
    # 2. GPU Check
    print("\n2. GPU CHECK")
    print("-" * 40)
    import torch
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  cuDNN enabled: {torch.backends.cudnn.enabled}")
        # Enable optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print(f"  cuDNN benchmark: ENABLED")
        print(f"  TF32 (Ampere): ENABLED")
    else:
        print("  [X] CUDA NOT AVAILABLE - Training will be VERY slow!")
        all_passed = False
    
    # 3. CPU/RAM Check
    print("\n3. CPU/RAM CHECK")
    print("-" * 40)
    import psutil
    print(f"  CPU cores (physical): {psutil.cpu_count(logical=False)}")
    print(f"  CPU cores (logical): {psutil.cpu_count(logical=True)}")
    mem = psutil.virtual_memory()
    print(f"  RAM total: {mem.total / 1e9:.2f} GB")
    print(f"  RAM available: {mem.available / 1e9:.2f} GB")
    if mem.available / 1e9 < 4:
        print(f"  [!] WARNING: Low RAM available. Close other apps!")
    
    # 4. HDF5 Check
    print("\n4. HDF5 FILE CHECK")
    print("-" * 40)
    import h5py
    import numpy as np
    
    spec_h5_path = 'D:/FYP/data/features/logmel_packed.h5'
    env_h5_path = 'D:/FYP/data/features/environmental_packed.h5'
    
    with h5py.File(spec_h5_path, 'r') as f:
        print(f"  Spectrogram shape: {f['features'].shape}")
        print(f"  Spectrogram dtype: {f['features'].dtype}")
        print(f"  Spectrogram chunks: {f['features'].chunks}")
        print(f"  Has indices: {'indices' in f}")
        if 'indices' in f:
            print(f"  Index count: {len(f['indices/manifest_idx'])}")
    
    with h5py.File(env_h5_path, 'r') as f:
        print(f"  Environmental shape: {f['features'].shape}")
        print(f"  Environmental dtype: {f['features'].dtype}")
    
    # 5. Manifest Check
    print("\n5. MANIFEST CHECK")
    print("-" * 40)
    import pandas as pd
    
    train_df = pd.read_csv('data/manifests/train_speaker_independent.csv', low_memory=False)
    val_df = pd.read_csv('data/manifests/val_speaker_independent.csv', low_memory=False)
    unified_df = pd.read_csv('data/manifests/unified_manifest.csv', low_memory=False)
    
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Val samples: {len(val_df):,}")
    print(f"  Unified samples: {len(unified_df):,}")
    
    # Check required columns
    required_cols = ['filepath', 'label', 'attack_type', 'dataset']
    for col in required_cols:
        if col not in train_df.columns:
            print(f"  [X] MISSING COLUMN: {col}")
            all_passed = False
    
    # Check class balance
    print(f"\n  Label distribution:")
    for label, count in train_df['label'].value_counts().items():
        pct = count / len(train_df) * 100
        print(f"    {label}: {count:,} ({pct:.1f}%)")
    
    print(f"\n  Dataset distribution:")
    for ds, count in train_df['dataset'].value_counts().items():
        pct = count / len(train_df) * 100
        print(f"    {ds}: {count:,} ({pct:.1f}%)")
    
    # 6. Model Check
    print("\n6. MODEL CHECK")
    print("-" * 40)
    from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
    
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Total parameters: {total_params:,}")
    print(f"  Model size: {total_params * 4 / 1e6:.2f} MB")
    
    # Test forward pass on CPU
    spec = torch.randn(4, 1, 64, 400)
    env = torch.randn(4, 12)
    with torch.no_grad():
        b, m = model(spec, env)
    print(f"  Forward pass (CPU): OK - Binary {b.shape}, Multiclass {m.shape}")
    
    # 7. GPU Memory Test
    print("\n7. GPU MEMORY TEST")
    print("-" * 40)
    if torch.cuda.is_available():
        device = torch.device('cuda')
        model = model.to(device)
        
        # Test with batch size 64 (FP16)
        for batch_size in [32, 64, 96, 128]:
            try:
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                
                spec = torch.randn(batch_size, 1, 64, 400, device=device)
                env = torch.randn(batch_size, 12, device=device)
                
                with torch.cuda.amp.autocast():
                    b, m = model(spec, env)
                    loss = b.sum() + m.sum()
                loss.backward()
                
                peak_mb = torch.cuda.max_memory_allocated() / 1e6
                vram_total = torch.cuda.get_device_properties(0).total_memory / 1e6
                pct_used = peak_mb / vram_total * 100
                
                status = "[OK]" if pct_used < 85 else "[!] HIGH"
                print(f"  Batch {batch_size}: {peak_mb:.0f} MB ({pct_used:.1f}% VRAM) {status}")
                
                del spec, env, b, m, loss
                torch.cuda.empty_cache()
                
            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"  Batch {batch_size}: [X] OOM (Out of Memory)")
                    break
                else:
                    raise
        
        # Recommend batch size
        print(f"\n  Recommended batch size: 64 (with FP16 mixed precision)")
    
    # 8. Data Loading Speed Test
    print("\n8. DATA LOADING SPEED TEST")
    print("-" * 40)
    from phase4.hybrid_dataset import HybridDataset
    
    # Test with small subset
    test_df = train_df.head(100).copy()
    
    dataset = HybridDataset(
        test_df,
        spec_h5_path,
        env_h5_path,
        unified_manifest_path='data/manifests/unified_manifest.csv'
    )
    
    # Time single sample load
    start = time.time()
    for i in range(10):
        sample = dataset[i]
    single_time = (time.time() - start) / 10
    print(f"  Single sample load: {single_time*1000:.2f} ms")
    
    # Verify sample
    print(f"  Sample spectrogram shape: {sample['spectrogram'].shape}")
    print(f"  Sample environmental shape: {sample['environmental'].shape}")
    print(f"  Sample binary_label: {sample['binary_label'].item()}")
    print(f"  Sample multiclass_label: {sample['multiclass_label'].item()}")
    print(f"  Sample domain: {sample['domain']}")
    
    # Check for NaN/Inf
    if torch.isnan(sample['spectrogram']).any() or torch.isinf(sample['spectrogram']).any():
        print("  [X] WARNING: NaN/Inf in spectrogram!")
        all_passed = False
    else:
        print("  [OK] No NaN/Inf in features")
    
    dataset.close()
    
    # 9. DataLoader Speed Test
    print("\n9. DATALOADER SPEED TEST")
    print("-" * 40)
    from torch.utils.data import DataLoader
    from phase4.hybrid_dataset import collate_fn
    
    dataset = HybridDataset(
        train_df.head(1000).copy(),
        spec_h5_path,
        env_h5_path,
        unified_manifest_path='data/manifests/unified_manifest.csv'
    )
    
    loader = DataLoader(
        dataset,
        batch_size=64,
        shuffle=True,
        num_workers=4,  # Test with 4 workers first
        pin_memory=True,
        prefetch_factor=2,
        persistent_workers=True,
        collate_fn=collate_fn
    )
    
    # Time batch loading
    start = time.time()
    for i, batch in enumerate(loader):
        if i >= 5:
            break
    batch_time = (time.time() - start) / 5
    samples_per_sec = 64 / batch_time
    print(f"  Batch load time (workers=4): {batch_time*1000:.0f} ms")
    print(f"  Samples/sec: {samples_per_sec:.0f}")
    print(f"  Estimated epoch time: {len(train_df) / samples_per_sec / 60:.1f} min")
    
    dataset.close()
    
    # 10. Loss Function Check
    print("\n10. LOSS FUNCTION CHECK")
    print("-" * 40)
    from phase3.multi_task_loss import MultiTaskLoss, compute_class_weights_from_labels
    
    # Compute class weights
    binary_labels = (train_df['label'] == 'spoof').astype(int).values
    binary_weights = compute_class_weights_from_labels(binary_labels, 2)
    print(f"  Binary class weights: {binary_weights}")
    
    attack_type_map = {'bonafide': 0, 'synthesis': 1, 'conversion': 2, 'replay': 3}
    multiclass_labels = train_df['attack_type'].map(attack_type_map).fillna(0).astype(int).values
    multiclass_weights = compute_class_weights_from_labels(multiclass_labels, 4)
    print(f"  Multiclass weights: {[round(w, 3) for w in multiclass_weights]}")
    
    loss_fn = MultiTaskLoss(
        binary_weight=0.7,
        multiclass_weight=0.3,
        binary_class_weights=binary_weights,
        multiclass_class_weights=multiclass_weights
    )
    
    # Test loss computation
    binary_logits = torch.randn(8, 2)
    multiclass_logits = torch.randn(8, 4)
    binary_labels_t = torch.randint(0, 2, (8,))
    multiclass_labels_t = torch.randint(0, 4, (8,))
    
    total, bin_loss, mc_loss = loss_fn(binary_logits, multiclass_logits, binary_labels_t, multiclass_labels_t)
    print(f"  Loss computation: OK (total={total.item():.4f})")
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("[OK] ALL CHECKS PASSED - READY FOR TRAINING")
    else:
        print("[X] SOME CHECKS FAILED - FIX ISSUES BEFORE TRAINING")
    print("=" * 80)
    
    # Training command
    print("\nTRAINING COMMAND:")
    print("-" * 80)
    cmd = """cd E:\\FYP
conda activate fassd
python code/phase4/train_hybrid_model.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 D:/FYP/data/features/logmel_packed.h5 --environmental_h5 D:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 64 --epochs 20 --num_workers 8"""
    print(cmd)
    print("-" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

