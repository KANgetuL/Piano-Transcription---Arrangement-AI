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
class AudioSegment:
    """Time-sliced chunk description used as model preprocessing output."""

    segment_id: str
    start_sec: float
    end_sec: float
    sample_rate: int


@dataclass(slots=True)
class NoteEvent:
    """Single note event predicted by a model."""

    pitch_midi: int
    velocity: int
    start_sec: float
    end_sec: float
    hand: Literal["left", "right", "auto"] = "auto"


@dataclass(slots=True)
class ChordEvent:
    """Chord event extracted from harmonic analysis."""

    symbol: str
    start_sec: float
    end_sec: float


@dataclass(slots=True)
class TranscriptionRequest:
    """Protocol input for model orchestration layer."""

    source_path: Path
    mode: TranscriptionMode
    task_id: str
    sample_rate: int = 44100


@dataclass(slots=True)
class TranscriptionResult:
    """Protocol output for model orchestration layer."""

    task_id: str
    title: str
    tempo_bpm: int
    key_signature: str
    time_signature: str
    bars: int
    segments: list[AudioSegment] = field(default_factory=list)
    notes: list[NoteEvent] = field(default_factory=list)
    chords: list[ChordEvent] = field(default_factory=list)


@dataclass(slots=True)
class ScoreDocument:
    """Minimal score representation before real model output is integrated."""

    title: str
    notes: list[str] = field(default_factory=list)
    tempo_bpm: int = 120


def to_score_document(result: TranscriptionResult) -> ScoreDocument:
    """Convert protocol result to current minimal score document format."""

    note_lines = [
        f"{n.pitch_midi} v{n.velocity} {n.start_sec:.2f}-{n.end_sec:.2f} {n.hand}"
        for n in result.notes
    ]
    if not note_lines:
        note_lines = ["no-notes"]
    return ScoreDocument(title=result.title, notes=note_lines, tempo_bpm=result.tempo_bpm)
