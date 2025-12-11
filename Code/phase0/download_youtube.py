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
import numpy as np

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


def download_video_audio(url_or_query, output_dir, domain, video_id=None, max_retries=2):
    """Download audio from a YouTube video or search query."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Use yt-dlp to download audio
    output_template = os.path.join(output_dir, f"%(id)s.%(ext)s")
    
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
    
    try:
        # Load audio using torchaudio (GPU-compatible)
        waveform, sr = torchaudio.load(audio_path)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample if needed (GPU-accelerated)
        if sr != target_sr:
            if use_gpu and torch.cuda.is_available():
                waveform = waveform.to(device)
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr).to(device)
            else:
                resampler = T.Resample(orig_freq=sr, new_freq=target_sr)
            waveform = resampler(waveform)
            sr = target_sr
        
        duration = waveform.shape[1] / sr
        
        if duration < 1.0:
            return []  # Too short
        
        clips = []
        clip_idx = 0
        start = 0
        
        while start + clip_length <= duration:
            end = start + clip_length
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            clip_audio = waveform[:, start_sample:end_sample]
            
            # Move to CPU and convert to numpy for saving
            clip_audio_cpu = clip_audio.cpu().squeeze(0).numpy()
            
            # Save clip
            clip_name = f"{Path(audio_path).stem}_clip{clip_idx:04d}.wav"
            clip_path = os.path.join(output_dir, clip_name)
            sf.write(clip_path, clip_audio_cpu, sr)
            clips.append(clip_path)
            
            clip_idx += 1
            start += (clip_length - overlap)  # Move forward with overlap
        
        # Clear GPU cache
        if use_gpu and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return clips
    except Exception as e:
        print(f"[ERROR] Failed to split {audio_path}: {e}")
        return []


def get_channel_video_urls(channel_name_or_url, max_videos=10):
    """Get video URLs from a YouTube channel using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(url)s",
        "--playlist-end", str(max_videos),
        "--quiet",
        "--no-warnings",
        "--socket-timeout", "30"
    ]
    
    # Handle both channel URLs and channel names
    if channel_name_or_url.startswith("http"):
        cmd.append(channel_name_or_url)
    else:
        # Search for channel and get first result's channel URL
        search_cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(channel_url)s",
            "--playlist-end", "1",
            "--quiet",
            "--default-search", "ytsearch1",
            f"{channel_name_or_url} channel"
        ]
        try:
            result = subprocess.run(search_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout.strip():
                channel_url = result.stdout.strip().split('\n')[0]
                if channel_url.startswith("http"):
                    cmd.append(channel_url)
                else:
                    return []
            else:
                return []
        except:
            return []
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return urls
    except:
        pass
    
    return []


def download_from_channels(channels, output_dir, domain, max_videos=300):
    """Download videos from specific YouTube channels."""
    downloaded = []
    
    print(f"[INFO] Fetching videos from {len(channels)} channels...")
    
    for channel in tqdm(channels, desc=f"Downloading from channels ({domain})"):
        # Get video URLs from channel
        video_urls = get_channel_video_urls(channel, max_videos=50)
        
        if not video_urls:
            # Fallback to search if channel URL extraction fails
            print(f"[WARN] Could not extract channel videos for {channel}, trying search...")
            query = f"{channel} latest"
            video_path = download_video_audio(query, output_dir, domain)
            if video_path:
                downloaded.append(video_path)
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
    
    print(f"[INFO] Processing {len(downloaded_files)} audio files into clips (using {'GPU' if use_gpu else 'CPU'})")
    
    for audio_file in tqdm(downloaded_files, desc="Processing audio into clips"):
        clips = split_audio_into_clips(audio_file, clips_dir, clip_length=clip_length, use_gpu=use_gpu)
        all_clips.extend(clips)
        
        # Remove original long file to save space
        try:
            os.remove(audio_file)
        except:
            pass
    
    # Final GPU cleanup
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"[GPU] Processing complete. VRAM usage: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
    
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

