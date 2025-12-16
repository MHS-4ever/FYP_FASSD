"""
Create Speaker-Independent Splits for Phase 1

Splits the unified dataset by speaker (not by sample) to ensure no speaker overlap
between train/validation/test sets. This is critical for true generalization.

This script:
1. Groups samples by speaker_id
2. Splits speakers into train/val/test (80/10/10)
3. Ensures balanced real/fake distribution in each split
4. Ensures both ASVspoof and Real-world data in each split
5. Creates separate manifest files for each split

Usage:
    python create_speaker_independent_split.py --manifest data/manifests/unified_manifest.csv --output_dir data/manifests --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1
"""

import argparse
import os
import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm
import json


def get_speaker_statistics(df):
    """
    Get statistics for each speaker.
    
    Returns:
        DataFrame with columns: speaker_id, dataset, label, count
    """
    speaker_stats = df.groupby(['speaker_id', 'dataset', 'label']).size().reset_index(name='count')
    return speaker_stats


def split_speakers_stratified(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_seed=42):
    """
    Split speakers into train/val/test ensuring:
    1. No speaker overlap between splits
    2. Approximately balanced real/fake distribution
    3. Both ASVspoof and Real-world in each split
    
    Note: Stratification is approximate. Speakers with both real and fake samples
    are assigned to a single group based on the primary (mode) label/dataset.
    This may slightly skew balance but is acceptable for Phase-1.
    
    Args:
        df: Unified manifest DataFrame
        train_ratio: Proportion of speakers for training
        val_ratio: Proportion of speakers for validation
        test_ratio: Proportion of speakers for testing
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with keys: 'train_speakers', 'val_speakers', 'test_speakers'
    """
    np.random.seed(random_seed)
    
    # Get unique speakers
    all_speakers = df['speaker_id'].unique()
    print(f"\n[INFO] Total unique speakers: {len(all_speakers):,}")
    
    # Use groupby for efficient computation of primary dataset/label per speaker
    # This is much faster than iterating and filtering the dataframe for each speaker
    print("[INFO] Computing speaker groups (this may take a moment)...")
    speaker_groups = df.groupby('speaker_id').agg({
        'dataset': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',
        'label': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'
    }).reset_index()
    
    # Create group keys
    speaker_groups['group_key'] = speaker_groups['dataset'].astype(str) + '_' + speaker_groups['label'].astype(str)
    
    # Group speakers by their group key
    speakers_by_group = defaultdict(list)
    for _, row in speaker_groups.iterrows():
        group_key = row['group_key']
        speaker_id = row['speaker_id']
        speakers_by_group[group_key].append(speaker_id)
    
    print(f"[INFO] Speaker groups: {len(speakers_by_group)}")
    # Show top groups by size
    group_sizes = [(group, len(speakers)) for group, speakers in speakers_by_group.items()]
    group_sizes.sort(key=lambda x: x[1], reverse=True)
    for group, size in group_sizes[:10]:  # Show top 10 groups
        print(f"  - {group}: {size:,} speakers")
    if len(group_sizes) > 10:
        print(f"  ... and {len(group_sizes) - 10} more groups")
    
    # Split speakers from each group
    train_speakers = []
    val_speakers = []
    test_speakers = []
    
    for group_key, speakers in speakers_by_group.items():
        # Shuffle speakers in this group
        np.random.shuffle(speakers)
        
        n_speakers = len(speakers)
        n_train = int(n_speakers * train_ratio)
        n_val = int(n_speakers * val_ratio)
        n_test = n_speakers - n_train - n_val  # Remaining goes to test
        
        train_speakers.extend(speakers[:n_train])
        val_speakers.extend(speakers[n_train:n_train+n_val])
        test_speakers.extend(speakers[n_train+n_val:])
    
    # Verify no overlap
    train_set = set(train_speakers)
    val_set = set(val_speakers)
    test_set = set(test_speakers)
    
    assert len(train_set & val_set) == 0, "Speaker overlap between train and val!"
    assert len(train_set & test_set) == 0, "Speaker overlap between train and test!"
    assert len(val_set & test_set) == 0, "Speaker overlap between val and test!"
    
    print(f"\n[OK] Speaker split complete:")
    print(f"  - Train: {len(train_speakers):,} speakers")
    print(f"  - Validation: {len(val_speakers):,} speakers")
    print(f"  - Test: {len(test_speakers):,} speakers")
    
    return {
        'train_speakers': train_speakers,
        'val_speakers': val_speakers,
        'test_speakers': test_speakers
    }


