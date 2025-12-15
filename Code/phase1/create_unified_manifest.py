"""
Create Unified Manifest for Phase 1

Combines ASVspoof datasets (LA, DF, PA) with Real-world data into a single unified manifest.

**IMPORTANT NOTE**: ASVspoof_PA (Physical Access) dataset is NEWLY ADDED and was NOT used 
in the previous pipeline. Previous pipeline only used ASVspoof_LA and ASVspoof_DF. This 
unified pipeline now includes all three ASVspoof datasets for comprehensive attack type coverage.

This script:
1. Loads ASVspoof manifest (or creates it if needed) - includes LA, DF, and PA
2. Loads Real-world manifest
3. Standardizes columns and labels
4. Combines into unified manifest with all required metadata
5. Maps domains and attack types correctly

Usage:
    python create_unified_manifest.py --asvspoof_manifest data/manifests/unified_asvspoof_manifest.csv --realworld_manifest data/realworld/manifest_realworld.csv --output data/manifests/unified_manifest.csv
"""

import argparse
import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import sys

# Add parent directory to path to import from code/
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)

# Import parsing functions from parent create_unified_manifest
# Use importlib to avoid naming conflicts
import importlib.util
parent_script = os.path.join(parent_dir, 'create_unified_manifest.py')
if os.path.exists(parent_script):
    spec = importlib.util.spec_from_file_location("asvspoof_parser", parent_script)
    asvspoof_parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asvspoof_parser)
    parse_la_metadata = asvspoof_parser.parse_la_metadata
    parse_df_metadata = asvspoof_parser.parse_df_metadata
    parse_pa_metadata = asvspoof_parser.parse_pa_metadata
else:
    # Fallback: define functions inline if parent script doesn't exist
    def parse_la_metadata(metadata_path, clips_dir):
        """Parse LA (Logical Access) metadata."""
        print(f"\n[LA] Parsing metadata from: {metadata_path}")
        if not os.path.exists(metadata_path):
            print(f"[ERROR] Metadata file not found: {metadata_path}")
            return []
        records = []
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Reading LA metadata"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 6:
                    continue
                speaker_id = parts[0]
                file_id = parts[1]
                label = parts[5]
                if label == "bonafide":
                    label = "bonafide"
                    attack_type = "bonafide"
                else:
                    label = "spoof"
                    attack_type = "synthesis"
                audio_file = os.path.join(clips_dir, f"{file_id}.flac")
                if not os.path.exists(audio_file):
                    audio_file = os.path.join(clips_dir, f"{file_id}.wav")
                if not os.path.exists(audio_file):
                    continue
                records.append({
                    "filepath": audio_file,
                    "filename": os.path.basename(audio_file),
                    "file_id": file_id,
                    "speaker_id": speaker_id,
                    "label": label,
                    "dataset": "LA",
                    "attack_type": attack_type
                })
        print(f"[LA] Found {len(records)} valid records")
        return records
    
    def parse_df_metadata(metadata_path, clips_dir):
        """Parse DF (DeepFake) metadata."""
        print(f"\n[DF] Parsing metadata from: {metadata_path}")
        if not os.path.exists(metadata_path):
            print(f"[ERROR] Metadata file not found: {metadata_path}")
            return []
        records = []
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Reading DF metadata"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 6:
                    continue
                speaker_id = parts[0]
                file_id = parts[1]
                label = parts[5]
                if label == "bonafide":
                    label = "bonafide"
                    attack_type = "bonafide"
                else:
                    label = "spoof"
                    attack_type = "conversion"
                audio_file = os.path.join(clips_dir, f"{file_id}.flac")
                if not os.path.exists(audio_file):
                    audio_file = os.path.join(clips_dir, f"{file_id}.wav")
                if not os.path.exists(audio_file):
                    continue
                records.append({
                    "filepath": audio_file,
                    "filename": os.path.basename(audio_file),
                    "file_id": file_id,
                    "speaker_id": speaker_id,
                    "label": label,
                    "dataset": "DF",
                    "attack_type": attack_type
                })
        print(f"[DF] Found {len(records)} valid records")
        return records
    
    def parse_pa_metadata(metadata_path, clips_dir):
        """Parse PA (Physical Access) metadata."""
        print(f"\n[PA] Parsing metadata from: {metadata_path}")
        if not os.path.exists(metadata_path):
            print(f"[ERROR] Metadata file not found: {metadata_path}")
            return []
        records = []
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Reading PA metadata"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 10:
                    continue
                speaker_id = parts[0]
                file_id = parts[1]
                label = None
                for part in parts:
                    if part in ["bonafide", "spoof"]:
                        label = part
                        break
                if label is None:
                    continue
                if label == "bonafide":
                    label = "bonafide"
                    attack_type = "bonafide"
                else:
                    label = "spoof"
                    attack_type = "replay"
                audio_file = os.path.join(clips_dir, f"{file_id}.flac")
                if not os.path.exists(audio_file):
                    audio_file = os.path.join(clips_dir, f"{file_id}.wav")
                if not os.path.exists(audio_file):
                    continue
                records.append({
                    "filepath": audio_file,
                    "filename": os.path.basename(audio_file),
                    "file_id": file_id,
                    "speaker_id": speaker_id,
                    "label": label,
                    "dataset": "PA",
                    "attack_type": attack_type
                })
        print(f"[PA] Found {len(records)} valid records")
        return records


