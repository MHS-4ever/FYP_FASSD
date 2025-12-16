#Phase 1 – Baseline Feature Extraction
#Authors : M. Hasnain & Rana M. Areeb
#Project : FASSD – Forensic Acoustic Synthetic Speech Detection

#This script:
# 1. Reads the verified manifest CSV.
# 2. Extracts LFCC & log-Mel features from each WAV file.
# 3. Saves them as .npy arrays for later training.
# 4. Includes TEST_MODE to process only a small subset.


import os
import numpy as np
import pandas as pd
import librosa
import torch
import torchaudio
from tqdm import tqdm

# ------------------------------------------------------------
# 🔧 CONFIGURATION
# ------------------------------------------------------------
manifest_path = r"E:\FYP\data\manifests\asvspoof2021_df_manifest.csv"
save_root = r"E:\FYP\data\features"
os.makedirs(save_root, exist_ok=True)

# Toggle for quick tests (True = process only first 100 files)
TEST_MODE = False
NUM_TEST = 100

SAMPLE_RATE = 16000
N_FFT = 512
HOP_LENGTH = 160
WIN_LENGTH = 400
N_MELS = 64
N_LFCC = 20

# ------------------------------------------------------------
# 📦 Helper functions
# ------------------------------------------------------------
def extract_lfcc(y, sr, n_lfcc=N_LFCC, n_fft=N_FFT, hop_length=HOP_LENGTH):
    """Compute LFCC using linear-spaced filterbanks."""
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length)) ** 2
    mel_fb = librosa.filters.mel(sr=sr, n_fft=n_fft, n_mels=n_lfcc, fmin=0, fmax=sr/2)
    # replace mel with linear spacing
    lin_fb = np.linspace(0, S.shape[0]-1, n_lfcc).astype(int)
    lfcc = librosa.feature.mfcc(S=np.log(S[lin_fb, :] + 1e-12), n_mfcc=n_lfcc)
    return lfcc.astype(np.float32)

def extract_logmel(y, sr, n_mels=N_MELS):
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH,
        n_mels=n_mels, power=2.0
    )
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)
    return log_mel.astype(np.float32)

# ------------------------------------------------------------
# 🚀 Main extraction
# ------------------------------------------------------------
df = pd.read_csv(manifest_path)
if TEST_MODE:
    df = df.head(NUM_TEST)
    print(f"⚙️ TEST_MODE: extracting first {len(df)} files")

lfcc_dir = os.path.join(save_root, "lfcc")
mel_dir  = os.path.join(save_root, "logmel")
os.makedirs(lfcc_dir, exist_ok=True)
os.makedirs(mel_dir,  exist_ok=True)

metadata = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Extracting features"):
    fp = row["filepath"]
    label = row["label"]
    try:
        # load mono, resample
        y, sr = torchaudio.load(fp)
        y = y.mean(0).numpy()
        if sr != SAMPLE_RATE:
            y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)

        # LFCC
        lfcc = extract_lfcc(y, SAMPLE_RATE)
        np.save(os.path.join(lfcc_dir, os.path.basename(fp).replace(".wav", "_lfcc.npy")), lfcc)

        # log-Mel
        logmel = extract_logmel(y, SAMPLE_RATE)
        np.save(os.path.join(mel_dir, os.path.basename(fp).replace(".wav", "_mel.npy")), logmel)

        metadata.append({
            "filename": os.path.basename(fp),
            "label": label,
            "lfcc_path": os.path.join(lfcc_dir, os.path.basename(fp).replace(".wav", "_lfcc.npy")),
            "mel_path":  os.path.join(mel_dir,  os.path.basename(fp).replace(".wav", "_mel.npy"))
        })

    except Exception as e:
        print(f"[Error] {fp}: {e}")
        continue

# ------------------------------------------------------------
# 💾 Save feature manifest
# ------------------------------------------------------------
meta_df = pd.DataFrame(metadata)
out_csv = os.path.join(save_root, "features_manifest.csv")
meta_df.to_csv(out_csv, index=False)
print(f"\n✅ Feature extraction complete.")
print(f"Features manifest saved to: {out_csv}")
print(f"Total processed samples: {len(meta_df)}")
