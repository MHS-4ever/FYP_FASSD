"""
Hybrid Deepfake Audio Detector

Combines:
1. Environmental Classifier (environmental features)
2. ResNet CNN (spectrogram-based synthetic artifact detection)

Fusion: Weighted combination of both scores for final prediction
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import argparse
import numpy as np
import torch
import librosa
import pickle
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

from models.resnet_cnn import DeepResNetCNN
from features.environmental_features import EnvironmentalFeatureExtractor


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


def predict_resnet(audio_path, model, device, chunk_duration=10, overlap=2):
    """
    Predict using ResNet CNN on long audio files.
    Splits into chunks and averages predictions.
    """
    y, sr = librosa.load(audio_path, sr=16000)
    duration = len(y) / sr
    
    if duration <= chunk_duration:
        # Short audio: process directly
        mel = extract_mel(audio_path)
        mel = pad_or_crop(mel)
        mel = normalize(mel)
        mel_tensor = torch.from_numpy(mel).unsqueeze(0).unsqueeze(0).float().to(device)
        
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(mel_tensor)
                probs = torch.softmax(logits, dim=1)[0, 1].item()
        
        return probs
    
    # Long audio: chunk and average
    chunk_samples = int(chunk_duration * sr)
    overlap_samples = int(overlap * sr)
    step_samples = chunk_samples - overlap_samples
    
    chunks = []
    for start in range(0, len(y) - chunk_samples + 1, step_samples):
        chunk = y[start:start + chunk_samples]
        mel = librosa.feature.melspectrogram(y=chunk, sr=sr, n_mels=64)
        log_mel = librosa.power_to_db(mel, ref=np.max)
        mel = pad_or_crop(log_mel.astype(np.float32))
        mel = normalize(mel)
        chunks.append(mel)
    
    if not chunks:
        return 0.5  # Default if no chunks
    
    # Process in batches
    batch_size = 32
    all_probs = []
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch = torch.stack([torch.from_numpy(c) for c in batch_chunks])
        batch = batch.unsqueeze(1).float().to(device)
        
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(batch)
                probs = torch.softmax(logits, dim=1)[:, 1]
                all_probs.extend(probs.cpu().numpy())
    
    return np.mean(all_probs)


def predict_environmental(audio_path, env_model, env_scaler):
    """Predict using environmental classifier."""
    extractor = EnvironmentalFeatureExtractor()
    features = extractor.extract_vector(audio_path)
    features_scaled = env_scaler.transform([features])
    prob_fake = env_model.predict_proba(features_scaled)[0, 1]
    return prob_fake


def parse_args():
    ap = argparse.ArgumentParser("Hybrid Deepfake Audio Detector")
    ap.add_argument("--audio_path", type=str, default=None,
                    help="Path to single audio file (or directory for batch)")
    ap.add_argument("--audio_dir", type=str, default=r"E:\FYP\testing_audios",
                    help="Directory containing audio files (for batch processing)")
    ap.add_argument("--resnet_model", type=str, 
                    default=r"E:\FYP\models_saved\resnet_cnn_mel_robust.pth",
                    help="Path to ResNet CNN model")
    ap.add_argument("--env_model", type=str,
                    default=r"E:\FYP\models_saved\environment_classifier.pkl",
                    help="Path to environmental classifier model")
    ap.add_argument("--env_scaler", type=str,
                    default=r"E:\FYP\models_saved\environment_classifier_scaler.pkl",
                    help="Path to environmental classifier scaler")
    ap.add_argument("--weight_resnet", type=float, default=0.3,
                    help="Weight for ResNet CNN score (default: 0.3, reduced due to domain mismatch)")
    ap.add_argument("--weight_env", type=float, default=0.7,
                    help="Weight for environmental classifier score (default: 0.7)")
    ap.add_argument("--use_env_only", action="store_true",
                    help="Use only environmental classifier (ignore ResNet CNN)")
    ap.add_argument("--threshold", type=float, default=0.75,
                    help="Decision threshold (default: 0.75 for real-world audio, 0.5 for ASVspoof-like data)")
    ap.add_argument("--output_csv", type=str, default=None,
                    help="Path to save results CSV (optional)")
    return ap.parse_args()


def main():
    args = parse_args()
    
    # Validate weights sum to 1.0
    total_weight = args.weight_resnet + args.weight_env
    if abs(total_weight - 1.0) > 0.01:
        print(f"[WARN] Weights don't sum to 1.0 ({total_weight:.2f}). Normalizing...")
        args.weight_resnet = args.weight_resnet / total_weight
        args.weight_env = args.weight_env / total_weight
    
    print("="*80)
    print("HYBRID DEEPFAKE AUDIO DETECTOR")
    print("="*80)
    print(f"\n[CONFIG]")
    print(f"  ResNet CNN weight: {args.weight_resnet:.2f}")
    print(f"  Environmental weight: {args.weight_env:.2f}")
    print(f"  Decision threshold: {args.threshold:.2f}")
    print()
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")
    
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print(f"[GPU] GPU: {torch.cuda.get_device_name(0)}")
    
    # Load ResNet CNN model
    print(f"\n[LOADING] ResNet CNN model...")
    resnet_model = DeepResNetCNN().to(device)
    checkpoint = torch.load(args.resnet_model, map_location=device, weights_only=False)
    resnet_model.load_state_dict(checkpoint['model'])
    resnet_model.eval()
    print(f"[OK] ResNet CNN loaded: {args.resnet_model}")
    
    # Load environmental classifier
    print(f"\n[LOADING] Environmental classifier...")
    with open(args.env_model, 'rb') as f:
        env_model = pickle.load(f)
    with open(args.env_scaler, 'rb') as f:
        env_scaler = pickle.load(f)
    print(f"[OK] Environmental classifier loaded: {args.env_model}")
    
    # Find audio files
    if args.audio_path:
        if os.path.isfile(args.audio_path):
            audio_files = [Path(args.audio_path)]
        else:
            print(f"[ERROR] Audio file not found: {args.audio_path}")
            return
    else:
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.m4a']:
            audio_files.extend(Path(args.audio_dir).glob(f'*{ext}'))
        
        if not audio_files:
            print(f"[ERROR] No audio files found in {args.audio_dir}")
            return
    
    print(f"\n[INFO] Found {len(audio_files)} audio file(s)")
    print("\n" + "="*80)
    print("PREDICTIONS")
    print("="*80 + "\n")
    
    # Process each audio
    results = []
    for audio_path in tqdm(audio_files, desc="Processing", colour="cyan"):
        try:
            # Get environmental classifier prediction
            env_score = predict_environmental(str(audio_path), env_model, env_scaler)
            
            if args.use_env_only:
                # Use only environmental classifier
                hybrid_score = env_score
                resnet_score = None
            else:
                # Get ResNet CNN prediction
                resnet_score = predict_resnet(str(audio_path), resnet_model, device)
                
                # Domain mismatch detection: If ResNet is too confident (>=0.99), reduce its weight
                # This happens when model trained on ASVspoof encounters real-world audio
                if resnet_score >= 0.99:
                    # ResNet is likely failing due to domain mismatch
                    # Give more weight to environmental classifier
                    effective_resnet_weight = args.weight_resnet * 0.2  # Reduce weight by 80%
                    effective_env_weight = args.weight_env + (args.weight_resnet * 0.8)
                else:
                    effective_resnet_weight = args.weight_resnet
                    effective_env_weight = args.weight_env
                
                # Combine scores (weighted average)
                hybrid_score = (effective_resnet_weight * resnet_score) + (effective_env_weight * env_score)
            
            # Make prediction
            prediction = "FAKE" if hybrid_score >= args.threshold else "REAL"
            
            # Store results
            results.append({
                'filename': audio_path.name,
                'resnet_score': resnet_score if resnet_score is not None else 'N/A',
                'env_score': env_score,
                'hybrid_score': hybrid_score,
                'prediction': prediction,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Print result
            if args.use_env_only:
                print(f"{audio_path.name:30s} | Env: {env_score:.3f} | {prediction} (Env-only)")
            else:
                print(f"{audio_path.name:30s} | ResNet: {resnet_score:.3f} | Env: {env_score:.3f} | "
                      f"Hybrid: {hybrid_score:.3f} | {prediction}")
        
        except Exception as e:
            print(f"[ERROR] Failed to process {audio_path.name}: {e}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    n_fake = sum(1 for r in results if r['prediction'] == 'FAKE')
    n_real = sum(1 for r in results if r['prediction'] == 'REAL')
    print(f"  Total files: {len(results)}")
    print(f"  Predicted FAKE: {n_fake}")
    print(f"  Predicted REAL: {n_real}")
    if not args.use_env_only:
        resnet_scores = [r['resnet_score'] for r in results if r['resnet_score'] != 'N/A']
        if resnet_scores:
            print(f"  Average ResNet score: {np.mean(resnet_scores):.3f}")
    print(f"  Average Env score: {np.mean([r['env_score'] for r in results]):.3f}")
    print(f"  Average Hybrid score: {np.mean([r['hybrid_score'] for r in results]):.3f}")
    
    # Save to CSV if requested
    if args.output_csv:
        import pandas as pd
        df = pd.DataFrame(results)
        os.makedirs(os.path.dirname(args.output_csv) if os.path.dirname(args.output_csv) else '.', exist_ok=True)
        df.to_csv(args.output_csv, index=False)
        print(f"\n[SAVE] Results saved to: {args.output_csv}")
    
    print("\n[SUCCESS] Hybrid detection complete!")


if __name__ == "__main__":
    main()

