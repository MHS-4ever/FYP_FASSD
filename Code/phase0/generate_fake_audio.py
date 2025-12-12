"""
Generate Fake Audio using TTS Models for Phase 0 Data Collection

Generates synthetic speech using TTS models to create fake audio samples.
Optimized for GPU acceleration (RTX 3050, CUDA 13.1).

⚠️ ENVIRONMENT REQUIREMENT:
    - For --method xtts or --method tortoise: MUST use 'ttsgen' conda environment
    - For --method simple: Can use 'fassd' conda environment

Usage:
    # From ttsgen environment (for xtts/tortoise):
    conda activate ttsgen
    python generate_fake_audio.py --num_clips 3000 --method xtts --output_dir data/realworld/synthetic
    
    # From fassd environment (for simple method only):
    conda activate fassd
    python generate_fake_audio.py --num_clips 3000 --method simple --output_dir data/realworld/synthetic
"""

import argparse
import os
import json
import csv
from pathlib import Path
from tqdm import tqdm
import numpy as np
import soundfile as sf
import torch

# Set deterministic seed for reproducibility
torch.manual_seed(42)
np.random.seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)

# Standard target sample rate for forensic pipelines
TARGET_SR = 16000

# Patch torch.load for PyTorch 2.6+ compatibility with TTS library
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# GPU Setup
if torch.cuda.is_available():
    device = torch.device("cuda")
    torch.backends.cudnn.benchmark = True
    print(f"[GPU] Using GPU: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("[WARN] CUDA not available - using CPU (this will be slow)")


def load_sentences(corpus_path=None):
    """Load sentences for TTS generation."""
    if corpus_path and os.path.exists(corpus_path):
        with open(corpus_path, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]
    else:
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
        ] * 50
    
    return sentences


def generate_with_xtts(text, output_path, model=None, speaker_wav_path=None):
    """Generate speech using XTTS v2 (Coqui TTS) with GPU acceleration."""
    try:
        from TTS.api import TTS
        
        if model is None:
            use_gpu = device.type == "cuda"
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
            print(f"[TTS] XTTS model loaded on {'GPU' if use_gpu else 'CPU'}")
        else:
            tts = model
        
        if speaker_wav_path is None or not os.path.exists(speaker_wav_path):
            raise ValueError("XTTS requires speaker_wav_path - a reference audio file is mandatory")
        
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav_path,
            language="en",
            file_path=output_path
        )
        
        # XTTS may output at different sample rates, standardize to 16kHz
        try:
            import torchaudio
            waveform, sr = torchaudio.load(output_path)
            if sr != TARGET_SR:
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=TARGET_SR)
                waveform = resampler(waveform)
                # Normalize
                max_val = torch.max(torch.abs(waveform))
                if max_val > 0:
                    waveform = waveform / (max_val + 1e-9)
                torchaudio.save(output_path, waveform, TARGET_SR)
        except Exception:
            pass  # If resampling fails, keep original
        
        return True
    except ImportError:
        print("[WARN] TTS library not installed. Install with: pip install TTS")
        return False
    except Exception as e:
        print(f"[ERROR] TTS generation failed: {e}")
        return False


