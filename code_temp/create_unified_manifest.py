"""
Create unified manifest combining all three ASVspoof datasets (LA, DF, PA).

This script:
1. Reads trial metadata from all three datasets
2. Extracts labels (bonafide/spoof) and speaker IDs
3. Maps file IDs to actual audio file paths
4. Creates a unified manifest with dataset labels (LA/DF/PA) and attack types
"""

import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# Configuration
BASE_DIR = r"E:\FYP\DataSet\English"
KEYS_DIR = os.path.join(BASE_DIR, "keys")
OUTPUT_DIR = r"E:\FYP\data\manifests"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "unified_asvspoof_manifest.csv")

# Dataset directories
LA_CLIPS_DIR = os.path.join(BASE_DIR, "ASVspoof2021_LA_eval", "LA_clips")
DF_CLIPS_DIR = os.path.join(BASE_DIR, "ASVspoof2021_DF_eval", "DF_clips")
PA_CLIPS_DIR = os.path.join(BASE_DIR, "ASVspoof2021_PA_eval", "PA_clips")

# Trial metadata files
LA_METADATA = os.path.join(KEYS_DIR, "LA", "CM", "trial_metadata.txt")
DF_METADATA = os.path.join(KEYS_DIR, "DF", "CM", "trial_metadata.txt")
PA_METADATA = os.path.join(KEYS_DIR, "PA", "CM", "trial_metadata.txt")


def parse_la_metadata(metadata_path, clips_dir):
    """Parse LA (Logical Access) metadata."""
    print(f"\n[LA] Parsing metadata from: {metadata_path}")
    
    if not os.path.exists(metadata_path):
        print(f"[ERROR] Metadata file not found: {metadata_path}")
        return []
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading LA metadata"):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 6:
                continue
            
            speaker_id = parts[0]
            file_id = parts[1]
            label = parts[5]  # bonafide or spoof
            
            # Map label
            if label == "bonafide":
                label = "bonafide"
                attack_type = "bonafide"
            else:
                label = "spoof"
                attack_type = "synthesis"  # LA is synthesis attacks
            
            # Find audio file
            audio_file = os.path.join(clips_dir, f"{file_id}.flac")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(clips_dir, f"{file_id}.wav")
            
            if not os.path.exists(audio_file):
                continue  # Skip if file not found
            
            records.append({
                "filepath": audio_file,
                "filename": os.path.basename(audio_file),
                "file_id": file_id,
                "speaker_id": speaker_id,
                "label": label,
                "dataset": "LA",
                "attack_type": attack_type
            })
    
    print(f"[LA] Found {len(records)} valid records")
    return records


def parse_df_metadata(metadata_path, clips_dir):
    """Parse DF (DeepFake) metadata."""
    print(f"\n[DF] Parsing metadata from: {metadata_path}")
    
    if not os.path.exists(metadata_path):
        print(f"[ERROR] Metadata file not found: {metadata_path}")
        return []
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading DF metadata"):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 6:
                continue
            
            speaker_id = parts[0]
            file_id = parts[1]
            label = parts[5]  # bonafide or spoof
            
            # Map label
            if label == "bonafide":
                label = "bonafide"
                attack_type = "bonafide"
            else:
                label = "spoof"
                attack_type = "conversion"  # DF is conversion attacks
            
            # Find audio file
            audio_file = os.path.join(clips_dir, f"{file_id}.flac")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(clips_dir, f"{file_id}.wav")
            
            if not os.path.exists(audio_file):
                continue  # Skip if file not found
            
            records.append({
                "filepath": audio_file,
                "filename": os.path.basename(audio_file),
                "file_id": file_id,
                "speaker_id": speaker_id,
                "label": label,
                "dataset": "DF",
                "attack_type": attack_type
            })
    
    print(f"[DF] Found {len(records)} valid records")
    return records


