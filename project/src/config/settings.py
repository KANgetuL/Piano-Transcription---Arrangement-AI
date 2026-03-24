from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Application-level settings with safe defaults."""

    supported_audio_extensions: tuple[str, ...] = (".mp3", ".wav")
    output_dir: Path = Path("./outputs")


def get_settings() -> AppSettings:
    return AppSettings()
