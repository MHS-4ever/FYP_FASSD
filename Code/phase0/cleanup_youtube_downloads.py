"""
Cleanup script for YouTube downloads.

Removes original downloaded WAV files after they've been processed into clips,
and removes incomplete download files (.part files).

Usage:
    python cleanup_youtube_downloads.py --data_dir data/realworld/youtube/broadcast/broadcast
"""

import argparse
import os
from pathlib import Path


def cleanup_downloads(data_dir):
    """Remove original WAV files and incomplete downloads, keeping only clips."""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"[ERROR] Directory does not exist: {data_dir}")
        return
    
    clips_dir = data_path / "clips"
    if not clips_dir.exists():
        print(f"[WARN] Clips directory not found: {clips_dir}")
        return
    
    # Count clips
    num_clips = len(list(clips_dir.glob("*.wav")))
    print(f"[INFO] Found {num_clips} clips in {clips_dir}")
    
    # Find original WAV files (not in clips directory)
    wav_files = [f for f in data_path.glob("*.wav") if f.parent == data_path]
    part_files = list(data_path.glob("*.part"))
    
    print(f"[INFO] Found {len(wav_files)} original WAV files to remove")
    print(f"[INFO] Found {len(part_files)} incomplete download files (.part) to remove")
    
    if not wav_files and not part_files:
        print("[OK] No files to clean up")
        return
    
    # Ask for confirmation
    total_size = sum(f.stat().st_size for f in wav_files + part_files)
    total_size_gb = total_size / (1024**3)
    
    print(f"[INFO] Total size to free: {total_size_gb:.2f} GB")
    print("[INFO] This will remove original WAV files and incomplete downloads")
    print("[INFO] Clips will be preserved")
    
    # Remove WAV files
    removed_wav = 0
    for wav_file in wav_files:
        try:
            wav_file.unlink()
            removed_wav += 1
        except Exception as e:
            print(f"[WARN] Failed to remove {wav_file.name}: {e}")
    
    # Remove .part files
    removed_part = 0
    for part_file in part_files:
        try:
            part_file.unlink()
            removed_part += 1
        except Exception as e:
            print(f"[WARN] Failed to remove {part_file.name}: {e}")
    
    print(f"[OK] Cleanup complete:")
    print(f"  - Removed {removed_wav} WAV files")
    print(f"  - Removed {removed_part} incomplete download files")
    print(f"  - Kept {num_clips} clips in {clips_dir}")


def main():
    parser = argparse.ArgumentParser("Cleanup YouTube Downloads")
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Directory containing downloaded files and clips subdirectory")
    
    args = parser.parse_args()
    cleanup_downloads(args.data_dir)


if __name__ == "__main__":
    main()

