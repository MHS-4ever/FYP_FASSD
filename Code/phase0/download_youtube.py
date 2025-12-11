"""
Automated YouTube Audio Downloader for Phase 0 Data Collection

Downloads audio from YouTube videos based on search queries or channel names,
then processes them into clips suitable for training.
Optimized for GPU acceleration (RTX 3050, CUDA 13.1) using torchaudio.

Usage:
    python download_youtube.py --domain broadcast --max_videos 300
    python download_youtube.py --domain podcast --max_videos 500
    python download_youtube.py --domain social --max_videos 300
"""

import argparse
import os
import subprocess
import json
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
    print(f"[GPU] CUDA Version: {torch.version.cuda}")
    USE_GPU = True
else:
    device = torch.device("cpu")
    USE_GPU = False
    print("[INFO] CUDA not available - using CPU for audio processing")


def download_video_audio(url_or_query, output_dir, domain, max_retries=2):
    """Download audio from a YouTube video or search query."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Use yt-dlp to download audio
    # Fix: Use domain name directly, not nested path
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    for attempt in range(max_retries):
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",  # Best quality
            "--no-playlist",
            "--output", output_template,
            "--quiet",
            "--no-warnings",
            "--no-check-certificate",  # Sometimes helps with connection issues
            "--socket-timeout", "30"  # 30 second socket timeout
        ]
        
        # Add URL or search query
        if url_or_query.startswith("http"):
            cmd.append(url_or_query)
        else:
            # Search query - limit to 1 result for faster response
            cmd.extend(["--default-search", "ytsearch1", url_or_query])
        
        try:
            # Shorter timeout for individual downloads (2 minutes)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                # Find the downloaded file
                wav_files = list(Path(output_dir).glob("*.wav"))
                if wav_files:
                    return str(wav_files[-1])  # Return most recent
            elif attempt < max_retries - 1:
                continue  # Retry
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                continue  # Retry
            print(f"[WARN] Timeout downloading (after {max_retries} attempts): {url_or_query[:50]}")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                continue  # Retry
            # Don't print error for search queries (they fail often)
            if url_or_query.startswith("http"):
                print(f"[WARN] Failed to download {url_or_query[:50]}: {str(e)[:50]}")
            return None
    
    return None


def split_audio_into_clips(audio_path, output_dir, clip_length=10, overlap=1, use_gpu=False, target_sr=16000):
    """
    Split long audio file into clips using GPU-accelerated torchaudio.
    
    Args:
        audio_path: Path to input audio file
        output_dir: Directory to save clips
        clip_length: Length of each clip in seconds
        overlap: Overlap between clips in seconds
        use_gpu: Whether to use GPU for processing
        target_sr: Target sample rate (default: 16000)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file exists and is readable
    if not os.path.exists(audio_path):
        return []
    
    # Try multiple methods to load the audio
    waveform = None
    sr = None
    
    # Method 1: Try torchaudio first (GPU-compatible, faster)
    try:
        waveform, sr = torchaudio.load(audio_path)
        if waveform is not None and sr is not None:
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
    except Exception:
        waveform = None
        sr = None
    
    # Method 2: Try librosa as fallback (more robust for corrupted files)
    if waveform is None:
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=target_sr, mono=True, duration=None)
            if len(y) > 0:
                # Convert to torch tensor format for consistent processing
                # librosa.load already resampled to target_sr
                waveform = torch.from_numpy(y).unsqueeze(0)
                sr = target_sr
            else:
                return []  # Empty file
        except Exception:
            return []  # Both methods failed
    
    if waveform is None or sr is None:
        return []
    
    # Resample if needed (only for torchaudio loaded files that weren't already target_sr)
    if sr != target_sr:
        try:
            if use_gpu and torch.cuda.is_available() and isinstance(waveform, torch.Tensor):
                waveform = waveform.to(device)
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr).to(device)
                waveform = resampler(waveform)
            elif isinstance(waveform, torch.Tensor):
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr)
                waveform = resampler(waveform)
            sr = target_sr
        except Exception:
            return []  # Resampling failed
    
    # Get duration (waveform is always torch.Tensor at this point)
    duration = waveform.shape[1] / sr
    
    if duration < 1.0:
        return []  # Too short
    
    # Generate clips
    clips = []
    clip_idx = 0
    start = 0
    
    while start + clip_length <= duration:
        end = start + clip_length
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        
        # Extract clip (waveform is always torch.Tensor at this point)
        clip_audio = waveform[:, start_sample:end_sample]
        clip_audio_cpu = clip_audio.cpu().squeeze(0).numpy()
        
        # Save clip
        clip_name = f"{Path(audio_path).stem}_clip{clip_idx:04d}.wav"
        clip_path = os.path.join(output_dir, clip_name)
        
        try:
            sf.write(clip_path, clip_audio_cpu, sr)
            clips.append(clip_path)
        except Exception:
            # Skip this clip if write fails
            pass
        
        clip_idx += 1
        start += (clip_length - overlap)  # Move forward with overlap
    
    # Clear GPU cache
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return clips


