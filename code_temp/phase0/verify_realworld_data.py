"""
Verify Real-World Data Quality for Phase 0

Checks audio quality, duration, sample rate, and generates quality report.

Usage:
    python verify_realworld_data.py --data_dir data/realworld/processed --manifest data/realworld/manifest_realworld.csv
"""

import argparse
import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import librosa
import numpy as np
import json


def verify_audio_file(filepath, min_duration=1.0, max_duration=10.0, target_sr=16000):
    """
    Verify a single audio file.
    
    Returns:
        dict with verification results
    """
    result = {
        "filepath": filepath,
        "exists": False,
        "valid": False,
        "duration": 0.0,
        "sample_rate": 0,
        "channels": 0,
        "corrupted": False,
        "duration_ok": False,
        "sr_ok": False,
        "errors": []
    }
    
    # Check if file exists
    if not os.path.exists(filepath):
        result["errors"].append("File does not exist")
        return result
    
    result["exists"] = True
    
    try:
        # Load audio
        y, sr = librosa.load(filepath, sr=None, mono=False)
        
        # Get metadata
        if y.ndim == 1:
            result["channels"] = 1
        else:
            result["channels"] = y.shape[0]
        
        result["sample_rate"] = sr
        result["duration"] = len(y) / sr if y.ndim == 1 else y.shape[1] / sr
        
        # Check duration
        if result["duration"] < min_duration:
            result["errors"].append(f"Too short: {result['duration']:.2f}s < {min_duration}s")
        elif result["duration"] > max_duration:
            result["errors"].append(f"Too long: {result['duration']:.2f}s > {max_duration}s")
        else:
            result["duration_ok"] = True
        
        # Check sample rate
        if sr != target_sr:
            result["errors"].append(f"Wrong sample rate: {sr} Hz != {target_sr} Hz")
        else:
            result["sr_ok"] = True
        
        # Check for corruption (NaN, Inf, all zeros)
        if y.ndim == 1:
            audio_data = y
        else:
            audio_data = y[0]  # Check first channel
        
        if np.any(np.isnan(audio_data)):
            result["corrupted"] = True
            result["errors"].append("Contains NaN values")
        elif np.any(np.isinf(audio_data)):
            result["corrupted"] = True
            result["errors"].append("Contains Inf values")
        elif np.all(audio_data == 0):
            result["corrupted"] = True
            result["errors"].append("All zeros (silent)")
        elif np.max(np.abs(audio_data)) < 1e-6:
            result["errors"].append("Very quiet (possible issue)")
        
        # If no errors, mark as valid
        if not result["errors"]:
            result["valid"] = True
        
    except Exception as e:
        result["corrupted"] = True
        result["errors"].append(f"Load error: {str(e)}")
    
    return result


def verify_from_manifest(manifest_path, data_dir=None, min_duration=1.0, max_duration=10.0, target_sr=16000, sample=None):
    """Verify all files in manifest."""
    df = pd.read_csv(manifest_path)
    
    if sample:
        df = df.sample(n=min(sample, len(df)), random_state=42)
        print(f"[INFO] Sampling {len(df)} files for verification")
    
    results = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Verifying audio"):
        filepath = row['filepath']
        
        # If relative path, make absolute
        if not os.path.isabs(filepath) and data_dir:
            filepath = os.path.join(data_dir, filepath)
        
        result = verify_audio_file(filepath, min_duration, max_duration, target_sr)
        results.append(result)
    
    return results


