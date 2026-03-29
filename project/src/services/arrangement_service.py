from __future__ import annotations

from dataclasses import replace

from src.models.entities import ChordEvent, NoteEvent, TranscriptionMode


def mode_tempo(mode: TranscriptionMode) -> int:
    """Return a default tempo aligned with the selected transcription mode."""

    tempo_map: dict[TranscriptionMode, int] = {
        "normal": 120,
        "pop": 124,
        "electronic": 128,
        "classical": 112,
        "black": 140,
    }
    return tempo_map[mode]


def apply_mode_arrangement(
    mode: TranscriptionMode,
    notes: list[NoteEvent],
    chords: list[ChordEvent],
) -> tuple[list[NoteEvent], list[ChordEvent]]:
    """Apply lightweight mode-specific arrangement rules over inferred notes/chords."""

    if mode == "normal":
        return list(notes), list(chords)
    if mode == "pop":
        return _arrange_pop(notes), list(chords)
    if mode == "electronic":
        return _arrange_electronic(notes), _arrange_electronic_chords(chords)
    if mode == "classical":
        return _arrange_classical(notes), list(chords)
    return _arrange_black(notes), list(chords)


def _arrange_pop(notes: list[NoteEvent]) -> list[NoteEvent]:
    arranged: list[NoteEvent] = []
    for note in notes:
        if note.hand == "right":
            arranged.append(replace(note, velocity=min(127, note.velocity + 8)))
            continue
        arranged.append(replace(note, velocity=max(1, note.velocity - 8)))
    return arranged


def _arrange_electronic(notes: list[NoteEvent]) -> list[NoteEvent]:
    arranged: list[NoteEvent] = []
    for note in notes:
        start = round(note.start_sec * 4) / 4
        end = round(note.end_sec * 4) / 4
        if end <= start:
            end = start + 0.25
        arranged.append(replace(note, start_sec=start, end_sec=end, velocity=96))
    return arranged


def _arrange_electronic_chords(chords: list[ChordEvent]) -> list[ChordEvent]:
    return [replace(chord, symbol=f"{chord.symbol}:loop") for chord in chords]


def _arrange_classical(notes: list[NoteEvent]) -> list[NoteEvent]:
    arranged: list[NoteEvent] = list(notes)
    for note in notes:
        if note.hand != "right":
            continue
        arranged.append(
            NoteEvent(
                pitch_midi=min(127, note.pitch_midi + 12),
                velocity=max(1, note.velocity - 10),
                start_sec=note.start_sec,
                end_sec=note.end_sec,
                hand="right",
            )
        )
    return arranged


def _arrange_black(notes: list[NoteEvent]) -> list[NoteEvent]:
    arranged: list[NoteEvent] = list(notes)
    for note in notes:
        duration = max(0.1, note.end_sec - note.start_sec)
        mid = note.start_sec + duration / 2
        arranged.append(
            NoteEvent(
                pitch_midi=min(127, note.pitch_midi + 12),
                velocity=min(127, note.velocity + 12),
                start_sec=note.start_sec,
                end_sec=mid,
                hand=note.hand,
            )
        )
        arranged.append(
            NoteEvent(
                pitch_midi=max(0, note.pitch_midi - 12),
                velocity=min(127, note.velocity + 6),
                start_sec=mid,
                end_sec=note.end_sec,
                hand=note.hand,
            )
        )
    return arranged