def load_asvspoof_manifest(manifest_path, base_dir=None, keys_dir=None):
    """
    Load ASVspoof manifest. If it doesn't exist, create it from metadata.
    
    Args:
        manifest_path: Path to existing ASVspoof manifest CSV
        base_dir: Base directory for ASVspoof datasets (if creating new)
        keys_dir: Keys directory for metadata files (if creating new)
    
    Returns:
        DataFrame with ASVspoof data
    """
    if os.path.exists(manifest_path):
        print(f"[INFO] Loading existing ASVspoof manifest: {manifest_path}")
        df = pd.read_csv(manifest_path)
        print(f"[OK] Loaded {len(df):,} ASVspoof samples")
        return df
    
    # If manifest doesn't exist, create it
    print(f"[WARNING] ASVspoof manifest not found: {manifest_path}")
    print("[INFO] Creating ASVspoof manifest from metadata...")
    
    if base_dir is None or keys_dir is None:
        raise ValueError("ASVspoof manifest not found and base_dir/keys_dir not provided to create it")
    
    # Dataset directories
    la_clips_dir = os.path.join(base_dir, "ASVspoof2021_LA_eval", "LA_clips")
    df_clips_dir = os.path.join(base_dir, "ASVspoof2021_DF_eval", "DF_clips")
    pa_clips_dir = os.path.join(base_dir, "ASVspoof2021_PA_eval", "PA_clips")
    
    # Trial metadata files
    la_metadata = os.path.join(keys_dir, "LA", "CM", "trial_metadata.txt")
    df_metadata = os.path.join(keys_dir, "DF", "CM", "trial_metadata.txt")
    pa_metadata = os.path.join(keys_dir, "PA", "CM", "trial_metadata.txt")
    
    all_records = []
    
    # Parse all three datasets
    if os.path.exists(la_metadata):
        la_records = parse_la_metadata(la_metadata, la_clips_dir)
        all_records.extend(la_records)
    
    if os.path.exists(df_metadata):
        df_records = parse_df_metadata(df_metadata, df_clips_dir)
        all_records.extend(df_records)
    
    if os.path.exists(pa_metadata):
        pa_records = parse_pa_metadata(pa_metadata, pa_clips_dir)
        all_records.extend(pa_records)
    
    df = pd.DataFrame(all_records)
    
    # Save for future use
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    df.to_csv(manifest_path, index=False)
    print(f"[OK] Created and saved ASVspoof manifest: {manifest_path}")
    
    return df


def standardize_asvspoof_manifest(df_asvspoof):
    """
    Standardize ASVspoof manifest to match unified format.
    
    Adds missing columns: domain, source
    Maps dataset names correctly
    """
    print("\n[INFO] Standardizing ASVspoof manifest...")
    
    # Add domain column (ASVspoof is typically studio/clean)
    df_asvspoof['domain'] = 'studio'
    
    # Add source column
    df_asvspoof['source'] = 'clean'
    
    # Ensure label is correct (bonafide/spoof)
    df_asvspoof['label'] = df_asvspoof['label'].map({
        'bonafide': 'bonafide',
        'spoof': 'spoof'
    })
    
    # Ensure dataset column is correct
    df_asvspoof['dataset'] = df_asvspoof['dataset'].map({
        'LA': 'LA',
        'DF': 'DF',
        'PA': 'PA'
    })
    
    # Add duration if missing (will be None, can be filled later if needed)
    if 'duration' not in df_asvspoof.columns:
        df_asvspoof['duration'] = None
    
    # Ensure filepath is absolute or relative correctly
    # Convert to string if Path object
    if 'filepath' in df_asvspoof.columns:
        df_asvspoof['filepath'] = df_asvspoof['filepath'].astype(str)
    
    print(f"[OK] Standardized {len(df_asvspoof):,} ASVspoof samples")
    return df_asvspoof


