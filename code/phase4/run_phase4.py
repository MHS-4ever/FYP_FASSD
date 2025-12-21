"""
Phase 4 Orchestrator: Run all Phase 4 training steps

This script orchestrates the Phase 4 training process:
1. Train hybrid model on speaker-independent splits

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
        help='Skip model training (if already trained)'
    )
    parser.add_argument(
        '--train-only',
        action='store_true',
        help='Only run training (skip other steps)'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("PHASE 4: HYBRID MODEL TRAINING")
    print("="*80)
    print()
    print("[INFO] This script will run all Phase 4 steps:")
    print("  1. Train hybrid model on speaker-independent splits")
    print()
    
    success = True
    
    # Step 1: Train hybrid model
    if not args.skip_training:
        # Run training unless explicitly skipped
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'train_hybrid_model.py')
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
        print("  - Trained hybrid model: models_saved/hybrid_resnet_environmental.pth")
        print("  - Training logs: reports/logs/training_hybrid_model.csv")
        print("  - Learning curves: reports/figures/learning_curves_hybrid.png")
        print()
        print("[INFO] Next steps:")
        print("  - Phase 5: Evaluation (evaluate trained model on test set)")
        print("  - Analyze training results and adjust hyperparameters if needed")
    else:
        print("[WARNING] Some steps failed. Please review errors above.")
        print("  - Fix training issues before proceeding to Phase 5")
    
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

