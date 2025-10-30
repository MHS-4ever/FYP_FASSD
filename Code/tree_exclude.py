#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import argparse


EXCLUDED_FOLDERS = [
    r"E:\FYP\DataSet\English\DeepFake (DF)\DF_clips",
    r"E:\FYP\DataSet\English\Logical Access (LA)\LA_clips",
    r"E:\FYP\data\features\lfcc",
    r"E:\FYP\data\features\logmel",
    r"E:\FYP\data\features_augmented\lfcc",
    r"E:\FYP\data\features_augmented\logmel",
    r"E:\FYP\data\noise_rir\musan",
    r"E:\FYP\data\noise_rir\rir"
]

def norm(p):
    return os.path.normcase(os.path.normpath(p))

EXCLUDED_FOLDERS = [norm(p) for p in EXCLUDED_FOLDERS]

def is_excluded(path):
    p = norm(path)
    for ex in EXCLUDED_FOLDERS:
        # If ex is a prefix of p (same or subpath), skip
        try:
            if os.path.commonpath([p, ex]) == ex:
                return True
        except ValueError:
            # Different drives or invalid comparison; not excluded
            pass
    return False

def list_dir(path, ignore_hidden):
    try:
        with os.scandir(path) as it:
            entries = []
            for e in it:
                if ignore_hidden and e.name.startswith('.'):
                    continue
                entries.append(e)
            # sort: dirs first, then files, both alphabetically
            entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            return entries
    except PermissionError:
        return []
    except FileNotFoundError:
        return []

def draw_tree(root, prefix="", depth=0, max_depth=None, include_files=True, ignore_hidden=True, out_lines=None):
    if out_lines is None:
        out_lines = []

    if max_depth is not None and depth > max_depth:
        return out_lines

    if is_excluded(root):
        return out_lines

    entries = list_dir(root, ignore_hidden)
    # If not including files, filter to dirs only
    if not include_files:
        entries = [e for e in entries if e.is_dir()]

    # Exclude subtrees that are in excluded list
    entries = [e for e in entries if not is_excluded(os.path.join(root, e.name))]

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        line = f"{prefix}{connector}{entry.name}"
        out_lines.append(line)

        if entry.is_dir(follow_symlinks=False):
            extension = "    " if i == len(entries) - 1 else "│   "
            if max_depth is None or depth < max_depth:
                draw_tree(
                    os.path.join(root, entry.name),
                    prefix + extension,
                    depth + 1,
                    max_depth,
                    include_files,
                    ignore_hidden,
                    out_lines,
                )
    return out_lines

def main():
    parser = argparse.ArgumentParser(description="Print directory tree while excluding specific folders.")
    parser.add_argument("root", nargs="?", default=r"E:\FYP", help="Root folder to tree (default: E:\\FYP)")
    parser.add_argument("--max-depth", type=int, default=None, help="Limit depth (default: unlimited)")
    parser.add_argument("--files", action="store_true", help="Include files (default: directories only)")
    parser.add_argument("--show-hidden", action="store_true", help="Include hidden entries (default: no)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    print(root)
    print("│")
    lines = draw_tree(
        root,
        prefix="",
        depth=1,
        max_depth=args.max_depth,
        include_files=args.files,
        ignore_hidden=not args.show_hidden,
        out_lines=[],
    )
    print("\n".join(lines))

if __name__ == "__main__":
    main()
