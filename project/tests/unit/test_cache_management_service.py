from __future__ import annotations

from pathlib import Path

from src.services.cache_management_service import clear_cache, get_cache_status


def test_get_cache_status_returns_zero_for_missing_dir(tmp_path: Path) -> None:
    status = get_cache_status(tmp_path / "missing_cache")

    assert status.file_count == 0
    assert status.total_size_bytes == 0


def test_get_cache_status_counts_nested_files(tmp_path: Path) -> None:
    cache_dir = tmp_path / "transcription_cache"
    (cache_dir / "a").mkdir(parents=True)
    (cache_dir / "a" / "x.bin").write_bytes(b"12345")
    (cache_dir / "y.bin").write_bytes(b"12")

    status = get_cache_status(cache_dir)

    assert status.file_count == 2
    assert status.total_size_bytes == 7


def test_clear_cache_removes_files_and_nested_dirs(tmp_path: Path) -> None:
    cache_dir = tmp_path / "transcription_cache"
    (cache_dir / "nested").mkdir(parents=True)
    (cache_dir / "nested" / "x.bin").write_bytes(b"123")
    (cache_dir / "root.bin").write_bytes(b"1")

    removed = clear_cache(cache_dir)

    assert removed == 2
    status = get_cache_status(cache_dir)
    assert status.file_count == 0
    assert status.total_size_bytes == 0