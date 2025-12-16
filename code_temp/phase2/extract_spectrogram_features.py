"""
Extract Log-Mel Spectrogram Features for Phase 2

Extracts log-mel spectrograms from all audio files in the unified manifest.
Features are extracted with the following parameters:
- Sample rate: 16,000 Hz
- Window size: 25ms (400 samples)
- Hop size: 10ms (160 samples)
- Mel bins: 64
- FFT size: 512
- Target length: 400 frames (~4 seconds)

Features are saved as individual .npy files and can be packed into HDF5 later.

Usage:
    python extract_spectrogram_features.py --manifest data/manifests/unified_manifest.csv --output_dir data/features/spectrograms
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import librosa
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
SAMPLE_RATE = 16000
N_FFT = 512
HOP_LENGTH = 160  # 10ms at 16kHz
WIN_LENGTH = 400  # 25ms at 16kHz
N_MELS = 64
TARGET_FRAMES = 400  # ~4 seconds at 10ms hop


def extract_logmel(y, sr, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH, win_length=WIN_LENGTH):
    """
    Extract log-mel spectrogram from audio signal.
    
    Args:
        y: Audio signal
        sr: Sample rate
        n_mels: Number of mel bins
        n_fft: FFT size
        hop_length: Hop size in samples
        win_length: Window size in samples
    
    Returns:
        log_mel: Log-mel spectrogram [n_mels, time_frames]
    """
    mel_spec = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        n_mels=n_mels,
        power=2.0
    )
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)
    return log_mel.astype(np.float32)


def pad_or_truncate(spectrogram, target_frames=TARGET_FRAMES):
    """
    Pad or truncate spectrogram to fixed length.
    
    Args:
        spectrogram: Spectrogram array [n_mels, time_frames]
        target_frames: Target number of time frames
    
    Returns:
        processed: Padded/truncated spectrogram [n_mels, target_frames]
    """
    n_mels, n_frames = spectrogram.shape
    
    if n_frames < target_frames:
        # Pad with zeros
        pad_width = target_frames - n_frames
        spectrogram = np.pad(spectrogram, ((0, 0), (0, pad_width)), mode='constant', constant_values=0)
    elif n_frames > target_frames:
        # Truncate
        spectrogram = spectrogram[:, :target_frames]
    
    return spectrogram


def process_audio_file(audio_path, output_path):
    """
    Process a single audio file and extract spectrogram features.
    
    Args:
        audio_path: Path to audio file
        output_path: Path to save extracted features
    
    Returns:
        success: True if successful, False otherwise
        error_msg: Error message if failed
    """
    try:
        # Load audio
        if not os.path.exists(audio_path):
            return False, f"File not found: {audio_path}"
        
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        
        if len(y) == 0:
            return False, "Empty audio file"
        
        # Extract log-mel spectrogram
        log_mel = extract_logmel(y, sr)
        
        # Pad or truncate to fixed length
        log_mel = pad_or_truncate(log_mel, TARGET_FRAMES)
        
        # Verify shape
        expected_shape = (N_MELS, TARGET_FRAMES)
        if log_mel.shape != expected_shape:
            return False, f"Unexpected shape: {log_mel.shape}, expected {expected_shape}"
        
        # Save as .npy
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.save(output_path, log_mel)
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Extract log-mel spectrogram features")
    parser.add_argument(
        '--manifest',
        type=str,
        default=r'E:\FYP\data\manifests\unified_manifest.csv',
        help='Path to unified manifest CSV'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=r'E:\FYP\data\features\spectrograms',
        help='Output directory for spectrogram features'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume extraction (skip existing files)'
    )
    parser.add_argument(
        '--max_samples',
        type=int,
        default=None,
        help='Maximum number of samples to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Load manifest
    print(f"[INFO] Loading manifest: {args.manifest}")
    if not os.path.exists(args.manifest):
        print(f"[ERROR] Manifest not found: {args.manifest}")
        return 1
    
    df = pd.read_csv(args.manifest, low_memory=False)
    print(f"[INFO] Loaded {len(df)} samples from manifest")
    
    # Limit samples if specified
    if args.max_samples:
        df = df.head(args.max_samples)
        print(f"[INFO] Processing first {len(df)} samples (test mode)")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each file
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    print(f"\n[INFO] Extracting spectrogram features...")
    print(f"[INFO] Output directory: {args.output_dir}")
    print(f"[INFO] Target shape: [{N_MELS}, {TARGET_FRAMES}]")
    print()
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting spectrograms"):
        audio_path = row['filepath']
        
        # Generate output path using manifest index to ensure uniqueness
        # This prevents collisions if multiple files share the same basename
        audio_basename = os.path.basename(audio_path)
        audio_name = os.path.splitext(audio_basename)[0]
        # Use manifest index as prefix to ensure uniqueness
        output_path = os.path.join(args.output_dir, f"{idx:08d}_{audio_name}_logmel.npy")
        
        # Check if already exists
        if args.resume and os.path.exists(output_path):
            skipped_count += 1
            continue
        
        # Process file
        success, error_msg = process_audio_file(audio_path, output_path)
        
        if success:
            success_count += 1
        else:
            error_count += 1
            errors.append((audio_path, error_msg))
            if len(errors) <= 10:  # Keep first 10 errors for reporting
                tqdm.write(f"[ERROR] {audio_path}: {error_msg}")
    
    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total samples:     {len(df)}")
    print(f"Successful:        {success_count}")
    print(f"Errors:            {error_count}")
    print(f"Skipped (resume):  {skipped_count}")
    print()
    
    if errors:
        print(f"[WARN] {len(errors)} files failed to process")
        if len(errors) > 10:
            print(f"[INFO] Showing first 10 errors (total: {len(errors)})")
        print()
        for audio_path, error_msg in errors[:10]:
            print(f"  - {audio_path}: {error_msg}")
    
    # Save error log if there are errors
    if errors:
        error_log_path = os.path.join(args.output_dir, "extraction_errors.log")
        with open(error_log_path, 'w') as f:
            f.write("Spectrogram Extraction Errors\n")
            f.write("="*80 + "\n\n")
            for audio_path, error_msg in errors:
                f.write(f"{audio_path}\n")
                f.write(f"  Error: {error_msg}\n\n")
        print(f"\n[INFO] Error log saved to: {error_log_path}")
    
    print(f"\n[INFO] Features saved to: {args.output_dir}")
    print(f"[INFO] Expected shape: [{N_MELS}, {TARGET_FRAMES}]")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

