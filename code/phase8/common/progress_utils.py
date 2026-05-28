"""
Shared progress display for long-running Phase 8 scripts.
"""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, TypeVar

T = TypeVar("T")

_TQDM_AVAILABLE = False
try:
    from tqdm import tqdm as _tqdm

    _TQDM_AVAILABLE = True
except ImportError:
    _tqdm = None  # type: ignore


def progress_method() -> str:
    return "tqdm" if _TQDM_AVAILABLE else "fallback"


def iter_with_progress(
    items: Iterable[T],
    *,
    total: int | None,
    desc: str,
    enabled: bool = True,
    progress_every: int = 100,
    unit: str = "it",
) -> Iterator[T]:
    """Iterate with tqdm bar or periodic console prints."""
    if not enabled:
        yield from items
        return

    if _TQDM_AVAILABLE and _tqdm is not None:
        yield from _tqdm(items, total=total, desc=desc, unit=unit)
        return

    n = 0
    for item in items:
        n += 1
        if progress_every > 0 and (n == 1 or n % progress_every == 0 or (total and n == total)):
            tot_s = str(total) if total is not None else "?"
            print(f"[progress] {desc}: {n}/{tot_s}", flush=True)
        yield item
    if total is not None and n > 0 and (progress_every <= 0 or n % progress_every != 0):
        print(f"[progress] {desc}: {n}/{total} done", flush=True)


def run_with_progress(
    total: int,
    desc: str,
    fn: Callable[[int], None],
    *,
    enabled: bool = True,
    progress_every: int = 100,
) -> None:
    """Run indexed loop 0..total-1 with progress."""
    if total <= 0:
        return

    def _gen():
        for i in range(total):
            yield i

    for i in iter_with_progress(
        _gen(),
        total=total,
        desc=desc,
        enabled=enabled,
        progress_every=progress_every,
    ):
        fn(i)
