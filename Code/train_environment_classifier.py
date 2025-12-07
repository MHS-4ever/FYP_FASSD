"""
Train Supervised Environmental Classifier

This script trains a CLASSIFIER (not anomaly detector) using both real and fake samples.
This should perform much better than anomaly detection.

Training:
1. Extracts environmental features from BOTH bonafide and spoof samples
2. Trains a supervised classifier (Random Forest or XGBoost)
3. Tests on validation set
4. Validates on Trump audios

Expected performance: 70-90% accuracy (much better than 25% with anomaly detection)
"""

import os
import argparse
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
import time

from features.environmental_features import EnvironmentalFeatureExtractor


def extract_from_audio_dir(audio_dir, label, max_samples=None, desc="Extracting"):
    """
    Extract environmental features directly from audio directory.
    
    Args:
        audio_dir: Directory containing audio files
        label: 0 for real (bonafide), 1 for fake (spoof)
        max_samples: Maximum number of samples to extract (None for all, -1 for all)
        desc: Progress bar description
    """
    print(f"[INFO] Extracting from audio directory: {audio_dir}")
    
    audio_files = []
    for ext in ['.wav', '.flac']:
        audio_files.extend(Path(audio_dir).glob(f'*{ext}'))
    
    if not audio_files:
        print(f"[WARN] No audio files found in {audio_dir}")
        return None, None, None
    
    print(f"[INFO] Found {len(audio_files):,} audio files")
    
    if max_samples is not None and max_samples > 0 and len(audio_files) > max_samples:
        audio_files = audio_files[:max_samples]
        print(f"[INFO] Limited to {max_samples:,} samples")
    elif max_samples == -1:
        print(f"[INFO] Using all {len(audio_files):,} available samples")
    
    extractor = EnvironmentalFeatureExtractor()
    features_list = []
    labels = []
    filenames = []
    
    for audio_path in tqdm(audio_files, desc=desc, colour="green"):
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
    
    print(f"[OK] Extracted {len(features_list):,} feature vectors")
    
    return features_array, labels_array, filenames


def parse_args():
    ap = argparse.ArgumentParser("Train Supervised Environmental Classifier")
    ap.add_argument("--max_real_samples", type=int, default=20000,
                    help="Maximum number of real (bonafide) samples for training (default: 20000). Use -1 for all.")
    ap.add_argument("--max_fake_samples", type=int, default=20000,
                    help="Maximum number of fake (spoof) samples for training (default: 20000). Use -1 for all.")
    ap.add_argument("--test_size", type=float, default=0.2,
                    help="Fraction of data to use for testing (default: 0.2)")
    ap.add_argument("--n_estimators", type=int, default=100,
                    help="Number of trees in Random Forest (default: 100)")
    ap.add_argument("--max_depth", type=int, default=20,
                    help="Maximum depth of trees (default: 20, None for unlimited)")
    ap.add_argument("--output_dir", default=r"E:\FYP\models_saved",
                    help="Directory to save model and scaler")
    ap.add_argument("--model_name", default="environment_classifier.pkl",
                    help="Name for saved model file")
    ap.add_argument("--scaler_name", default="environment_classifier_scaler.pkl",
                    help="Name for saved scaler file")
    return ap.parse_args()


