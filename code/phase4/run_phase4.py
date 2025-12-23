"""
Phase 4 Orchestrator: Run all Phase 4 steps in sequence

This script runs Phase 4 training:
1. Train hybrid model on mixed data (50% ASVspoof + 50% Real-world)

Usage:
    python run_phase4.py [--skip-training]
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
    parser = argparse.ArgumentParser(description="Run all Phase 4 steps")
    parser.add_argument(
        '--skip-training',
        action='store_true',
        help='Skip training (for testing only)'
    )
    parser.add_argument(
        '--train-manifest',
        type=str,
        default='data/manifests/train_speaker_independent.csv',
        help='Path to training manifest (default: data/manifests/train_speaker_independent.csv)'
    )
    parser.add_argument(
        '--val-manifest',
        type=str,
        default='data/manifests/val_speaker_independent.csv',
        help='Path to validation manifest (default: data/manifests/val_speaker_independent.csv)'
    )
    parser.add_argument(
        '--spectrogram-h5',
        type=str,
        default='D:/FYP/data/features/logmel_packed.h5',
        help='Path to spectrogram HDF5 file (default: D:/FYP/data/features/logmel_packed.h5)'
    )
    parser.add_argument(
        '--environmental-h5',
        type=str,
        default='D:/FYP/data/features/environmental_packed.h5',
        help='Path to environmental HDF5 file (default: D:/FYP/data/features/environmental_packed.h5)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models_saved',
        help='Output directory for models and logs (default: models_saved)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=64,
        help='Batch size (default: 64, optimized for RTX 3050 6GB)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=20,
        help='Number of epochs (default: 20)'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("PHASE 4: HYBRID MODEL TRAINING")
    print("="*80)
    print()
    print("[INFO] This script will run Phase 4 training:")
    print("  1. Train hybrid model on mixed data (50% ASVspoof + 50% Real-world)")
    print()
    print("[INFO] Configuration:")
    print(f"  Train manifest: {args.train_manifest}")
    print(f"  Val manifest: {args.val_manifest}")
    print(f"  Spectrogram HDF5: {args.spectrogram_h5}")
    print(f"  Environmental HDF5: {args.environmental_h5}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Epochs: {args.epochs}")
    print()
    
    success = True
    
    # Step 1: Train hybrid model
    if not args.skip_training:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'train_hybrid_model.py'),
            '--train_manifest', args.train_manifest,
            '--val_manifest', args.val_manifest,
            '--spectrogram_h5', args.spectrogram_h5,
            '--environmental_h5', args.environmental_h5,
            '--output_dir', args.output_dir,
            '--batch_size', str(args.batch_size),
            '--epochs', str(args.epochs)
        ]
        
        if not run_command(cmd, "Train Hybrid Model"):
            print("\n[ERROR] Training failed. Please review and fix issues.")
            success = False
    else:
        print("\n[SKIP] Skipping training")
    
    # Final summary
    print("\n" + "="*80)
    if success:
        print("✓ PHASE 4 COMPLETED SUCCESSFULLY")
    else:
        print("⚠ PHASE 4 COMPLETED WITH ERRORS")
    print("="*80)
    print()
    
    if success:
        print("[INFO] Phase 4 outputs:")
        print(f"  - Trained model: {args.output_dir}/hybrid_resnet_environmental_best.pth")
        print(f"  - Training logs: {args.output_dir}/logs/training_hybrid_model.csv")
        print()
        print("[INFO] Next steps:")
        print("  - Phase 5: Evaluation (requires trained model from Phase 4)")
        print("  - Evaluate model on test set and generate reports")
    else:
        print("[WARNING] Some steps failed. Please review errors above.")
        print("  - Fix training issues before proceeding to Phase 5")
    
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

