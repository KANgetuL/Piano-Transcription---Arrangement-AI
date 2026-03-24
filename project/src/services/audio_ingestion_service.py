from __future__ import annotations

from pathlib import Path


def validate_audio_file(path: Path, supported_extensions: tuple[str, ...]) -> None:
    """Validate existence and extension for an input audio file."""

    if not path.exists():
        raise FileNotFoundError(f"[ingestion] [validate_audio_file] [file not found: {path}]")

    if path.suffix.lower() not in supported_extensions:
        raise ValueError(
            "[ingestion] [validate_audio_file] "
            f"[unsupported extension: {path.suffix}; expected one of {supported_extensions}]"
        )
