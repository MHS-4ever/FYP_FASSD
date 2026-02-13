"""
One-off: extract environmental, LFCC, and log-mel for one Trump clip and save visualizations.
"""
import os
import sys
import numpy as np
import librosa
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Audio path (Trump testing audios)
AUDIO_PATH = r"E:\FYP\testing_audios\trump\trump_r1.wav"
OUT_DIR = r"E:\FYP\reports\figures"
os.makedirs(OUT_DIR, exist_ok=True)

# Feature params (match pipeline)
SR = 16000
N_FFT = 512
HOP_LENGTH = 160
N_MELS = 64
N_LFCC = 20

def extract_lfcc(y, sr):
    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)) ** 2
    lin_fb = np.linspace(0, S.shape[0]-1, N_LFCC).astype(int)
    lfcc = librosa.feature.mfcc(S=np.log(S[lin_fb, :] + 1e-12), n_mfcc=N_LFCC)
    return lfcc.astype(np.float32)

def extract_logmel(y, sr):
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH,
        n_mels=N_MELS, power=2.0
    )
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)
    return log_mel.astype(np.float32)

def main():
    if not os.path.isfile(AUDIO_PATH):
        print(f"Audio not found: {AUDIO_PATH}")
        return
    y, sr = librosa.load(AUDIO_PATH, sr=SR, mono=True)
    print(f"Loaded {AUDIO_PATH}: {len(y)/sr:.2f}s, sr={sr}")

    # Environmental
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from features.environmental_features import EnvironmentalFeatureExtractor
    ext = EnvironmentalFeatureExtractor(sr=SR)
    env_dict = ext.extract_all(AUDIO_PATH)
    env_names = list(env_dict.keys())
    env_vals = [env_dict[k] for k in env_names]
    # Normalize rolloff for display (Hz -> kHz)
    if 'spectral_rolloff' in env_dict:
        idx = env_names.index('spectral_rolloff')
        env_vals[idx] = env_dict['spectral_rolloff'] / 1000.0

    lfcc = extract_lfcc(y, sr)
    logmel = extract_logmel(y, sr)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10))
    fig.suptitle(f"Features for one clip: {os.path.basename(AUDIO_PATH)}", fontsize=12)

    # Log-Mel
    ax = axes[0]
    im = ax.imshow(logmel, aspect="auto", origin="lower", cmap="magma")
    ax.set_ylabel("Mel bin")
    ax.set_xlabel("Time frame")
    ax.set_title("Log-Mel spectrogram (64 mel bins)")
    plt.colorbar(im, ax=ax, label="dB")

    # LFCC
    ax = axes[1]
    im = ax.imshow(lfcc, aspect="auto", origin="lower", cmap="viridis")
    ax.set_ylabel("LFCC index")
    ax.set_xlabel("Time frame")
    ax.set_title("LFCC (20 coefficients)")
    plt.colorbar(im, ax=ax, label="Coeff.")

    # Environmental (bar chart)
    ax = axes[2]
    x = np.arange(len(env_names))
    bars = ax.bar(x, env_vals, color="steelblue", edgecolor="navy")
    ax.set_xticks(x)
    ax.set_xticklabels(env_names, rotation=45, ha="right")
    ax.set_ylabel("Value")
    ax.set_title("Environmental features (12-D)")
    ax.axhline(0, color="gray", linewidth=0.5)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "one_clip_features_trump_r1.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
