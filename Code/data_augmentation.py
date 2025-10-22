# ============================================================
# Robust augmentation with GPU-accelerated feature extraction
# - CPU threads: loading + augmentations (noise/RIR/codec/gain)
# - GPU (CUDA): LFCC + Log-Mel extraction via torchaudio
# - Checkpointing & resume, batched incremental writes
# ============================================================

import os, random
import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy import signal

import multiprocessing
from joblib import Parallel, delayed

import torch
import torchaudio
import torchaudio.transforms as T
import torch.nn.functional as F

# ------------------------------
# CONFIG PATHS
# ------------------------------
musan_root    = r"E:\FYP\data\noise_rir\musan"
rir_root      = r"E:\FYP\data\noise_rir\rir"
manifest_in   = r"E:\FYP\data\features\features_manifest_labeled.csv"
base_audio_dir= r"E:\FYP\DataSet\English\DeepFake (DF)\DF_clips"
output_dir    = r"E:\FYP\data\features_augmented"
checkpoint_fp = os.path.join(output_dir, "augmentation_checkpoint.csv")

os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "lfcc"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "logmel"), exist_ok=True)

# ------------------------------
# DEVICE / CUDA
# ------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🟩 Using device: {device}")

# Pre-build GPU transforms (lazy-inited inside worker to avoid thread race)
SR = 16000
def build_transforms():
    # These run on GPU (or CPU if CUDA not available)
    mel = T.MelSpectrogram(sample_rate=SR, n_fft=512, hop_length=160, n_mels=64).to(device)
    lfcc = T.LFCC(sample_rate=SR, n_filter=64, n_lfcc=20, speckwargs={"n_fft":512, "hop_length":160}).to(device)
    return mel, lfcc

# ------------------------------
# LOAD & RESUME
# ------------------------------
df = pd.read_csv(manifest_in)
print(f"📄 Loaded {len(df)} files for augmentation")

done_set = set()
if os.path.exists(checkpoint_fp):
    done = pd.read_csv(checkpoint_fp)
    done_set = set(done['filename'])
    print(f"🔄 Resuming from checkpoint — {len(done_set)} already processed")
    df = df[~df['filename'].isin(done_set)].reset_index(drop=True)

print(f"Remaining to process: {len(df)}")

# ------------------------------
# SPEED / PARALLELISM
# ------------------------------
# Threading works best with a single CUDA context (don’t use multiprocess + CUDA).
NUM_CORES = max(1, min(8, multiprocessing.cpu_count() - 1))
print(f"🧠 Using {NUM_CORES} CPU threads for parallel augmentation")

# ------------------------------
# UTIL: scan datasets once (recursive)
# ------------------------------
def list_wavs(root_dir):
    files = []
    if not os.path.exists(root_dir):
        return files
    for r, _, fs in os.walk(root_dir):
        for f in fs:
            if f.lower().endswith(".wav"):
                files.append(os.path.join(r, f))
    return files

NOISE_FILES = list_wavs(musan_root)
RIR_FILES   = list_wavs(rir_root)
print(f"🔎 Found {len(NOISE_FILES)} MUSAN wavs, {len(RIR_FILES)} RIR wavs")

# ------------------------------
# AUGMENTATION HELPERS (CPU tensors)
# ------------------------------
def load_audio_cpu(path, sr=SR):
    # torchaudio.load -> torch tensor on CPU
    wav, file_sr = torchaudio.load(path)  # [C, L] on CPU
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if file_sr != sr:
        wav = T.Resample(orig_freq=file_sr, new_freq=sr)(wav)
    return wav.squeeze(0).contiguous()  # [L] CPU tensor

def add_noise_cpu(audio_cpu, snr_db=10):
    try:
        if len(NOISE_FILES) == 0:
            return audio_cpu
        nf = random.choice(NOISE_FILES)
        noise = load_audio_cpu(nf)  # CPU [L]
        if noise.numel() < audio_cpu.numel():
            reps = int(np.ceil(audio_cpu.numel()/noise.numel()))
            noise = noise.repeat(reps)[:audio_cpu.numel()]
        else:
            noise = noise[:audio_cpu.numel()]
        sig_power   = audio_cpu.pow(2).mean().item()
        noise_power = noise.pow(2).mean().item()
        if noise_power == 0:
            return audio_cpu
        scale = np.sqrt(sig_power/(10**(snr_db/10)*noise_power))
        return audio_cpu + noise*scale
    except Exception as e:
        print(f"[Noise error] {e}")
        return audio_cpu

