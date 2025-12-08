"""
Create Real-World Data Manifest for Phase 0

Scans processed audio directory and creates a manifest CSV with all required metadata.

Usage:
    python create_realworld_manifest.py --data_dir data/realworld/processed --output data/realworld/manifest_realworld.csv
"""

import argparse
import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import librosa
import json


def infer_domain_from_path(filepath):
    """Infer domain from file path."""
    path_lower = str(filepath).lower()
    
    if "broadcast" in path_lower or "news" in path_lower or "tv" in path_lower:
        return "broadcast"
    elif "podcast" in path_lower:
        return "podcast"
    elif "phone" in path_lower or "call" in path_lower:
        return "phone"
    elif "social" in path_lower or "tiktok" in path_lower:
        return "social"
    elif "studio" in path_lower or "vctk" in path_lower:
        return "studio"
    elif "librispeech" in path_lower or "read" in path_lower:
        return "read_speech"  # LibriSpeech is read speech
    elif "voxceleb" in path_lower:
        return "broadcast"  # VoxCeleb is from YouTube interviews
    else:
        return "unknown"


def infer_dataset_from_path(filepath):
    """Infer dataset source from file path."""
    path_lower = str(filepath).lower()
    
    if "librispeech" in path_lower:
        return "librispeech"
    elif "vctk" in path_lower:
        return "vctk"
    elif "voxceleb" in path_lower or "voxceleb1" in path_lower:
        return "voxceleb1"
    elif "youtube" in path_lower:
        return "youtube"
    elif "synthetic" in path_lower or "tts" in path_lower or "fake" in path_lower:
        return "synthetic"
    elif "manual" in path_lower:
        return "manual"
    else:
        return "unknown"


def infer_label_from_path(filepath):
    """Infer label (bonafide/spoof) from file path."""
    path_lower = str(filepath).lower()
    
    if "fake" in path_lower or "spoof" in path_lower or "synthetic" in path_lower or "tts" in path_lower:
        return "spoof"
    else:
        return "bonafide"


def infer_attack_type(filepath, label):
    """Infer attack type for spoof audio."""
    if label == "bonafide":
        return "bonafide"
    
    path_lower = str(filepath).lower()
    
    if "replay" in path_lower:
        return "replay"
    elif "tts" in path_lower or "synthesis" in path_lower:
        return "synthesis"
    elif "conversion" in path_lower:
        return "conversion"
    else:
        return "synthesis"  # Default for synthetic


def extract_speaker_id(filepath):
    """Extract speaker ID from filename if possible."""
    # Common patterns: speaker_001, spk_123, etc.
    filename = Path(filepath).stem
    parts = filename.split("_")
    
    for part in parts:
        if part.startswith("spk") or part.startswith("speaker"):
            return part
        if part.isdigit() and len(part) >= 3:
            return f"spk_{part}"
    
    # Use filename hash as fallback
    import hashlib
    return f"spk_{hashlib.md5(filename.encode()).hexdigest()[:8]}"


def get_audio_duration(filepath):
    """Get audio duration in seconds."""
    try:
        y, sr = librosa.load(filepath, sr=None)
        return len(y) / sr
    except:
        return 0.0


def scan_directory(data_dir, recursive=True):
    """Scan directory for audio files and extract metadata."""
    data_path = Path(data_dir)
    
    # Find all WAV files
    if recursive:
        audio_files = list(data_path.rglob("*.wav"))
    else:
        audio_files = list(data_path.glob("*.wav"))
    
    print(f"[INFO] Found {len(audio_files)} audio files")
    
    manifest_data = []
    
    for audio_file in tqdm(audio_files, desc="Creating manifest"):
        # Get relative path
        rel_path = audio_file.relative_to(data_path)
        
        # Infer metadata
        domain = infer_domain_from_path(rel_path)
        dataset = infer_dataset_from_path(rel_path)
        label = infer_label_from_path(rel_path)
        attack_type = infer_attack_type(rel_path, label)
        speaker_id = extract_speaker_id(rel_path)
        duration = get_audio_duration(str(audio_file))
        
        # Determine source
        if dataset == "synthetic":
            source = "synthetic"
        elif dataset in ["voxceleb", "commonvoice", "vctk"]:
            source = "public_dataset"
        elif dataset == "youtube":
            source = "youtube"
        elif dataset == "manual":
            source = "manual"
        else:
            source = "unknown"
        
        manifest_data.append({
            "filepath": str(audio_file),
            "label": label,
            "dataset": dataset,
            "domain": domain,
            "attack_type": attack_type,
            "speaker_id": speaker_id,
            "source": source,
            "duration": round(duration, 2)
        })
    
    return manifest_data


def main():
    parser = argparse.ArgumentParser("Create Real-World Data Manifest")
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Directory containing processed audio files")
    parser.add_argument("--output", type=str, required=True,
                       help="Output manifest CSV path")
    parser.add_argument("--recursive", action="store_true", default=True,
                       help="Scan subdirectories recursively")
    
    args = parser.parse_args()
    
    print(f"[INFO] Scanning directory: {args.data_dir}")
    
    # Scan and create manifest
    manifest_data = scan_directory(args.data_dir, recursive=args.recursive)
    
    if not manifest_data:
        print("[ERROR] No audio files found!")
        return
    
    # Create DataFrame
    df = pd.DataFrame(manifest_data)
    
    # Save manifest
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False)
    
    print(f"[OK] Manifest saved to: {args.output}")
    print(f"[OK] Total samples: {len(df)}")
    
    # Print statistics
    print("\n[STATISTICS]")
    print(f"  Total samples: {len(df)}")
    print(f"\n  Label distribution:")
    print(df['label'].value_counts())
    print(f"\n  Domain distribution:")
    print(df['domain'].value_counts())
    print(f"\n  Dataset distribution:")
    print(df['dataset'].value_counts())
    print(f"\n  Source distribution:")
    print(df['source'].value_counts())
    
    if 'attack_type' in df.columns:
        print(f"\n  Attack type distribution:")
        print(df['attack_type'].value_counts())
    
    print(f"\n  Duration statistics:")
    print(f"    Mean: {df['duration'].mean():.2f}s")
    print(f"    Min: {df['duration'].min():.2f}s")
    print(f"    Max: {df['duration'].max():.2f}s")


if __name__ == "__main__":
    main()

