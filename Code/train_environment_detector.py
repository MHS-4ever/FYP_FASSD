"""
Train Environmental Anomaly Detector

This script:
1. Extracts environmental features from bonafide samples
2. Trains anomaly detector (Isolation Forest)
3. Tests on spoof samples
4. Validates on Trump audios

Training time: ~10-20 minutes (feature extraction is the bottleneck)
"""

import os
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from tqdm import tqdm
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

from features.environmental_features import EnvironmentalFeatureExtractor


def extract_features_from_manifest(manifest_path, feature_type='mel', max_samples=None, desc="Extracting"):
    """
    Extract environmental features from audio files in manifest.
    
    Args:
        manifest_path: Path to CSV manifest
        max_samples: Limit number of samples (for faster testing)
        desc: Progress bar description
    """
    print(f"[INFO] Loading manifest: {manifest_path}")
    df = pd.read_csv(manifest_path)
    
    # Filter to bonafide or spoof as needed
    print(f"[INFO] Total samples in manifest: {len(df)}")
    
    if max_samples:
        df = df.head(max_samples)
        print(f"[INFO] Limited to {max_samples} samples for faster processing")
    
    # Extract features
    extractor = EnvironmentalFeatureExtractor()
    features_list = []
    labels = []
    filenames = []
    
    print(f"[INFO] Extracting environmental features...")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc=desc, colour="green"):
        try:
            # Get audio path based on feature type
            if feature_type == 'mel' and 'mel_path' in row:
                # We need actual audio file, not feature file
                # Convert feature path to audio path
                audio_path = row['mel_path'].replace('_mel.npy', '.wav').replace('/logmel/', '/audio/')
                
                # If that doesn't exist, skip (we need actual audio for env features)
                if not os.path.exists(audio_path):
                    # Try alternative: look in original dataset
                    filename = row['filename']
                    # This is a workaround - we'll extract from a subset for now
                    continue
            else:
                continue
            
            # Extract environmental features
            feature_vector = extractor.extract_vector(audio_path)
            features_list.append(feature_vector)
            
            label = 1 if row['label'] == 'spoof' else 0
            labels.append(label)
            filenames.append(row['filename'])
            
        except Exception as e:
            # Skip files that can't be processed
            continue
    
    if len(features_list) == 0:
        print("[ERROR] No features extracted. Audio files not accessible.")
        print("[INFO] Using alternative approach: Extract from accessible audio files")
        return None, None, None
    
    features_array = np.vstack(features_list)
    labels_array = np.array(labels)
    
    print(f"[OK] Extracted features from {len(features_list)} samples")
    
    return features_array, labels_array, filenames


def extract_from_audio_dir(audio_dir, label, max_samples=500):
    """
    Extract environmental features directly from audio directory.
    Faster approach when manifest audio paths aren't accessible.
    """
    print(f"[INFO] Extracting from audio directory: {audio_dir}")
    
    audio_files = []
    for ext in ['.wav', '.flac']:
        audio_files.extend(Path(audio_dir).glob(f'*{ext}'))
    
    if not audio_files:
        print(f"[WARN] No audio files found in {audio_dir}")
        return None, None, None
    
    print(f"[INFO] Found {len(audio_files)} audio files")
    
    if max_samples and len(audio_files) > max_samples:
        audio_files = audio_files[:max_samples]
        print(f"[INFO] Limited to {max_samples} samples")
    
    extractor = EnvironmentalFeatureExtractor()
    features_list = []
    labels = []
    filenames = []
    
    for audio_path in tqdm(audio_files, desc="Extracting env features", colour="green"):
        try:
            feature_vector = extractor.extract_vector(str(audio_path))
            features_list.append(feature_vector)
            labels.append(label)
            filenames.append(audio_path.name)
        except Exception as e:
            continue
    
    if len(features_list) == 0:
        return None, None, None
    
    features_array = np.vstack(features_list)
    labels_array = np.array(labels)
    
    print(f"[OK] Extracted {len(features_list)} feature vectors")
    
    return features_array, labels_array, filenames


