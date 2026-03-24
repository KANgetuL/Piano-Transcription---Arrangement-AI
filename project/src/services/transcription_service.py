from __future__ import annotations

from pathlib import Path

from src.models.entities import ScoreDocument, TranscriptionMode


def transcribe_stub(source_path: Path, mode: TranscriptionMode) -> ScoreDocument:
    """Temporary stub that will be replaced by real model orchestration."""

    title = source_path.stem
    notes = [f"mode={mode}", "C4 quarter", "E4 quarter", "G4 half"]
    return ScoreDocument(title=title, notes=notes, tempo_bpm=120)
