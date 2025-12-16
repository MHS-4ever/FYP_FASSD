"""
Phase 1 Orchestrator: Run all Phase 1 steps in sequence

This script runs all Phase 1 tasks in the correct order:
1. Create unified manifest (ASVspoof + Real-world)
2. Create speaker-independent splits
3. Analyze dataset statistics

Usage:
    python run_phase1.py [--skip-steps STEP1,STEP2]
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
    parser = argparse.ArgumentParser(description="Run all Phase 1 steps")
    parser.add_argument(
        '--skip-steps',
        type=str,
        default='',
        help='Comma-separated list of steps to skip (create_manifest,create_splits,analyze)'
    )
    parser.add_argument(
        '--asvspoof_manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_asvspoof_manifest.csv',
        help='Path to ASVspoof manifest (or will create if not exists)'
    )
    parser.add_argument(
        '--realworld_manifest',
        type=str,
        default=r'E:\FYP\data\realworld\manifest_realworld.csv',
        help='Path to Real-world manifest'
    )
    parser.add_argument(
        '--unified_manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Output path for unified manifest'
    )
    parser.add_argument(
        '--split_dir',
        type=str,
        default=r'E:\FYP\data\manifests',
        help='Directory for split manifests'
    )
    parser.add_argument(
        '--stats_output',
        type=str,
        default=r'E:\FYP\data\statistics\unified_dataset_stats.json',
        help='Output path for statistics JSON'
    )
    parser.add_argument(
        '--asvspoof_base_dir',
        type=str,
        default=r'E:\FYP\DataSet\English',
        help='Base directory for ASVspoof datasets (if creating manifest)'
    )
    parser.add_argument(
        '--train_ratio',
        type=float,
        default=0.8,
        help='Training split ratio (default: 0.8)'
    )
    parser.add_argument(
        '--val_ratio',
        type=float,
        default=0.1,
        help='Validation split ratio (default: 0.1)'
    )
    parser.add_argument(
        '--test_ratio',
        type=float,
        default=0.1,
        help='Test split ratio (default: 0.1)'
    )
    parser.add_argument(
        '--random_seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Parse skip steps
    skip_steps = [s.strip().lower() for s in args.skip_steps.split(',') if s.strip()]
    
    print("="*80)
    print("PHASE 1: UNIFIED DATASET PREPARATION")
    print("="*80)
    print()
    print("[INFO] This script will run all Phase 1 steps:")
    print("  1. Create unified manifest (ASVspoof LA/DF/PA + Real-world)")
    print("  2. Create speaker-independent splits")
    print("  3. Analyze dataset statistics")
    print()
    print("[NOTE] ASVspoof_PA is NEWLY ADDED (was not used in previous pipeline)")
    print("       Previous pipeline only used ASVspoof_LA and ASVspoof_DF.")
    print()
    
    if skip_steps:
        print(f"[INFO] Skipping steps: {', '.join(skip_steps)}")
    print()
    
    # Step 1: Create unified manifest
    success = True
    
    if 'create_manifest' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'create_unified_manifest.py'),
            '--asvspoof_manifest', args.asvspoof_manifest,
            '--realworld_manifest', args.realworld_manifest,
            '--output', args.unified_manifest,
            '--asvspoof_base_dir', args.asvspoof_base_dir
        ]
        
        if not run_command(cmd, "Create Unified Manifest"):
            print("\n[ERROR] Failed to create unified manifest. Cannot continue.")
            return 1
    else:
        print("\n[SKIP] Skipping unified manifest creation")
    
    # Step 2: Create speaker-independent splits
    if 'create_splits' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'create_speaker_independent_split.py'),
            '--manifest', args.unified_manifest,
            '--output_dir', args.split_dir,
            '--train_ratio', str(args.train_ratio),
            '--val_ratio', str(args.val_ratio),
            '--test_ratio', str(args.test_ratio),
            '--random_seed', str(args.random_seed)
        ]
        
        if not run_command(cmd, "Create Speaker-Independent Splits"):
            print("\n[WARNING] Failed to create splits. Continuing with statistics...")
            success = False
    else:
        print("\n[SKIP] Skipping split creation")
    
    # Step 3: Analyze statistics
    if 'analyze' not in skip_steps:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'analyze_unified_dataset.py'),
            '--manifest', args.unified_manifest,
            '--split_dir', args.split_dir,
            '--output', args.stats_output
        ]
        
        if not run_command(cmd, "Analyze Dataset Statistics"):
            print("\n[WARNING] Failed to analyze statistics")
            success = False
    else:
        print("\n[SKIP] Skipping statistics analysis")
    
    # Final summary
    print("\n" + "="*80)
    if success:
        print("✓ PHASE 1 COMPLETED SUCCESSFULLY")
    else:
        print("⚠ PHASE 1 COMPLETED WITH WARNINGS")
    print("="*80)
    print()
    print("[INFO] Output files:")
    print(f"  - Unified manifest: {args.unified_manifest}")
    print(f"  - Train split: {os.path.join(args.split_dir, 'train_speaker_independent.csv')}")
    print(f"  - Val split: {os.path.join(args.split_dir, 'val_speaker_independent.csv')}")
    print(f"  - Test split: {os.path.join(args.split_dir, 'test_speaker_independent.csv')}")
    print(f"  - Statistics: {args.stats_output}")
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
