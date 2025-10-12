#Step 0.3 – ASVspoof 2021 DF Dataset Integrity Check & Manifest Creation
#Author : M. Hasnain & Rana M. Areeb
#Project: FYP – Forensic Acoustic Synthetic Speech Detection (FASSD)

#This script:
#1. Verifies all WAV files listed in ASVspoof2021.DF.cm.eval.trl.txt exist.
#2. Checks that they can be opened with soundfile.
#3. Computes audio duration and sample rate.
#4. Saves a clean CSV manifest for model training.

#Output:
#  D:/UNI/FYP/data/manifests/asvspoof2021_df_manifest.csv


import os
import pandas as pd
import soundfile as sf
from tqdm import tqdm

# ------------------------------------------------------------
# 🔧 PATHS – update this if your folder names differ
# ------------------------------------------------------------
base_path = r"D:\UNI\FYP\DataSet\English\DeepFake (DF)"
clips_dir = os.path.join(base_path, "DF_clips")
trl_file = os.path.join(base_path, "ASVspoof2021.DF.cm.eval.trl.txt")
output_dir = r"D:\UNI\FYP\data\manifests"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, "asvspoof2021_df_manifest.csv")

# ------------------------------------------------------------
# 🧩 Step 1 – Load metadata file
# ------------------------------------------------------------
if not os.path.exists(trl_file):
    raise FileNotFoundError(f"Trial file not found: {trl_file}")

# Load the file list (single column, no labels)
df = pd.read_csv(trl_file, sep=' ', header=None, names=['filename'])

# Add the .wav extension
df['filename'] = df['filename'].astype(str) + ".wav"

# Assign temporary placeholder label (we'll fix later in training)
df['label'] = "unknown"

# Build full file paths
df['filepath'] = df['filename'].apply(lambda x: os.path.join(clips_dir, x))


# ------------------------------------------------------------
# 🧪 Step 2 – Verify files and extract audio info
# ------------------------------------------------------------
durations, samplerates, valid_flags = [], [], []

print(f"\n🔍 Checking {len(df)} audio files ...\n")
for fp in tqdm(df['filepath'], desc="Verifying audio files"):
    if os.path.exists(fp):
        try:
            info = sf.info(fp)
            durations.append(round(info.duration, 2))
            samplerates.append(info.samplerate)
            valid_flags.append(True)
        except Exception as e:
            print(f"[Error reading] {fp}: {e}")
            durations.append(None)
            samplerates.append(None)
            valid_flags.append(False)
    else:
        durations.append(None)
        samplerates.append(None)
        valid_flags.append(False)

df['duration'] = durations
df['samplerate'] = samplerates
df['is_valid'] = valid_flags

# ------------------------------------------------------------
# 📊 Step 3 – Summary
# ------------------------------------------------------------
missing = df[~df['is_valid']]
print(f"\n✅ Total valid files: {df['is_valid'].sum()}")
print(f"❌ Missing or unreadable files: {len(missing)}")

if not missing.empty:
    missing.to_csv(os.path.join(output_dir, "missing_files.csv"), index=False)
    print(f"⚠️ Missing file list saved to: {os.path.join(output_dir, 'missing_files.csv')}")

# ------------------------------------------------------------
# 💾 Step 4 – Save final manifest
# ------------------------------------------------------------
manifest = df[df['is_valid']][['filepath', 'label', 'duration']]
manifest.to_csv(output_csv, index=False)
print(f"\n📁 Manifest saved to: {output_csv}")
print(f"Total usable samples: {len(manifest)}")
print(f"\nManifest file exists: {os.path.exists(output_csv)}")
