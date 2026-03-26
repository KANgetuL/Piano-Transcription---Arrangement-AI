from __future__ import annotations

from src.models.entities import (
    AudioSegment,
    ChordEvent,
    NoteEvent,
    TranscriptionRequest,
    TranscriptionResult,
)


def transcribe_stub(request: TranscriptionRequest) -> TranscriptionResult:
    """Temporary protocol-level stub for future model orchestration."""

    mode_bias = {
        "normal": 60,
        "pop": 64,
        "electronic": 67,
        "classical": 62,
        "black": 72,
    }
    base_pitch = mode_bias[request.mode]

    segments = [
        AudioSegment(segment_id=f"{request.task_id}_seg_01", start_sec=0.0, end_sec=1.5, sample_rate=request.sample_rate)
    ]
    notes = [
        NoteEvent(pitch_midi=base_pitch, velocity=90, start_sec=0.0, end_sec=0.5, hand="right"),
        NoteEvent(pitch_midi=base_pitch + 4, velocity=88, start_sec=0.5, end_sec=1.0, hand="right"),
        NoteEvent(pitch_midi=base_pitch - 12, velocity=84, start_sec=0.0, end_sec=1.0, hand="left"),
    ]
    chords = [ChordEvent(symbol="C:maj", start_sec=0.0, end_sec=1.5)]

    return TranscriptionResult(
        task_id=request.task_id,
        title=request.source_path.stem,
        tempo_bpm=120,
        key_signature="C",
        time_signature="4/4",
        bars=1,
        segments=segments,
        notes=notes,
        chords=chords,
    )
