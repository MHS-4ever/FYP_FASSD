"""
Analyze Unified Dataset Statistics for Phase 1

Generates comprehensive statistics about the unified dataset including:
- Total samples per dataset
- Total samples per attack type
- Total samples per domain
- Speaker count per split
- Real/fake distribution per split
- Domain distribution per split

Usage:
    python analyze_unified_dataset.py --manifest data/manifests/unified_manifest.csv --output data/statistics/unified_dataset_stats.json
"""

import argparse
import os
import pandas as pd
import json
from pathlib import Path


def analyze_unified_manifest(df, output_file):
    """
    Analyze unified manifest and generate statistics.
    
    Args:
        df: Unified manifest DataFrame
        output_file: Path to save statistics JSON
    """
    print("\n[INFO] Analyzing unified manifest...")
    
    stats = {
        'total_samples': len(df),
        'total_speakers': df['speaker_id'].nunique() if 'speaker_id' in df.columns else None,
        'by_dataset': {},
        'by_label': {},
        'by_attack_type': {},
        'by_domain': {},
        'by_source': {},
        'dataset_label_crosstab': {},
        'dataset_domain_crosstab': {},
        'label_attack_crosstab': {}
    }
    
    # By dataset
    if 'dataset' in df.columns:
        dataset_counts = df['dataset'].value_counts().to_dict()
        stats['by_dataset'] = {str(k): int(v) for k, v in dataset_counts.items()}
        
        # Speakers per dataset
        if 'speaker_id' in df.columns:
            speakers_per_dataset = df.groupby('dataset')['speaker_id'].nunique().to_dict()
            stats['speakers_per_dataset'] = {str(k): int(v) for k, v in speakers_per_dataset.items()}
    
    # By label
    if 'label' in df.columns:
        label_counts = df['label'].value_counts().to_dict()
        stats['by_label'] = {str(k): int(v) for k, v in label_counts.items()}
        
        # Real/Fake ratio
        if 'bonafide' in label_counts and 'spoof' in label_counts:
            total = label_counts['bonafide'] + label_counts['spoof']
            stats['real_ratio'] = label_counts['bonafide'] / total if total > 0 else 0
            stats['fake_ratio'] = label_counts['spoof'] / total if total > 0 else 0
    
    # By attack type
    if 'attack_type' in df.columns:
        attack_counts = df['attack_type'].value_counts().to_dict()
        stats['by_attack_type'] = {str(k): int(v) for k, v in attack_counts.items()}
    
    # By domain
    if 'domain' in df.columns:
        domain_counts = df['domain'].value_counts().to_dict()
        stats['by_domain'] = {str(k): int(v) for k, v in domain_counts.items()}
    
    # By source
    if 'source' in df.columns:
        source_counts = df['source'].value_counts().to_dict()
        stats['by_source'] = {str(k): int(v) for k, v in source_counts.items()}
    
    # Cross-tabulations
    if 'dataset' in df.columns and 'label' in df.columns:
        crosstab = pd.crosstab(df['dataset'], df['label'])
        stats['dataset_label_crosstab'] = {
            str(row): {str(col): int(crosstab.loc[row, col]) for col in crosstab.columns}
            for row in crosstab.index
        }
    
    if 'dataset' in df.columns and 'domain' in df.columns:
        crosstab = pd.crosstab(df['dataset'], df['domain'])
        stats['dataset_domain_crosstab'] = {
            str(row): {str(col): int(crosstab.loc[row, col]) for col in crosstab.columns}
            for row in crosstab.index
        }
    
    if 'label' in df.columns and 'attack_type' in df.columns:
        crosstab = pd.crosstab(df['label'], df['attack_type'])
        stats['label_attack_crosstab'] = {
            str(row): {str(col): int(crosstab.loc[row, col]) for col in crosstab.columns}
            for row in crosstab.index
        }
    
    # Duration statistics (if available)
    if 'duration' in df.columns:
        duration_data = df['duration'].dropna()
        if len(duration_data) > 0:
            stats['duration'] = {
                'mean': float(duration_data.mean()),
                'median': float(duration_data.median()),
                'min': float(duration_data.min()),
                'max': float(duration_data.max()),
                'std': float(duration_data.std())
            }
    
    # Save statistics
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"[OK] Statistics saved to: {output_file}")
    
    return stats


