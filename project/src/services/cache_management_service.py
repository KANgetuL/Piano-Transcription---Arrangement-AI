from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CacheStatus:
    cache_dir: Path
    file_count: int
    total_size_bytes: int


def get_cache_status(cache_dir: Path) -> CacheStatus:
    if not cache_dir.exists():
        return CacheStatus(cache_dir=cache_dir, file_count=0, total_size_bytes=0)

    file_count = 0
    total_size_bytes = 0
    for path in cache_dir.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        total_size_bytes += path.stat().st_size

    return CacheStatus(cache_dir=cache_dir, file_count=file_count, total_size_bytes=total_size_bytes)


def clear_cache(cache_dir: Path) -> int:
    if not cache_dir.exists():
        return 0

    removed = 0
    for path in sorted(cache_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            path.unlink()
            removed += 1
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                # Keep non-empty directories untouched.
                pass

    return removed