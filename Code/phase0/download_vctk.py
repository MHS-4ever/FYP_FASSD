"""
Download VCTK Dataset Helper Script

VCTK is downloaded manually, but this script helps organize and verify.

Usage:
    python download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk
"""

import argparse
import os
from pathlib import Path
from tqdm import tqdm
import librosa


def verify_vctk(data_dir):
    """Verify VCTK dataset structure and count files."""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"[ERROR] Directory does not exist: {data_dir}")
        return False
    
    # Find all WAV files
    wav_files = list(data_path.rglob("*.wav"))
    
    print(f"[INFO] Found {len(wav_files)} audio files")
    
    # Count speakers (VCTK format: p225_001.wav)
    speakers = set()
    for wav_file in wav_files:
        filename = wav_file.stem
        # Extract speaker ID (e.g., p225 from p225_001.wav)
        if filename.startswith('p'):
            speaker_id = filename.split('_')[0]
            speakers.add(speaker_id)
    
    print(f"[INFO] Found {len(speakers)} unique speakers")
    
    # Sample a few files to verify they're valid
    print("[INFO] Verifying sample files...")
    valid = 0
    invalid = 0
    
    for wav_file in tqdm(wav_files[:100], desc="Verifying"):  # Check first 100
        try:
            y, sr = librosa.load(str(wav_file), sr=None, duration=0.1)
            if len(y) > 0:
                valid += 1
            else:
                invalid += 1
        except:
            invalid += 1
    
    print(f"[OK] Valid files: {valid}/{valid+invalid} (sample)")
    
    return True


def print_download_instructions():
    """Print instructions for downloading VCTK."""
    print("="*60)
    print("VCTK CORPUS DOWNLOAD INSTRUCTIONS")
    print("="*60)
    print("\n1. Visit: https://datashare.ed.ac.uk/handle/10283/3443")
    print("\n2. Click 'Download' button")
    print("   - Dataset size: ~10 GB")
    print("   - Speakers: 110 (English, various accents)")
    print("   - Format: WAV files")
    print("\n3. Extract the downloaded archive")
    print("\n4. Move to project directory:")
    print("   mv VCTK-Corpus data/realworld/public_datasets/vctk/")
    print("\n5. Verify with this script:")
    print("   python download_vctk.py --verify --data_dir data/realworld/public_datasets/vctk")
    print("\nNote: VCTK requires manual download (no direct wget link)")
    print("="*60)


def main():
    parser = argparse.ArgumentParser("VCTK Dataset Helper")
    parser.add_argument("--verify", action="store_true",
                       help="Verify downloaded dataset")
    parser.add_argument("--data_dir", type=str,
                       default="data/realworld/public_datasets/vctk",
                       help="VCTK data directory")
    parser.add_argument("--instructions", action="store_true",
                       help="Print download instructions")
    
    args = parser.parse_args()
    
    if args.instructions:
        print_download_instructions()
        return
    
    if args.verify:
        verify_vctk(args.data_dir)
    else:
        print("[INFO] Use --verify to verify dataset or --instructions for download help")
        print_download_instructions()


if __name__ == "__main__":
    main()

