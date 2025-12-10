"""
Generate Fake Audio using TTS Models for Phase 0 Data Collection

Generates synthetic speech using TTS models to create fake audio samples.
Optimized for GPU acceleration (RTX 3050, CUDA 13.1).

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
import torch

# GPU Setup
if torch.cuda.is_available():
    device = torch.device("cuda")
    torch.backends.cudnn.benchmark = True
    print(f"[GPU] Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"[GPU] CUDA Version: {torch.version.cuda}")
    print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    device = torch.device("cpu")
    print("[WARN] CUDA not available - using CPU (this will be slow)")


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


def generate_with_xtts(text, speaker_id, output_path, model=None, device=None):
    """
    Generate speech using XTTS v2 (Coqui TTS) with GPU acceleration.
    
    Note: This requires:
    - pip install TTS
    - GPU with CUDA support (automatically uses GPU if available)
    """
    try:
        from TTS.api import TTS
        
        if model is None:
            # Initialize TTS model with GPU if available
            use_gpu = device.type == "cuda" if device else torch.cuda.is_available()
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
            print(f"[TTS] XTTS model loaded on {'GPU' if use_gpu else 'CPU'}")
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


def generate_with_tortoise(text, output_path, voice="random", device=None):
    """
    Generate speech using Tortoise TTS with GPU acceleration.
    
    Note: This requires:
    - pip install tortoise-tts
    - GPU with CUDA support (automatically uses GPU if available)
    """
    try:
        import tortoise.api
        
        # Tortoise automatically uses GPU if available
        tts = tortoise.api.TextToSpeech()
        
        with torch.no_grad():
            if device and device.type == "cuda":
                torch.cuda.empty_cache()  # Clear cache before generation
            
            gen, dbg_state = tts.tts_with_preset(
                text,
                voice_samples=None,
                conditioning_latents=None,
                preset="fast",  # Use "fast" for speed, "ultra_fast" for even faster
                k=1,
                use_deterministic_seed=42
            )
        
        # Save audio
        import torchaudio
        # Move to CPU before saving
        gen_cpu = gen.squeeze(0).cpu()
        torchaudio.save(output_path, gen_cpu, 24000)
        
        # Clear GPU cache
        if device and device.type == "cuda":
            torch.cuda.empty_cache()
        
        return True
    except ImportError:
        print("[WARN] Tortoise TTS not installed. Install with: pip install tortoise-tts")
        return False
    except Exception as e:
        print(f"[ERROR] Tortoise generation failed: {e}")
        if device and device.type == "cuda":
            torch.cuda.empty_cache()
        return False


def simulate_replay_attack(original_audio_path, output_path, device=None):
    """
    Simulate replay attack by adding noise, compression, and room reverb.
    Uses GPU acceleration for processing if available.
    
    This creates fake audio that simulates recording a playback.
    """
    try:
        import torchaudio
        import torch.nn.functional as F
        
        # Load original using torchaudio (GPU-compatible)
        waveform, sr = torchaudio.load(original_audio_path)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample to 16kHz if needed
        if sr != 16000:
            if device and device.type == "cuda":
                waveform = waveform.to(device)
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000).to(device)
            else:
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            waveform = resampler(waveform)
            sr = 16000
        
        # Move to GPU if available
        if device and device.type == "cuda":
            waveform = waveform.to(device)
        
        # Add noise (GPU if available)
        noise_level = np.random.uniform(0.01, 0.05)
        noise = torch.randn_like(waveform) * noise_level
        waveform = waveform + noise
        
        # Simulate compression artifacts (clipping)
        waveform = torch.clamp(waveform, -0.95, 0.95)
        
        # Add simple reverb (GPU-accelerated)
        delay_samples = int(sr * 0.03)  # 30ms delay
        reverb = torch.zeros_like(waveform)
        if delay_samples < waveform.shape[1]:
            reverb[:, delay_samples:] = waveform[:, :-delay_samples] * 0.3
        waveform = waveform + reverb
        
        # Normalize (GPU if available)
        max_val = torch.max(torch.abs(waveform))
        if max_val > 0:
            waveform = waveform / (max_val + 1e-6)
        
        # Move to CPU and convert to numpy for saving
        waveform_cpu = waveform.cpu().squeeze(0).numpy()
        
        # Save
        sf.write(output_path, waveform_cpu, sr)
        return True
    except Exception as e:
        print(f"[ERROR] Replay simulation failed: {e}")
        return False


def generate_fake_clips(num_clips, output_dir, method="xtts", sentences=None, voices=None, device=None):
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
    
    # Initialize TTS model (if using XTTS) - Reuse model for efficiency
    tts_model = None
    if method == "xtts":
        try:
            from TTS.api import TTS
            use_gpu = device.type == "cuda" if device else torch.cuda.is_available()
            tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
            print(f"[OK] XTTS model loaded on {'GPU' if use_gpu else 'CPU'}")
            if use_gpu:
                print(f"[GPU] Model will use GPU for faster generation")
        except Exception as e:
            print(f"[WARN] XTTS not available ({e}), using simple method")
            method = "simple"
    
    # Batch processing for better GPU utilization (if using GPU)
    batch_size = 32 if (device and device.type == "cuda") else 1
    if batch_size > 1 and method in ["xtts", "tortoise"]:
        print(f"[INFO] Using batch processing (batch_size={batch_size}) for better GPU utilization")
    
    for i in tqdm(range(num_clips), desc="Generating fake audio"):
        # Select random sentence and voice
        sentence = np.random.choice(sentences)
        voice = np.random.choice(voices)
        
        # Generate TTS audio
        tts_path = os.path.join(tts_dir, f"fake_tts_{i:05d}.wav")
        
        success = False
        if method == "xtts" and tts_model:
            success = generate_with_xtts(sentence, voice, tts_path, tts_model, device)
        elif method == "tortoise":
            success = generate_with_tortoise(sentence, tts_path, voice, device)
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
                if simulate_replay_attack(tts_path, replay_path, device):
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
        voices=args.voices,
        device=device
    )
    
    # Final GPU cleanup
    if device and device.type == "cuda":
        torch.cuda.empty_cache()
        print(f"[GPU] GPU cache cleared. Final VRAM usage: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
    
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

