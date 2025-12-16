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
import re
from pathlib import Path
from tqdm import tqdm
import torch
import torchaudio
import torchaudio.transforms as T
import soundfile as sf
import csv

# Set deterministic seed for reproducibility
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)

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


def download_video_audio(url_or_query, output_dir, timeout=120, max_duration=1800):
    """
    Download audio from a YouTube video or search query.
    
    Args:
        url_or_query: YouTube URL or search query
        output_dir: Output directory
        timeout: Timeout in seconds (default: 120)
        max_duration: Maximum video duration in seconds (default: 1800 = 30 min)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file already exists
    if url_or_query.startswith("http"):
        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url_or_query)
        if video_id_match:
            video_id = video_id_match.group(1)
            existing_file = os.path.join(output_dir, f"{video_id}.wav")
            if os.path.exists(existing_file) and os.path.getsize(existing_file) > 1000:
                return existing_file
    
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "--output", output_template,
        "--quiet",
        "--no-warnings",
        "--socket-timeout", "15",
        "--fragment-retries", "1",
        "--retries", "1",
        "--match-filter", f"duration < {max_duration}"  # Filter by duration
    ]
    
    # Add URL or search query
    if url_or_query.startswith("http"):
        cmd.append(url_or_query)
    else:
        # Use ytsearch10 to get 10 videos per search (much faster!)
        cmd.extend(["--default-search", "ytsearch10", url_or_query])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            wav_files = list(Path(output_dir).glob("*.wav"))
            if wav_files:
                # Return the most recently created file
                wav_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return str(wav_files[0])
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    
    return None


def download_multiple_videos_from_query(query, output_dir, max_results=10, max_duration=1800, timeout=300):
    """
    Download multiple videos from a single search query (much more efficient).
    
    Args:
        query: Search query string
        output_dir: Output directory
        max_results: Maximum number of videos to download from this query (default: 10)
        max_duration: Maximum video duration in seconds (default: 1800 = 30 min)
        timeout: Timeout in seconds (default: 300 for batch)
    
    Returns:
        List of downloaded file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "--output", output_template,
        "--quiet",
        "--no-warnings",
        "--socket-timeout", "15",
        "--fragment-retries", "1",
        "--retries", "1",
        "--match-filter", f"duration < {max_duration}",
        "--default-search", f"ytsearch{max_results}",
        query
    ]
    
    downloaded_files = []
    existing_files_before = set(Path(output_dir).glob("*.wav"))
    existing_video_ids_before = {f.stem for f in existing_files_before}
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            # Find newly created files
            existing_files_after = set(Path(output_dir).glob("*.wav"))
            new_files = existing_files_after - existing_files_before
            
            # Double-check: only return files with new video IDs (extra safety)
            downloaded_files = []
            for f in new_files:
                if f.stat().st_size > 1000:
                    video_id = f.stem
                    if video_id not in existing_video_ids_before:
                        downloaded_files.append(str(f))
                        existing_video_ids_before.add(video_id)  # Track it
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    
    return downloaded_files


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
    # GPU resampling only beneficial for long files (>2-3 minutes)
    # For short clips, CPU is often faster due to transfer overhead
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
    # Example: 10s clip with 1s overlap means clips at 0-10s, 9-19s, 18-28s, etc.
    clips = []
    clip_idx = 0
    start = 0
    
    while start + clip_length <= duration:
        end = start + clip_length
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        
        clip_audio = waveform[:, start_sample:end_sample]
        
        # Normalize audio to prevent amplitude bias across sources
        # Important for forensic ML consistency
        max_val = torch.max(torch.abs(clip_audio))
        if max_val > 0:
            clip_audio = clip_audio / (max_val + 1e-9)
        
        clip_audio_cpu = clip_audio.cpu().squeeze(0).numpy()
        
        clip_name = f"{Path(audio_path).stem}_clip{clip_idx:04d}.wav"
        clip_path = os.path.join(output_dir, clip_name)
        
        try:
            sf.write(clip_path, clip_audio_cpu, sr)
            clips.append(clip_path)
        except Exception:
            pass
        
        clip_idx += 1
        # Sliding window: move forward by (clip_length - overlap)
        # e.g., 10s clip with 1s overlap: next clip starts at 9s
        start += (clip_length - overlap)
    
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return clips


