from __future__ import annotations

from pathlib import Path

from src.config.settings import get_settings
from src.models.entities import AudioFileInfo
from src.services.audio_ingestion_service import delete_audio_file, list_audio_files, rename_audio_file


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
