"""
Automated YouTube Audio Downloader for Phase 0 Data Collection

Downloads audio from YouTube videos based on search queries or channel names,
then processes them into clips suitable for training.

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
import librosa
import soundfile as sf


def download_video_audio(url_or_query, output_dir, domain, video_id=None):
    """Download audio from a YouTube video or search query."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Use yt-dlp to download audio
    output_template = os.path.join(output_dir, f"%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",  # Best quality
        "--no-playlist",
        "--output", output_template,
        "--quiet",
        "--no-warnings"
    ]
    
    # Add URL or search query
    if url_or_query.startswith("http"):
        cmd.append(url_or_query)
    else:
        # Search query
        cmd.extend(["--default-search", "ytsearch", url_or_query])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            # Find the downloaded file
            wav_files = list(Path(output_dir).glob("*.wav"))
            if wav_files:
                return str(wav_files[-1])  # Return most recent
        return None
    except subprocess.TimeoutError:
        print(f"[WARN] Timeout downloading: {url_or_query}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to download {url_or_query}: {e}")
        return None


def split_audio_into_clips(audio_path, output_dir, clip_length=10, overlap=1):
    """
    Split long audio file into clips of specified length.
    
    Args:
        audio_path: Path to input audio file
        output_dir: Directory to save clips
        clip_length: Length of each clip in seconds
        overlap: Overlap between clips in seconds
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = len(y) / sr
        
        if duration < 1.0:
            return []  # Too short
        
        clips = []
        clip_idx = 0
        start = 0
        
        while start + clip_length <= duration:
            end = start + clip_length
            clip_audio = y[int(start * sr):int(end * sr)]
            
            # Save clip
            clip_name = f"{Path(audio_path).stem}_clip{clip_idx:04d}.wav"
            clip_path = os.path.join(output_dir, clip_name)
            sf.write(clip_path, clip_audio, sr)
            clips.append(clip_path)
            
            clip_idx += 1
            start += (clip_length - overlap)  # Move forward with overlap
        
        return clips
    except Exception as e:
        print(f"[ERROR] Failed to split {audio_path}: {e}")
        return []


def download_from_channels(channels, output_dir, domain, max_videos=300):
    """Download videos from specific YouTube channels."""
    downloaded = []
    
    for channel in tqdm(channels, desc=f"Downloading from channels ({domain})"):
        # Search for channel videos
        query = f"{channel} latest"
        video_path = download_video_audio(query, output_dir, domain)
        
        if video_path:
            downloaded.append(video_path)
            if len(downloaded) >= max_videos:
                break
    
    return downloaded


def download_from_search_queries(queries, output_dir, domain, max_videos=300):
    """Download videos from search queries."""
    downloaded = []
    
    for query in tqdm(queries, desc=f"Downloading from queries ({domain})"):
        video_path = download_video_audio(query, output_dir, domain)
        
        if video_path:
            downloaded.append(video_path)
            if len(downloaded) >= max_videos:
                break
    
    return downloaded


def process_downloaded_audio(downloaded_files, output_dir, domain, clip_length=10):
    """Process downloaded audio files into clips."""
    clips_dir = os.path.join(output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    all_clips = []
    
    for audio_file in tqdm(downloaded_files, desc="Processing audio into clips"):
        clips = split_audio_into_clips(audio_file, clips_dir, clip_length=clip_length)
        all_clips.extend(clips)
        
        # Remove original long file to save space
        try:
            os.remove(audio_file)
        except:
            pass
    
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
    
    args = parser.parse_args()
    
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
    clips = process_downloaded_audio(downloaded, domain_output, args.domain, args.clip_length)
    
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