def get_channel_video_urls(channel_url, max_videos=50):
    """Get video URLs from a YouTube channel with timeout."""
    print(f"[INFO] Fetching videos from channel: {channel_url[:50]}...")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(url)s",
        "--playlist-end", str(max_videos),
        "--quiet",
        "--no-warnings",
        "--socket-timeout", "10",
        "--fragment-retries", "1",
        "--retries", "1"
    ]
    cmd.append(channel_url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            urls = [line.strip() for line in result.stdout.strip().split('\n') 
                   if line.strip() and line.strip().startswith("http")]
            print(f"[OK] Found {len(urls)} videos from channel")
            return urls[:max_videos]
        else:
            print(f"[WARN] Failed to fetch channel videos (return code: {result.returncode})")
    except subprocess.TimeoutExpired:
        print(f"[WARN] Timeout fetching videos from channel (30s limit)")
    except Exception as e:
        print(f"[WARN] Error fetching channel videos: {str(e)[:50]}")
    
    return []


def download_from_channels(channels, output_dir, domain, max_videos=300, max_channel_time=300):
    """
    Download videos from specific YouTube channels.
    
    Args:
        channels: List of channel URLs
        output_dir: Output directory
        domain: Domain name
        max_videos: Maximum number of videos to download
        max_channel_time: Maximum time (seconds) to spend per channel before skipping
    """
    downloaded = []
    videos_per_channel = max_videos // max(len(channels), 1)
    
    import time
    for channel_idx, channel in enumerate(channels, 1):
        if len(downloaded) >= max_videos:
            break
        
        print(f"[INFO] Processing channel {channel_idx}/{len(channels)}: {channel}")
        channel_start_time = time.time()
        
        # Get video URLs with timeout
        video_urls = get_channel_video_urls(channel, max_videos=videos_per_channel)
        
        if not video_urls:
            print(f"[WARN] No videos found from channel, skipping...")
            continue
        
        # Download from this channel
        for url_idx, url in enumerate(video_urls, 1):
            if len(downloaded) >= max_videos:
                break
            
            # Check if we're spending too much time on this channel
            if time.time() - channel_start_time > max_channel_time:
                print(f"[WARN] Spent {max_channel_time}s on channel, moving to next...")
                break
            
            print(f"[INFO] Downloading video {url_idx}/{len(video_urls)} from channel...")
            video_path = download_video_audio(url, output_dir)
            if video_path and video_path not in downloaded:
                # Extract video ID to check for duplicates
                video_id = Path(video_path).stem
                # Check if we already have this video ID (in case of duplicates)
                existing_ids = {Path(f).stem for f in downloaded}
                if video_id not in existing_ids:
                    downloaded.append(video_path)
                    if len(downloaded) % 10 == 0:
                        print(f"[OK] Downloaded {len(downloaded)}/{max_videos} videos total")
            elif not video_path:
                print(f"[WARN] Failed to download video, continuing...")
    
    return downloaded

def download_from_search_queries(queries, output_dir, domain, max_videos=300, existing_downloaded=None):
    """
    Download videos from search queries using batch downloads (much faster!).
    Will keep trying until max_videos is reached.
    """
    if existing_downloaded is None:
        existing_downloaded = []
    
    downloaded = []
    existing_set = set(existing_downloaded)
    
    # Get all existing video IDs from already downloaded files and output directory
    existing_video_ids = set()
    for file_path in existing_downloaded:
        video_id = Path(file_path).stem
        existing_video_ids.add(video_id)
    
    # Also check files already in output_dir (from previous runs)
    for existing_file in Path(output_dir).glob("*.wav"):
        video_id = existing_file.stem
        existing_video_ids.add(video_id)
        existing_set.add(str(existing_file))
    
    # Set max duration based on domain
    max_duration_map = {
        "broadcast": 1800,  # 30 minutes
        "podcast": 1800,    # 30 minutes
        "social": 900       # 15 minutes
    }
    max_duration = max_duration_map.get(domain, 1800)
    
    # Expand queries with domain keywords
    keywords = {
        "broadcast": ["news", "breaking news", "latest news", "news today", "news update", 
                     "headlines", "news report", "world news", "current events", "news analysis"],
        "podcast": ["podcast", "interview", "conversation", "podcast episode", "talk show",
                   "discussion", "podcast latest", "interview show", "long form", "podcast series"],
        "social": ["vlog", "shorts", "real voice", "daily vlog", "voice over",
                  "talking vlog", "personal vlog", "vlog latest", "real voice latest", "social media"]
    }
    
    domain_keywords = keywords.get(domain, [])
    expanded_queries = []
    
    # Base queries
    for query in queries:
        expanded_queries.append(query)
        for keyword in domain_keywords[:5]:
            expanded_queries.append(f"{query} {keyword}")
            expanded_queries.append(f"{keyword} {query}")
    
    # Standalone keywords
    expanded_queries.extend(domain_keywords[:10])
    
    # Add date/recency modifiers for more variety
    date_modifiers = ["latest", "new", "recent", "today", "2024", "2023"]
    for keyword in domain_keywords[:8]:
        for modifier in date_modifiers:
            expanded_queries.append(f"{keyword} {modifier}")
            expanded_queries.append(f"{modifier} {keyword}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in expanded_queries:
        q_lower = q.lower().strip()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)
    
    query_idx = 0
    max_queries_to_try = max_videos * 2  # Allow many more queries (not all will succeed)
    
    # Use batch downloads - much faster!
    with tqdm(total=max_videos, desc=f"Downloading videos ({domain})") as pbar:
        while len(downloaded) < max_videos and query_idx < max_queries_to_try:
            # Cycle through queries if we've exhausted the list
            if query_idx >= len(unique_queries):
                # Generate more variations
                print(f"[INFO] Exhausted {len(unique_queries)} queries, generating more variations...")
                for base_query in queries[:5]:
                    for modifier in ["latest", "new", "recent", "episode", "full", "complete", "2024", "2023"]:
                        new_query = f"{base_query} {modifier}"
                        if new_query.lower() not in seen:
                            unique_queries.append(new_query)
                            seen.add(new_query.lower())
                
                # Also try standalone keywords with more modifiers
                for keyword in domain_keywords[:10]:
                    for modifier in ["latest", "new", "recent", "today", "episode"]:
                        new_query = f"{keyword} {modifier}"
                        if new_query.lower() not in seen:
                            unique_queries.append(new_query)
                            seen.add(new_query.lower())
                
                query_idx = 0  # Reset to start of expanded list
            
            query = unique_queries[query_idx]
            query_idx += 1
            
            # Download multiple videos from this query (batch download)
            new_files = download_multiple_videos_from_query(
                query, output_dir, max_results=10, max_duration=max_duration, timeout=300
            )
            
            # Add only new, unique files (check by both file path and video ID)
            for file_path in new_files:
                video_id = Path(file_path).stem
                # Check if we've seen this video ID before (strongest check)
                if video_id not in existing_video_ids and file_path not in downloaded and file_path not in existing_set:
                    downloaded.append(file_path)
                    existing_set.add(file_path)
                    existing_video_ids.add(video_id)  # Track by ID too
                    pbar.update(1)
                    if len(downloaded) >= max_videos:
                        break
            
            if len(downloaded) % 20 == 0:
                print(f"[OK] Downloaded {len(downloaded)}/{max_videos} videos (query {query_idx}, {len(unique_queries)} total)")
    
    if len(downloaded) < max_videos:
        print(f"[WARN] Only downloaded {len(downloaded)}/{max_videos} videos after {query_idx} queries")
    else:
        print(f"[OK] Successfully downloaded {len(downloaded)} videos from {query_idx} queries")
    
    return downloaded


def process_downloaded_audio(downloaded_files, output_dir, domain, clip_length=10, use_gpu=False):
    """Process downloaded audio files into clips and save metadata CSV."""
    clips_dir = os.path.join(output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    all_clips = []
    failed_files = []
    clip_metadata = []  # For CSV export
    
    print(f"[INFO] Processing {len(downloaded_files)} audio files into clips")
    
    for audio_file in tqdm(downloaded_files, desc="Processing audio into clips"):
        if not os.path.exists(audio_file):
            failed_files.append(audio_file)
            continue
        
        try:
            file_size = os.path.getsize(audio_file)
            if file_size < 1000:
                failed_files.append(audio_file)
                continue
        except:
            failed_files.append(audio_file)
            continue
        
        source_video_id = Path(audio_file).stem
        clips = split_audio_into_clips(audio_file, clips_dir, clip_length=clip_length, use_gpu=use_gpu)
        if clips:
            all_clips.extend(clips)
            # Record metadata for each clip
            for clip_path in clips:
                clip_metadata.append({
                    "clip_path": os.path.relpath(clip_path, output_dir),
                    "domain": domain,
                    "source_video": source_video_id,
                    "duration": clip_length,
                    "sr": 16000,
                    "label": "bonafide"
                })
            # Remove original file to save space
            try:
                os.remove(audio_file)
            except:
                pass
        else:
            failed_files.append(audio_file)
    
    if use_gpu and torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Save clip metadata CSV
    csv_path = os.path.join(output_dir, "clips_metadata.csv")
    if clip_metadata:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["clip_path", "domain", "source_video", "duration", "sr", "label"])
            writer.writeheader()
            writer.writerows(clip_metadata)
        print(f"[OK] Saved clip metadata to: {csv_path}")
    
    print(f"[OK] Created {len(all_clips)} clips from {len(downloaded_files) - len(failed_files)} files")
    if failed_files:
        print(f"[WARN] Failed to process {len(failed_files)} files")
    
    return all_clips


def find_project_root():
    """Find the project root directory (where 'data' folder exists)."""
    current = Path(__file__).resolve().parent
    # Start from Code/phase0, go up to find FYP root
    # Check current, then parent (Code), then parent.parent (FYP)
    for level in [current, current.parent, current.parent.parent]:
        if level and (level / "data").exists() and (level / "Code").exists():
            return level
    # Fallback: go up two levels from Code/phase0
    return current.parent.parent


def main():
    parser = argparse.ArgumentParser("Download YouTube Audio for Phase 0")
    parser.add_argument("--domain", type=str, required=False, 
                       choices=["broadcast", "podcast", "social", "all"],
                       default="all",
                       help="Domain type: broadcast, podcast, social, or all")
    parser.add_argument("--max_videos", type=int, default=300,
                       help="Maximum number of videos to download per domain")
    parser.add_argument("--output_dir", type=str, 
                       default="data/realworld/youtube",
                       help="Output directory for downloaded audio")
    parser.add_argument("--clip_length", type=int, default=10,
                       help="Length of each clip in seconds")
    parser.add_argument("--use_gpu", action="store_true",
                       help="Use GPU for audio processing (default: auto-detect)")
    parser.add_argument("--process_existing", action="store_true",
                       help="Process existing downloaded files without downloading new ones")
    parser.add_argument("--skip_channels", action="store_true",
                       help="Skip channel downloads and only use search queries (faster, more reliable)")
    
    args = parser.parse_args()
    
    # Resolve output_dir relative to project root
    project_root = find_project_root()
    if not os.path.isabs(args.output_dir):
        args.output_dir = os.path.join(str(project_root), args.output_dir)
    
    # GPU usage: default to auto-detect if not explicitly set
    use_gpu = args.use_gpu and USE_GPU
    if not args.use_gpu:
        use_gpu = USE_GPU  # Auto-detect by default
    
    # Handle "all" domain mode
    if args.domain == "all":
        domains = ["broadcast", "podcast", "social"]
        for domain in domains:
            print(f"\n{'='*60}")
            print(f"[INFO] Processing domain: {domain}")
            print(f"{'='*60}\n")
            
            # Check if output_dir already ends with domain name to avoid duplication
            output_path = Path(args.output_dir)
            if output_path.name == domain:
                domain_output = str(output_path)
            else:
                domain_output = os.path.join(args.output_dir, domain)
            os.makedirs(domain_output, exist_ok=True)
            
            if args.process_existing:
                # Process existing files
                domain_path = Path(domain_output)
                if not domain_path.exists():
                    print(f"[WARN] Directory does not exist: {domain_output}")
                    continue
                
                existing_files = list(domain_path.glob("*.wav"))
                if existing_files:
                    print(f"[INFO] Found {len(existing_files)} existing files to process in {domain_output}")
                    clips = process_downloaded_audio(
                        [str(f) for f in existing_files],
                        domain_output,
                        domain,
                        args.clip_length,
                        use_gpu=use_gpu
                    )
                    print(f"[OK] Created {len(clips)} clips for {domain}")
                else:
                    print(f"[INFO] No existing files found for {domain} in {domain_output}")
                    print(f"[INFO] Searched in: {domain_path.absolute()}")
            else:
                # Download and process
                if domain == "broadcast":
                    channels = [
                        "https://www.youtube.com/@GeoNews",
                        "https://www.youtube.com/@BBCNews",
                        "https://www.youtube.com/@CNN"
                    ]
                    queries = ["news broadcast", "breaking news", "latest news"]
                elif domain == "podcast":
                    channels = [
                        "https://www.youtube.com/@lexfridman",
                        "https://www.youtube.com/@joerogan",
                        "https://www.youtube.com/@TED"
                    ]
                    queries = ["podcast interview", "podcast conversation"]
                elif domain == "social":
                    channels = [
                        "https://www.youtube.com/@MrBeast",
                        "https://www.youtube.com/@mkbhd"
                    ]
                    queries = ["vlog real voice", "daily vlog"]
                
                downloaded = []
                if channels and not args.skip_channels:
                    print(f"[INFO] Starting channel downloads (max {args.max_videos} videos)...")
                    print(f"[INFO] Note: Channels can be slow. Use --skip_channels to use only search queries.")
                    downloaded.extend(download_from_channels(channels, domain_output, domain, args.max_videos))
                    print(f"[OK] Downloaded {len(downloaded)} videos from channels")
                elif args.skip_channels:
                    print(f"[INFO] Skipping channels (--skip_channels flag set)")
                
                if len(downloaded) < args.max_videos and queries:
                    remaining = args.max_videos - len(downloaded)
                    additional = download_from_search_queries(queries, domain_output, domain, remaining, downloaded)
                    downloaded.extend(additional)
                    downloaded = list(dict.fromkeys(downloaded))
                
                print(f"[OK] Downloaded {len(downloaded)} videos for {domain}")
                
                if downloaded:
                    clips = process_downloaded_audio(downloaded, domain_output, domain, args.clip_length, use_gpu=use_gpu)
                    print(f"[OK] Created {len(clips)} clips for {domain}")
                    
                    metadata = {
                        "domain": domain,
                        "videos_downloaded": len(downloaded),
                        "clips_created": len(clips),
                        "clip_length": args.clip_length
                    }
                    metadata_path = os.path.join(domain_output, "metadata.json")
                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f, indent=2)
        
        return
    
    # Single domain mode
    # Check if output_dir already ends with domain name to avoid duplication
    output_path = Path(args.output_dir)
    if output_path.name == args.domain:
        domain_output = str(output_path)
    else:
        domain_output = os.path.join(args.output_dir, args.domain)
    os.makedirs(domain_output, exist_ok=True)
    
    if args.process_existing:
        # Process existing files
        domain_path = Path(domain_output)
        if not domain_path.exists():
            print(f"[WARN] Directory does not exist: {domain_output}")
            print(f"[INFO] Looking for files in: {domain_path.absolute()}")
            return
        
        existing_files = list(domain_path.glob("*.wav"))
        if existing_files:
            print(f"[INFO] Found {len(existing_files)} existing files to process in {domain_output}")
            clips = process_downloaded_audio(
                [str(f) for f in existing_files],
                domain_output,
                args.domain,
                args.clip_length,
                use_gpu=use_gpu
            )
            print(f"[OK] Created {len(clips)} clips")
        else:
            print(f"[INFO] No existing files found in {domain_output}")
            print(f"[INFO] Searched in: {domain_path.absolute()}")
    else:
        # Download and process
        if args.domain == "broadcast":
            channels = [
                "https://www.youtube.com/@GeoNews",
                "https://www.youtube.com/@BBCNews",
                "https://www.youtube.com/@CNN"
            ]
            queries = ["news broadcast", "breaking news", "latest news"]
        elif args.domain == "podcast":
            channels = [
                "https://www.youtube.com/@lexfridman",
                "https://www.youtube.com/@joerogan",
                "https://www.youtube.com/@TED"
            ]
            queries = ["podcast interview", "podcast conversation"]
        elif args.domain == "social":
            channels = [
                "https://www.youtube.com/@MrBeast",
                "https://www.youtube.com/@mkbhd"
            ]
            queries = ["vlog real voice", "daily vlog"]
        
        downloaded = []
        if channels and not args.skip_channels:
            print(f"[INFO] Starting channel downloads (max {args.max_videos} videos)...")
            print(f"[INFO] Note: Channels can be slow. Use --skip_channels to use only search queries.")
            downloaded.extend(download_from_channels(channels, domain_output, args.domain, args.max_videos))
            print(f"[OK] Downloaded {len(downloaded)} videos from channels")
        elif args.skip_channels:
            print(f"[INFO] Skipping channels (--skip_channels flag set)")
        
        if len(downloaded) < args.max_videos and queries:
            remaining = args.max_videos - len(downloaded)
            additional = download_from_search_queries(queries, domain_output, args.domain, remaining, downloaded)
            downloaded.extend(additional)
            downloaded = list(dict.fromkeys(downloaded))
        
        print(f"[OK] Downloaded {len(downloaded)} videos")
        
        if downloaded:
            clips = process_downloaded_audio(downloaded, domain_output, args.domain, args.clip_length, use_gpu=use_gpu)
            print(f"[OK] Created {len(clips)} clips")
            
            metadata = {
                "domain": args.domain,
                "videos_downloaded": len(downloaded),
                "clips_created": len(clips),
                "clip_length": args.clip_length
            }
            metadata_path = os.path.join(domain_output, "metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"[OK] Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()
