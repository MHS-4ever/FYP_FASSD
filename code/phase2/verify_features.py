"""
Verify Extracted Features for Phase 2

Verifies that all extracted features are valid and match expected specifications:
- Spectrogram features: Shape [64, 400], no NaN/Inf values
- Environmental features: Shape [12], no NaN/Inf values
- All samples have features
- Feature ranges are reasonable

Usage:
    python verify_features.py --manifest data/features/features_manifest_unified.csv --spectrogram_h5 data/features/logmel_packed.h5 --environmental_h5 data/features/environmental_packed.h5
"""

import argparse
import os
import sys
import h5py
import numpy as np
import pandas as pd
from tqdm import tqdm
import json


def convert_to_native_types(obj):
    """
    Convert numpy types to native Python types for JSON serialization.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_native_types(item) for item in obj)
    else:
        return obj


def verify_spectrograms(h5_path, manifest_df):
    """
    Verify spectrogram features.
    
    Args:
        h5_path: Path to spectrogram HDF5 file
        manifest_df: Manifest DataFrame
    
    Returns:
        results: Dictionary with verification results
    """
    print(f"\n[VERIFY] Verifying spectrograms: {h5_path}")
    
    if not os.path.exists(h5_path):
        return {
            'valid': False,
            'error': 'HDF5 file not found'
        }
    
    results = {
        'valid': True,
        'num_samples': 0,
        'expected_shape': (64, 400),
        'shape_matches': 0,
        'has_nan': 0,
        'has_inf': 0,
        'value_range': None,
        'errors': []
    }
    
    try:
        with h5py.File(h5_path, 'r') as h5f:
            features = h5f['features']
            results['num_samples'] = features.shape[0]
            
            print(f"[INFO] Found {results['num_samples']} spectrogram features")
            print(f"[INFO] Expected shape: {results['expected_shape']}")
            print(f"[INFO] Actual shape: {features.shape}")
            
            # Verify shape
            if features.shape[1:] == results['expected_shape']:
                results['shape_matches'] = results['num_samples']
            else:
                results['valid'] = False
                results['errors'].append(f"Shape mismatch: {features.shape[1:]} != {results['expected_shape']}")
            
            # Vectorized check for NaN/Inf (much faster than checking one by one)
            print(f"[INFO] Checking all {results['num_samples']} samples for NaN/Inf (vectorized)...")
            
            # Load data in chunks to avoid memory issues
            chunk_size = 10000
            nan_indices = []
            inf_indices = []
            
            for chunk_start in tqdm(range(0, results['num_samples'], chunk_size), desc="Checking samples"):
                chunk_end = min(chunk_start + chunk_size, results['num_samples'])
                chunk_data = features[chunk_start:chunk_end]
                
                # Vectorized NaN/Inf check
                nan_mask = np.any(np.isnan(chunk_data), axis=(1, 2))
                inf_mask = np.any(np.isinf(chunk_data), axis=(1, 2))
                
                # Collect indices with issues
                chunk_nan_indices = np.where(nan_mask)[0] + chunk_start
                chunk_inf_indices = np.where(inf_mask)[0] + chunk_start
                
                nan_indices.extend(chunk_nan_indices.tolist())
                inf_indices.extend(chunk_inf_indices.tolist())
            
            results['has_nan'] = len(nan_indices)
            results['has_inf'] = len(inf_indices)
            
            if results['has_nan'] > 0:
                results['valid'] = False
                for idx in nan_indices[:10]:  # Report first 10
                    results['errors'].append(f"Sample {idx} contains NaN")
                if len(nan_indices) > 10:
                    results['errors'].append(f"... and {len(nan_indices) - 10} more samples with NaN")
            
            if results['has_inf'] > 0:
                results['valid'] = False
                for idx in inf_indices[:10]:  # Report first 10
                    results['errors'].append(f"Sample {idx} contains Inf")
                if len(inf_indices) > 10:
                    results['errors'].append(f"... and {len(inf_indices) - 10} more samples with Inf")
            
            # Compute value range (use larger sample for better statistics)
            sample_size = min(50000, results['num_samples'])  # Increased from 10000
            sample_data = features[:sample_size]
            results['value_range'] = {
                'min': float(np.min(sample_data)),
                'max': float(np.max(sample_data)),
                'mean': float(np.mean(sample_data)),
                'std': float(np.std(sample_data))
            }
            
            print(f"[INFO] Value range: [{results['value_range']['min']:.2f}, {results['value_range']['max']:.2f}]")
            print(f"[INFO] Mean: {results['value_range']['mean']:.2f}, Std: {results['value_range']['std']:.2f}")
            
    except Exception as e:
        results['valid'] = False
        results['error'] = str(e)
        results['errors'].append(f"Exception: {str(e)}")
    
    return results


def verify_environmental(h5_path, manifest_df):
    """
    Verify environmental features.
    
    Args:
        h5_path: Path to environmental HDF5 file
        manifest_df: Manifest DataFrame
    
    Returns:
        results: Dictionary with verification results
    """
    print(f"\n[VERIFY] Verifying environmental features: {h5_path}")
    
    if not os.path.exists(h5_path):
        return {
            'valid': False,
            'error': 'HDF5 file not found'
        }
    
    results = {
        'valid': True,
        'num_samples': 0,
        'expected_shape': (12,),
        'shape_matches': 0,
        'has_nan': 0,
        'has_inf': 0,
        'value_range': None,
        'feature_ranges': {},
        'errors': []
    }
    
    feature_names = [
        'rt60', 'drr', 'snr', 'background_level', 'silence_ratio',
        'spectral_tilt', 'spectral_flatness', 'spectral_rolloff',
        'cleanliness_score', 'high_freq_content', 'background_consistency',
        'env_stability'
    ]
    
    try:
        with h5py.File(h5_path, 'r') as h5f:
            features = h5f['features']
            results['num_samples'] = features.shape[0]
            
            print(f"[INFO] Found {results['num_samples']} environmental features")
            print(f"[INFO] Expected shape: {results['expected_shape']}")
            print(f"[INFO] Actual shape: {features.shape}")
            
            # Verify shape
            if features.shape[1:] == results['expected_shape']:
                results['shape_matches'] = results['num_samples']
            else:
                results['valid'] = False
                results['errors'].append(f"Shape mismatch: {features.shape[1:]} != {results['expected_shape']}")
            
            # Vectorized check for NaN/Inf (much faster than checking one by one)
            print(f"[INFO] Checking all {results['num_samples']} samples for NaN/Inf (vectorized)...")
            
            # Load data in chunks to avoid memory issues
            chunk_size = 10000
            nan_indices = []
            inf_indices = []
            
            for chunk_start in tqdm(range(0, results['num_samples'], chunk_size), desc="Checking samples"):
                chunk_end = min(chunk_start + chunk_size, results['num_samples'])
                chunk_data = features[chunk_start:chunk_end]
                
                # Vectorized NaN/Inf check
                nan_mask = np.any(np.isnan(chunk_data), axis=1)
                inf_mask = np.any(np.isinf(chunk_data), axis=1)
                
                # Collect indices with issues
                chunk_nan_indices = np.where(nan_mask)[0] + chunk_start
                chunk_inf_indices = np.where(inf_mask)[0] + chunk_start
                
                nan_indices.extend(chunk_nan_indices.tolist())
                inf_indices.extend(chunk_inf_indices.tolist())
            
            results['has_nan'] = len(nan_indices)
            results['has_inf'] = len(inf_indices)
            
            if results['has_nan'] > 0:
                results['valid'] = False
                for idx in nan_indices[:10]:  # Report first 10
                    results['errors'].append(f"Sample {idx} contains NaN")
                if len(nan_indices) > 10:
                    results['errors'].append(f"... and {len(nan_indices) - 10} more samples with NaN")
            
            if results['has_inf'] > 0:
                results['valid'] = False
                for idx in inf_indices[:10]:  # Report first 10
                    results['errors'].append(f"Sample {idx} contains Inf")
                if len(inf_indices) > 10:
                    results['errors'].append(f"... and {len(inf_indices) - 10} more samples with Inf")
            
            # Compute value ranges per feature (use larger sample for better statistics)
            sample_size = min(50000, results['num_samples'])  # Increased from 10000
            sample_data = features[:sample_size]
            results['value_range'] = {
                'min': float(np.min(sample_data)),
                'max': float(np.max(sample_data)),
                'mean': float(np.mean(sample_data)),
                'std': float(np.std(sample_data))
            }
            
            # Per-feature ranges
            for i, name in enumerate(feature_names):
                feature_data = sample_data[:, i]
                results['feature_ranges'][name] = {
                    'min': float(np.min(feature_data)),
                    'max': float(np.max(feature_data)),
                    'mean': float(np.mean(feature_data)),
                    'std': float(np.std(feature_data))
                }
            
            print(f"[INFO] Overall value range: [{results['value_range']['min']:.2f}, {results['value_range']['max']:.2f}]")
            print(f"[INFO] Mean: {results['value_range']['mean']:.2f}, Std: {results['value_range']['std']:.2f}")
            
    except Exception as e:
        results['valid'] = False
        results['error'] = str(e)
        results['errors'].append(f"Exception: {str(e)}")
    
    return results


def verify_manifest(manifest_path, spectrogram_h5, environmental_h5):
    """
    Verify that manifest indices match HDF5 files.
    
    Args:
        manifest_path: Path to features manifest
        spectrogram_h5: Path to spectrogram HDF5
        environmental_h5: Path to environmental HDF5
    
    Returns:
        results: Dictionary with verification results
    """
    print(f"\n[VERIFY] Verifying manifest indices...")
    
    if not os.path.exists(manifest_path):
        return {
            'valid': False,
            'error': 'Manifest file not found'
        }
    
    df = pd.read_csv(manifest_path, low_memory=False)
    
    results = {
        'valid': True,
        'total_samples': len(df),
        'has_spectrogram_idx': 0,
        'has_environmental_idx': 0,
        'has_both': 0,
        'missing_spectrogram': 0,
        'missing_environmental': 0,
        'errors': []
    }
    
    # Check indices
    if 'spectrogram_idx' in df.columns:
        results['has_spectrogram_idx'] = (df['spectrogram_idx'] >= 0).sum()
        results['missing_spectrogram'] = (df['spectrogram_idx'] < 0).sum()
    else:
        results['valid'] = False
        results['errors'].append("Manifest missing 'spectrogram_idx' column")
    
    if 'environmental_idx' in df.columns:
        results['has_environmental_idx'] = (df['environmental_idx'] >= 0).sum()
        results['missing_environmental'] = (df['environmental_idx'] < 0).sum()
    else:
        results['valid'] = False
        results['errors'].append("Manifest missing 'environmental_idx' column")
    
    if 'spectrogram_idx' in df.columns and 'environmental_idx' in df.columns:
        results['has_both'] = ((df['spectrogram_idx'] >= 0) & (df['environmental_idx'] >= 0)).sum()
    
    # Verify indices are within HDF5 bounds
    if os.path.exists(spectrogram_h5):
        with h5py.File(spectrogram_h5, 'r') as h5f:
            max_spectrogram_idx = h5f['features'].shape[0] - 1
        
        invalid_spectrogram = df[df['spectrogram_idx'] > max_spectrogram_idx]
        if len(invalid_spectrogram) > 0:
            results['valid'] = False
            results['errors'].append(f"{len(invalid_spectrogram)} samples have invalid spectrogram indices")
    
    if os.path.exists(environmental_h5):
        with h5py.File(environmental_h5, 'r') as h5f:
            max_environmental_idx = h5f['features'].shape[0] - 1
        
        invalid_environmental = df[df['environmental_idx'] > max_environmental_idx]
        if len(invalid_environmental) > 0:
            results['valid'] = False
            results['errors'].append(f"{len(invalid_environmental)} samples have invalid environmental indices")
    
    print(f"[INFO] Total samples: {results['total_samples']}")
    print(f"[INFO] Samples with spectrogram: {results['has_spectrogram_idx']}")
    print(f"[INFO] Samples with environmental: {results['has_environmental_idx']}")
    print(f"[INFO] Samples with both: {results['has_both']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Verify extracted features")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\features\features_manifest_unified.csv',
        help='Path to features manifest CSV'
    )
    parser.add_argument(
        '--spectrogram_h5',
        type=str,
        default=r'E:\FYP\data\features\logmel_packed.h5',
        help='Path to spectrogram HDF5 file'
    )
    parser.add_argument(
        '--environmental_h5',
        type=str,
        default=r'E:\FYP\data\features\environmental_packed.h5',
        help='Path to environmental HDF5 file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=r'E:\FYP\data\features\verification_report.json',
        help='Output path for verification report'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("FEATURE VERIFICATION")
    print("="*80)
    
    # Load manifest if it exists
    manifest_df = None
    if os.path.exists(args.manifest):
        manifest_df = pd.read_csv(args.manifest, low_memory=False)
        print(f"[INFO] Loaded manifest with {len(manifest_df)} samples")
    else:
        print(f"[WARN] Manifest not found: {args.manifest}")
    
    # Verify spectrograms
    spectrogram_results = verify_spectrograms(args.spectrogram_h5, manifest_df)
    
    # Verify environmental features
    environmental_results = verify_environmental(args.environmental_h5, manifest_df)
    
    # Verify manifest
    manifest_results = verify_manifest(args.manifest, args.spectrogram_h5, args.environmental_h5)
    
    # Compile report
    report = {
        'spectrogram': spectrogram_results,
        'environmental': environmental_results,
        'manifest': manifest_results,
        'overall_valid': (
            spectrogram_results.get('valid', False) and
            environmental_results.get('valid', False) and
            manifest_results.get('valid', False)
        )
    }
    
    # Print summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    print(f"\nSpectrogram Features:")
    print(f"  Valid: {spectrogram_results.get('valid', False)}")
    if spectrogram_results.get('valid', False):
        print(f"  Samples: {spectrogram_results.get('num_samples', 0)}")
        print(f"  Shape matches: {spectrogram_results.get('shape_matches', 0)}")
        print(f"  NaN values: {spectrogram_results.get('has_nan', 0)}")
        print(f"  Inf values: {spectrogram_results.get('has_inf', 0)}")
    else:
        print(f"  Error: {spectrogram_results.get('error', 'Unknown error')}")
    
    print(f"\nEnvironmental Features:")
    print(f"  Valid: {environmental_results.get('valid', False)}")
    if environmental_results.get('valid', False):
        print(f"  Samples: {environmental_results.get('num_samples', 0)}")
        print(f"  Shape matches: {environmental_results.get('shape_matches', 0)}")
        print(f"  NaN values: {environmental_results.get('has_nan', 0)}")
        print(f"  Inf values: {environmental_results.get('has_inf', 0)}")
    else:
        print(f"  Error: {environmental_results.get('error', 'Unknown error')}")
    
    print(f"\nManifest:")
    print(f"  Valid: {manifest_results.get('valid', False)}")
    if manifest_results.get('valid', False):
        print(f"  Total samples: {manifest_results.get('total_samples', 0)}")
        print(f"  With spectrogram: {manifest_results.get('has_spectrogram_idx', 0)}")
        print(f"  With environmental: {manifest_results.get('has_environmental_idx', 0)}")
        print(f"  With both: {manifest_results.get('has_both', 0)}")
    else:
        print(f"  Errors: {manifest_results.get('errors', [])}")
    
    print(f"\nOverall: {'✓ VALID' if report['overall_valid'] else '✗ INVALID'}")
    
    # Save report (convert numpy types to native Python types for JSON)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    report_serializable = convert_to_native_types(report)
    with open(args.output, 'w') as f:
        json.dump(report_serializable, f, indent=2)
    print(f"\n[INFO] Verification report saved to: {args.output}")
    
    return 0 if report['overall_valid'] else 1


if __name__ == "__main__":
    sys.exit(main())