def create_split_manifests(df, speaker_splits, output_dir):
    """
    Create manifest files for each split.
    
    Args:
        df: Unified manifest DataFrame
        speaker_splits: Dictionary with speaker lists for each split
        output_dir: Directory to save split manifests
    
    Returns:
        Dictionary with split statistics
    """
    os.makedirs(output_dir, exist_ok=True)
    
    splits = {
        'train': speaker_splits['train_speakers'],
        'val': speaker_splits['val_speakers'],
        'test': speaker_splits['test_speakers']
    }
    
    split_stats = {}
    
    for split_name, speakers in splits.items():
        # Filter dataframe for this split
        df_split = df[df['speaker_id'].isin(speakers)].copy()
        
        # Save manifest
        output_file = os.path.join(output_dir, f"{split_name}_speaker_independent.csv")
        df_split.to_csv(output_file, index=False)
        
        # Calculate statistics
        stats = {
            'split': split_name,
            'n_speakers': len(speakers),
            'n_samples': len(df_split),
            'by_dataset': df_split['dataset'].value_counts().to_dict(),
            'by_label': df_split['label'].value_counts().to_dict(),
            'by_attack_type': df_split['attack_type'].value_counts().to_dict(),
            'by_domain': df_split['domain'].value_counts().to_dict(),
            'real_ratio': len(df_split[df_split['label'] == 'bonafide']) / len(df_split) if len(df_split) > 0 else 0,
            'fake_ratio': len(df_split[df_split['label'] == 'spoof']) / len(df_split) if len(df_split) > 0 else 0,
        }
        
        split_stats[split_name] = stats
        
        print(f"\n[{split_name.upper()}]")
        print(f"  Speakers: {stats['n_speakers']:,}")
        print(f"  Samples: {stats['n_samples']:,}")
        print(f"  Real/Fake: {stats['real_ratio']:.2%} / {stats['fake_ratio']:.2%}")
        print(f"  Saved to: {output_file}")
    
    return split_stats


def verify_splits(df, speaker_splits):
    """
    Verify that splits meet requirements:
    1. No speaker overlap
    2. Balanced real/fake distribution
    3. Both ASVspoof and Real-world in each split
    """
    print("\n" + "="*80)
    print("VERIFYING SPLITS")
    print("="*80)
    
    splits = {
        'train': speaker_splits['train_speakers'],
        'val': speaker_splits['val_speakers'],
        'test': speaker_splits['test_speakers']
    }
    
    all_checks_passed = True
    
    for split_name, speakers in splits.items():
        df_split = df[df['speaker_id'].isin(speakers)]
        
        print(f"\n[{split_name.upper()}]")
        
        # Check 1: Has both ASVspoof and Real-world
        datasets = df_split['dataset'].unique()
        has_asvspoof = any(d in ['LA', 'DF', 'PA'] for d in datasets)
        has_realworld = 'RealWorld' in datasets
        
        if has_asvspoof and has_realworld:
            print("  ✓ Contains both ASVspoof and Real-world data")
        else:
            print(f"  ✗ Missing data: ASVspoof={has_asvspoof}, Real-world={has_realworld}")
            all_checks_passed = False
        
        # Check 2: Has both real and fake samples
        labels = df_split['label'].unique()
        has_real = 'bonafide' in labels
        has_fake = 'spoof' in labels
        
        if has_real and has_fake:
            print("  ✓ Contains both bonafide and spoof samples")
        else:
            print(f"  ✗ Missing labels: bonafide={has_real}, spoof={has_fake}")
            all_checks_passed = False
        
        # Check 3: Reasonable real/fake ratio
        real_count = len(df_split[df_split['label'] == 'bonafide'])
        fake_count = len(df_split[df_split['label'] == 'spoof'])
        total = len(df_split)
        
        if total > 0:
            real_ratio = real_count / total
            print(f"  ✓ Real/Fake ratio: {real_ratio:.2%} / {1-real_ratio:.2%}")
            
            # Warn if ratio is extreme (but don't fail)
            if real_ratio < 0.01 or real_ratio > 0.99:
                print(f"  ⚠ Warning: Extreme real/fake ratio")
        else:
            print("  ✗ No samples in split!")
            all_checks_passed = False
    
    # Check 4: No speaker overlap
    train_set = set(speaker_splits['train_speakers'])
    val_set = set(speaker_splits['val_speakers'])
    test_set = set(speaker_splits['test_speakers'])
    
    if len(train_set & val_set) == 0 and len(train_set & test_set) == 0 and len(val_set & test_set) == 0:
        print("\n  ✓ No speaker overlap between splits")
    else:
        print("\n  ✗ Speaker overlap detected!")
        all_checks_passed = False
    
    return all_checks_passed


