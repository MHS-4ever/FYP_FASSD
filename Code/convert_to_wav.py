import os
import subprocess
from multiprocessing import Pool, cpu_count, Manager
from pathlib import Path
import time

def convert_single_file(args):
    """Convert a single audio file using FFmpeg (much faster than pydub)"""
    filename, input_folder, output_folder, counter, lock = args
    
    file_path = os.path.join(input_folder, filename)
    output_filename = os.path.splitext(filename)[0] + '.wav'
    output_path = os.path.join(output_folder, output_filename)
    
    # Skip if already converted
    if os.path.exists(output_path):
        with lock:
            counter['skipped'] += 1
            if counter['skipped'] % 100 == 0:
                print(f"Skipped {counter['skipped']} already converted files...")
        return f"SKIP: {filename}"
    
    # Only process audio files
    if not filename.lower().endswith(('.mp3', '.flac', '.ogg', '.wav', '.m4a', '.aac')):
        return f"SKIP: {filename} (not audio)"
    
    try:
        # Use FFmpeg for fast conversion: 16kHz, mono
        result = subprocess.run(
            ['ffmpeg', '-i', file_path, '-ar', '16000', '-ac', '1', '-y', output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30
        )
        
        if result.returncode == 0:
            with lock:
                counter['success'] += 1
                total_done = counter['success'] + counter['failed']
                if total_done % 100 == 0:
                    elapsed = time.time() - counter['start_time']
                    rate = total_done / elapsed
                    remaining = counter['total'] - total_done - counter['skipped']
                    eta = remaining / rate if rate > 0 else 0
                    print(f"[{total_done}/{counter['total']}] Rate: {rate:.1f} files/sec | ETA: {eta/3600:.1f} hours")
            return f"OK: {filename}"
        else:
            with lock:
                counter['failed'] += 1
            return f"FAIL: {filename}"
            
    except Exception as e:
        with lock:
            counter['failed'] += 1
        return f"ERROR: {filename}: {e}"

def convert_all_to_wav(input_folder, output_folder, num_workers=None):
    """Convert all audio files using parallel processing"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all files
    files = [f for f in os.listdir(input_folder) 
             if os.path.isfile(os.path.join(input_folder, f))]
    total = len(files)
    
    print(f"Found {total} files to process")
    
    # Use all CPU cores by default
    if num_workers is None:
        num_workers = cpu_count()
    
    print(f"Using {num_workers} parallel workers")
    
    # Shared counter for progress tracking
    manager = Manager()
    counter = manager.dict()
    counter['success'] = 0
    counter['failed'] = 0
    counter['skipped'] = 0
    counter['total'] = total
    counter['start_time'] = time.time()
    lock = manager.Lock()
    
    # Prepare arguments for each file
    args_list = [(f, input_folder, output_folder, counter, lock) for f in files]
    
    start_time = time.time()
    
    # Process files in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(convert_single_file, args_list)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Total files: {total}")
    print(f"Successful: {counter['success']}")
    print(f"Failed: {counter['failed']}")
    print(f"Skipped: {counter['skipped']}")
    print(f"Time elapsed: {elapsed/3600:.2f} hours ({elapsed/60:.1f} minutes)")
    print(f"Average rate: {(counter['success'] + counter['failed'])/elapsed:.1f} files/second")
    print(f"{'='*60}")

if __name__ == "__main__":
    input_folder = input("Enter the path to the folder containing audio clips: ").strip()
    output_folder = input("Enter the path to the output folder for WAV clips: ").strip()
    
    # Optional: customize number of workers (default: all CPU cores)
    custom_workers = input(f"Number of workers (default {cpu_count()}, press Enter to use default): ").strip()
    num_workers = int(custom_workers) if custom_workers else None
    
    print(f"\nStarting conversion...")
    convert_all_to_wav(input_folder, output_folder, num_workers)
