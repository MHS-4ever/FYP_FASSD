"""
Extract Environmental Features for Phase 2

Extracts 12 environmental acoustic features from all audio files in the unified manifest.
Features include:
1. RT60 (Reverberation Time)
2. DRR (Direct-to-Reverberant Ratio)
3. SNR (Signal-to-Noise Ratio)
4. Background Noise Level
5. Silence Ratio
6. Spectral Tilt
7. Spectral Flatness
8. Spectral Rolloff
9. Cleanliness Score
10. High-Frequency Content
11. Background Consistency
12. Environmental Stability

Features are saved as individual .npy files and can be packed into HDF5 later.

Usage:
    python extract_environmental_features.py --manifest data/manifests/unified_manifest.csv --output_dir data/features/environmental
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to import environmental features
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)

try:
    from features.environmental_features import EnvironmentalFeatureExtractor
except ImportError:
    # Try alternative path
    sys.path.insert(0, os.path.join(parent_dir, '..', 'code'))
    from features.environmental_features import EnvironmentalFeatureExtractor


def process_audio_file(audio_path, output_path):
    """
    Process a single audio file and extract environmental features.
    
    Args:
        audio_path: Path to audio file
        output_path: Path to save extracted features
    
    Returns:
        success: True if successful, False otherwise
        error_msg: Error message if failed
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_path):
            return False, f"File not found: {audio_path}"
        
        # Extract features
        extractor = EnvironmentalFeatureExtractor(sr=16000)
        feature_vector = extractor.extract_vector(audio_path)
        
        # Verify shape
        expected_shape = (12,)
        if feature_vector.shape != expected_shape:
            return False, f"Unexpected shape: {feature_vector.shape}, expected {expected_shape}"
        
        # Check for invalid values
        if np.any(np.isnan(feature_vector)) or np.any(np.isinf(feature_vector)):
            return False, "Feature vector contains NaN or Inf values"
        
        # Save as .npy
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.save(output_path, feature_vector)
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Extract environmental features")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=r'E:\FYP\data\features\environmental',
        help='Output directory for environmental features'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume extraction (skip existing files)'
    )
    parser.add_argument(
        '--max_samples',
        type=int,
        default=None,
        help='Maximum number of samples to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Load manifest
    print(f"[INFO] Loading manifest: {args.manifest}")
    if not os.path.exists(args.manifest):
        print(f"[ERROR] Manifest not found: {args.manifest}")
        return 1
    
    df = pd.read_csv(args.manifest, low_memory=False)
    print(f"[INFO] Loaded {len(df)} samples from manifest")
    
    # Limit samples if specified
    if args.max_samples:
        df = df.head(args.max_samples)
        print(f"[INFO] Processing first {len(df)} samples (test mode)")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each file
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    print(f"\n[INFO] Extracting environmental features...")
    print(f"[INFO] Output directory: {args.output_dir}")
    print(f"[INFO] Feature vector shape: [12]")
    print()
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting environmental features"):
        audio_path = row['filepath']
        
        # Generate output path using manifest index to ensure uniqueness
        # This prevents collisions if multiple files share the same basename
        audio_basename = os.path.basename(audio_path)
        audio_name = os.path.splitext(audio_basename)[0]
        # Use manifest index as prefix to ensure uniqueness
        output_path = os.path.join(args.output_dir, f"{idx:08d}_{audio_name}_env.npy")
        
        # Check if already exists
        if args.resume and os.path.exists(output_path):
            skipped_count += 1
            continue
        
        # Process file
        success, error_msg = process_audio_file(audio_path, output_path)
        
        if success:
            success_count += 1
        else:
            error_count += 1
            errors.append((audio_path, error_msg))
            if len(errors) <= 10:  # Keep first 10 errors for reporting
                tqdm.write(f"[ERROR] {audio_path}: {error_msg}")
    
    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total samples:     {len(df)}")
    print(f"Successful:        {success_count}")
    print(f"Errors:            {error_count}")
    print(f"Skipped (resume):  {skipped_count}")
    print()
    
    if errors:
        print(f"[WARN] {len(errors)} files failed to process")
        if len(errors) > 10:
            print(f"[INFO] Showing first 10 errors (total: {len(errors)})")
        print()
        for audio_path, error_msg in errors[:10]:
            print(f"  - {audio_path}: {error_msg}")
    
    # Save error log if there are errors
    if errors:
        error_log_path = os.path.join(args.output_dir, "extraction_errors.log")
        with open(error_log_path, 'w') as f:
            f.write("Environmental Feature Extraction Errors\n")
            f.write("="*80 + "\n\n")
            for audio_path, error_msg in errors:
                f.write(f"{audio_path}\n")
                f.write(f"  Error: {error_msg}\n\n")
        print(f"\n[INFO] Error log saved to: {error_log_path}")
    
    print(f"\n[INFO] Features saved to: {args.output_dir}")
    print(f"[INFO] Feature vector shape: [12]")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

