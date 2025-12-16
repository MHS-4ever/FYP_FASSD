"""
Phase 2 Orchestrator: Run all Phase 2 steps in sequence

This script runs all Phase 2 tasks in the correct order:
1. Extract spectrogram features (log-mel spectrograms)
2. Extract environmental features
3. Pack features to HDF5
4. Verify features

Usage:
    python run_phase2.py [--skip-steps STEP1,STEP2]
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# Add current directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def run_command(cmd, description):
    """Run a command and handle errors."""
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print("="*80)
    print(f"[INFO] Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {description} failed: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run all Phase 2 steps")
    parser.add_argument(
        '--skip-steps',
        type=str,
        default='',
        help='Comma-separated list of steps to skip (extract_spectrograms,extract_environmental,pack,verify)'
    )
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--spectrogram_dir',
        type=str,
        default=r'E:\FYP\data\features\spectrograms',
        help='Output directory for spectrogram features'
    )
    parser.add_argument(
        '--environmental_dir',
        type=str,
        default=r'E:\FYP\data\features\environmental',
        help='Output directory for environmental features'
    )
    parser.add_argument(
        '--features_dir',
        type=str,
        default=r'E:\FYP\data\features',
        help='Output directory for packed HDF5 files'
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
    
    # Parse skip steps
    skip_steps = [s.strip().lower() for s in args.skip_steps.split(',') if s.strip()]
    
    print("="*80)
    print("PHASE 2: FEATURE EXTRACTION")
    print("="*80)
    print()
    print("[INFO] This script will run all Phase 2 steps:")
    print("  1. Extract spectrogram features (log-mel spectrograms)")
    print("  2. Extract environmental features")
    print("  3. Pack features to HDF5")
    print("  4. Verify features")
    print()
    
    if skip_steps:
        print(f"[INFO] Skipping steps: {', '.join(skip_steps)}")
    print()
    
    success = True
    
    # Step 1: Extract spectrogram features
    if 'extract_spectrograms' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'extract_spectrogram_features.py'),
            '--manifest', args.manifest,
            '--output_dir', args.spectrogram_dir
        ]
        if args.resume:
            cmd.append('--resume')
        if args.max_samples:
            cmd.extend(['--max_samples', str(args.max_samples)])
        
        if not run_command(cmd, "Extract Spectrogram Features"):
            print("\n[ERROR] Failed to extract spectrogram features. Cannot continue.")
            return 1
    else:
        print("\n[SKIP] Skipping spectrogram extraction")
    
    # Step 2: Extract environmental features
    if 'extract_environmental' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'extract_environmental_features.py'),
            '--manifest', args.manifest,
            '--output_dir', args.environmental_dir
        ]
        if args.resume:
            cmd.append('--resume')
        if args.max_samples:
            cmd.extend(['--max_samples', str(args.max_samples)])
        
        if not run_command(cmd, "Extract Environmental Features"):
            print("\n[ERROR] Failed to extract environmental features. Cannot continue.")
            return 1
    else:
        print("\n[SKIP] Skipping environmental feature extraction")
    
    # Step 3: Pack features to HDF5
    if 'pack' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'pack_features_to_hdf5.py'),
            '--manifest', args.manifest,
            '--spectrogram_dir', args.spectrogram_dir,
            '--environmental_dir', args.environmental_dir,
            '--output_dir', args.features_dir
        ]
        
        if not run_command(cmd, "Pack Features to HDF5"):
            print("\n[WARNING] Failed to pack features. Continuing with verification...")
            success = False
    else:
        print("\n[SKIP] Skipping feature packing")
    
    # Step 4: Verify features
    if 'verify' not in skip_steps:
        features_manifest = os.path.join(args.features_dir, 'features_manifest_unified.csv')
        spectrogram_h5 = os.path.join(args.features_dir, 'logmel_packed.h5')
        environmental_h5 = os.path.join(args.features_dir, 'environmental_packed.h5')
        
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'verify_features.py'),
            '--manifest', features_manifest,
            '--spectrogram_h5', spectrogram_h5,
            '--environmental_h5', environmental_h5
        ]
        
        if not run_command(cmd, "Verify Features"):
            print("\n[WARNING] Feature verification failed")
            success = False
    else:
        print("\n[SKIP] Skipping feature verification")
    
    # Final summary
    print("\n" + "="*80)
    if success:
        print("✓ PHASE 2 COMPLETED SUCCESSFULLY")
    else:
        print("⚠ PHASE 2 COMPLETED WITH WARNINGS")
    print("="*80)
    print()
    print("[INFO] Output files:")
    print(f"  - Spectrogram features: {args.spectrogram_dir}")
    print(f"  - Environmental features: {args.environmental_dir}")
    print(f"  - Packed HDF5 files: {args.features_dir}")
    print(f"    - logmel_packed.h5")
    print(f"    - environmental_packed.h5")
    print(f"    - features_manifest_unified.csv")
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