def main():
    # Configuration
    BONAFIDE_AUDIO_DIR = r"E:\FYP\DataSet\English\ASVspoof2021_LA_eval\LA_clips"  # Real/bonafide samples
    SPOOF_AUDIO_DIR = r"E:\FYP\DataSet\English\ASVspoof2021_DF_eval\DF_clips"  # Fake/synthetic samples (for testing)
    OUTPUT_DIR = r"E:\FYP\models_saved"
    MODEL_NAME = "environment_detector.pkl"
    SCALER_NAME = "environment_scaler.pkl"
    
    # Training parameters
    MAX_TRAIN_SAMPLES = 5000  # Use 5000 samples for training (fast)
    MAX_TEST_SAMPLES = 1000  # Use 1000 samples for testing
    CONTAMINATION = 0.1  # Expected proportion of outliers
    
    print("="*80)
    print("TRAINING ENVIRONMENTAL ANOMALY DETECTOR")
    print("="*80)
    print()
    
    # Check if we can access audio files
    if not os.path.exists(BONAFIDE_AUDIO_DIR):
        print(f"[ERROR] Bonafide audio directory not found: {BONAFIDE_AUDIO_DIR}")
        print("[INFO] Please check the dataset path.")
        return
    
    print(f"[OK] Bonafide audio directory found: {BONAFIDE_AUDIO_DIR}")
    
    # Extract features from bonafide samples
    print("\n[STEP 1] Extracting environmental features from BONAFIDE samples...")
    X_bonafide, y_bonafide, files_bonafide = extract_from_audio_dir(
        BONAFIDE_AUDIO_DIR, 
        label=0,
        max_samples=MAX_TRAIN_SAMPLES
    )
    
    if X_bonafide is None:
        print("[ERROR] Failed to extract features. Check audio directory paths.")
        return
    
    print(f"[OK] Training data: {X_bonafide.shape[0]} samples, {X_bonafide.shape[1]} features")
    
    # Normalize features
    print("\n[STEP 2] Normalizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_bonafide)
    print("[OK] Features normalized")
    
    # Train Isolation Forest
    print("\n[STEP 3] Training Isolation Forest anomaly detector...")
    print(f"[INFO] Contamination: {CONTAMINATION} (expected outlier ratio)")
    
    model = IsolationForest(
        contamination=CONTAMINATION,
        max_samples='auto',
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        verbose=1
    )
    
    model.fit(X_scaled)
    print("[OK] Model trained!")
    
    # Validate on training data
    print("\n[STEP 4] Validating on training data...")
    train_pred = model.predict(X_scaled)
    train_scores = model.score_samples(X_scaled)
    
    n_normal = np.sum(train_pred == 1)
    n_anomaly = np.sum(train_pred == -1)
    print(f"[INFO] Training predictions: {n_normal} normal, {n_anomaly} anomalies")
    print(f"[INFO] Anomaly score range: [{train_scores.min():.3f}, {train_scores.max():.3f}]")
    
    # Save model
    print("\n[STEP 5] Saving model...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    model_path = os.path.join(OUTPUT_DIR, MODEL_NAME)
    scaler_path = os.path.join(OUTPUT_DIR, SCALER_NAME)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"[SAVE] Model saved: {model_path}")
    print(f"[SAVE] Scaler saved: {scaler_path}")
    
    # Test on spoof samples
    print("\n[STEP 6] Testing on SPOOF samples...")
    if os.path.exists(SPOOF_AUDIO_DIR):
        X_spoof, y_spoof, spoof_files = extract_from_audio_dir(
            SPOOF_AUDIO_DIR, 
            label=1,  # Spoof samples
            max_samples=MAX_TEST_SAMPLES
        )
        
        if X_spoof is not None:
            X_spoof_scaled = scaler.transform(X_spoof)
            spoof_pred = model.predict(X_spoof_scaled)
            spoof_scores = model.score_samples(X_spoof_scaled)
            
            # Anomaly detector: -1 = anomaly (fake), 1 = normal (real)
            # For spoof samples, we expect -1 (anomaly)
            n_detected_fake = np.sum(spoof_pred == -1)
            n_false_negative = np.sum(spoof_pred == 1)  # Should be fake but predicted as normal
            
            print("\n" + "="*80)
            print("SPOOF SAMPLE TEST RESULTS")
            print("="*80)
            print(f"[INFO] Tested on {len(spoof_files)} spoof samples")
            print(f"[INFO] Detected as FAKE (anomaly): {n_detected_fake}/{len(spoof_files)} ({n_detected_fake/len(spoof_files)*100:.1f}%)")
            print(f"[INFO] False Negatives (missed): {n_false_negative}/{len(spoof_files)} ({n_false_negative/len(spoof_files)*100:.1f}%)")
            print(f"[INFO] Anomaly score range: [{spoof_scores.min():.3f}, {spoof_scores.max():.3f}]")
            print("="*80)
    
    # Test on Trump audios (if available)
    print("\n[STEP 7] Testing on Trump audios (if available)...")
    test_dir = r"E:\FYP\testing_audios"
    if os.path.exists(test_dir):
        X_test, y_test, test_files = extract_from_audio_dir(test_dir, label=-1, max_samples=None)
        
        if X_test is not None:
            X_test_scaled = scaler.transform(X_test)
            test_pred = model.predict(X_test_scaled)
            test_scores = model.score_samples(X_test_scaled)
            
            print("\n" + "="*80)
            print("TRUMP AUDIO TEST RESULTS")
            print("="*80)
            
            for i, filename in enumerate(test_files):
                pred_label = "NORMAL (Real)" if test_pred[i] == 1 else "ANOMALY (Fake)"
                score = test_scores[i]
                
                # Determine if actually real or fake
                actual = "REAL" if 'r' in filename.lower() and 'trump_r' in filename.lower() else "FAKE"
                correct = "✅" if (test_pred[i] == 1 and actual == "REAL") or (test_pred[i] == -1 and actual == "FAKE") else "❌"
                
                print(f"{correct} {filename:20s} | {pred_label:18s} | Score: {score:6.3f} | Actual: {actual}")
            
            # Accuracy
            correct_count = sum([
                1 for i, f in enumerate(test_files) 
                if (test_pred[i] == 1 and 'trump_r' in f.lower()) or (test_pred[i] == -1 and 'trump_f' in f.lower())
            ])
            accuracy = correct_count / len(test_files) * 100 if len(test_files) > 0 else 0
            
            print("\n" + "="*80)
            print(f"[RESULTS] Accuracy on Trump test: {correct_count}/{len(test_files)} = {accuracy:.1f}%")
            print("="*80)
    else:
        print(f"[INFO] Trump test directory not found: {test_dir}")
        print("[INFO] Skipping Trump audio test")
    
    print("\n[SUCCESS] Environmental detector training complete!")
    print("\nNext step: Combine with ResNet CNN for hybrid detection")
    print(f"Run: python predict_hybrid.py (after implementing)")


if __name__ == "__main__":
    main()