def analyze_splits(split_dir, output_file):
    """
    Analyze split manifests and generate statistics.
    
    Args:
        split_dir: Directory containing split manifests
        output_file: Path to save split statistics JSON
    """
    print("\n[INFO] Analyzing splits...")
    
    splits = ['train', 'val', 'test']
    split_stats = {}
    
    for split_name in splits:
        split_file = os.path.join(split_dir, f"{split_name}_speaker_independent.csv")
        
        if not os.path.exists(split_file):
            print(f"[WARNING] Split file not found: {split_file}")
            continue
        
        df_split = pd.read_csv(split_file, low_memory=False)
        
        stats = {
            'split': split_name,
            'n_samples': len(df_split),
            'n_speakers': df_split['speaker_id'].nunique() if 'speaker_id' in df_split.columns else None,
            'by_dataset': {},
            'by_label': {},
            'by_attack_type': {},
            'by_domain': {},
            'real_ratio': 0,
            'fake_ratio': 0
        }
        
        # By dataset
        if 'dataset' in df_split.columns:
            stats['by_dataset'] = df_split['dataset'].value_counts().to_dict()
        
        # By label
        if 'label' in df_split.columns:
            label_counts = df_split['label'].value_counts().to_dict()
            stats['by_label'] = label_counts
            
            total = sum(label_counts.values())
            if total > 0:
                stats['real_ratio'] = label_counts.get('bonafide', 0) / total
                stats['fake_ratio'] = label_counts.get('spoof', 0) / total
        
        # By attack type
        if 'attack_type' in df_split.columns:
            stats['by_attack_type'] = df_split['attack_type'].value_counts().to_dict()
        
        # By domain
        if 'domain' in df_split.columns:
            stats['by_domain'] = df_split['domain'].value_counts().to_dict()
        
        split_stats[split_name] = stats
    
    # Save split statistics
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(split_stats, f, indent=2)
    
    print(f"[OK] Split statistics saved to: {output_file}")
    
    return split_stats


def print_summary(stats):
    """Print summary statistics to console."""
    print("\n" + "="*80)
    print("UNIFIED DATASET STATISTICS SUMMARY")
    print("="*80)
    
    print(f"\nTotal Samples: {stats['total_samples']:,}")
    
    if stats.get('total_speakers'):
        print(f"Total Speakers: {stats['total_speakers']:,}")
    
    if stats.get('by_dataset'):
        print("\nBy Dataset:")
        for dataset, count in sorted(stats['by_dataset'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {dataset}: {count:,}")
    
    if stats.get('by_label'):
        print("\nBy Label:")
        for label, count in sorted(stats['by_label'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {label}: {count:,}")
        
        if 'real_ratio' in stats:
            print(f"\nReal/Fake Ratio: {stats['real_ratio']:.2%} / {stats['fake_ratio']:.2%}")
    
    if stats.get('by_attack_type'):
        print("\nBy Attack Type:")
        for attack, count in sorted(stats['by_attack_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {attack}: {count:,}")
    
    if stats.get('by_domain'):
        print("\nBy Domain:")
        for domain, count in sorted(stats['by_domain'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain}: {count:,}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Analyze unified dataset statistics")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--split_dir',
        type=str,
        default=r'E:\FYP\data\manifests',
        help='Directory containing split manifests (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=r'E:\FYP\data\statistics\unified_dataset_stats.json',
        help='Output path for statistics JSON'
    )
    parser.add_argument(
        '--split_output',
        type=str,
        default=None,
        help='Output path for split statistics JSON (default: {output_dir}/split_statistics.json)'
    )
    
    args = parser.parse_args()
    
    # Set default split_output
    if args.split_output is None:
        args.split_output = os.path.join(os.path.dirname(args.output), "split_statistics.json")
    
    print("="*80)
    print("ANALYZING UNIFIED DATASET")
    print("="*80)
    
    # Load unified manifest
    if not os.path.exists(args.manifest):
        raise FileNotFoundError(f"Unified manifest not found: {args.manifest}")
    
    print(f"\n[INFO] Loading unified manifest: {args.manifest}")
    df = pd.read_csv(args.manifest, low_memory=False)
    print(f"[OK] Loaded {len(df):,} samples")
    
    # Analyze unified manifest
    stats = analyze_unified_manifest(df, args.output)
    
    # Print summary
    print_summary(stats)
    
    # Analyze splits if directory provided
    if args.split_dir and os.path.exists(args.split_dir):
        split_stats = analyze_splits(args.split_dir, args.split_output)
        
        print("\n" + "="*80)
        print("SPLIT STATISTICS SUMMARY")
        print("="*80)
        
        for split_name, stats in split_stats.items():
            print(f"\n[{split_name.upper()}]")
            print(f"  Samples: {stats['n_samples']:,}")
            if stats.get('n_speakers'):
                print(f"  Speakers: {stats['n_speakers']:,}")
            if 'real_ratio' in stats:
                print(f"  Real/Fake: {stats['real_ratio']:.2%} / {stats['fake_ratio']:.2%}")
    
    print("\n" + "="*80)
    print("VALIDATION CHECKPOINT")
    print("="*80)
    print("\n[INFO] Review the statistics above and verify:")
    print("  1. Each split contains both ASVspoof and Real-world data")
    print("  2. Each split contains both bonafide and spoof samples")
    print("  3. Real/fake ratios are approximately similar across splits")
    print("  4. No split has 0 samples for a required dataset")
    print("\n[INFO] If any of these checks fail, fix issues before proceeding to Phase-2.")
    print("="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
