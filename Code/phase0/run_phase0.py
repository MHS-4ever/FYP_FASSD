"""
Master Script for Phase 0 Data Collection

Orchestrates all Phase 0 data collection steps.

Usage:
    python run_phase0.py --all                    # Run all steps
    python run_phase0.py --youtube --fake        # Run specific steps
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"[STEP] {description}")
    print(f"{'='*60}")
    print(f"[CMD] {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] Command not found. Make sure scripts are in Code/phase0/")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("[INFO] Checking dependencies...")
    
    required = ['yt-dlp', 'librosa', 'soundfile', 'pandas', 'numpy']
    missing = []
    
    for dep in required:
        try:
            if dep == 'yt-dlp':
                __import__('yt_dlp')
            elif dep == 'soundfile':
                __import__('soundfile')
            else:
                __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} (MISSING)")
            missing.append(dep)
    
    if missing:
        print(f"\n[WARN] Missing dependencies: {', '.join(missing)}")
        print(f"[INFO] Install with: pip install {' '.join(missing)}")
        return False
    
    print("[OK] All dependencies installed")
    return True


def main():
    parser = argparse.ArgumentParser("Phase 0 Data Collection Master Script")
    parser.add_argument("--all", action="store_true",
                       help="Run all automated steps")
    parser.add_argument("--youtube", action="store_true",
                       help="Download YouTube audio")
    parser.add_argument("--fake", action="store_true",
                       help="Generate fake audio")
    parser.add_argument("--process", action="store_true",
                       help="Process audio files")
    parser.add_argument("--manifest", action="store_true",
                       help="Create manifest")
    parser.add_argument("--verify", action="store_true",
                       help="Verify data quality")
    parser.add_argument("--youtube_max", type=int, default=300,
                       help="Max YouTube videos per domain")
    parser.add_argument("--fake_num", type=int, default=3000,
                       help="Number of fake clips to generate")
    parser.add_argument("--data_dir", type=str, default="data/realworld",
                       help="Base data directory")
    
    args = parser.parse_args()
    
    # If --all, set all flags
    if args.all:
        args.youtube = True
        args.fake = True
        args.process = True
        args.manifest = True
        args.verify = True
    
    # Check if any step is requested
    if not any([args.youtube, args.fake, args.process, args.manifest, args.verify]):
        print("[ERROR] No steps specified. Use --all or specify individual steps.")
        parser.print_help()
        return
    
    print("="*60)
    print("PHASE 0: REAL-WORLD DATA COLLECTION")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n[WARN] Some dependencies missing. Continue anyway? (y/n)")
        response = input().strip().lower()
        if response != 'y':
            print("[INFO] Exiting. Install dependencies and try again.")
            return
    
    # Get script directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent  # Go up to FYP root
    
    success = True
    
    # Step 1: Download YouTube audio
    if args.youtube:
        for domain in ["broadcast", "podcast", "social"]:
            cmd = [
                sys.executable,
                str(script_dir / "download_youtube.py"),
                "--domain", domain,
                "--max_videos", str(args.youtube_max),
                "--output_dir", str(base_dir / args.data_dir / "youtube")
            ]
            if not run_command(cmd, f"Download YouTube {domain} audio"):
                success = False
    
    # Step 2: Generate fake audio
    if args.fake:
        cmd = [
            sys.executable,
            str(script_dir / "generate_fake_audio.py"),
            "--num_clips", str(args.fake_num),
            "--output_dir", str(base_dir / args.data_dir / "synthetic")
        ]
        if not run_command(cmd, "Generate fake audio"):
            success = False
    
    # Step 3: Process audio
    if args.process:
        cmd = [
            sys.executable,
            str(script_dir / "process_audio.py"),
            "--input_dir", str(base_dir / args.data_dir),
            "--output_dir", str(base_dir / args.data_dir / "processed")
        ]
        if not run_command(cmd, "Process audio files"):
            success = False
    
    # Step 4: Create manifest
    if args.manifest:
        cmd = [
            sys.executable,
            str(script_dir / "create_realworld_manifest.py"),
            "--data_dir", str(base_dir / args.data_dir / "processed"),
            "--output", str(base_dir / args.data_dir / "manifest_realworld.csv")
        ]
        if not run_command(cmd, "Create manifest"):
            success = False
    
    # Step 5: Verify quality
    if args.verify:
        cmd = [
            sys.executable,
            str(script_dir / "verify_realworld_data.py"),
            "--manifest", str(base_dir / args.data_dir / "manifest_realworld.csv"),
            "--output", str(base_dir / args.data_dir / "quality_report.json")
        ]
        if not run_command(cmd, "Verify data quality"):
            success = False
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("[SUCCESS] Phase 0 data collection completed!")
        print(f"[INFO] Check output in: {base_dir / args.data_dir}")
        print(f"[INFO] Manifest: {base_dir / args.data_dir / 'manifest_realworld.csv'}")
    else:
        print("[WARNING] Some steps failed. Check errors above.")
    print("="*60)


if __name__ == "__main__":
    main()

