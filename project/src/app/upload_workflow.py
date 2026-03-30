from __future__ import annotations

from pathlib import Path

from src.config.settings import get_settings
from src.models.entities import AudioFileInfo
from src.services.audio_ingestion_service import delete_audio_file, get_audio_file_info, list_audio_files, rename_audio_file


def list_recent_uploads(upload_dir: Path, max_items: int = 5) -> list[AudioFileInfo]:
    """List recent uploaded files using application-level extension settings."""

    settings = get_settings()
    return list_audio_files(
        directory=upload_dir,
        supported_extensions=settings.supported_audio_extensions,
        max_items=max_items,
    )


def rename_uploaded_file(path: Path, new_name: str) -> Path:
    """Rename an uploaded file using application-level extension settings."""

    settings = get_settings()
    return rename_audio_file(path=path, new_name=new_name, supported_extensions=settings.supported_audio_extensions)


def delete_uploaded_file(path: Path) -> None:
    """Delete an uploaded file using application-level extension settings."""

    settings = get_settings()
    delete_audio_file(path=path, supported_extensions=settings.supported_audio_extensions)


def collect_batch_upload_files(paths: tuple[str, ...]) -> tuple[list[AudioFileInfo], list[Path]]:
    """Validate selected files for batch upload and return valid infos plus skipped paths."""

    settings = get_settings()
    valid_files: list[AudioFileInfo] = []
    skipped_files: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if path in seen:
            continue
        seen.add(path)
        try:
            valid_files.append(
                get_audio_file_info(path=path, supported_extensions=settings.supported_audio_extensions)
            )
        except (FileNotFoundError, ValueError):
            skipped_files.append(path)
    return valid_files, skipped_files
