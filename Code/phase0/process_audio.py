"""
Process Audio Files for Phase 0 Data Collection

Converts audio files to WAV format, resamples to 16kHz, and ensures quality.

Usage:
    python process_audio.py --input_dir data/realworld --output_dir data/realworld/processed
"""

import argparse
import os
from pathlib import Path
from tqdm import tqdm
import librosa
import soundfile as sf
import numpy as np


def process_audio_file(input_path, output_path, target_sr=16000, min_duration=1.0, max_duration=10.0):
    """
    Process a single audio file.
    
    Args:
        input_path: Input audio file path
        output_path: Output WAV file path
        target_sr: Target sample rate (default: 16000)
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds
    
    Returns:
        (success, duration, error_message)
    """
    try:
        # Load audio
        y, sr = librosa.load(input_path, sr=None, mono=True)
        duration = len(y) / sr
        
        # Check duration
        if duration < min_duration:
            return False, duration, f"Too short: {duration:.2f}s < {min_duration}s"
        
        # Truncate if too long
        if duration > max_duration:
            max_samples = int(max_duration * sr)
            y = y[:max_samples]
            duration = max_duration
        
        # Resample if needed
        if sr != target_sr:
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        
        # Normalize
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val * 0.95  # Prevent clipping
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as WAV
        sf.write(output_path, y, target_sr)
        
        return True, duration, None
        
    except Exception as e:
        return False, 0, str(e)


def process_directory(input_dir, output_dir, extensions=None, target_sr=16000, 
                     min_duration=1.0, max_duration=10.0, recursive=True):
    """
    Process all audio files in a directory.
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
        extensions: List of file extensions to process (default: ['.wav', '.mp3', '.flac', '.m4a'])
        target_sr: Target sample rate
        min_duration: Minimum duration
        max_duration: Maximum duration
        recursive: Process subdirectories recursively
    
    Returns:
        Dictionary with processing statistics
    """
    if extensions is None:
        extensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm']
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Find all audio files
    audio_files = []
    if recursive:
        for ext in extensions:
            audio_files.extend(input_path.rglob(f"*{ext}"))
    else:
        for ext in extensions:
            audio_files.extend(input_path.glob(f"*{ext}"))
    
    print(f"[INFO] Found {len(audio_files)} audio files to process")
    
    # Process files
    stats = {
        "total": len(audio_files),
        "success": 0,
        "failed": 0,
        "too_short": 0,
        "errors": []
    }
    
    for audio_file in tqdm(audio_files, desc="Processing audio"):
        # Create output path (preserve relative structure)
        rel_path = audio_file.relative_to(input_path)
        output_file = output_path / rel_path.with_suffix('.wav')
        
        # Process
        success, duration, error = process_audio_file(
            str(audio_file),
            str(output_file),
            target_sr=target_sr,
            min_duration=min_duration,
            max_duration=max_duration
        )
        
        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
            if "Too short" in str(error):
                stats["too_short"] += 1
            stats["errors"].append({
                "file": str(audio_file),
                "error": error
            })
    
    return stats


def main():
    parser = argparse.ArgumentParser("Process Audio Files for Phase 0")
    parser.add_argument("--input_dir", type=str, required=True,
                       help="Input directory containing audio files")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="Output directory for processed WAV files")
    parser.add_argument("--target_sr", type=int, default=16000,
                       help="Target sample rate (default: 16000)")
    parser.add_argument("--min_duration", type=float, default=1.0,
                       help="Minimum duration in seconds (default: 1.0)")
    parser.add_argument("--max_duration", type=float, default=10.0,
                       help="Maximum duration in seconds (default: 10.0)")
    parser.add_argument("--recursive", action="store_true", default=True,
                       help="Process subdirectories recursively")
    parser.add_argument("--extensions", type=str, nargs="+",
                       default=['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'],
                       help="File extensions to process")
    
    args = parser.parse_args()
    
    print(f"[INFO] Processing audio files")
    print(f"[INFO] Input: {args.input_dir}")
    print(f"[INFO] Output: {args.output_dir}")
    print(f"[INFO] Target sample rate: {args.target_sr} Hz")
    print(f"[INFO] Duration range: {args.min_duration}-{args.max_duration} seconds")
    
    # Process
    stats = process_directory(
        args.input_dir,
        args.output_dir,
        extensions=args.extensions,
        target_sr=args.target_sr,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        recursive=args.recursive
    )
    
    # Print statistics
    print("\n[RESULTS] Processing Statistics:")
    print(f"  Total files: {stats['total']}")
    print(f"  Success: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Too short: {stats['too_short']}")
    
    if stats['errors'] and len(stats['errors']) <= 10:
        print("\n[ERRORS] Sample errors:")
        for err in stats['errors'][:10]:
            print(f"  {err['file']}: {err['error']}")
    
    print(f"\n[OK] Processed audio saved to: {args.output_dir}")


if __name__ == "__main__":
    main()

