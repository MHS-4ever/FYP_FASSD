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
    
    # VCTK structure: audio files are in wav48_silence_trimmed subdirectory
    # Check common VCTK subdirectories
    audio_dirs = [
        data_path / "wav48_silence_trimmed",  # Standard VCTK structure
        data_path / "wav48",                   # Alternative structure
        data_path                              # Root directory (fallback)
    ]
    
    # Find all audio files (WAV or FLAC)
    wav_files = []
    for audio_dir in audio_dirs:
        if audio_dir.exists():
            wav_files.extend(list(audio_dir.rglob("*.wav")))
            wav_files.extend(list(audio_dir.rglob("*.flac")))
            if wav_files:
                print(f"[INFO] Found audio files in: {audio_dir.relative_to(data_path) if audio_dir != data_path else 'root'}")
                break
    
    if not wav_files:
        # If still no files, try searching entire directory recursively
        wav_files = list(data_path.rglob("*.wav"))
        wav_files.extend(list(data_path.rglob("*.flac")))
        
        if not wav_files:
            print(f"[ERROR] No audio files found in {data_dir}")
            print(f"[INFO] Expected location: {data_path / 'wav48_silence_trimmed'}")
            print(f"[INFO] Please check:")
            print(f"  1. VCTK dataset is properly extracted")
            print(f"  2. Audio files are in 'wav48_silence_trimmed' subdirectory")
            print(f"  3. File format is .wav or .flac")
            return False
    
    print(f"[INFO] Found {len(wav_files)} audio files")
    
    # Count speakers (VCTK format: p225_001.wav or speaker_id/p225_001.wav)
    speakers = set()
    for wav_file in wav_files:
        filename = wav_file.stem
        # Extract speaker ID (e.g., p225 from p225_001.wav)
        if filename.startswith('p') and '_' in filename:
            speaker_id = filename.split('_')[0]
            speakers.add(speaker_id)
        # Alternative: check parent directory
        elif wav_file.parent.name.startswith('p'):
            speakers.add(wav_file.parent.name)
    
    print(f"[INFO] Found {len(speakers)} unique speakers")
    
    if len(speakers) > 0:
        # Show sample speaker IDs
        sample_speakers = sorted(list(speakers))[:10]
        print(f"[INFO] Sample speakers: {', '.join(sample_speakers)}")
    
    # Sample a few files to verify they're valid
    print("[INFO] Verifying sample files...")
    valid = 0
    invalid = 0
    
    sample_size = min(100, len(wav_files))
    if sample_size == 0:
        print("[WARN] No files to verify")
        return False
    
    for wav_file in tqdm(wav_files[:sample_size], desc="Verifying"):
        try:
            y, sr = librosa.load(str(wav_file), sr=None, duration=0.1)
            if len(y) > 0:
                valid += 1
            else:
                invalid += 1
        except Exception as e:
            invalid += 1
            if invalid == 1:  # Print first error as example
                print(f"\n[WARN] Sample error on {wav_file.name}: {str(e)}")
    
    print(f"[OK] Valid files: {valid}/{valid+invalid} (sample of {sample_size})")
    
    if valid == 0 and len(wav_files) > 0:
        print(f"[WARN] All sampled files failed verification. Check audio format/corruption.")
    
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

