"""
Environmental Acoustic Feature Extraction for Deepfake Detection

Extracts environmental characteristics that distinguish real recordings
from AI-generated audio:
- Real: Natural room acoustics, background noise, mic imperfections
- AI: Too clean, missing ambience, unnatural reverb
"""

import numpy as np
import librosa
import scipy.signal as signal
from scipy.stats import entropy


class EnvironmentalFeatureExtractor:
    """
    Extract environmental acoustic features that AI struggles to replicate.
    """
    
    def __init__(self, sr=16000):
        self.sr = sr
    
    def extract_all(self, audio_path):
        """
        Extract all environmental features from audio file.
        
        Returns:
            dict: Dictionary of environmental features
        """
        # Load audio
        y, _ = librosa.load(audio_path, sr=self.sr)
        
        features = {}
        
        # 1. Room Acoustics
        features['rt60'] = self.compute_rt60(y)
        features['drr'] = self.compute_drr(y)
        
        # 2. Background Noise Analysis
        features['snr'] = self.compute_snr(y)
        features['background_level'] = self.compute_background_level(y)
        features['silence_ratio'] = self.compute_silence_ratio(y)
        
        # 3. Spectral Characteristics
        features['spectral_tilt'] = self.compute_spectral_tilt(y)
        features['spectral_flatness'] = self.compute_spectral_flatness(y)
        features['spectral_rolloff'] = self.compute_spectral_rolloff(y)
        
        # 4. "Too Clean" Indicators (suspicious for AI)
        features['cleanliness_score'] = self.compute_cleanliness(y)
        features['high_freq_content'] = self.compute_high_freq_content(y)
        
        # 5. Temporal Consistency
        features['background_consistency'] = self.compute_background_consistency(y)
        features['env_stability'] = self.compute_env_stability(y)
        
        return features
    
    def compute_rt60(self, y):
        """
        Estimate RT60 (reverberation time) - time for sound to decay by 60dB.
        
        Real rooms: 0.2-2.0 seconds (depending on size)
        AI-generated: Often 0 or unnatural values
        """
        try:
            # Simple energy decay method
            energy = librosa.feature.rms(y=y)[0]
            energy_db = librosa.power_to_db(energy**2, ref=np.max)
            
            # Find decay time from peak to -60dB
            if len(energy_db) > 10:
                peak_idx = np.argmax(energy_db)
                if peak_idx < len(energy_db) - 1:
                    decay = energy_db[peak_idx:]
                    below_60 = np.where(decay < (np.max(decay) - 60))[0]
                    if len(below_60) > 0:
                        rt60_frames = below_60[0]
                        rt60_seconds = rt60_frames * 512 / self.sr  # Hop length
                        return float(rt60_seconds)
            
            return 0.0  # No measurable decay
        except:
            return 0.0
    
    def compute_drr(self, y):
        """
        Direct-to-Reverberant Ratio.
        
        High DRR: Direct sound dominates (studio/close-mic)
        Low DRR: Reverb dominates (large room)
        """
        try:
            # Use autocorrelation to estimate direct vs reverberant energy
            autocorr = librosa.autocorrelate(y)
            if len(autocorr) > 100:
                direct_energy = np.sum(autocorr[:50])
                reverb_energy = np.sum(autocorr[50:200])
                drr = direct_energy / max(reverb_energy, 1e-6)
                return float(np.log10(drr + 1))
            return 0.0
        except:
            return 0.0
    
    def compute_snr(self, y):
        """
        Signal-to-Noise Ratio.
        
        Real recordings: 15-40 dB (some background noise)
        AI-generated: Often >50 dB (too clean - SUSPICIOUS)
        """
        try:
            # Detect voice activity using energy threshold
            rms = librosa.feature.rms(y=y)[0]
            threshold = np.percentile(rms, 30)  # Bottom 30% is likely silence/noise
            
            noise_frames = rms < threshold
            signal_frames = rms >= threshold
            
            if np.sum(noise_frames) > 0 and np.sum(signal_frames) > 0:
                noise_power = np.mean(rms[noise_frames]**2)
                signal_power = np.mean(rms[signal_frames]**2)
                snr = 10 * np.log10(signal_power / max(noise_power, 1e-10))
                return float(snr)
            
            return 100.0  # No noise detected (VERY suspicious!)
        except:
            return 100.0
    
    def compute_background_level(self, y):
        """
        Average background noise level.
        
        Real: -40 to -60 dB
        AI: Often < -80 dB (nearly silent - suspicious)
        """
        try:
            rms = librosa.feature.rms(y=y)[0]
            background = np.percentile(rms, 20)  # Bottom 20% energy
            background_db = librosa.amplitude_to_db([background])[0]
            return float(background_db)
        except:
            return -100.0
    
    def compute_silence_ratio(self, y):
        """
        Ratio of silence to total duration.
        
        Real: Usually has some silence/pauses (0.1-0.3)
        AI: Often continuous speech or perfect silence
        """
        try:
            rms = librosa.feature.rms(y=y)[0]
            threshold = np.percentile(rms, 10)
            silence_ratio = np.sum(rms < threshold) / len(rms)
            return float(silence_ratio)
        except:
            return 0.0
    
    def compute_spectral_tilt(self, y):
        """
        Spectral tilt - slope of frequency spectrum.
        
        Natural voices: Negative tilt (higher freqs quieter)
        Some AI: Unnatural tilt pattern
        """
        try:
            spec = np.abs(librosa.stft(y))
            avg_spectrum = np.mean(spec, axis=1)
            
            # Compute slope in log-log space
            freqs = librosa.fft_frequencies(sr=self.sr)
            log_freqs = np.log10(freqs[1:] + 1)
            log_mags = np.log10(avg_spectrum[1:] + 1e-10)
            
            # Linear regression to get slope
            slope = np.polyfit(log_freqs, log_mags, 1)[0]
            return float(slope)
        except:
            return 0.0
    
    def compute_spectral_flatness(self, y):
        """
        Spectral flatness (Wiener entropy).
        
        High flatness: Noise-like (natural background)
        Low flatness: Tonal (pure synthetic voice)
        """
        try:
            flatness = librosa.feature.spectral_flatness(y=y)
            return float(np.mean(flatness))
        except:
            return 0.0
    
    def compute_spectral_rolloff(self, y):
        """
        Frequency below which 85% of energy is contained.
        
        Natural speech: 2000-4000 Hz
        Some AI: Unusual rolloff patterns
        """
        try:
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=self.sr, roll_percent=0.85)
            return float(np.mean(rolloff))
        except:
            return 0.0
    
    def compute_cleanliness(self, y):
        """
        "Cleanliness" score - how perfect/clean the audio is.
        
        Too clean = SUSPICIOUS (likely AI-generated)
        Some imperfections = NORMAL (likely real)
        
        Combines: High SNR + Low background + Perfect silence
        """
        snr = self.compute_snr(y)
        bg_level = self.compute_background_level(y)
        
        # Scoring: Higher = more suspicious
        cleanliness = 0.0
        
        if snr > 50:  # Extremely high SNR
            cleanliness += 0.4
        elif snr > 40:
            cleanliness += 0.2
        
        if bg_level < -70:  # Nearly silent background
            cleanliness += 0.3
        elif bg_level < -60:
            cleanliness += 0.15
        
        # Check for unnatural silence patterns
        rms = librosa.feature.rms(y=y)[0]
        near_zero = np.sum(rms < 1e-4) / len(rms)
        if near_zero > 0.3:  # >30% of frames are nearly silent
            cleanliness += 0.3
        
        return float(min(cleanliness, 1.0))
    
    def compute_high_freq_content(self, y):
        """
        High frequency content ratio.
        
        Real: Natural rolloff, less high-freq content
        Some AI: Unnatural high-freq characteristics
        """
        try:
            spec = np.abs(librosa.stft(y))
            
            # Split spectrum into low and high freq
            mid_point = spec.shape[0] // 2
            low_energy = np.sum(spec[:mid_point]**2)
            high_energy = np.sum(spec[mid_point:]**2)
            
            high_ratio = high_energy / max(low_energy + high_energy, 1e-10)
            return float(high_ratio)
        except:
            return 0.0
    
    def compute_background_consistency(self, y):
        """
        How consistent is the background noise throughout recording.
        
        Real: Fairly consistent background
        Edited/fake: Inconsistent or too perfect
        """
        try:
            # Divide audio into segments
            segment_length = self.sr * 2  # 2-second segments
            n_segments = len(y) // segment_length
            
            if n_segments < 2:
                return 0.5  # Too short to assess
            
            background_levels = []
            for i in range(n_segments):
                start = i * segment_length
                end = start + segment_length
                segment = y[start:end]
                
                rms = librosa.feature.rms(y=segment)[0]
                bg_level = np.percentile(rms, 20)
                background_levels.append(bg_level)
            
            # Compute coefficient of variation
            if np.mean(background_levels) > 1e-6:
                cv = np.std(background_levels) / np.mean(background_levels)
                consistency = 1.0 / (1.0 + cv)  # Lower CV = more consistent
                return float(consistency)
            
            return 0.0
        except:
            return 0.5
    
    def compute_env_stability(self, y):
        """
        Environmental stability - how stable is the acoustic environment.
        
        Real: Relatively stable with natural variations
        Synthetic: Too stable (suspicious) or inconsistent
        """
        try:
            # Compute spectral centroids over time
            centroids = librosa.feature.spectral_centroid(y=y, sr=self.sr)[0]
            
            # Measure variation
            centroid_std = np.std(centroids)
            centroid_mean = np.mean(centroids)
            
            if centroid_mean > 0:
                variation = centroid_std / centroid_mean
                # Natural speech: moderate variation (0.1-0.3)
                # Too stable (<0.05) or too variable (>0.5) is suspicious
                if 0.05 < variation < 0.5:
                    stability = 1.0
                else:
                    stability = 0.5
                return float(stability)
            
            return 0.5
        except:
            return 0.5
    
    def extract_vector(self, audio_path):
        """
        Extract features as a numerical vector for ML models.
        
        Returns:
            numpy array: 12-dimensional feature vector
        """
        features = self.extract_all(audio_path)
        
        vector = np.array([
            features['rt60'],
            features['drr'],
            features['snr'],
            features['background_level'],
            features['silence_ratio'],
            features['spectral_tilt'],
            features['spectral_flatness'],
            features['spectral_rolloff'] / 1000.0,  # Normalize
            features['cleanliness_score'],
            features['high_freq_content'],
            features['background_consistency'],
            features['env_stability']
        ], dtype=np.float32)
        
        return vector


