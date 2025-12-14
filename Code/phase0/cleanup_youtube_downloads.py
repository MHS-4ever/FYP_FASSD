"""
Cleanup and Process script for YouTube downloads.

Processes all downloaded videos into clips, removes duplicates, and regenerates metadata.
Handles cases where clips_metadata.csv was deleted or needs to be regenerated.

Usage:
    python cleanup_youtube_downloads.py --data_dir data/realworld/youtube/broadcast
    python cleanup_youtube_downloads.py --data_dir data/realworld/youtube/podcast
    python cleanup_youtube_downloads.py --data_dir data/realworld/youtube/social
"""

import argparse
import os
import json
import csv
from pathlib import Path
from tqdm import tqdm
import torch
import torchaudio
import torchaudio.transforms as T
import soundfile as sf

# GPU Setup
if torch.cuda.is_available():
    device = torch.device("cuda")
    torch.backends.cudnn.benchmark = True
    print(f"[GPU] Using GPU: {torch.cuda.get_device_name(0)}")
    USE_GPU = True
else:
    device = torch.device("cpu")
    USE_GPU = False
    print("[INFO] CUDA not available - using CPU for audio processing")


def find_project_root():
    """Find the project root directory (where 'data' folder exists)."""
    current = Path(__file__).resolve().parent
    for level in [current, current.parent, current.parent.parent]:
        if level and (level / "data").exists() and (level / "Code").exists():
            return level
    return current.parent.parent


def split_audio_into_clips(audio_path, output_dir, clip_length=10, overlap=1, use_gpu=False, target_sr=16000):
    """Split long audio file into clips."""
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(audio_path):
        return []
    
    # Load audio
    try:
        waveform, sr = torchaudio.load(audio_path)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
    except Exception:
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=target_sr, mono=True)
            waveform = torch.from_numpy(y).unsqueeze(0)
            sr = target_sr
        except Exception:
            return []
    
    if waveform is None or sr is None:
        return []
    
    # Resample if needed
    if sr != target_sr:
        try:
            num_samples = waveform.shape[1]
            use_gpu_resample = use_gpu and torch.cuda.is_available() and num_samples > 5_000_000
            
            if use_gpu_resample:
                waveform = waveform.to(device)
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr).to(device)
                waveform = resampler(waveform)
            else:
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr)
                waveform = resampler(waveform)
            sr = target_sr
        except Exception:
            return []
    
    duration = waveform.shape[1] / sr
    if duration < 1.0:
        return []
    
    # Generate clips with sliding window and overlap
    clips = []
    clip_idx = 0
    start = 0
    
    while start + clip_length <= duration:
        end = start + clip_length
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        
        clip_audio = waveform[:, start_sample:end_sample]
        
        # Normalize audio to prevent amplitude bias across sources
        max_val = torch.max(torch.abs(clip_audio))
        if max_val > 0:
            clip_audio = clip_audio / (max_val + 1e-9)
        
        clip_audio_cpu = clip_audio.cpu().squeeze(0).numpy()
        
        clip_name = f"{Path(audio_path).stem}_clip{clip_idx:04d}.wav"
        clip_path = os.path.join(output_dir, clip_name)
        
        # Skip if clip already exists
        if os.path.exists(clip_path):
            clips.append(clip_path)
        else:
            try:
                sf.write(clip_path, clip_audio_cpu, sr)
                clips.append(clip_path)
            except Exception:
                pass
        
        clip_idx += 1
        start += (clip_length - overlap)
    
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return clips


def extract_video_id_from_clip(clip_filename):
    """Extract video ID from clip filename (format: {video_id}_clip{number}.wav)."""
    # Remove .wav extension
    stem = Path(clip_filename).stem
    # Find _clip pattern
    if "_clip" in stem:
        video_id = stem.split("_clip")[0]
        return video_id
    return None