def apply_rir_cpu(audio_cpu):
    try:
        if len(RIR_FILES) == 0:
            return audio_cpu
        rf  = random.choice(RIR_FILES)
        rir = load_audio_cpu(rf)
        denom = torch.sqrt((rir.pow(2).sum() + 1e-8))
        rir = rir/denom
        # CPU convolution (fast enough) then trim
        reverbed = torch.from_numpy(signal.convolve(audio_cpu.numpy(), rir.numpy(), mode="full")[:audio_cpu.numel()])
        return reverbed
    except Exception as e:
        print(f"[RIR error] {e}")
        return audio_cpu

def codec_sim_cpu(audio_cpu, sr=SR):
    try:
        # downsample then upsample (AMR/codec-like)
        rate = random.choice([8000, 12000, 16000])
        if rate == sr:
            return audio_cpu
        down = T.Resample(orig_freq=sr, new_freq=rate)(audio_cpu.unsqueeze(0)).squeeze(0)
        up   = T.Resample(orig_freq=rate, new_freq=sr)(down.unsqueeze(0)).squeeze(0)
        return up
    except Exception as e:
        print(f"[Codec error] {e}")
        return audio_cpu

def random_gain_cpu(audio_cpu):
    gain = np.random.uniform(0.8, 1.2)
    return audio_cpu*gain

# ------------------------------
# PER-FILE PIPELINE (CPU -> GPU features)
# ------------------------------
# Build GPU transforms once per thread
mel_tf, lfcc_tf = build_transforms()

def process_one(row):
    try:
        wav_path = os.path.join(base_audio_dir, row['filename'])
        if not os.path.exists(wav_path):
            return None

        # -------- CPU: load & augment
        audio = load_audio_cpu(wav_path)  # CPU [L]
        if random.random() < 0.5:
            audio = add_noise_cpu(audio)
        if random.random() < 0.3:
            audio = apply_rir_cpu(audio)
        if random.random() < 0.3:
            audio = codec_sim_cpu(audio)
        audio = random_gain_cpu(audio)

        # -------- GPU: feature extraction
        wav = audio.to(device).unsqueeze(0)  # [1, L] on GPU
        # (Optional) small clamp to avoid inf/nan
        wav = torch.clamp(wav, -1.0, 1.0)

        mel  = mel_tf(wav)         # [1, n_mels, T]
        lfcc = lfcc_tf(wav)        # [1, n_lfcc, T]

        # Save to disk (CPU numpy)
        base = os.path.splitext(os.path.basename(row['filename']))[0]
        lfcc_path = os.path.join(output_dir, "lfcc",  f"{base}_aug_lfcc.npy")
        mel_path  = os.path.join(output_dir,  "logmel",f"{base}_aug_mel.npy")
        np.save(lfcc_path, lfcc.squeeze(0).detach().cpu().numpy())
        np.save(mel_path,  mel.squeeze(0).detach().cpu().numpy())

        return [row['filename'], row['label'], lfcc_path, mel_path]
    except Exception as e:
        print(f"[Skip] {row['filename']} -> {e}")
        return None

# ------------------------------
# BATCHED PARALLEL EXECUTION + CHECKPOINTING
# ------------------------------
batch_size = 2000  # write checkpoint after each batch
for start in range(0, len(df), batch_size):
    batch = df.iloc[start:start+batch_size]
    print(f"\n🚀 Processing batch {start}–{start+len(batch)}")

    # Threading lets all threads share the same CUDA context safely
    results = Parallel(n_jobs=NUM_CORES, backend="threading")(
        delayed(process_one)(row) for _, row in tqdm(batch.iterrows(), total=len(batch), desc="Augmenting")
    )

    results = [r for r in results if r is not None]
    if len(results) > 0:
        pd.DataFrame(results, columns=['filename', 'label', 'lfcc_path', 'mel_path']).to_csv(
            checkpoint_fp, mode='a', index=False, header=not os.path.exists(checkpoint_fp)
        )
        print(f"✅ Saved batch progress ({len(results)} files)")

print(f"\n✅ All batches complete. Checkpoint: {checkpoint_fp}")