def main():
    parser = argparse.ArgumentParser(description="Create speaker-independent splits")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=r'E:\FYP\data\manifests',
        help='Output directory for split manifests'
    )
    parser.add_argument(
        '--train_ratio',
        type=float,
        default=0.8,
        help='Proportion of speakers for training (default: 0.8)'
    )
    parser.add_argument(
        '--val_ratio',
        type=float,
        default=0.1,
        help='Proportion of speakers for validation (default: 0.1)'
    )
    parser.add_argument(
        '--test_ratio',
        type=float,
        default=0.1,
        help='Proportion of speakers for testing (default: 0.1)'
    )
    parser.add_argument(
        '--random_seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")
    
    print("="*80)
    print("CREATING SPEAKER-INDEPENDENT SPLITS")
    print("="*80)
    print()
    print(f"[INFO] Split ratios: Train={args.train_ratio:.1%}, Val={args.val_ratio:.1%}, Test={args.test_ratio:.1%}")
    print(f"[INFO] Random seed: {args.random_seed}")
    print()
    
    # Load unified manifest
    if not os.path.exists(args.manifest):
        raise FileNotFoundError(f"Unified manifest not found: {args.manifest}")
    
    print(f"[INFO] Loading unified manifest: {args.manifest}")
    df = pd.read_csv(args.manifest, low_memory=False)
    print(f"[OK] Loaded {len(df):,} samples")
    
    # Check for speaker_id column
    if 'speaker_id' not in df.columns:
        raise ValueError("Manifest must contain 'speaker_id' column")
    
    # Remove rows with missing speaker_id
    initial_count = len(df)
    df = df[df['speaker_id'].notna()].copy()
    if len(df) < initial_count:
        print(f"[WARNING] Removed {initial_count - len(df)} samples with missing speaker_id")
    
    # Split speakers
    speaker_splits = split_speakers_stratified(
        df,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_seed=args.random_seed
    )
    
    # Create split manifests
    split_stats = create_split_manifests(df, speaker_splits, args.output_dir)
    
    # Verify splits
    all_checks_passed = verify_splits(df, speaker_splits)
    
    # Save statistics
    stats_file = os.path.join(args.output_dir, "split_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(split_stats, f, indent=2)
    print(f"\n[OK] Statistics saved to: {stats_file}")
    
    # Save speaker lists
    speakers_file = os.path.join(args.output_dir, "speaker_splits.json")
    speaker_splits_serializable = {
        'train_speakers': [str(s) for s in speaker_splits['train_speakers']],
        'val_speakers': [str(s) for s in speaker_splits['val_speakers']],
        'test_speakers': [str(s) for s in speaker_splits['test_speakers']]
    }
    with open(speakers_file, 'w') as f:
        json.dump(speaker_splits_serializable, f, indent=2)
    print(f"[OK] Speaker lists saved to: {speakers_file}")
    
    # Check for potential issues
    print("\n[INFO] Checking for potential issues...")
    issues_found = False
    for split_name, stats in split_stats.items():
        # Check if any dataset is missing
        if stats.get('by_dataset'):
            datasets = set(stats['by_dataset'].keys())
            required_datasets = {'LA', 'DF', 'PA', 'RealWorld'}
            missing = required_datasets - datasets
            if missing:
                print(f"  ⚠ Warning: {split_name} split missing datasets: {missing}")
                issues_found = True
        
        # Check if real or fake is missing
        if stats.get('by_label'):
            labels = set(stats['by_label'].keys())
            if 'bonafide' not in labels or 'spoof' not in labels:
                print(f"  ⚠ Warning: {split_name} split missing bonafide or spoof samples")
                issues_found = True
    
    if not issues_found:
        print("  ✓ No obvious issues detected")
    else:
        print("  ⚠ Review split_statistics.json for details")
    
    print("\n" + "="*80)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED")
    else:
        print("⚠ SOME CHECKS FAILED - Review output above")
    print("="*80)


if __name__ == "__main__":
    main()
