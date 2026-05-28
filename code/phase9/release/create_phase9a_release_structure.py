"""Create Phase 9A release skeleton structure.

This script is intentionally non-executed by Cursor in Phase 9A.
It can be run manually by the user later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SkeletonItem:
    path: Path
    is_dir: bool = False
    default_content: str = ""


REPO_ROOT = Path(__file__).resolve().parents[3]


def _touch_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return f"exists: {path.as_posix()}"
    path.write_text(content, encoding="utf-8")
    return f"created: {path.as_posix()}"


def _ensure_dir(path: Path) -> str:
    if path.exists():
        return f"exists: {path.as_posix()}"
    path.mkdir(parents=True, exist_ok=True)
    return f"created: {path.as_posix()}"


def build_items(root: Path) -> Iterable[SkeletonItem]:
    release = root / "release"
    reports = root / "reports" / "phase9"
    return (
        SkeletonItem(release, is_dir=True),
        SkeletonItem(release / "config", is_dir=True),
        SkeletonItem(release / "models" / "origin", is_dir=True),
        SkeletonItem(release / "models" / "replay", is_dir=True),
        SkeletonItem(release / "models" / "mixer", is_dir=True),
        SkeletonItem(release / "models" / "partial_segment", is_dir=True),
        SkeletonItem(release / "src", is_dir=True),
        SkeletonItem(release / "docs", is_dir=True),
        SkeletonItem(release / "sample_audio", is_dir=True),
        SkeletonItem(release / "sample_outputs", is_dir=True),
        SkeletonItem(reports / "roadmap", is_dir=True),
        SkeletonItem(reports / "release", is_dir=True),
        SkeletonItem(reports / "validation", is_dir=True),
        SkeletonItem(
            reports / "release" / "phase9a_release_structure_report.md",
            default_content=(
                "# Phase 9A Release Structure Report\n\n"
                "- skeleton created\n"
                "- no models packaged\n"
                "- no inference run\n"
                "- no app launched\n"
            ),
        ),
    )


def create_phase9a_release_structure() -> list[str]:
    logs: list[str] = []
    for item in build_items(REPO_ROOT):
        if item.is_dir:
            logs.append(_ensure_dir(item.path))
        else:
            logs.append(_touch_file(item.path, item.default_content))
    return logs


if __name__ == "__main__":
    print(
        "Phase 9A helper script ready. Run manually if you want to create "
        "missing skeleton folders/files."
    )
    for line in create_phase9a_release_structure():
        print(line)
