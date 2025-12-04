"""
Analyze environmental features of Trump audio files.
This will show the differences between real and AI-generated audio.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from pathlib import Path
from features.environmental_features import EnvironmentalFeatureExtractor

# Paths
AUDIO_DIR = r"E:\FYP\testing_audios"
OUTPUT_CSV = r"E:\FYP\reports\tests\environmental_analysis.csv"

def main():
    print("[INFO] Analyzing Trump audio environmental features...\n")
    
    # Find audio files
    audio_files = []
    for ext in ['.wav', '.mp3', '.flac']:
        audio_files.extend(Path(AUDIO_DIR).glob(f'*{ext}'))
    
    if not audio_files:
        print(f"[ERROR] No audio files found in {AUDIO_DIR}")
        return
    
    print(f"[INFO] Found {len(audio_files)} audio files\n")
    
    # Extract features
    extractor = EnvironmentalFeatureExtractor()
    results = []
    
    for audio_path in sorted(audio_files):
        print(f"\nAnalyzing: {audio_path.name}")
        print("-" * 80)
        
        features = extractor.extract_all(str(audio_path))
        features['filename'] = audio_path.name
        
        # Determine if features suggest real or fake
        suspicious_indicators = 0
        
        if features['snr'] > 45:
            suspicious_indicators += 1
            print("  ⚠️ SNR too high (too clean)")
        
        if features['background_level'] < -70:
            suspicious_indicators += 1
            print("  ⚠️ Background too quiet")
        
        if features['cleanliness_score'] > 0.6:
            suspicious_indicators += 1
            print("  ⚠️ Audio suspiciously clean")
        
        if features['rt60'] < 0.05:
            suspicious_indicators += 1
            print("  ⚠️ No natural reverberation")
        
        if suspicious_indicators == 0:
            print("  ✅ Environmental features appear natural")
        
        features['suspicious_indicators'] = suspicious_indicators
        features['env_suggests'] = 'FAKE' if suspicious_indicators >= 2 else 'REAL'
        
        results.append(features)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Reorder columns
    cols = ['filename', 'env_suggests', 'suspicious_indicators', 'cleanliness_score', 
            'snr', 'background_level', 'rt60', 'drr', 'background_consistency',
            'env_stability', 'spectral_tilt', 'spectral_flatness', 'spectral_rolloff',
            'silence_ratio', 'high_freq_content']
    df = df[cols]
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "="*80)
    print("ENVIRONMENTAL ANALYSIS SUMMARY")
    print("="*80)
    print(df[['filename', 'env_suggests', 'suspicious_indicators', 'cleanliness_score', 'snr']].to_string(index=False))
    
    print(f"\n[SAVE] Detailed results saved to: {OUTPUT_CSV}")
    
    # Compare real vs fake files
    real_files = [f for f in df['filename'] if 'r' in f and 'trump_r' in f]
    fake_files = [f for f in df['filename'] if 'f' in f and 'trump_f' in f]
    
    if real_files and fake_files:
        print("\n" + "="*80)
        print("COMPARISON: Real vs AI-Generated")
        print("="*80)
        
        real_df = df[df['filename'].isin(real_files)]
        fake_df = df[df['filename'].isin(fake_files)]
        
        print(f"\nReal Audio (n={len(real_df)}):")
        print(f"  Avg SNR:             {real_df['snr'].mean():.1f} dB")
        print(f"  Avg Cleanliness:     {real_df['cleanliness_score'].mean():.2%}")
        print(f"  Avg RT60:            {real_df['rt60'].mean():.3f} sec")
        print(f"  Env suggests REAL:   {(real_df['env_suggests']=='REAL').sum()}/{len(real_df)}")
        
        print(f"\nAI-Generated Audio (n={len(fake_df)}):")
        print(f"  Avg SNR:             {fake_df['snr'].mean():.1f} dB")
        print(f"  Avg Cleanliness:     {fake_df['cleanliness_score'].mean():.2%}")
        print(f"  Avg RT60:            {fake_df['rt60'].mean():.3f} sec")
        print(f"  Env suggests FAKE:   {(fake_df['env_suggests']=='FAKE').sum()}/{len(fake_df)}")
    
    print("\n" + "="*80)
    print("[OK] Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()

