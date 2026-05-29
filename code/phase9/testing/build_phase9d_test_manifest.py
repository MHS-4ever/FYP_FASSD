#!/usr/bin/env python3
"""
Phase 9D: build controlled end-to-end test manifest from Phase 7C1 raw audio folders.

Does not run inference. Default scan uses controlled category folders only (no full-tree rglob).
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9d_common import (  # noqa: E402
    AUDIO_EXTS,
    DEFAULT_CATEGORY_FOLDERS,
    category_for_folder_name,
    detect_expected_category,
    expectations_for_category,
    is_audio_file,
    make_case_id,
    progress,
    should_skip_dir_name,
)

MANIFEST_COLUMNS = [
    "case_id",
    "audio_path",
    "expected_category",
    "expected_primary_axis",
    "expected_fusion_behavior",
    "expected_manual_review",
    "notes",
]

DEFAULT_REPORT = "reports/phase9/testing/phase9d_manifest_build_report.md"
DEFAULT_OUTPUT_MANIFEST = "reports/phase9/testing/phase9d_test_manifest.csv"
DEFAULT_AUDIO_ROOT = "data/phase7c1/raw"
DEFAULT_BAD_AUDIO_DIR = "reports/phase9/testing/bad_audio_samples"


@dataclass
class ScanStats:
    audio_root: Path
    scan_mode: str
    folders_scanned: list[str] = field(default_factory=list)
    folders_missing: list[str] = field(default_factory=list)
    folders_skipped: list[str] = field(default_factory=list)
    files_considered: int = 0
    categories_found: dict[str, int] = field(default_factory=dict)
    rows_written: int = 0
    warnings: list[str] = field(default_factory=list)
    scan_stopped_early: bool = False


def resolve_project_path(value: str | Path, *, must_be_file: bool = False) -> Path:
    """Resolve path relative to current working directory (project root when run from repo)."""
    p = Path(value)
    if not p.is_absolute():
        p = Path.cwd() / p
    p = p.resolve()
    if must_be_file and p.exists() and p.is_dir():
        raise ValueError(f"Expected a file path, got directory: {p}")
    return p


def validate_manifest_csv_path(path: Path) -> Path:
    path = path.resolve()
    if path.suffix.lower() != ".csv":
        raise ValueError(f"output_manifest must be a CSV file path, got: {path}")
    if path.is_dir() or (path.exists() and path.is_dir()):
        raise ValueError(f"output_manifest must be a CSV file path, got directory: {path}")
    if path == Path.cwd().resolve():
        raise ValueError(f"output_manifest must be a CSV file path, got project root: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def validate_report_md_path(path: Path) -> Path:
    path = path.resolve()
    if path.suffix.lower() != ".md":
        raise ValueError(f"report must be a Markdown file path, got: {path}")
    if path.is_dir() or (path.exists() and path.is_dir()):
        raise ValueError(f"report must be a Markdown file path, got directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def validate_bad_audio_dir(path: Path, *, include_bad_audio: bool) -> Path:
    path = path.resolve()
    if path.is_file():
        raise ValueError(f"bad_audio_dir must be a directory path, got file: {path}")
    cwd = Path.cwd().resolve()
    if include_bad_audio and path == cwd:
        raise ValueError(
            "bad_audio_dir resolves to project root; refusing to create bad audio samples in cwd. "
            "Use --bad_audio_dir reports/phase9/testing/bad_audio_samples"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_audio_root_dir(path: Path) -> Path:
    path = path.resolve()
    if path.is_file():
        raise ValueError(f"audio_root must be a directory path, got file: {path}")
    return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Phase 9D controlled test manifest.")
    p.add_argument("--audio_root", default=DEFAULT_AUDIO_ROOT)
    p.add_argument("--output_manifest", default=DEFAULT_OUTPUT_MANIFEST)
    p.add_argument(
        "--report",
        default=DEFAULT_REPORT,
        help="Markdown report for manifest build diagnostics",
    )
    p.add_argument(
        "--scan_report",
        default=None,
        help=argparse.SUPPRESS,
    )
    p.add_argument("--max_per_category", type=int, default=5)
    p.add_argument("--include_bad_audio_tests", action="store_true")
    p.add_argument("--bad_audio_dir", default=DEFAULT_BAD_AUDIO_DIR)
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument(
        "--scan_mode",
        choices=("controlled_folders", "recursive_limited"),
        default="controlled_folders",
    )
    p.add_argument(
        "--category_folders",
        nargs="*",
        default=None,
        help="Subfolder names under audio_root to scan (default: Phase 7C1 controlled list)",
    )
    p.add_argument("--max_scan_files", type=int, default=5000)
    p.add_argument("--max_files_per_folder_scan", type=int, default=200)
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _maybe_tqdm(items: list, desc: str, no_progress: bool):
    if no_progress:
        return items
    try:
        from tqdm import tqdm

        return tqdm(items, desc=desc, unit="folder")
    except ImportError:
        return items


def _collect_audio_shallow(
    folder: Path,
    per_folder_limit: int,
    stats: ScanStats,
    max_scan_files: int,
) -> list[Path]:
    """Collect audio files in folder root and one subdirectory level (no deep walk)."""
    found: list[Path] = []

    def can_continue() -> bool:
        return len(found) < per_folder_limit and stats.files_considered < max_scan_files

    def add_file(path: Path) -> None:
        if not can_continue() or not is_audio_file(path):
            return
        found.append(path.resolve())
        stats.files_considered += 1

    def scan_dir(directory: Path, depth: int) -> None:
        if not can_continue():
            return
        if should_skip_dir_name(directory.name):
            stats.folders_skipped.append(str(directory))
            return
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if not can_continue():
                        return
                    if entry.is_symlink():
                        continue
                    p = Path(entry.path)
                    if entry.is_file(follow_symlinks=False):
                        add_file(p)
                    elif entry.is_dir(follow_symlinks=False) and depth < 1:
                        if should_skip_dir_name(p.name):
                            stats.folders_skipped.append(str(p))
                            continue
                        scan_dir(p, depth + 1)
        except (OSError, PermissionError) as exc:
            stats.warnings.append(f"scan error in {directory}: {exc}")

    if folder.is_dir() and not folder.is_symlink():
        scan_dir(folder, 0)
    return found


def _scan_controlled_folders(
    audio_root: Path,
    folder_names: list[str],
    max_per_category: int,
    max_scan_files: int,
    max_files_per_folder_scan: int,
    stats: ScanStats,
    no_progress: bool,
) -> dict[str, list[Path]]:
    """Scan only named category folders with early stopping per category."""
    candidate_cap = max(1, max_per_category * 3)
    per_folder_cap = min(max_files_per_folder_scan, candidate_cap * 2)
    grouped: dict[str, list[Path]] = defaultdict(list)

    iterable = _maybe_tqdm(folder_names, "category folders", no_progress)
    for folder_name in iterable:
        if stats.files_considered >= max_scan_files:
            stats.scan_stopped_early = True
            stats.warnings.append(f"max_scan_files ({max_scan_files}) reached; stopping scan")
            break

        folder_path = audio_root / folder_name
        if not folder_path.is_dir() or folder_path.is_symlink():
            stats.folders_missing.append(folder_name)
            continue

        category = category_for_folder_name(folder_name)
        if len(grouped[category]) >= candidate_cap:
            continue

        stats.folders_scanned.append(folder_name)
        remaining_global = max_scan_files - stats.files_considered
        limit = min(per_folder_cap, remaining_global)
        if limit <= 0:
            stats.scan_stopped_early = True
            break

        files = _collect_audio_shallow(folder_path, limit, stats, max_scan_files)
        for fpath in files:
            if len(grouped[category]) >= candidate_cap:
                break
            grouped[category].append(fpath)

        stats.categories_found[category] = len(grouped[category])

        if stats.files_considered >= max_scan_files:
            stats.scan_stopped_early = True
            stats.warnings.append(f"max_scan_files ({max_scan_files}) reached")
            break

    return grouped


def _iter_limited_recursive(
    audio_root: Path,
    max_scan_files: int,
    stats: ScanStats,
) -> Iterator[Path]:
    """Depth-limited walk with skip rules; fallback mode only."""
    stack: list[tuple[Path, int]] = [(audio_root, 0)]
    max_depth = 4

    while stack and stats.files_considered < max_scan_files:
        current, depth = stack.pop()
        if depth > max_depth:
            continue
        if current != audio_root and should_skip_dir_name(current.name):
            stats.folders_skipped.append(str(current))
            continue
        try:
            with os.scandir(current) as entries:
                dirs: list[Path] = []
                for entry in entries:
                    if stats.files_considered >= max_scan_files:
                        stats.scan_stopped_early = True
                        return
                    if entry.is_symlink():
                        continue
                    p = Path(entry.path)
                    if entry.is_file(follow_symlinks=False) and is_audio_file(p):
                        stats.files_considered += 1
                        yield p.resolve()
                    elif entry.is_dir(follow_symlinks=False):
                        dirs.append(p)
                for d in reversed(dirs):
                    stack.append((d, depth + 1))
        except (OSError, PermissionError) as exc:
            stats.warnings.append(f"recursive scan error in {current}: {exc}")


def _scan_recursive_limited(
    audio_root: Path,
    max_per_category: int,
    max_scan_files: int,
    stats: ScanStats,
) -> dict[str, list[Path]]:
    candidate_cap = max(1, max_per_category * 3)
    grouped: dict[str, list[Path]] = defaultdict(list)
    stats.folders_scanned.append(str(audio_root))

    for fpath in _iter_limited_recursive(audio_root, max_scan_files, stats):
        category = detect_expected_category(fpath)
        if len(grouped[category]) >= candidate_cap:
            continue
        grouped[category].append(fpath)
        stats.categories_found[category] = len(grouped[category])
        if all(len(v) >= candidate_cap for v in grouped.values()) and len(grouped) >= 8:
            break

    return grouped


def _select_per_category(
    grouped: dict[str, list[Path]],
    max_per_category: int,
    rng: random.Random,
) -> dict[str, list[Path]]:
    selected: dict[str, list[Path]] = {}
    for category, paths in sorted(grouped.items()):
        pool = list(paths)
        rng.shuffle(pool)
        selected[category] = sorted(pool[:max_per_category])
    return selected


def _write_bad_audio_samples(bad_dir: Path, no_progress: bool) -> list[Path]:
    bad_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    sr = 16000

    try:
        import numpy as np
    except ImportError:
        progress("WARNING: numpy unavailable; skipping bad audio synthesis.", no_progress)
        return created

    short_path = bad_dir / "bad_short_0.3sec.wav"
    silent_path = bad_dir / "bad_silent_3sec.wav"
    invalid_path = bad_dir / "bad_invalid.wav"
    short_wave = np.zeros(int(0.3 * sr), dtype=np.float32)
    silent_wave = np.zeros(int(3.0 * sr), dtype=np.float32)

    written = False
    try:
        import soundfile as sf

        sf.write(short_path, short_wave, sr)
        sf.write(silent_path, silent_wave, sr)
        written = True
    except ImportError:
        try:
            from scipy.io import wavfile

            wavfile.write(short_path, sr, short_wave)
            wavfile.write(silent_path, sr, silent_wave)
            written = True
        except ImportError:
            progress(
                "WARNING: soundfile/scipy unavailable; skipping WAV synthesis for bad audio.",
                no_progress,
            )

    if written:
        created.extend([short_path, silent_path])
        invalid_path.write_text("not a wav file\n", encoding="utf-8")
        created.append(invalid_path)
        progress(f"Created bad audio samples under {bad_dir}", no_progress)
    return created


def _write_scan_report(path: Path, stats: ScanStats, output_manifest: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9D Manifest Build Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- audio_root: `{stats.audio_root}`",
        f"- scan_mode: `{stats.scan_mode}`",
        f"- output_manifest: `{output_manifest}`",
        "",
        "## Summary",
        "",
        f"- folders_scanned: {len(stats.folders_scanned)}",
        f"- folders_missing: {len(stats.folders_missing)}",
        f"- folders_skipped: {len(stats.folders_skipped)}",
        f"- files_considered: {stats.files_considered}",
        f"- rows_written: {stats.rows_written}",
        f"- scan_stopped_early: {stats.scan_stopped_early}",
        "",
        "## Categories found (candidates before sampling)",
        "",
    ]
    if stats.categories_found:
        for cat, count in sorted(stats.categories_found.items()):
            lines.append(f"- `{cat}`: {count}")
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Folders scanned",
            "",
        ]
    )
    for name in stats.folders_scanned:
        lines.append(f"- `{name}`")
    if not stats.folders_scanned:
        lines.append("- (none)")

    if stats.folders_missing:
        lines.extend(["", "## Folders missing (not under audio_root)", ""])
        for name in stats.folders_missing:
            lines.append(f"- `{name}`")

    if stats.folders_skipped:
        lines.extend(["", "## Skipped paths (protected names)", ""])
        for name in stats.folders_skipped[:30]:
            lines.append(f"- `{name}`")
        if len(stats.folders_skipped) > 30:
            lines.append(f"- ... and {len(stats.folders_skipped) - 30} more")

    if stats.warnings:
        lines.extend(["", "## Warnings", ""])
        for w in stats.warnings:
            lines.append(f"- {w}")

    lines.extend(
        [
            "",
            "## Note",
            "",
            "Phase 9D controlled testing scans Phase 7C1 raw category folders only.",
            "Augmented, RIR, noise, features, embeddings, and other massive datasets are",
            "**excluded by default** from this first architecture verification pass.",
            "Large-scale stress testing can be added in a later phase after the local pipeline is stable.",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_manifest(args: argparse.Namespace) -> Path:
    project_root = Path.cwd().resolve()
    report_arg = args.scan_report if args.scan_report else args.report

    audio_root = validate_audio_root_dir(resolve_project_path(args.audio_root))
    output_manifest = validate_manifest_csv_path(resolve_project_path(args.output_manifest))
    report_path = validate_report_md_path(resolve_project_path(report_arg))
    bad_audio_dir = validate_bad_audio_dir(
        resolve_project_path(args.bad_audio_dir),
        include_bad_audio=args.include_bad_audio_tests,
    )
    rng = random.Random(args.random_seed)

    folder_names = list(args.category_folders) if args.category_folders else list(DEFAULT_CATEGORY_FOLDERS)
    stats = ScanStats(audio_root=audio_root, scan_mode=args.scan_mode)

    progress(f"resolved audio_root: {audio_root}", args.no_progress)
    progress(f"output_manifest: {output_manifest}", args.no_progress)
    progress(f"bad_audio_dir: {bad_audio_dir}", args.no_progress)
    progress(f"report: {report_path}", args.no_progress)
    progress(f"scan_mode: {args.scan_mode}", args.no_progress)
    progress(f"category_folders: {len(folder_names)} names", args.no_progress)

    if not audio_root.is_dir():
        stats.warnings.append(f"audio_root does not exist: {audio_root}")

    if args.scan_mode == "controlled_folders":
        grouped = _scan_controlled_folders(
            audio_root,
            folder_names,
            args.max_per_category,
            args.max_scan_files,
            args.max_files_per_folder_scan,
            stats,
            args.no_progress,
        )
    else:
        stats.warnings.append("recursive_limited mode: use only when audio_root is small")
        grouped = _scan_recursive_limited(
            audio_root,
            args.max_per_category,
            args.max_scan_files,
            stats,
        )

    if args.include_bad_audio_tests:
        for bad_path in _write_bad_audio_samples(bad_audio_dir, args.no_progress):
            category = detect_expected_category(bad_path)
            grouped[category].append(bad_path.resolve())
            stats.categories_found[category] = len(grouped[category])

    selected = _select_per_category(grouped, args.max_per_category, rng)

    rows: list[dict[str, str]] = []
    counters: dict[str, int] = defaultdict(int)
    for category in sorted(selected.keys()):
        for audio_path in selected[category]:
            counters[category] += 1
            idx = counters[category]
            exp = expectations_for_category(category)
            try:
                rel_audio = audio_path.relative_to(project_root)
            except ValueError:
                rel_audio = audio_path
            rows.append(
                {
                    "case_id": make_case_id(category, idx, audio_path.stem),
                    "audio_path": str(rel_audio).replace("\\", "/"),
                    "expected_category": category,
                    "expected_primary_axis": exp["expected_primary_axis"],
                    "expected_fusion_behavior": exp["expected_fusion_behavior"],
                    "expected_manual_review": exp["expected_manual_review"],
                    "notes": exp["notes"],
                }
            )

    with output_manifest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    stats.rows_written = len(rows)
    _write_scan_report(report_path, stats, output_manifest)

    progress(f"folders_scanned: {len(stats.folders_scanned)}", args.no_progress)
    progress(f"files_considered: {stats.files_considered}", args.no_progress)
    progress(f"categories_found: {len(stats.categories_found)}", args.no_progress)
    progress(f"rows_written: {stats.rows_written}", args.no_progress)
    progress(f"Manifest: {output_manifest}", args.no_progress)
    progress(f"Scan report: {report_path}", args.no_progress)

    if not rows and audio_root.is_dir():
        warnings.warn(f"No audio files found in controlled folders under {audio_root}")
    elif not audio_root.is_dir():
        warnings.warn(f"Audio root does not exist: {audio_root}")

    return output_manifest


def main() -> int:
    args = parse_args()
    build_manifest(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
