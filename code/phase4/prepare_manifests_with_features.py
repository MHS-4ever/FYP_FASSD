"""
Prepare Phase 4 Training Manifests with Feature Indices

This script merges speaker-independent split manifests with the features manifest
to add spectrogram_idx and environmental_idx columns required for training.

Usage:
    python code/phase4/prepare_manifests_with_features.py
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def prepare_manifest(split_manifest_path, features_manifest_path, output_path, split_name):
    """
    Merge split manifest with features manifest to add feature indices.
    
    Args:
        split_manifest_path: Path to speaker-independent split manifest
        features_manifest_path: Path to features manifest with indices
        output_path: Path to save merged manifest
        split_name: Name of split (for logging)
    """
    print(f"\n[{split_name.upper()}] Loading split manifest: {split_manifest_path}")
    split_df = pd.read_csv(split_manifest_path, low_memory=False)
    print(f"[INFO] {split_name} samples: {len(split_df)}")
    print(f"[INFO] {split_name} columns: {list(split_df.columns)}")
    
    print(f"\n[{split_name.upper()}] Loading features manifest: {features_manifest_path}")
    features_df = pd.read_csv(features_manifest_path, low_memory=False)
    print(f"[INFO] Features manifest samples: {len(features_df)}")
    print(f"[INFO] Features manifest columns: {list(features_df.columns)}")
    
    # Identify the merge key (filepath or similar)
    # Check common column names
    merge_keys = ['filepath', 'path', 'audio_path', 'filename']
    merge_key = None
    
    for key in merge_keys:
        if key in split_df.columns and key in features_df.columns:
            merge_key = key
            break
    
    if merge_key is None:
        # Try to find a common column
        common_cols = set(split_df.columns) & set(features_df.columns)
        if len(common_cols) == 0:
            raise ValueError(f"No common columns found between split and features manifests. "
                           f"Split columns: {list(split_df.columns)}, "
                           f"Features columns: {list(features_df.columns)}")
        merge_key = list(common_cols)[0]
        print(f"[WARNING] Using '{merge_key}' as merge key (may not be ideal)")
    else:
        print(f"[INFO] Merging on column: '{merge_key}'")
    
    # Merge to get feature indices
    print(f"\n[{split_name.upper()}] Merging manifests...")
    merged_df = split_df.merge(
        features_df[['spectrogram_idx', 'environmental_idx', merge_key]],
        on=merge_key,
        how='inner'
    )
    
    print(f"[INFO] After merge: {len(merged_df)} samples (dropped {len(split_df) - len(merged_df)} without features)")
    
    # Filter samples that have both features
    before_filter = len(merged_df)
    merged_df = merged_df[
        (merged_df['spectrogram_idx'] >= 0) & (merged_df['environmental_idx'] >= 0)
    ].reset_index(drop=True)
    
    print(f"[INFO] Samples with both features: {len(merged_df)} (dropped {before_filter - len(merged_df)} with missing features)")
    
    # Save merged manifest
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"[OK] Saved merged manifest to: {output_path}")
    
    # Print statistics
    if 'label' in merged_df.columns:
        print(f"\n[{split_name.upper()}] Label distribution:")
        print(merged_df['label'].value_counts())
    
    return merged_df


def main():
    """Main function to prepare both train and validation manifests."""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    
    train_split_path = project_root / 'data' / 'manifests' / 'train_speaker_independent.csv'
    val_split_path = project_root / 'data' / 'manifests' / 'val_speaker_independent.csv'
    features_manifest_path = project_root / 'data' / 'features' / 'features_manifest_unified.csv'
    
    train_output_path = project_root / 'data' / 'manifests' / 'train_speaker_independent_with_features.csv'
    val_output_path = project_root / 'data' / 'manifests' / 'val_speaker_independent_with_features.csv'
    
    print("="*80)
    print("PHASE 4: PREPARE MANIFESTS WITH FEATURE INDICES")
    print("="*80)
    
    # Check input files exist
    if not train_split_path.exists():
        print(f"[ERROR] Training split not found: {train_split_path}")
        return 1
    if not val_split_path.exists():
        print(f"[ERROR] Validation split not found: {val_split_path}")
        return 1
    if not features_manifest_path.exists():
        print(f"[ERROR] Features manifest not found: {features_manifest_path}")
        return 1
    
    try:
        # Prepare training manifest
        train_df = prepare_manifest(
            train_split_path, 
            features_manifest_path, 
            train_output_path,
            'TRAIN'
        )
        
        # Prepare validation manifest
        val_df = prepare_manifest(
            val_split_path, 
            features_manifest_path, 
            val_output_path,
            'VAL'
        )
        
        print("\n" + "="*80)
        print("✓ MANIFESTS PREPARED SUCCESSFULLY")
        print("="*80)
        print(f"\n[INFO] Training manifest: {train_output_path}")
        print(f"       Samples: {len(train_df)}")
        print(f"\n[INFO] Validation manifest: {val_output_path}")
        print(f"       Samples: {len(val_df)}")
        print("\n[INFO] Next step: Run training with these manifests:")
        print(f"       python code/phase4/train_hybrid_model.py")
        print(f"       --train_manifest {train_output_path}")
        print(f"       --val_manifest {val_output_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Failed to prepare manifests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