def get_channel_video_urls(channel_name_or_url, max_videos=10):
    """Get video URLs from a YouTube channel using yt-dlp."""
    # Use shorter timeouts and limit videos to avoid hangs
    max_videos = min(max_videos, 20)  # Limit to 20 videos per channel to avoid timeouts
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(url)s",
        "--playlist-end", str(max_videos),
        "--quiet",
        "--no-warnings",
        "--socket-timeout", "15",  # Shorter socket timeout
        "--extractor-args", "youtube:skip=dash"  # Skip DASH to speed up
    ]
    
    # Handle both channel URLs and channel names
    if channel_name_or_url.startswith("http"):
        cmd.append(channel_name_or_url)
    else:
        # For channel names, use search instead of trying to extract channel URL
        # This is faster and more reliable
        return []
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)  # Shorter timeout
        if result.returncode == 0:
            urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip() and line.strip().startswith("http")]
            return urls[:max_videos]  # Limit results
    except subprocess.TimeoutExpired:
        print(f"[WARN] Timeout fetching videos from channel: {channel_name_or_url[:50]}")
        return []
    except Exception as e:
        return []
    
    return []


def download_from_channels(channels, output_dir, domain, max_videos=300):
    """Download videos from specific YouTube channels using direct channel URLs."""
    downloaded = []
    
    print(f"[INFO] Fetching videos from {len(channels)} channels...")
    
    for channel in tqdm(channels, desc=f"Downloading from channels ({domain})"):
        if len(downloaded) >= max_videos:
            break
        
        # Get video URLs from channel
        video_urls = get_channel_video_urls(channel, max_videos=50)
        
        if not video_urls:
            # Fallback to search if channel URL extraction fails
            print(f"[WARN] Could not extract channel videos for {channel}, trying search...")
            query = f"{channel} latest"
            video_path = download_video_audio(query, output_dir, domain)
            if video_path:
                downloaded.append(video_path)
                print(f"[OK] Downloaded {len(downloaded)}/{max_videos} videos")
        else:
            # Download from extracted URLs
            for url in video_urls[:20]:  # Limit per channel
                if len(downloaded) >= max_videos:
                    break
                video_path = download_video_audio(url, output_dir, domain)
                if video_path:
                    downloaded.append(video_path)
                    print(f"[OK] Downloaded {len(downloaded)}/{max_videos} videos")
                    if len(downloaded) >= max_videos:
                        break
    
    return downloaded


def download_from_search_queries(queries, output_dir, domain, max_videos=300):
    """Download videos from search queries."""
    downloaded = []
    
    for query in tqdm(queries, desc=f"Downloading from queries ({domain})"):
        if len(downloaded) >= max_videos:
            break
            
        video_path = download_video_audio(query, output_dir, domain)
        
        if video_path:
            downloaded.append(video_path)
            print(f"[OK] Downloaded {len(downloaded)}/{max_videos} videos")
    
    return downloaded