def regenerate_metadata_from_clips(data_path, clips_dir, domain, clip_length=10):
    """
    Regenerate metadata CSV from existing clips when original videos are missing.
    
    Args:
        data_path: Path to domain directory
        clips_dir: Path to clips directory
        domain: Domain name
        clip_length: Clip length in seconds
    """
    print(f"[INFO] Regenerating metadata from existing clips...")
    
    # Find all clip files
    clip_files = list(clips_dir.glob("*.wav"))
    print(f"[INFO] Found {len(clip_files)} existing clips")
    
    clip_metadata = []
    video_ids = set()
    
    for clip_file in tqdm(clip_files, desc="Scanning clips"):
        video_id = extract_video_id_from_clip(clip_file.name)
        if video_id:
            video_ids.add(video_id)
            clip_metadata.append({
                "clip_path": str(clip_file.resolve()),  # Full absolute path
                "domain": domain,
                "source_video": video_id,
                "duration": clip_length,
                "sr": 16000,
                "label": "bonafide"
            })
        else:
            # Fallback: use filename without extension as video_id
            video_id = clip_file.stem
            video_ids.add(video_id)
            clip_metadata.append({
                "clip_path": str(clip_file.resolve()),
                "domain": domain,
                "source_video": video_id,
                "duration": clip_length,
                "sr": 16000,
                "label": "bonafide"
            })
    
    # Save clip metadata CSV
    csv_path = data_path / "clips_metadata.csv"
    if clip_metadata:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["clip_path", "domain", "source_video", "duration", "sr", "label"])
            writer.writeheader()
            writer.writerows(clip_metadata)
        print(f"[OK] Regenerated clip metadata CSV: {csv_path}")
        print(f"[OK] Total clips: {len(clip_metadata)}")
        print(f"[OK] Unique videos: {len(video_ids)}")
    
    # Save/update metadata.json
    metadata = {
        "domain": domain,
        "videos_total": len(video_ids),
        "clips_created": len(clip_metadata),
        "clip_length": clip_length,
        "output_dir": str(data_path),
        "note": "Metadata regenerated from existing clips (original videos not available)"
    }
    
    metadata_path = data_path / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[OK] Updated metadata.json: {metadata_path}")
    
    return len(clip_metadata), len(video_ids)