def main():
    args = parse_args()
    
    # Configuration
    BONAFIDE_AUDIO_DIR = r"E:\FYP\DataSet\English\ASVspoof2021_LA_eval\LA_clips"  # Real/bonafide samples
    SPOOF_AUDIO_DIR = r"E:\FYP\DataSet\English\ASVspoof2021_DF_eval\DF_clips"  # Fake/synthetic samples
    OUTPUT_DIR = args.output_dir
    MODEL_NAME = args.model_name
    SCALER_NAME = args.scaler_name
    
    print("="*80)
    print("TRAINING SUPERVISED ENVIRONMENTAL CLASSIFIER")
    print("="*80)
    print()
    print("[INFO] This classifier learns from BOTH real and fake samples")
    print("[INFO] Expected to perform much better than anomaly detection")
    print()
    
    # Check directories
    if not os.path.exists(BONAFIDE_AUDIO_DIR):
        print(f"[ERROR] Bonafide audio directory not found: {BONAFIDE_AUDIO_DIR}")
        return
    
    if not os.path.exists(SPOOF_AUDIO_DIR):
        print(f"[ERROR] Spoof audio directory not found: {SPOOF_AUDIO_DIR}")
        return
    
    # Count available samples
    real_files = list(Path(BONAFIDE_AUDIO_DIR).glob('*.wav'))
    fake_files = list(Path(SPOOF_AUDIO_DIR).glob('*.wav'))
    
    print(f"[INFO] Available real samples: {len(real_files):,}")
    print(f"[INFO] Available fake samples: {len(fake_files):,}")
    
    # Determine actual number of samples
    max_real = args.max_real_samples if args.max_real_samples != -1 else len(real_files)
    max_fake = args.max_fake_samples if args.max_fake_samples != -1 else len(fake_files)
    max_real = min(max_real, len(real_files))
    max_fake = min(max_fake, len(fake_files))
    
    print(f"[INFO] Using {max_real:,} real samples and {max_fake:,} fake samples")
    
    # Estimate time
    total_samples = max_real + max_fake
    estimated_minutes = (total_samples * 3) / 60
    print(f"[INFO] Estimated feature extraction time: ~{estimated_minutes:.1f} minutes ({estimated_minutes/60:.1f} hours)")
    print()
    
    # Extract features from real samples
    print("\n[STEP 1] Extracting environmental features from REAL (bonafide) samples...")
    start_time = time.time()
    X_real, y_real, files_real = extract_from_audio_dir(
        BONAFIDE_AUDIO_DIR,
        label=0,  # 0 = real
        max_samples=max_real,
        desc="Extracting from real samples"
    )
    
    if X_real is None:
        print("[ERROR] Failed to extract features from real samples")
        return
    
    # Extract features from fake samples
    print("\n[STEP 2] Extracting environmental features from FAKE (spoof) samples...")
    X_fake, y_fake, files_fake = extract_from_audio_dir(
        SPOOF_AUDIO_DIR,
        label=1,  # 1 = fake
        max_samples=max_fake,
        desc="Extracting from fake samples"
    )
    
    if X_fake is None:
        print("[ERROR] Failed to extract features from fake samples")
        return
    
    extraction_time = time.time() - start_time
    print(f"\n[TIME] Feature extraction completed in {extraction_time/60:.1f} minutes")
    
    # Combine datasets
    print("\n[STEP 3] Combining datasets...")
    X = np.vstack([X_real, X_fake])
    y = np.hstack([y_real, y_fake])
    
    print(f"[OK] Combined dataset: {len(X):,} samples, {X.shape[1]} features")
    print(f"[INFO] Real samples: {np.sum(y == 0):,} ({np.sum(y == 0)/len(y)*100:.1f}%)")
    print(f"[INFO] Fake samples: {np.sum(y == 1):,} ({np.sum(y == 1)/len(y)*100:.1f}%)")
    
    # Split into train/test
    print("\n[STEP 4] Splitting into train/test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )
    
    print(f"[OK] Train set: {len(X_train):,} samples")
    print(f"[OK] Test set: {len(X_test):,} samples")
    
    # Normalize features
    print("\n[STEP 5] Normalizing features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("[OK] Features normalized")
    
    # Train Random Forest classifier
    print("\n[STEP 6] Training Random Forest classifier...")
    print(f"[INFO] n_estimators: {args.n_estimators}, max_depth: {args.max_depth}")
    
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        verbose=1
    )
    
    model.fit(X_train_scaled, y_train)
    print("[OK] Model trained!")
    
    # Evaluate on test set
    print("\n[STEP 7] Evaluating on test set...")
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]  # Probability of fake
    
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print("\n" + "="*80)
    print("TEST SET RESULTS")
    print("="*80)
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"AUC-ROC: {auc:.3f}")
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives (Real predicted as Real):  {tn}")
    print(f"  False Positives (Real predicted as Fake): {fp}")
    print(f"  False Negatives (Fake predicted as Real): {fn}")
    print(f"  True Positives (Fake predicted as Fake):  {tp}")
    print(f"\n  Precision (Fake): {tp/(tp+fp)*100:.1f}%")
    print(f"  Recall (Fake):    {tp/(tp+fn)*100:.1f}%")
    print("="*80)
    
    # Feature importance
    print("\n[STEP 8] Feature importance analysis...")
    feature_names = [
        'rt60', 'drr', 'snr', 'background_level', 'silence_ratio',
        'spectral_tilt', 'spectral_flatness', 'spectral_rolloff',
        'cleanliness_score', 'high_freq_content', 'background_consistency', 'env_stability'
    ]
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\nTop features by importance:")
    for i, idx in enumerate(indices[:5]):
        print(f"  {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
    
    # Save model
    print("\n[STEP 9] Saving model...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    model_path = os.path.join(OUTPUT_DIR, MODEL_NAME)
    scaler_path = os.path.join(OUTPUT_DIR, SCALER_NAME)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"[SAVE] Model saved: {model_path}")
    print(f"[SAVE] Scaler saved: {scaler_path}")
    
    # Test on Trump audios
    print("\n[STEP 10] Testing on Trump audios...")
    test_dir = r"E:\FYP\testing_audios"
    if os.path.exists(test_dir):
        X_trump, y_trump, trump_files = extract_from_audio_dir(
            test_dir, label=-1, max_samples=None, desc="Extracting from Trump audios"
        )
        
        if X_trump is not None:
            X_trump_scaled = scaler.transform(X_trump)
            trump_pred = model.predict(X_trump_scaled)
            trump_proba = model.predict_proba(X_trump_scaled)[:, 1]
            
            print("\n" + "="*80)
            print("TRUMP AUDIO TEST RESULTS")
            print("="*80)
            
            correct_count = 0
            for i, filename in enumerate(trump_files):
                pred_label = "FAKE" if trump_pred[i] == 1 else "REAL"
                proba = trump_proba[i]
                
                # Determine actual label
                actual = "REAL" if 'r' in filename.lower() and 'trump_r' in filename.lower() else "FAKE"
                correct = "✅" if pred_label == actual else "❌"
                if pred_label == actual:
                    correct_count += 1
                
                print(f"{correct} {filename:20s} | Predicted: {pred_label:4s} ({proba:.3f}) | Actual: {actual}")
            
            accuracy_trump = correct_count / len(trump_files) * 100
            print("\n" + "="*80)
            print(f"[RESULTS] Accuracy on Trump test: {correct_count}/{len(trump_files)} = {accuracy_trump:.1f}%")
            print("="*80)
    else:
        print(f"[INFO] Trump test directory not found: {test_dir}")
    
    print("\n" + "="*80)
    print("[SUCCESS] Environmental classifier training complete!")
    print("="*80)
    print(f"\n[SUMMARY]")
    print(f"  - Training samples: {len(X_train):,} (Real: {np.sum(y_train == 0):,}, Fake: {np.sum(y_train == 1):,})")
    print(f"  - Test accuracy: {accuracy*100:.2f}%")
    print(f"  - Test AUC-ROC: {auc:.3f}")
    print(f"  - Model saved: {os.path.join(OUTPUT_DIR, MODEL_NAME)}")
    print(f"\nNext step: Combine with ResNet CNN for hybrid detection")


if __name__ == "__main__":
    main()

