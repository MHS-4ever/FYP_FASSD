"""
Phase 3 Orchestrator: Run all Phase 3 steps in sequence

This script runs all Phase 3 tasks:
1. Test hybrid architecture (forward pass, shapes, gradients, etc.)

Usage:
    python run_phase3.py [--skip-tests]
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
    parser = argparse.ArgumentParser(description="Run all Phase 3 steps")
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip architecture tests'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Only run tests (skip other steps)'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("PHASE 3: HYBRID MODEL ARCHITECTURE")
    print("="*80)
    print()
    print("[INFO] This script will run all Phase 3 steps:")
    print("  1. Test hybrid architecture (forward pass, shapes, gradients, etc.)")
    print()
    
    success = True
    
    # Step 1: Test architecture
    if not args.skip_tests or args.test_only:
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'test_hybrid_architecture.py')
        ]
        
        if not run_command(cmd, "Test Hybrid Architecture"):
            print("\n[ERROR] Architecture tests failed. Please review and fix issues.")
            success = False
    else:
        print("\n[SKIP] Skipping architecture tests")
    
    # Final summary
    print("\n" + "="*80)
    if success:
        print("✓ PHASE 3 COMPLETED SUCCESSFULLY")
    else:
        print("⚠ PHASE 3 COMPLETED WITH ERRORS")
    print("="*80)
    print()
    
    if success:
        print("[INFO] Phase 3 outputs:")
        print("  - Hybrid model architecture: code/phase3/hybrid_resnet_environmental.py")
        print("  - Multi-task loss: code/phase3/multi_task_loss.py")
        print("  - Test results: See output above")
        print()
        print("[INFO] Next steps:")
        print("  - Phase 4: Training (requires architecture from Phase 3)")
        print("  - Use the hybrid model for end-to-end training")
    else:
        print("[WARNING] Some steps failed. Please review errors above.")
        print("  - Fix architecture issues before proceeding to Phase 4")
    
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