def generate_with_tortoise(text, output_path, device=None):
    """Generate speech using Tortoise TTS with GPU acceleration."""
    try:
        import tortoise.api
        
        tts = tortoise.api.TextToSpeech()
        
        with torch.no_grad():
            if device and device.type == "cuda":
                torch.cuda.empty_cache()
            
            gen, dbg_state = tts.tts_with_preset(
                text,
                voice_samples=None,
                conditioning_latents=None,
                preset="fast",
                k=1,
                use_deterministic_seed=42
            )
        
        import torchaudio
        gen_cpu = gen.squeeze(0).cpu()
        # Tortoise outputs at 24kHz, resample to standard 16kHz
        if gen_cpu.shape[0] > 0:
            resampler = torchaudio.transforms.Resample(orig_freq=24000, new_freq=TARGET_SR)
            gen_cpu = resampler(gen_cpu.unsqueeze(0)).squeeze(0)
        torchaudio.save(output_path, gen_cpu, TARGET_SR)
        
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
    """Simulate replay attack by adding noise, compression, and room reverb."""
    try:
        import torchaudio
        import torch.nn.functional as F
        
        # Load audio
        waveform = None
        sr = None
        
        try:
            waveform, sr = torchaudio.load(original_audio_path)
        except Exception:
            try:
                audio_data, sr = sf.read(original_audio_path)
                if len(audio_data.shape) == 1:
                    waveform = torch.from_numpy(audio_data).unsqueeze(0)
                else:
                    waveform = torch.from_numpy(audio_data.mean(axis=1)).unsqueeze(0)
            except Exception:
                try:
                    import librosa
                    audio_data, sr = librosa.load(original_audio_path, sr=16000, mono=True)
                    waveform = torch.from_numpy(audio_data).unsqueeze(0)
                except Exception:
                    return False
        
        if waveform is None or sr is None:
            return False
        
        # Convert to mono
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
        
        # Add noise
        noise_level = np.random.uniform(0.01, 0.05)
        noise = torch.randn_like(waveform) * noise_level
        waveform = waveform + noise
        
        # Simulate compression
        waveform = torch.clamp(waveform, -0.95, 0.95)
        
        # Add simple reverb
        delay_samples = int(sr * 0.03)
        reverb = torch.zeros_like(waveform)
        if delay_samples < waveform.shape[1]:
            reverb[:, delay_samples:] = waveform[:, :-delay_samples] * 0.3
        waveform = waveform + reverb
        
        # Normalize
        max_val = torch.max(torch.abs(waveform))
        if max_val > 0:
            waveform = waveform / (max_val + 1e-6)
        
        # Save
        waveform_cpu = waveform.cpu().squeeze(0).numpy()
        sf.write(output_path, waveform_cpu, sr)
        return True
    except Exception as e:
        print(f"[ERROR] Replay simulation failed: {e}")
        return False


