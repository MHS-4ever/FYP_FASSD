import os, random, soundfile as sf
import numpy as np
import librosa
from tqdm import tqdm
from scipy import signal
import pandas as pd

# ------------------------------
# CONFIG PATHS
# ------------------------------
musan_root = r"D:\UNI\FYP\data\noise_rir\musan"
rir_root = r"D:\UNI\FYP\data\noise_rir\rir"
manifest_in = r"D:\UNI\FYP\data\features\features_manifest_labeled.csv"
output_dir = r"D:\UNI\FYP\data\features_augmented"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "lfcc"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "logmel"), exist_ok=True)

# ------------------------------
# LOAD METADATA
# ------------------------------
df = pd.read_csv(manifest_in)
print(f"Loaded {len(df)} files for augmentation")

# ------------------------------
# HELPERS
# ------------------------------
def add_noise(audio, snr_db=10):
    """Add random MUSAN noise to signal at target SNR."""
    noise_dirs = [os.path.join(musan_root, d) for d in os.listdir(musan_root)]
    noise_file = random.choice([os.path.join(nd, f) for nd in noise_dirs for f in os.listdir(nd)])
    noise, _ = librosa.load(noise_file, sr=16000)
    if len(noise) < len(audio):
        noise = np.tile(noise, int(np.ceil(len(audio)/len(noise))))
    noise = noise[:len(audio)]
    sig_power = np.mean(audio**2)
    noise_power = np.mean(noise**2)
    scale = np.sqrt(sig_power / (10**(snr_db/10) * noise_power))
    noisy = audio + noise * scale
    return noisy

def apply_rir(audio):
    """Simulate room impulse response (reverberation)."""
    rir_files = [os.path.join(rir_root, f) for f in os.listdir(rir_root) if f.endswith('.wav')]
    rir_file = random.choice(rir_files)
    rir, _ = librosa.load(rir_file, sr=16000)
    rir = rir / np.sqrt(np.sum(rir**2))
    return signal.convolve(audio, rir, mode='full')[:len(audio)]

def random_gain(audio):
    """Random volume scaling."""
    gain = np.random.uniform(0.8, 1.2)
    return audio * gain

def codec_simulation(audio, sr=16000):
    """Simulate compression effect (resample down & up)."""
    rates = [8000, 12000, 16000]
    new_sr = random.choice(rates)
    resampled = librosa.resample(audio, orig_sr=sr, target_sr=new_sr)
    return librosa.resample(resampled, orig_sr=new_sr, target_sr=sr)

# ------------------------------
# MAIN AUGMENTATION LOOP
# ------------------------------
augmented_data = []
for i, row in tqdm(df.iterrows(), total=len(df), desc="Augmenting"):
    try:
        # Construct actual audio path from your dataset folder
        base_audio_dir = r"D:\UNI\FYP\DataSet\English\DeepFake (DF)\DF_clips"
        wav_path = os.path.join(base_audio_dir, row['filename'])
        if not os.path.exists(wav_path):
            print(f"[Missing audio] {wav_path}")
            continue
        audio, sr = librosa.load(wav_path, sr=16000)
        # randomly pick augmentations
        if random.random() < 0.5:
            audio = add_noise(audio)
        if random.random() < 0.3:
            audio = apply_rir(audio)
        if random.random() < 0.3:
            audio = codec_simulation(audio)
        audio = random_gain(audio)

        # Extract LFCC / log-mel again
        lfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
        mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_fft=512, hop_length=160, n_mels=64)

        base = os.path.splitext(os.path.basename(row['filename']))[0]
        lfcc_path = os.path.join(output_dir, "lfcc", f"{base}_aug_lfcc.npy")
        mel_path = os.path.join(output_dir, "logmel", f"{base}_aug_mel.npy")
        np.save(lfcc_path, lfcc)
        np.save(mel_path, mel)

        augmented_data.append([row['filename'], row['label'], lfcc_path, mel_path])
    except Exception as e:
        print(f"[Skip] {row['filename']} -> {e}")

# ------------------------------
# SAVE MANIFEST
# ------------------------------
aug_df = pd.DataFrame(augmented_data, columns=['filename', 'label', 'lfcc_path', 'mel_path'])
aug_df.to_csv(os.path.join(output_dir, "features_manifest_augmented.csv"), index=False)
print(f"✅ Augmented features saved to {output_dir}")
print(f"Total augmented samples: {len(aug_df)}")
