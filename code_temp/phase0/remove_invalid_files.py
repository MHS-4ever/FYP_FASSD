"""
Remove Invalid Files from Manifest and Optionally Delete Physical Files

Removes files marked as invalid in the quality report from the manifest.
Optionally deletes the physical files to save space.

Usage:
    python remove_invalid_files.py --manifest data/realworld/manifest_realworld.csv --quality_report data/realworld/statistics/quality_report.json --output data/realworld/manifest_realworld_clean.csv --delete_files
"""

import argparse
import pandas as pd
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser("Remove Invalid Files from Manifest")
    parser.add_argument("--manifest", type=str, required=True,
                       help="Input manifest CSV file")
    parser.add_argument("--quality_report", type=str, required=True,
                       help="Quality report JSON file")
    parser.add_argument("--output", type=str, required=True,
                       help="Output cleaned manifest CSV file")
    parser.add_argument("--delete_files", action="store_true",
                       help="Delete physical files (default: only remove from manifest)")
    
    args = parser.parse_args()
    
    # Load quality report
    print(f"[INFO] Loading quality report: {args.quality_report}")
    with open(args.quality_report, "r", encoding="utf-8") as f:
        quality_report = json.load(f)
    
    # Get list of failed files
    failed_files = [f["filepath"] for f in quality_report["failed_files"]]
    print(f"[INFO] Found {len(failed_files)} invalid files to remove")
    
    # Load manifest
    print(f"[INFO] Loading manifest: {args.manifest}")
    df = pd.read_csv(args.manifest)
    original_count = len(df)
    print(f"[INFO] Original manifest: {original_count} files")
    
    # Remove failed files from manifest
    # Normalize paths for comparison (handle both absolute and relative paths)
    failed_paths = set()
    for failed_file in failed_files:
        # Try both absolute and relative paths
        failed_paths.add(Path(failed_file).resolve())
        failed_paths.add(Path(failed_file))
        # Also try with forward slashes
        failed_paths.add(Path(failed_file.replace("\\", "/")))
    
    def is_failed_file(filepath):
        """Check if filepath matches any failed file."""
        path = Path(filepath)
        # Try absolute path
        if path.resolve() in failed_paths:
            return True
        # Try relative path
        if path in failed_paths:
            return True
        # Try normalized string comparison
        path_str = str(path).replace("\\", "/")
        for failed in failed_files:
            if path_str in str(failed).replace("\\", "/") or str(failed).replace("\\", "/") in path_str:
                return True
        return False
    
    # Filter out failed files
    df_clean = df[~df['filepath'].apply(is_failed_file)]
    removed_count = original_count - len(df_clean)
    
    print(f"[INFO] Removed {removed_count} invalid files from manifest")
    print(f"[INFO] Clean manifest: {len(df_clean)} files")
    
    # Save cleaned manifest
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    print(f"[OK] Cleaned manifest saved to: {output_path}")
    
    # Optionally delete physical files
    if args.delete_files:
        print(f"\n[INFO] Deleting {len(failed_files)} physical files...")
        deleted_count = 0
        not_found_count = 0
        
        for failed_file in failed_files:
            file_path = Path(failed_file)
            # Try absolute path first
            if not file_path.is_absolute():
                # Try relative to project root
                project_root = Path.cwd()
                file_path = project_root / file_path
            
            if file_path.exists():
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARN] Could not delete {file_path}: {e}")
            else:
                not_found_count += 1
        
        print(f"[OK] Deleted {deleted_count} files")
        if not_found_count > 0:
            print(f"[INFO] {not_found_count} files not found (may have been deleted already)")
    else:
        print(f"\n[INFO] Physical files not deleted (use --delete_files to remove them)")
    
    # Summary
    print(f"\n[SUMMARY]")
    print(f"  Original files: {original_count}")
    print(f"  Invalid files: {removed_count}")
    print(f"  Clean files: {len(df_clean)}")
    print(f"  Validity rate: {len(df_clean)/original_count*100:.2f}%")


if __name__ == "__main__":
    main()