def parse_pa_metadata(metadata_path, clips_dir):
    """Parse PA (Physical Access) metadata."""
    print(f"\n[PA] Parsing metadata from: {metadata_path}")
    
    if not os.path.exists(metadata_path):
        print(f"[ERROR] Metadata file not found: {metadata_path}")
        return []
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading PA metadata"):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 10:
                continue
            
            speaker_id = parts[0]
            file_id = parts[1]
            label = parts[9]  # bonafide or spoof (position may vary, check)
            
            # Try to find label (it's usually near the end)
            label = None
            for part in parts:
                if part in ["bonafide", "spoof"]:
                    label = part
                    break
            
            if label is None:
                continue
            
            # Map label
            if label == "bonafide":
                label = "bonafide"
                attack_type = "bonafide"
            else:
                label = "spoof"
                attack_type = "replay"  # PA is replay attacks
            
            # Find audio file
            audio_file = os.path.join(clips_dir, f"{file_id}.flac")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(clips_dir, f"{file_id}.wav")
            
            if not os.path.exists(audio_file):
                continue  # Skip if file not found
            
            records.append({
                "filepath": audio_file,
                "filename": os.path.basename(audio_file),
                "file_id": file_id,
                "speaker_id": speaker_id,
                "label": label,
                "dataset": "PA",
                "attack_type": attack_type
            })
    
    print(f"[PA] Found {len(records)} valid records")
    return records


def main():
    print("="*80)
    print("CREATING UNIFIED ASVSPOOF MANIFEST")
    print("="*80)
    print()
    print("[INFO] This script combines all three ASVspoof datasets:")
    print("  - LA (Logical Access): Synthesis attacks")
    print("  - DF (DeepFake): Conversion attacks")
    print("  - PA (Physical Access): Replay attacks")
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Parse all three datasets
    all_records = []
    
    # LA dataset
    la_records = parse_la_metadata(LA_METADATA, LA_CLIPS_DIR)
    all_records.extend(la_records)
    
    # DF dataset
    df_records = parse_df_metadata(DF_METADATA, DF_CLIPS_DIR)
    all_records.extend(df_records)
    
    # PA dataset
    pa_records = parse_pa_metadata(PA_METADATA, PA_CLIPS_DIR)
    all_records.extend(pa_records)
    
    # Create DataFrame
    print(f"\n[INFO] Creating unified manifest...")
    df = pd.DataFrame(all_records)
    
    # Print statistics
    print("\n" + "="*80)
    print("DATASET STATISTICS")
    print("="*80)
    print(f"\nTotal samples: {len(df):,}")
    print(f"\nBy Dataset:")
    print(df['dataset'].value_counts())
    print(f"\nBy Label:")
    print(df['label'].value_counts())
    print(f"\nBy Attack Type:")
    print(df['attack_type'].value_counts())
    print(f"\nBy Dataset and Label:")
    print(pd.crosstab(df['dataset'], df['label']))
    print(f"\nUnique speakers: {df['speaker_id'].nunique():,}")
    print(f"\nSpeakers per dataset:")
    print(df.groupby('dataset')['speaker_id'].nunique())
    
    # Save manifest
    print(f"\n[INFO] Saving manifest to: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Manifest saved with {len(df):,} samples")
    
    # Save summary
    summary_file = OUTPUT_FILE.replace(".csv", "_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("UNIFIED ASVSPOOF MANIFEST SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total samples: {len(df):,}\n\n")
        f.write("By Dataset:\n")
        f.write(str(df['dataset'].value_counts()) + "\n\n")
        f.write("By Label:\n")
        f.write(str(df['label'].value_counts()) + "\n\n")
        f.write("By Attack Type:\n")
        f.write(str(df['attack_type'].value_counts()) + "\n\n")
        f.write("By Dataset and Label:\n")
        f.write(str(pd.crosstab(df['dataset'], df['label'])) + "\n\n")
        f.write(f"Unique speakers: {df['speaker_id'].nunique():,}\n\n")
        f.write("Speakers per dataset:\n")
        f.write(str(df.groupby('dataset')['speaker_id'].nunique()) + "\n")
    
    print(f"[OK] Summary saved to: {summary_file}")
    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