def generate_report(results, output_path):
    """Generate quality report from verification results."""
    total = len(results)
    exists = sum(1 for r in results if r["exists"])
    valid = sum(1 for r in results if r["valid"])
    corrupted = sum(1 for r in results if r["corrupted"])
    duration_ok = sum(1 for r in results if r["duration_ok"])
    sr_ok = sum(1 for r in results if r["sr_ok"])
    
    # Collect all errors
    all_errors = {}
    for r in results:
        for error in r["errors"]:
            all_errors[error] = all_errors.get(error, 0) + 1
    
    # Duration statistics
    durations = [r["duration"] for r in results if r["duration"] > 0]
    sample_rates = [r["sample_rate"] for r in results if r["sample_rate"] > 0]
    
    report = {
        "summary": {
            "total_files": total,
            "files_exist": exists,
            "files_valid": valid,
            "files_corrupted": corrupted,
            "duration_ok": duration_ok,
            "sample_rate_ok": sr_ok,
            "validity_rate": valid / total if total > 0 else 0
        },
        "statistics": {
            "duration": {
                "mean": float(np.mean(durations)) if durations else 0,
                "min": float(np.min(durations)) if durations else 0,
                "max": float(np.max(durations)) if durations else 0,
                "std": float(np.std(durations)) if durations else 0
            },
            "sample_rate": {
                "unique_values": list(set(sample_rates)) if sample_rates else [],
                "most_common": int(np.bincount(sample_rates).argmax()) if sample_rates else 0
            }
        },
        "errors": all_errors,
        "failed_files": [
            {
                "filepath": r["filepath"],
                "errors": r["errors"]
            }
            for r in results if not r["valid"]
        ]
    }
    
    # Save report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    parser = argparse.ArgumentParser("Verify Real-World Data Quality")
    parser.add_argument("--data_dir", type=str, default=None,
                       help="Base data directory (for relative paths in manifest)")
    parser.add_argument("--manifest", type=str, required=True,
                       help="Manifest CSV file")
    parser.add_argument("--output", type=str, default="data/realworld/quality_report.json",
                       help="Output quality report JSON")
    parser.add_argument("--min_duration", type=float, default=1.0,
                       help="Minimum duration in seconds")
    parser.add_argument("--max_duration", type=float, default=10.0,
                       help="Maximum duration in seconds")
    parser.add_argument("--target_sr", type=int, default=16000,
                       help="Target sample rate")
    parser.add_argument("--sample", type=int, default=None,
                       help="Sample N files for verification (for large datasets)")
    
    args = parser.parse_args()
    
    print(f"[INFO] Verifying audio files from manifest: {args.manifest}")
    
    # Verify files
    results = verify_from_manifest(
        args.manifest,
        data_dir=args.data_dir,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        target_sr=args.target_sr,
        sample=args.sample
    )
    
    # Generate report
    print(f"[INFO] Generating quality report...")
    report = generate_report(results, args.output)
    
    # Print summary
    print("\n[QUALITY REPORT]")
    print(f"  Total files: {report['summary']['total_files']}")
    print(f"  Files exist: {report['summary']['files_exist']}")
    print(f"  Files valid: {report['summary']['files_valid']} ({report['summary']['validity_rate']*100:.1f}%)")
    print(f"  Files corrupted: {report['summary']['files_corrupted']}")
    print(f"  Duration OK: {report['summary']['duration_ok']}")
    print(f"  Sample rate OK: {report['summary']['sample_rate_ok']}")
    
    if report['statistics']['duration']['mean'] > 0:
        print(f"\n  Duration statistics:")
        print(f"    Mean: {report['statistics']['duration']['mean']:.2f}s")
        print(f"    Range: {report['statistics']['duration']['min']:.2f}s - {report['statistics']['duration']['max']:.2f}s")
    
    if report['errors']:
        print(f"\n  Common errors:")
        for error, count in sorted(report['errors'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {error}: {count}")
    
    if report['failed_files']:
        print(f"\n  Failed files: {len(report['failed_files'])}")
        if len(report['failed_files']) <= 10:
            for failed in report['failed_files']:
                print(f"    {failed['filepath']}: {', '.join(failed['errors'])}")
    
    print(f"\n[OK] Quality report saved to: {args.output}")


if __name__ == "__main__":
    main()

