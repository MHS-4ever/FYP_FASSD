"""
Generate Fake Audio using TTS Models for Phase 0 Data Collection

Generates synthetic speech using TTS models to create fake audio samples.

Usage:
    python generate_fake_audio.py --num_clips 3000 --output_dir data/realworld/synthetic
"""

import argparse
import os
import json
from pathlib import Path
from tqdm import tqdm
import numpy as np
import soundfile as sf


def load_sentences(corpus_path=None):
    """Load sentences for TTS generation."""
    if corpus_path and os.path.exists(corpus_path):
        with open(corpus_path, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]
    else:
        # Default sentences (mix of English and Urdu-like patterns)
        sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "Hello, how are you today?",
            "This is a test of the text to speech system.",
            "Artificial intelligence is transforming the world.",
            "Deep learning models can generate realistic speech.",
            "Voice synthesis technology has advanced significantly.",
            "Audio deepfake detection is an important research area.",
            "Machine learning requires large amounts of data.",
            "Natural language processing enables many applications.",
            "Computer vision and speech recognition are key AI fields.",
        ] * 50  # Repeat to get more sentences
    
    return sentences


def generate_with_xtts(text, speaker_id, output_path, model=None):
    """
    Generate speech using XTTS v2 (Coqui TTS).
    
    Note: This is a placeholder. Actual implementation requires:
    - pip install TTS
    - Download XTTS model
    """
    try:
        from TTS.api import TTS
        
        if model is None:
            # Initialize TTS model
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        else:
            tts = model
        
        # Generate speech
        tts.tts_to_file(
            text=text,
            speaker_wav=None,  # Use default voice or provide reference
            language="en",
            file_path=output_path
        )
        return True
    except ImportError:
        print("[WARN] TTS library not installed. Install with: pip install TTS")
        return False
    except Exception as e:
        print(f"[ERROR] TTS generation failed: {e}")
        return False


def generate_with_tortoise(text, output_path, voice="random"):
    """
    Generate speech using Tortoise TTS.
    
    Note: This is a placeholder. Actual implementation requires:
    - pip install tortoise-tts
    - Download Tortoise model
    """
    try:
        import tortoise.api
        
        tts = tortoise.api.TextToSpeech()
        gen, dbg_state = tts.tts_with_preset(
            text,
            voice_samples=None,
            conditioning_latents=None,
            preset="fast",
            k=1,
            use_deterministic_seed=42
        )
        
        # Save audio
        import torchaudio
        torchaudio.save(output_path, gen.squeeze(0).cpu(), 24000)
        return True
    except ImportError:
        print("[WARN] Tortoise TTS not installed. Install with: pip install tortoise-tts")
        return False
    except Exception as e:
        print(f"[ERROR] Tortoise generation failed: {e}")
        return False


def simulate_replay_attack(original_audio_path, output_path):
    """
    Simulate replay attack by adding noise, compression, and room reverb.
    
    This creates fake audio that simulates recording a playback.
    """
    try:
        import librosa
        import soundfile as sf
        
        # Load original
        y, sr = librosa.load(original_audio_path, sr=16000)
        
        # Add noise
        noise_level = np.random.uniform(0.01, 0.05)
        noise = np.random.normal(0, noise_level, len(y))
        y = y + noise
        
        # Simulate compression artifacts
        y = np.clip(y, -0.95, 0.95)  # Clipping
        
        # Add simple reverb (simplified)
        # In practice, use pyroomacoustics for proper RIR
        reverb = np.zeros_like(y)
        delay = int(sr * 0.03)  # 30ms delay
        reverb[delay:] = y[:-delay] * 0.3
        y = y + reverb
        
        # Normalize
        y = y / (np.max(np.abs(y)) + 1e-6)
        
        # Save
        sf.write(output_path, y, sr)
        return True
    except Exception as e:
        print(f"[ERROR] Replay simulation failed: {e}")
        return False