def standardize_realworld_manifest(df_realworld):
    """
    Standardize Real-world manifest to match unified format.
    
    Maps dataset name to 'RealWorld'
    Ensures all labels are 'bonafide' (except synthetic which should be 'spoof')
    Maps domains correctly
    """
    print("\n[INFO] Standardizing Real-world manifest...")
    
    # Map dataset to 'RealWorld'
    df_realworld['dataset'] = 'RealWorld'
    
    # Map domains: keep existing domains, but ensure consistency
    domain_mapping = {
        'read_speech': 'read_speech',
        'studio': 'studio',
        'broadcast': 'broadcast',
        'podcast': 'podcast',
        'social': 'social',
        'phone': 'phone',
        'synthetic': 'synthetic'  # Synthetic audio is spoof
    }
    
    if 'domain' in df_realworld.columns:
        df_realworld['domain'] = df_realworld['domain'].map(
            lambda x: domain_mapping.get(x, 'unknown')
        )
    
    # Update labels: synthetic should be spoof, everything else bonafide
    if 'domain' in df_realworld.columns:
        df_realworld['label'] = df_realworld.apply(
            lambda row: 'spoof' if row.get('domain') == 'synthetic' else 'bonafide',
            axis=1
        )
    
    # Update attack_type: synthetic should be 'synthesis', others 'bonafide'
    # Note: Real-world synthetic samples use same "synthesis" label as ASVspoof_LA,
    # but generation methods/quality may differ from ASVspoof synthetic samples
    if 'attack_type' in df_realworld.columns:
        df_realworld['attack_type'] = df_realworld.apply(
            lambda row: 'synthesis' if row.get('domain') == 'synthetic' else 'bonafide',
            axis=1
        )
    
    # Ensure source column exists
    if 'source' not in df_realworld.columns:
        df_realworld['source'] = 'realworld'
    else:
        # Map existing source values
        df_realworld['source'] = df_realworld['source'].map({
            'public_dataset': 'realworld',
            'youtube': 'realworld',
            'synthetic': 'realworld',
            'realworld': 'realworld'
        })
    
    # Ensure filepath is string
    if 'filepath' in df_realworld.columns:
        df_realworld['filepath'] = df_realworld['filepath'].astype(str)
    
    print(f"[OK] Standardized {len(df_realworld):,} Real-world samples")
    return df_realworld


def combine_manifests(df_asvspoof, df_realworld):
    """
    Combine ASVspoof and Real-world manifests into unified format.
    
    Ensures all required columns are present:
    - filepath
    - label (bonafide/spoof)
    - dataset (LA/DF/PA/RealWorld)
    - attack_type (bonafide/synthesis/conversion/replay)
    - domain (studio/broadcast/phone/podcast/social/read_speech)
    - speaker_id
    - source (clean/augmented/realworld)
    - duration (optional)
    """
    print("\n[INFO] Combining manifests...")
    
    # Define required columns
    required_columns = [
        'filepath', 'label', 'dataset', 'attack_type', 
        'domain', 'speaker_id', 'source'
    ]
    
    # Ensure both dataframes have all required columns
    for col in required_columns:
        if col not in df_asvspoof.columns:
            df_asvspoof[col] = None
        if col not in df_realworld.columns:
            df_realworld[col] = None
    
    # Select only required columns (plus duration if available)
    common_columns = list(set(required_columns + ['duration', 'filename', 'file_id']))
    common_columns = [col for col in common_columns if col in df_asvspoof.columns or col in df_realworld.columns]
    
    # Select columns that exist in both
    asvspoof_cols = [col for col in common_columns if col in df_asvspoof.columns]
    realworld_cols = [col for col in common_columns if col in df_realworld.columns]
    
    # Align columns
    df_asvspoof_aligned = df_asvspoof[asvspoof_cols].copy()
    df_realworld_aligned = df_realworld[realworld_cols].copy()
    
    # Add missing columns to each
    for col in common_columns:
        if col not in df_asvspoof_aligned.columns:
            df_asvspoof_aligned[col] = None
        if col not in df_realworld_aligned.columns:
            df_realworld_aligned[col] = None
    
    # Reorder columns consistently
    df_asvspoof_aligned = df_asvspoof_aligned[common_columns]
    df_realworld_aligned = df_realworld_aligned[common_columns]
    
    # Ensure both dataframes have same column order and dtypes
    for col in common_columns:
        if col in df_asvspoof_aligned.columns and col in df_realworld_aligned.columns:
            # Align dtypes if possible
            if df_asvspoof_aligned[col].dtype != df_realworld_aligned[col].dtype:
                try:
                    df_realworld_aligned[col] = df_realworld_aligned[col].astype(df_asvspoof_aligned[col].dtype)
                except (ValueError, TypeError):
                    pass  # Keep original dtype if conversion fails
    
    # Combine (suppress FutureWarning by ensuring no empty columns)
    df_unified = pd.concat([df_asvspoof_aligned, df_realworld_aligned], ignore_index=True, sort=False)
    
    print(f"[OK] Combined manifest: {len(df_unified):,} total samples")
    print(f"  - ASVspoof: {len(df_asvspoof_aligned):,}")
    print(f"  - Real-world: {len(df_realworld_aligned):,}")
    
    return df_unified