def analyze_audio(audio_path, verbose=True):
    """
    Analyze single audio file and print environmental characteristics.
    Useful for debugging and understanding differences.
    """
    extractor = EnvironmentalFeatureExtractor()
    features = extractor.extract_all(audio_path)
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Environmental Analysis: {os.path.basename(audio_path)}")
        print(f"{'='*80}")
        
        print("\n🏠 ROOM ACOUSTICS:")
        print(f"  RT60 (reverberation):    {features['rt60']:.3f} seconds")
        print(f"  Direct-Reverb Ratio:     {features['drr']:.3f}")
        
        print("\n🔊 BACKGROUND NOISE:")
        print(f"  SNR:                     {features['snr']:.1f} dB", end="")
        if features['snr'] > 50:
            print(" ⚠️ SUSPICIOUS (too clean)")
        else:
            print(" ✅ Normal")
        
        print(f"  Background Level:        {features['background_level']:.1f} dB")
        print(f"  Silence Ratio:           {features['silence_ratio']:.2%}")
        
        print("\n📊 SPECTRAL CHARACTERISTICS:")
        print(f"  Spectral Tilt:           {features['spectral_tilt']:.4f}")
        print(f"  Spectral Flatness:       {features['spectral_flatness']:.4f}")
        print(f"  Spectral Rolloff:        {features['spectral_rolloff']:.1f} Hz")
        
        print("\n🎯 ANOMALY INDICATORS:")
        print(f"  Cleanliness Score:       {features['cleanliness_score']:.2%}", end="")
        if features['cleanliness_score'] > 0.6:
            print(" ⚠️ SUSPICIOUS (too perfect)")
        else:
            print(" ✅ Normal")
        
        print(f"  Background Consistency:  {features['background_consistency']:.2%}")
        print(f"  Environment Stability:   {features['env_stability']:.2%}")
        
        print(f"\n{'='*80}\n")
    
    return features


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test on provided audio file
        audio_file = sys.argv[1]
        analyze_audio(audio_file)
    else:
        print("Usage: python environmental_features.py <audio_file>")
        print("Example: python environmental_features.py ../testing_audios/trump_r1.mp3")