def generate_fake_clips(num_clips, output_dir, method="xtts", sentences=None, voices=None):
    """
    Generate fake audio clips using TTS.
    
    Args:
        num_clips: Number of clips to generate
        output_dir: Output directory
        method: TTS method ("xtts", "tortoise", or "simple")
        sentences: List of sentences to use
        voices: List of voice IDs to use
    """
    os.makedirs(output_dir, exist_ok=True)
    
    tts_dir = os.path.join(output_dir, "tts")
    replay_dir = os.path.join(output_dir, "replay")
    os.makedirs(tts_dir, exist_ok=True)
    os.makedirs(replay_dir, exist_ok=True)
    
    if sentences is None:
        sentences = load_sentences()
    
    if voices is None:
        voices = ["voice1", "voice2", "voice3", "voice4", "voice5"]
    
    generated = []
    failed = 0
    
    # Initialize TTS model (if using XTTS)
    tts_model = None
    if method == "xtts":
        try:
            from TTS.api import TTS
            tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
            print("[OK] XTTS model loaded")
        except:
            print("[WARN] XTTS not available, using simple method")
            method = "simple"
    
    for i in tqdm(range(num_clips), desc="Generating fake audio"):
        # Select random sentence and voice
        sentence = np.random.choice(sentences)
        voice = np.random.choice(voices)
        
        # Generate TTS audio
        tts_path = os.path.join(tts_dir, f"fake_tts_{i:05d}.wav")
        
        success = False
        if method == "xtts" and tts_model:
            success = generate_with_xtts(sentence, voice, tts_path, tts_model)
        elif method == "tortoise":
            success = generate_with_tortoise(sentence, tts_path, voice)
        else:
            # Simple placeholder: generate silence (user should replace with actual TTS)
            # In practice, this should call actual TTS
            print(f"[WARN] Simple method: generating placeholder for clip {i}")
            # Create a simple sine wave as placeholder
            duration = 3.0  # 3 seconds
            sr = 16000
            t = np.linspace(0, duration, int(sr * duration))
            # Simple speech-like signal (placeholder)
            audio = np.sin(2 * np.pi * 200 * t) * np.exp(-t)  # Decaying tone
            sf.write(tts_path, audio, sr)
            success = True
        
        if success:
            generated.append(tts_path)
            
            # Create replay version (simulate recording of playback)
            if i < num_clips // 2:  # Generate replay for half
                replay_path = os.path.join(replay_dir, f"fake_replay_{i:05d}.wav")
                if simulate_replay_attack(tts_path, replay_path):
                    generated.append(replay_path)
        else:
            failed += 1
    
    print(f"[OK] Generated {len(generated)} fake audio clips")
    if failed > 0:
        print(f"[WARN] Failed to generate {failed} clips")
    
    return generated


def main():
    parser = argparse.ArgumentParser("Generate Fake Audio for Phase 0")
    parser.add_argument("--num_clips", type=int, default=3000,
                       help="Number of fake clips to generate")
    parser.add_argument("--output_dir", type=str, 
                       default="data/realworld/synthetic",
                       help="Output directory")
    parser.add_argument("--method", type=str, default="xtts",
                       choices=["xtts", "tortoise", "simple"],
                       help="TTS method to use")
    parser.add_argument("--corpus", type=str, default=None,
                       help="Path to text corpus file (one sentence per line)")
    parser.add_argument("--voices", type=str, nargs="+", default=None,
                       help="List of voice IDs to use")
    
    args = parser.parse_args()
    
    print(f"[INFO] Generating {args.num_clips} fake audio clips")
    print(f"[INFO] Method: {args.method}")
    print(f"[INFO] Output: {args.output_dir}")
    
    # Load sentences
    sentences = load_sentences(args.corpus) if args.corpus else None
    
    # Generate clips
    generated = generate_fake_clips(
        args.num_clips,
        args.output_dir,
        method=args.method,
        sentences=sentences,
        voices=args.voices
    )
    
    # Save metadata
    metadata = {
        "num_clips": len(generated),
        "method": args.method,
        "output_dir": args.output_dir
    }
    
    metadata_path = os.path.join(args.output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[OK] Metadata saved to: {metadata_path}")
    print(f"[OK] Fake audio generation complete!")


if __name__ == "__main__":
    main()

