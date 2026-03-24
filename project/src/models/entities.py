from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

JobStatus = Literal["queued", "running", "failed", "done"]
TranscriptionMode = Literal["normal", "pop", "electronic", "classical", "black"]


@dataclass(slots=True)
class TranscriptionJob:
    """Runtime job metadata for one transcription request."""

    source_path: Path
    mode: TranscriptionMode = "normal"
    status: JobStatus = "queued"
    progress: int = 0


@dataclass(slots=True)
class ScoreDocument:
    """Minimal score representation before real model output is integrated."""

    title: str
    notes: list[str] = field(default_factory=list)
    tempo_bpm: int = 120