def process_all_downloaded_videos(data_dir, clip_length=10, use_gpu=False):
    """
    Process all downloaded videos into clips, remove duplicates, and regenerate metadata.
    If original videos are missing but clips exist, regenerate metadata from clips.
    
    Args:
        data_dir: Directory containing downloaded WAV files and clips subdirectory
        clip_length: Length of each clip in seconds
        use_gpu: Whether to use GPU for processing
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"[ERROR] Directory does not exist: {data_dir}")
        return
    
    # Resolve to absolute path
    data_path = data_path.resolve()
    
    # Infer domain from path
    domain = data_path.name
    if domain not in ["broadcast", "podcast", "social"]:
        # Try parent directory
        if data_path.parent.name in ["broadcast", "podcast", "social"]:
            domain = data_path.parent.name
        else:
            domain = "unknown"
    
    clips_dir = data_path / "clips"
    os.makedirs(clips_dir, exist_ok=True)
    
    # Find all WAV files in the main directory (not in clips subdirectory)
    all_wav_files = list(data_path.glob("*.wav"))
    
    # Check if we have clips but no original videos (regenerate metadata only)
    existing_clips = list(clips_dir.glob("*.wav")) if clips_dir.exists() else []
    
    if len(all_wav_files) == 0 and len(existing_clips) > 0:
        print(f"[INFO] No original videos found, but {len(existing_clips)} clips exist")
        print(f"[INFO] Regenerating metadata from existing clips...")
        regenerate_metadata_from_clips(data_path, clips_dir, domain, clip_length)
        return
    
    # Remove duplicates by video ID
    unique_videos = {}
    for wav_file in all_wav_files:
        video_id = wav_file.stem
        if video_id not in unique_videos:
            unique_videos[video_id] = wav_file
        else:
            # Keep the larger file (more likely to be complete)
            existing_size = unique_videos[video_id].stat().st_size
            new_size = wav_file.stat().st_size
            if new_size > existing_size:
                # Remove the smaller duplicate
                try:
                    unique_videos[video_id].unlink()
                    print(f"[INFO] Removed duplicate: {unique_videos[video_id].name} (kept {wav_file.name})")
                except:
                    pass
                unique_videos[video_id] = wav_file
            else:
                # Remove the new duplicate
                try:
                    wav_file.unlink()
                    print(f"[INFO] Removed duplicate: {wav_file.name} (kept {unique_videos[video_id].name})")
                except:
                    pass
    
    video_files = list(unique_videos.values())
    
    print(f"[INFO] Found {len(all_wav_files)} WAV files, {len(video_files)} unique videos (removed {len(all_wav_files) - len(video_files)} duplicates)")
    print(f"[INFO] Domain: {domain}")
    print(f"[INFO] Processing videos into {clip_length}s clips...")
    
    # Check existing clips to avoid reprocessing
    existing_clips_set = set()
    if clips_dir.exists():
        existing_clip_files = list(clips_dir.glob("*.wav"))
        existing_clips_set = {f.stem for f in existing_clip_files}
        print(f"[INFO] Found {len(existing_clips_set)} existing clips")
    
    all_clips = []
    failed_files = []
    clip_metadata = []
    processed_videos = []
    
    # First, scan existing clips and add them to metadata
    if existing_clips_set:
        print(f"[INFO] Scanning existing clips to add to metadata...")
        for clip_stem in existing_clips_set:
            clip_path = clips_dir / f"{clip_stem}.wav"
            if clip_path.exists():
                video_id = extract_video_id_from_clip(clip_path.name)
                if not video_id:
                    video_id = clip_path.stem
                
                all_clips.append(str(clip_path))
                clip_metadata.append({
                    "clip_path": str(clip_path.resolve()),  # Full absolute path
                    "domain": domain,
                    "source_video": video_id,
                    "duration": clip_length,
                    "sr": 16000,
                    "label": "bonafide"
                })
    
    # Process each unique video
    for video_file in tqdm(video_files, desc="Processing videos into clips"):
        if not video_file.exists():
            failed_files.append(str(video_file))
            continue
        
        try:
            file_size = video_file.stat().st_size
            if file_size < 1000:
                failed_files.append(str(video_file))
                continue
        except:
            failed_files.append(str(video_file))
            continue
        
        source_video_id = video_file.stem
        
        # Check if clips already exist for this video
        existing_clips_for_video = [f for f in existing_clips_set if f.startswith(f"{source_video_id}_clip")]
        
        if existing_clips_for_video:
            # Clips already exist, skip processing (already added to metadata above)
            continue
        else:
            # Generate new clips
            clips = split_audio_into_clips(
                str(video_file), 
                str(clips_dir), 
                clip_length=clip_length, 
                use_gpu=use_gpu
            )
            
            if clips:
                all_clips.extend(clips)
                processed_videos.append(str(video_file))
                
                # Record metadata for each clip with FULL absolute path
                for clip_path in clips:
                    clip_metadata.append({
                        "clip_path": str(Path(clip_path).resolve()),  # Full absolute path
                        "domain": domain,
                        "source_video": source_video_id,
                        "duration": clip_length,
                        "sr": 16000,
                        "label": "bonafide"
                    })
                
                # Remove original file to save space (only if clips were created)
                try:
                    video_file.unlink()
                except:
                    pass
            else:
                failed_files.append(str(video_file))
    
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Remove duplicates from clip_metadata (in case of reprocessing)
    seen_clip_paths = set()
    unique_clip_metadata = []
    for clip_info in clip_metadata:
        clip_path = clip_info["clip_path"]
        if clip_path not in seen_clip_paths:
            seen_clip_paths.add(clip_path)
            unique_clip_metadata.append(clip_info)
    
    clip_metadata = unique_clip_metadata
    all_clips = list(seen_clip_paths)
    
    # Save clip metadata CSV with full absolute paths
    csv_path = data_path / "clips_metadata.csv"
    if clip_metadata:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["clip_path", "domain", "source_video", "duration", "sr", "label"])
            writer.writeheader()
            writer.writerows(clip_metadata)
        print(f"[OK] Saved clip metadata to: {csv_path}")
        print(f"[OK] Total clips in CSV: {len(clip_metadata)}")
    
    # Extract unique video IDs from clip metadata
    unique_video_ids = set(clip["source_video"] for clip in clip_metadata)
    
    # Save/update metadata.json
    metadata = {
        "domain": domain,
        "videos_processed": len(processed_videos),
        "videos_total": len(unique_video_ids),
        "clips_created": len(all_clips),
        "clip_length": clip_length,
        "output_dir": str(data_path)
    }
    
    metadata_path = data_path / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[OK] Saved metadata to: {metadata_path}")
    
    # Summary
    print(f"\n[SUMMARY] Processing Complete:")
    print(f"  - Unique videos: {len(unique_video_ids)}")
    print(f"  - Videos processed: {len(processed_videos)}")
    print(f"  - Videos skipped (clips exist): {len(video_files) - len(processed_videos)}")
    print(f"  - Total clips: {len(all_clips)}")
    print(f"  - Failed files: {len(failed_files)}")
    print(f"  - Clips metadata CSV: {csv_path}")
    
    if failed_files:
        print(f"\n[WARN] Failed to process {len(failed_files)} files (showing first 10):")
        for failed_file in failed_files[:10]:
            print(f"    {Path(failed_file).name}")
        if len(failed_files) > 10:
            print(f"    ... and {len(failed_files) - 10} more")


def main():
    parser = argparse.ArgumentParser("Cleanup and Process YouTube Downloads")
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Directory containing downloaded files and clips subdirectory")
    parser.add_argument("--clip_length", type=int, default=10,
                       help="Length of each clip in seconds (default: 10)")
    parser.add_argument("--use_gpu", action="store_true",
                       help="Use GPU for audio processing (default: auto-detect)")
    
    args = parser.parse_args()
    
    # Resolve data_dir relative to project root
    project_root = find_project_root()
    if not os.path.isabs(args.data_dir):
        args.data_dir = os.path.join(str(project_root), args.data_dir)
    
    # GPU usage
    use_gpu = args.use_gpu and USE_GPU
    if not args.use_gpu:
        use_gpu = USE_GPU  # Auto-detect by default
    
    print(f"[INFO] Processing directory: {args.data_dir}")
    print(f"[INFO] Using {'GPU' if use_gpu else 'CPU'} for processing")
    
    process_all_downloaded_videos(args.data_dir, args.clip_length, use_gpu=use_gpu)


if __name__ == "__main__":
    main()
