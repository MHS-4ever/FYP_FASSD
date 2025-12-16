"""
Download LibriSpeech Dataset Helper Script

LibriSpeech is downloaded manually, but this script helps organize and verify.

Usage:
    python download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech
"""

import argparse
import os
from pathlib import Path
from tqdm import tqdm
import librosa


def verify_librispeech(data_dir):
    """Verify LibriSpeech dataset structure and count files."""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"[ERROR] Directory does not exist: {data_dir}")
        return False
    
    # Find all WAV files
    wav_files = list(data_path.rglob("*.flac"))
    if not wav_files:
        wav_files = list(data_path.rglob("*.wav"))
    
    print(f"[INFO] Found {len(wav_files)} audio files")
    
    # Count speakers
    speakers = set()
    for wav_file in wav_files:
        # LibriSpeech structure: speaker_id/chapter_id/file.wav
        parts = wav_file.parts
        if len(parts) >= 2:
            speakers.add(parts[-3])  # speaker_id is usually 3 levels up
    
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
    """Print instructions for downloading LibriSpeech."""
    print("="*60)
    print("LIBRISPEECH DOWNLOAD INSTRUCTIONS")
    print("="*60)
    print("\n1. Visit: http://www.openslr.org/12/")
    print("\n2. Recommended downloads:")
    print("   - train-clean-100.tar.gz (6.3 GB, 251 speakers)")
    print("   - train-clean-360.tar.gz (30 GB, 921 speakers) - if you have space")
    print("   - dev-clean.tar.gz (337 MB, 40 speakers) - for validation")
    print("   - test-clean.tar.gz (346 MB, 40 speakers) - for testing")
    print("\n3. Download command (example):")
    print("   wget http://www.openslr.org/resources/12/train-clean-100.tar.gz")
    print("\n4. Extract:")
    print("   tar -xzf train-clean-100.tar.gz")
    print("\n5. Move to project directory:")
    print("   mv LibriSpeech data/realworld/public_datasets/librispeech/")
    print("\n6. Verify with this script:")
    print("   python download_librispeech.py --verify --data_dir data/realworld/public_datasets/librispeech")
    print("="*60)


def main():
    parser = argparse.ArgumentParser("LibriSpeech Dataset Helper")
    parser.add_argument("--verify", action="store_true",
                       help="Verify downloaded dataset")
    parser.add_argument("--data_dir", type=str,
                       default="data/realworld/public_datasets/librispeech",
                       help="LibriSpeech data directory")
    parser.add_argument("--instructions", action="store_true",
                       help="Print download instructions")
    
    args = parser.parse_args()
    
    if args.instructions:
        print_download_instructions()
        return
    
    if args.verify:
        verify_librispeech(args.data_dir)
    else:
        print("[INFO] Use --verify to verify dataset or --instructions for download help")
        print_download_instructions()


if __name__ == "__main__":
    main()