def process_downloaded_audio(downloaded_files, output_dir, domain, clip_length=10, use_gpu=False):
    """Process downloaded audio files into clips using GPU acceleration."""
    clips_dir = os.path.join(output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    all_clips = []
    failed_files = []
    successful_files = []
    file_clip_counts = {}  # Track clips per file for diversity analysis
    
    print(f"[INFO] Processing {len(downloaded_files)} audio files into clips (using {'GPU' if use_gpu else 'CPU'})")
    
    for audio_file in tqdm(downloaded_files, desc="Processing audio into clips"):
        if not os.path.exists(audio_file):
            failed_files.append((audio_file, "File not found"))
            continue
        
        # Check file size - skip if too small (likely corrupted)
        try:
            file_size = os.path.getsize(audio_file)
            if file_size < 1000:  # Less than 1KB is likely corrupted
                failed_files.append((audio_file, f"File too small ({file_size} bytes)"))
                continue
        except:
            failed_files.append((audio_file, "Cannot read file size"))
            continue
            
        clips = split_audio_into_clips(audio_file, clips_dir, clip_length=clip_length, use_gpu=use_gpu)
        if clips:
            all_clips.extend(clips)
            successful_files.append(audio_file)
            file_clip_counts[os.path.basename(audio_file)] = len(clips)
        else:
            failed_files.append((audio_file, "No clips generated (file may be too short or corrupted)"))
        
        # Remove original long file to save space (only if clips were created successfully)
        if clips:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                # File might be locked or permission issue - will be cleaned up later
                pass
    
    # Final GPU cleanup
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"[GPU] Processing complete. VRAM usage: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
    
    # Detailed reporting
    print(f"\n[INFO] Processing Summary:")
    print(f"  - Total files downloaded: {len(downloaded_files)}")
    print(f"  - Successfully processed: {len(successful_files)}")
    print(f"  - Failed to process: {len(failed_files)}")
    print(f"  - Total clips created: {len(all_clips)}")
    
    if successful_files:
        avg_clips = len(all_clips) / len(successful_files)
        print(f"  - Average clips per file: {avg_clips:.1f}")
        
        # Show diversity - files with most clips
        if file_clip_counts:
            sorted_files = sorted(file_clip_counts.items(), key=lambda x: x[1], reverse=True)
            print(f"\n[INFO] Top 5 files by clip count:")
            for filename, count in sorted_files[:5]:
                print(f"    {filename}: {count} clips")
    
    if failed_files:
        print(f"\n[WARN] Failed files (showing first 10):")
        for file_path, reason in failed_files[:10]:
            filename = os.path.basename(file_path)
            print(f"    {filename}: {reason}")
        if len(failed_files) > 10:
            print(f"    ... and {len(failed_files) - 10} more")
    
    return all_clips


def main():
    parser = argparse.ArgumentParser("Download YouTube Audio for Phase 0")
    parser.add_argument("--domain", type=str, required=True, 
                       choices=["broadcast", "podcast", "social"],
                       help="Domain type: broadcast, podcast, or social")
    parser.add_argument("--max_videos", type=int, default=300,
                       help="Maximum number of videos to download")
    parser.add_argument("--output_dir", type=str, 
                       default="data/realworld/youtube",
                       help="Output directory for downloaded audio")
    parser.add_argument("--clip_length", type=int, default=10,
                       help="Length of each clip in seconds")
    parser.add_argument("--use_gpu", action="store_true", default=True,
                       help="Use GPU for audio processing (default: True if CUDA available)")
    
    args = parser.parse_args()
    
    # Auto-detect GPU if not explicitly disabled
    use_gpu = args.use_gpu and USE_GPU
    
    # Define search strategies per domain
    if args.domain == "broadcast":
        channels = [
            "Geo News", "ARY News", "BBC News", 
            "DW News", "CNN", "Fox News", "Al Jazeera"
        ]
        queries = [
            "news broadcast latest",
            "television news report",
            "radio news bulletin"
        ]
    elif args.domain == "podcast":
        queries = [
            "podcast interview",
            "podcast conversation",
            "podcast discussion",
            "interview podcast"
        ]
        channels = []
    elif args.domain == "social":
        queries = [
            "tiktok real voice",
            "youtube shorts real voice",
            "social media video",
            "vlog real voice"
        ]
        channels = []
    
    # Create domain-specific output directory
    # If output_dir already ends with domain name, use it as-is
    output_path = Path(args.output_dir)
    if output_path.name == args.domain:
        domain_output = str(output_path)
    else:
        domain_output = os.path.join(args.output_dir, args.domain)
    os.makedirs(domain_output, exist_ok=True)
    
    print(f"[INFO] Starting download for domain: {args.domain}")
    print(f"[INFO] Target: {args.max_videos} videos")
    
    # Download videos
    downloaded = []
    if channels:
        downloaded.extend(download_from_channels(channels, domain_output, args.domain, args.max_videos))
    
    if len(downloaded) < args.max_videos and queries:
        remaining = args.max_videos - len(downloaded)
        downloaded.extend(download_from_search_queries(queries, domain_output, args.domain, remaining))
    
    print(f"[OK] Downloaded {len(downloaded)} videos")
    
    # Process into clips
    print(f"[INFO] Processing audio into {args.clip_length}s clips...")
    clips = process_downloaded_audio(downloaded, domain_output, args.domain, args.clip_length, use_gpu=use_gpu)
    
    print(f"[OK] Created {len(clips)} clips")
    print(f"[OK] Clips saved to: {os.path.join(domain_output, 'clips')}")
    
    # Save metadata
    metadata = {
        "domain": args.domain,
        "videos_downloaded": len(downloaded),
        "clips_created": len(clips),
        "clip_length": args.clip_length,
        "output_dir": domain_output
    }
    
    metadata_path = os.path.join(domain_output, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[OK] Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()