def main():
    parser = argparse.ArgumentParser(description="Create unified manifest combining ASVspoof and Real-world data")
    parser.add_argument(
        '--asvspoof_manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_asvspoof_manifest.csv',
        help='Path to ASVspoof manifest CSV (will create if not exists)'
    )
    parser.add_argument(
        '--realworld_manifest',
        type=str,
        default=r'E:\FYP\data\realworld\manifest_realworld.csv',
        help='Path to Real-world manifest CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Output path for unified manifest'
    )
    parser.add_argument(
        '--asvspoof_base_dir',
        type=str,
        default=r'E:\FYP\DataSet\English',
        help='Base directory for ASVspoof datasets (if creating manifest)'
    )
    parser.add_argument(
        '--asvspoof_keys_dir',
        type=str,
        default=None,
        help='Keys directory for ASVspoof metadata (default: {asvspoof_base_dir}/keys)'
    )
    
    args = parser.parse_args()
    
    # Set default keys_dir
    if args.asvspoof_keys_dir is None:
        args.asvspoof_keys_dir = os.path.join(args.asvspoof_base_dir, "keys")
    
    print("="*80)
    print("CREATING UNIFIED MANIFEST (ASVspoof + Real-world)")
    print("="*80)
    print()
    print("[NOTE] ASVspoof_PA dataset is NEWLY ADDED (was not used in previous pipeline)")
    print("       Previous pipeline only used ASVspoof_LA and ASVspoof_DF.")
    print("       This unified pipeline now includes all three ASVspoof datasets.")
    print()
    
    # Load ASVspoof manifest
    df_asvspoof = load_asvspoof_manifest(
        args.asvspoof_manifest,
        base_dir=args.asvspoof_base_dir,
        keys_dir=args.asvspoof_keys_dir
    )
    
    # Load Real-world manifest
    if not os.path.exists(args.realworld_manifest):
        raise FileNotFoundError(f"Real-world manifest not found: {args.realworld_manifest}")
    
    print(f"\n[INFO] Loading Real-world manifest: {args.realworld_manifest}")
    df_realworld = pd.read_csv(args.realworld_manifest)
    print(f"[OK] Loaded {len(df_realworld):,} Real-world samples")
    
    # Standardize both manifests
    df_asvspoof = standardize_asvspoof_manifest(df_asvspoof)
    df_realworld = standardize_realworld_manifest(df_realworld)
    
    # Combine
    df_unified = combine_manifests(df_asvspoof, df_realworld)
    
    # Print statistics
    print("\n" + "="*80)
    print("UNIFIED MANIFEST STATISTICS")
    print("="*80)
    print(f"\nTotal samples: {len(df_unified):,}")
    print(f"\nBy Dataset:")
    print(df_unified['dataset'].value_counts())
    print(f"\nBy Label:")
    print(df_unified['label'].value_counts())
    print(f"\nBy Attack Type:")
    print(df_unified['attack_type'].value_counts())
    print(f"\nBy Domain:")
    print(df_unified['domain'].value_counts())
    print(f"\nBy Source:")
    print(df_unified['source'].value_counts())
    print(f"\nBy Dataset and Label:")
    print(pd.crosstab(df_unified['dataset'], df_unified['label']))
    print(f"\nUnique speakers: {df_unified['speaker_id'].nunique():,}")
    
    # Save unified manifest
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"\n[INFO] Saving unified manifest to: {args.output}")
    df_unified.to_csv(args.output, index=False)
    print(f"[OK] Unified manifest saved with {len(df_unified):,} samples")
    
    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