def create_reference_speakers(num_speakers=5, output_dir=None, device=None, real_speaker_dir=None):
    """
    Create reference speaker audio files for XTTS.
    
    IMPORTANT: For forensic validity, use real human reference clips instead of TTS-generated ones.
    If real_speaker_dir is provided and contains valid audio files, those will be used.
    Otherwise, falls back to TTS-generated references (acceptable for Phase-0 but not ideal).
    
    Args:
        num_speakers: Number of reference speakers needed
        output_dir: Directory to save reference speakers
        device: Torch device
        real_speaker_dir: Optional path to directory containing real human reference audio clips
    """
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "data", "realworld", "synthetic", "reference_speakers")
    os.makedirs(output_dir, exist_ok=True)
    
    reference_speakers = []
    
    # Try to use real human reference clips first (preferred for forensic validity)
    if real_speaker_dir and os.path.exists(real_speaker_dir):
        print(f"[INFO] Looking for real human reference speakers in: {real_speaker_dir}")
        real_refs = list(Path(real_speaker_dir).glob("*.wav"))
        if len(real_refs) >= num_speakers:
            # Use real human clips
            for i, ref_path in enumerate(real_refs[:num_speakers]):
                # Ensure 16kHz and normalize
                try:
                    import torchaudio
                    waveform, sr = torchaudio.load(str(ref_path))
                    if sr != TARGET_SR:
                        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=TARGET_SR)
                        waveform = resampler(waveform)
                    # Normalize
                    max_val = torch.max(torch.abs(waveform))
                    if max_val > 0:
                        waveform = waveform / (max_val + 1e-9)
                    # Save processed reference
                    processed_path = os.path.join(output_dir, f"reference_speaker_{i:05d}.wav")
                    torchaudio.save(processed_path, waveform, TARGET_SR)
                    reference_speakers.append(processed_path)
                except Exception as e:
                    print(f"[WARN] Could not process real reference {ref_path}: {e}")
                    continue
            
            if len(reference_speakers) >= num_speakers:
                print(f"[OK] Using {len(reference_speakers)} real human reference speakers (forensically valid)")
                return reference_speakers[:num_speakers]
            else:
                print(f"[WARN] Only found {len(reference_speakers)} valid real references, will generate rest")
    
    # Check if reference speakers already exist
    for i in range(num_speakers):
        ref_path = os.path.join(output_dir, f"reference_speaker_{i:05d}.wav")
        if os.path.exists(ref_path):
            reference_speakers.append(ref_path)
    
    if len(reference_speakers) == num_speakers:
        print(f"[OK] Using existing {len(reference_speakers)} reference speaker files")
        return reference_speakers
    
    # Generate missing reference speakers
    print(f"[INFO] Creating {num_speakers - len(reference_speakers)} reference speaker files...")
    
    try:
        from TTS.api import TTS
        
        use_gpu = device.type == "cuda" if device else torch.cuda.is_available()
        
        simple_models = [
            "tts_models/en/ljspeech/tacotron2-DDC",
            "tts_models/en/ljspeech/glow-tts",
            "tts_models/en/vctk/vits",
        ]
        
        ref_tts = None
        for model_name in simple_models:
            try:
                ref_tts = TTS(model_name=model_name, gpu=use_gpu)
                print(f"[OK] Using {model_name} for reference speaker generation")
                break
            except Exception:
                continue
        
        if ref_tts is None:
            raise Exception("Could not load any simple TTS model")
        
        reference_texts = [
            "Hello, this is a reference speaker for text to speech synthesis.",
            "This voice will be used as a reference for generating synthetic audio.",
            "The quick brown fox jumps over the lazy dog.",
            "Artificial intelligence enables voice synthesis technology.",
            "Deep learning models can generate realistic human speech.",
        ]
        
        for i in range(num_speakers):
            ref_path = os.path.join(output_dir, f"reference_speaker_{i:05d}.wav")
            if not os.path.exists(ref_path):
                ref_text = reference_texts[i % len(reference_texts)]
                try:
                    ref_tts.tts_to_file(text=ref_text, file_path=ref_path)
                    reference_speakers.append(ref_path)
                except Exception:
                    # Fallback to synthetic (not ideal for forensics but acceptable for Phase-0)
                    duration = 2.0
                    t = np.linspace(0, duration, int(TARGET_SR * duration))
                    freq = 150 + (i * 20)
                    audio = np.sin(2 * np.pi * freq * t) * np.exp(-t * 0.5)
                    # Normalize
                    audio = audio / (np.max(np.abs(audio)) + 1e-9)
                    sf.write(ref_path, audio, TARGET_SR)
                    reference_speakers.append(ref_path)
            else:
                reference_speakers.append(ref_path)
        
        print(f"[OK] Created {len(reference_speakers)} reference speaker files")
        return reference_speakers
        
    except Exception as e:
        # Fallback: create synthetic reference audio
        print(f"[WARN] Could not use TTS for reference speakers ({e}), creating synthetic references")
        print(f"[WARN] NOTE: For forensic validity, use real human reference clips from your YouTube dataset")
        for i in range(num_speakers):
            ref_path = os.path.join(output_dir, f"reference_speaker_{i:05d}.wav")
            if not os.path.exists(ref_path):
                duration = 2.0
                t = np.linspace(0, duration, int(TARGET_SR * duration))
                freq = 150 + (i * 20)
                audio = (np.sin(2 * np.pi * freq * t) + 
                        0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                        0.1 * np.sin(2 * np.pi * freq * 3 * t)) * np.exp(-t * 0.5)
                audio = audio / (np.max(np.abs(audio)) + 1e-9)
                sf.write(ref_path, audio, TARGET_SR)
            reference_speakers.append(ref_path)
        return reference_speakers


