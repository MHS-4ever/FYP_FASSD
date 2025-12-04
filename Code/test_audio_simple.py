"""
Simple audio deepfake detector - Test real vs AI-generated audio

Usage: python test_audio_simple.py
"""

# Fix OpenMP duplicate library issue
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import pandas as pd
import torch
import librosa
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from models.resnet_cnn import DeepResNetCNN


def extract_mel(audio_path, n_mels=64, sr=16000):
    """Extract mel spectrogram from audio file."""
    y, _ = librosa.load(audio_path, sr=sr)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    log_mel = librosa.power_to_db(mel_spec, ref=np.max)
    return log_mel.astype(np.float32)


def pad_or_crop(features, target_frames=400):
    """Pad or crop features to target length."""
    T = features.shape[1]
    if T > target_frames:
        start = (T - target_frames) // 2
        features = features[:, start:start + target_frames]
    elif T < target_frames:
        pad = np.zeros((features.shape[0], target_frames - T), dtype=np.float32)
        features = np.concatenate([features, pad], axis=1)
    return features


def normalize(features):
    """Normalize features."""
    mean = np.mean(features)
    std = np.std(features)
    return (features - mean) / (std + 1e-5)


def predict_audio_long(audio_path, model, device, chunk_duration=10, overlap=2):
    """
    Predict if audio is real or fake (optimized for long audio files).
    
    For long audio (>1 min), processes in chunks and averages predictions.
    """
    # Load full audio to check duration
    y, sr = librosa.load(audio_path, sr=16000)
    duration = len(y) / sr
    
    # If audio is short (<30s), process normally
    if duration < 30:
        mel = extract_mel(audio_path)
        mel = pad_or_crop(mel, 400)
        mel = normalize(mel)
        mel = torch.from_numpy(mel).unsqueeze(0).unsqueeze(0).float()
        mel = mel.to(device)
        
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(mel)
                probs = torch.softmax(logits, dim=1)
                spoof_prob = probs[0, 1].item()
        
        return spoof_prob
    
    # For long audio, process in chunks with GPU batching
    chunk_samples = chunk_duration * sr
    overlap_samples = overlap * sr
    stride = chunk_samples - overlap_samples
    
    chunks = []
    for start in range(0, len(y) - chunk_samples + 1, stride):
        end = start + chunk_samples
        chunk = y[start:end]
        
        # Extract mel for chunk
        mel_spec = librosa.feature.melspectrogram(y=chunk, sr=sr, n_mels=64)
        log_mel = librosa.power_to_db(mel_spec, ref=np.max).astype(np.float32)
        log_mel = pad_or_crop(log_mel, 400)
        log_mel = normalize(log_mel)
        chunks.append(log_mel)
        
        # Process in batches of 32 for GPU efficiency
        if len(chunks) >= 32:
            batch_probs = process_batch(chunks, model, device)
            if 'all_probs' not in locals():
                all_probs = batch_probs
            else:
                all_probs = np.concatenate([all_probs, batch_probs])
            chunks = []
    
    # Process remaining chunks
    if chunks:
        batch_probs = process_batch(chunks, model, device)
        if 'all_probs' not in locals():
            all_probs = batch_probs
        else:
            all_probs = np.concatenate([all_probs, batch_probs])
    
    # Average predictions across all chunks
    avg_spoof_prob = np.mean(all_probs)
    
    return avg_spoof_prob


def process_batch(chunks, model, device):
    """Process a batch of chunks on GPU."""
    # Stack chunks into batch
    batch = torch.stack([torch.from_numpy(c) for c in chunks])
    batch = batch.unsqueeze(1).float()  # [N, 1, 64, 400]
    batch = batch.to(device)
    
    # Predict
    with torch.no_grad():
        with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
            logits = model(batch)
            probs = torch.softmax(logits, dim=1)[:, 1]  # Spoof probabilities
            
    return probs.cpu().numpy()


def main():
    # Config
    AUDIO_DIR = r"E:\FYP\testing_audios"
    MODEL_PATH = r"E:\FYP\models_saved\resnet_cnn_mel_robust.pth"
    OUTPUT_DIR = r"E:\FYP\reports\tests"
    THRESHOLD = 0.5
    
    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")
    
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print(f"[GPU] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load model
    print(f"[INFO] Loading model...")
    model = DeepResNetCNN().to(device)
    checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model'])
    model.eval()
    print(f"[OK] Model loaded\n")
    
    # Find audio files
    audio_files = []
    for ext in ['.wav', '.mp3', '.flac', '.m4a']:
        audio_files.extend(Path(AUDIO_DIR).glob(f'*{ext}'))
    
    if not audio_files:
        print(f"[ERROR] No audio files found in {AUDIO_DIR}")
        return
    
    print(f"[INFO] Found {len(audio_files)} audio files\n")
    print("="*80)
    print("TESTING AUDIO FILES")
    print("="*80 + "\n")
    
    # Process each audio
    results = []
    for audio_path in tqdm(audio_files, desc="Testing", colour="cyan"):
        try:
            spoof_prob = predict_audio_long(str(audio_path), model, device)
            is_fake = spoof_prob >= THRESHOLD
            confidence = spoof_prob if is_fake else (1 - spoof_prob)
            
            result = {
                'filename': audio_path.name,
                'prediction': 'FAKE (AI-Generated)' if is_fake else 'REAL (Human)',
                'confidence': f"{confidence*100:.2f}%",
                'spoof_probability': f"{spoof_prob:.4f}"
            }
            results.append(result)
            
            # Print result
            emoji = "🔴" if is_fake else "🟢"
            label = "FAKE" if is_fake else "REAL"
            print(f"{emoji} {audio_path.name:40s} -> {label:4s} | Spoof Prob: {spoof_prob:.4f} | Confidence: {confidence*100:.1f}%")
            
        except Exception as e:
            print(f"❌ {audio_path.name:40s} -> ERROR: {e}")
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create results dataframe
    df = pd.DataFrame(results)
    
    # Add metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add description column
    df.insert(0, 'test_date', test_date)
    df.insert(1, 'description', 'Trump voice - Real vs AI-generated audio test')
    
    # Save with timestamp
    output_file = os.path.join(OUTPUT_DIR, f'test_results_{timestamp}.csv')
    df.to_csv(output_file, index=False)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tested: {len(results)}")
    print(f"Real (Human): {sum(1 for r in results if 'REAL' in r['prediction'])}")
    print(f"Fake (AI):    {sum(1 for r in results if 'FAKE' in r['prediction'])}")
    
    # Show probability distribution
    probs = [float(r['spoof_probability']) for r in results]
    print(f"\nSpoof Probability Range:")
    print(f"  Min: {min(probs):.4f}")
    print(f"  Max: {max(probs):.4f}")
    print(f"  Avg: {sum(probs)/len(probs):.4f}")
    print(f"  Threshold: {THRESHOLD}")
    
    # Warning if all predictions are same
    if len(set(r['prediction'] for r in results)) == 1:
        print("\n⚠️  WARNING: All predictions are the same!")
        print("    This might indicate:")
        print("    1. Domain mismatch (model trained on different data)")
        print("    2. Threshold needs adjustment")
        print("    3. Audio characteristics very different from training data")
        print(f"\n    💡 Try adjusting threshold: Change THRESHOLD = {THRESHOLD} in the script")
        print(f"       Suggested: THRESHOLD = {sum(probs)/len(probs):.2f} (average)")
    
    print(f"\nResults saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    main()

