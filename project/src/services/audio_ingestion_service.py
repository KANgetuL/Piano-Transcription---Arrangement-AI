from __future__ import annotations

import os
from pathlib import Path
import wave

from src.models.entities import AudioFileInfo


def validate_audio_file(path: Path, supported_extensions: tuple[str, ...]) -> None:
    """Validate existence and extension for an input audio file."""

    if not path.exists():
        raise FileNotFoundError(f"[ingestion] [validate_audio_file] [file not found: {path}]")

    if path.suffix.lower() not in supported_extensions:
        raise ValueError(
            "[ingestion] [validate_audio_file] "
            f"[unsupported extension: {path.suffix}; expected one of {supported_extensions}]"
        )


def get_audio_file_info(path: Path, supported_extensions: tuple[str, ...]) -> AudioFileInfo:
    """Return normalized metadata for an uploaded audio file."""

    validate_audio_file(path, supported_extensions)
    size_bytes = path.stat().st_size
    duration_sec = _read_duration_sec(path)
    return AudioFileInfo(
        path=path,
        filename=path.name,
        extension=path.suffix.lower(),
        size_bytes=size_bytes,
        duration_sec=duration_sec,
    )


def list_audio_files(
    directory: Path,
    supported_extensions: tuple[str, ...],
    max_items: int = 5,
) -> list[AudioFileInfo]:
    """List uploaded audio files sorted by mtime desc with an optional cap."""

    if max_items < 1:
        raise ValueError("[ingestion] [list_audio_files] [max_items must be >= 1]")
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"[ingestion] [list_audio_files] [directory not found: {directory}]")

    candidates = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in supported_extensions
    ]
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return [get_audio_file_info(path, supported_extensions) for path in candidates[:max_items]]


def rename_audio_file(
    path: Path,
    new_name: str,
    supported_extensions: tuple[str, ...],
) -> Path:
    """Rename an uploaded audio file and preserve extension when omitted."""

    validate_audio_file(path, supported_extensions)
    normalized_name = new_name.strip()
    if not normalized_name:
        raise ValueError("[ingestion] [rename_audio_file] [new_name cannot be empty]")
    if any(sep in normalized_name for sep in ("/", "\\")):
        raise ValueError("[ingestion] [rename_audio_file] [new_name cannot contain path separators]")

    target_name = normalized_name
    if Path(normalized_name).suffix == "":
        target_name = normalized_name + path.suffix.lower()

    target_path = path.with_name(target_name)
    if target_path.exists() and target_path != path:
        raise FileExistsError(f"[ingestion] [rename_audio_file] [target exists: {target_path}]")

    path.rename(target_path)
    return target_path


def delete_audio_file(path: Path, supported_extensions: tuple[str, ...]) -> None:
    """Delete an uploaded audio file after validation."""

    validate_audio_file(path, supported_extensions)
    path.unlink()


def _read_duration_sec(path: Path) -> float | None:
    """Read duration from WAV metadata; return None for other formats."""

    if path.suffix.lower() != ".wav":
        return None

    try:
        with wave.open(os.fspath(path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frames = wav_file.getnframes()
    except (wave.Error, EOFError):
        return None

    if frame_rate <= 0:
        return None
    return frames / frame_rate