def generate_fake_clips(num_clips, output_dir, method="xtts", sentences=None, device=None, real_speaker_dir=None):
    """Generate fake audio clips using TTS and save labels CSV."""
    os.makedirs(output_dir, exist_ok=True)
    
    tts_dir = os.path.join(output_dir, "tts")
    replay_dir = os.path.join(output_dir, "replay")
    os.makedirs(tts_dir, exist_ok=True)
    os.makedirs(replay_dir, exist_ok=True)
    
    if sentences is None:
        sentences = load_sentences()
    
    generated = []
    failed = 0
    clip_metadata = []  # For CSV export
    
    # Initialize TTS model (if using XTTS)
    tts_model = None
    reference_speakers = []
    
    if method == "xtts":
        try:
            from TTS.api import TTS
            use_gpu = device.type == "cuda" if device else torch.cuda.is_available()
            tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
            print(f"[OK] XTTS model loaded on {'GPU' if use_gpu else 'CPU'}")
            
            reference_speakers = create_reference_speakers(
                num_speakers=5,
                output_dir=os.path.join(output_dir, "reference_speakers"),
                device=device,
                real_speaker_dir=real_speaker_dir
            )
        except Exception as e:
            print(f"[WARN] XTTS not available ({e}), using simple method")
            method = "simple"
    
    for i in tqdm(range(num_clips), desc="Generating fake audio"):
        sentence = np.random.choice(sentences)
        tts_path = os.path.join(tts_dir, f"fake_tts_{i:05d}.wav")
        
        success = False
        subtype = method
        if method == "xtts" and tts_model:
            speaker_wav = reference_speakers[i % len(reference_speakers)] if reference_speakers else None
            success = generate_with_xtts(sentence, tts_path, tts_model, speaker_wav_path=speaker_wav)
            subtype = "xtts"
        elif method == "tortoise":
            success = generate_with_tortoise(sentence, tts_path, device)
            subtype = "tortoise"
        else:
            # Simple placeholder (standardized to 16kHz)
            duration = 3.0
            t = np.linspace(0, duration, int(TARGET_SR * duration))
            audio = np.sin(2 * np.pi * 200 * t) * np.exp(-t)
            # Normalize
            audio = audio / (np.max(np.abs(audio)) + 1e-9)
            sf.write(tts_path, audio, TARGET_SR)
            success = True
            subtype = "simple"
        
        if success:
            generated.append(tts_path)
            # Record metadata
            clip_metadata.append({
                "path": os.path.relpath(tts_path, output_dir),
                "label": "spoof",
                "subtype": subtype,
                "attack_type": "synthesis",
                "duration": 3.0,
                "sr": TARGET_SR
            })
            
            # Create replay version for half
            if i < num_clips // 2:
                replay_path = os.path.join(replay_dir, f"fake_replay_{i:05d}.wav")
                if simulate_replay_attack(tts_path, replay_path, device):
                    generated.append(replay_path)
                    clip_metadata.append({
                        "path": os.path.relpath(replay_path, output_dir),
                        "label": "spoof",
                        "subtype": f"{subtype}_replay",
                        "attack_type": "replay",
                        "duration": 3.0,
                        "sr": TARGET_SR
                    })
        else:
            failed += 1
    
    # Save labels CSV
    csv_path = os.path.join(output_dir, "labels.csv")
    if clip_metadata:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "label", "subtype", "attack_type", "duration", "sr"])
            writer.writeheader()
            writer.writerows(clip_metadata)
        print(f"[OK] Saved labels CSV to: {csv_path}")
    
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
    parser.add_argument("--real_speaker_dir", type=str, default=None,
                       help="Path to directory with real human reference audio clips (recommended for forensic validity)")
    
    args = parser.parse_args()
    
    print(f"[INFO] Generating {args.num_clips} fake audio clips")
    print(f"[INFO] Method: {args.method}")
    print(f"[INFO] Output: {args.output_dir}")
    
    sentences = load_sentences(args.corpus) if args.corpus else None
    
    # Resolve output_dir relative to project root
    def find_project_root():
        """Find the project root directory (where 'data' folder exists)."""
        current = Path(__file__).resolve().parent
        for level in [current, current.parent, current.parent.parent]:
            if level and (level / "data").exists() and (level / "Code").exists():
                return level
        return current.parent.parent
    
    project_root = find_project_root()
    if not os.path.isabs(args.output_dir):
        args.output_dir = os.path.join(str(project_root), args.output_dir)
    
    # Resolve real_speaker_dir if provided
    real_speaker_dir = None
    if args.real_speaker_dir:
        if not os.path.isabs(args.real_speaker_dir):
            real_speaker_dir = os.path.join(str(project_root), args.real_speaker_dir)
        else:
            real_speaker_dir = args.real_speaker_dir
    
    generated = generate_fake_clips(
        args.num_clips,
        args.output_dir,
        method=args.method,
        sentences=sentences,
        device=device,
        real_speaker_dir=real_speaker_dir
    )
    
    if device and device.type == "cuda":
        torch.cuda.empty_cache()
    
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
