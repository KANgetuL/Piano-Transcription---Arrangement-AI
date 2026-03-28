from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


NOTE_PATTERN = re.compile(
    r"^(?P<pitch>\d{1,3})\s+v(?P<velocity>\d{1,3})\s+(?P<start>\d+(?:\.\d+)?)-(?P<end>\d+(?:\.\d+)?)\s+(?P<hand>\w+)$"
)
CHORD_PATTERN = re.compile(
    r"^chord\s+(?P<symbol>\S+)\s+(?P<start>\d+(?:\.\d+)?)-(?P<end>\d+(?:\.\d+)?)$"
)


@dataclass(slots=True)
class EditableNote:
    pitch_midi: int
    velocity: int
    start_sec: float
    end_sec: float
    hand: str


@dataclass(slots=True)
class EditableChord:
    symbol: str
    start_sec: float
    end_sec: float


@dataclass(slots=True)
class EditableScore:
    notes: list[EditableNote] = field(default_factory=list)
    chords: list[EditableChord] = field(default_factory=list)


def load_editable_score(path: Path) -> EditableScore:
    score = EditableScore()
    if not path.exists():
        raise FileNotFoundError(path)

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        note_match = NOTE_PATTERN.match(line)
        if note_match:
            score.notes.append(
                EditableNote(
                    pitch_midi=int(note_match.group("pitch")),
                    velocity=int(note_match.group("velocity")),
                    start_sec=float(note_match.group("start")),
                    end_sec=float(note_match.group("end")),
                    hand=note_match.group("hand"),
                )
            )
            continue

        chord_match = CHORD_PATTERN.match(line)
        if chord_match:
            score.chords.append(
                EditableChord(
                    symbol=chord_match.group("symbol"),
                    start_sec=float(chord_match.group("start")),
                    end_sec=float(chord_match.group("end")),
                )
            )

    return score


def save_editable_score(score: EditableScore, path: Path) -> None:
    lines: list[str] = []
    for note in score.notes:
        lines.append(_format_note(note))
    for chord in score.chords:
        lines.append(_format_chord(chord))
    path.write_text("\n".join(lines), encoding="utf-8")


def update_note_pitch(score: EditableScore, note_index: int, pitch_midi: int) -> None:
    _check_note_index(score, note_index)
    if not 0 <= pitch_midi <= 127:
        raise ValueError("pitch_midi must be in [0, 127]")
    score.notes[note_index].pitch_midi = pitch_midi


def update_note_duration(score: EditableScore, note_index: int, duration_sec: float) -> None:
    _check_note_index(score, note_index)
    if duration_sec <= 0:
        raise ValueError("duration_sec must be greater than 0")
    note = score.notes[note_index]
    note.end_sec = note.start_sec + duration_sec


def add_chord(score: EditableScore, symbol: str, start_sec: float, end_sec: float) -> None:
    _check_time_range(start_sec, end_sec)
    score.chords.append(EditableChord(symbol=symbol, start_sec=start_sec, end_sec=end_sec))


def update_chord(
    score: EditableScore,
    chord_index: int,
    symbol: str | None = None,
    start_sec: float | None = None,
    end_sec: float | None = None,
) -> None:
    _check_chord_index(score, chord_index)
    chord = score.chords[chord_index]
    if symbol is not None:
        chord.symbol = symbol

    new_start = chord.start_sec if start_sec is None else start_sec
    new_end = chord.end_sec if end_sec is None else end_sec
    _check_time_range(new_start, new_end)
    chord.start_sec = new_start
    chord.end_sec = new_end


def remove_chord(score: EditableScore, chord_index: int) -> None:
    _check_chord_index(score, chord_index)
    del score.chords[chord_index]


def scale_rhythm(score: EditableScore, factor: float) -> None:
    if factor <= 0:
        raise ValueError("factor must be greater than 0")
    for note in score.notes:
        note.start_sec *= factor
        note.end_sec *= factor
    for chord in score.chords:
        chord.start_sec *= factor
        chord.end_sec *= factor


def _check_note_index(score: EditableScore, note_index: int) -> None:
    if note_index < 0 or note_index >= len(score.notes):
        raise IndexError("note index out of range")


def _check_chord_index(score: EditableScore, chord_index: int) -> None:
    if chord_index < 0 or chord_index >= len(score.chords):
        raise IndexError("chord index out of range")


def _check_time_range(start_sec: float, end_sec: float) -> None:
    if start_sec < 0:
        raise ValueError("start_sec must be >= 0")
    if end_sec <= start_sec:
        raise ValueError("end_sec must be greater than start_sec")


def _format_note(note: EditableNote) -> str:
    return f"{note.pitch_midi} v{note.velocity} {note.start_sec:.2f}-{note.end_sec:.2f} {note.hand}"


def _format_chord(chord: EditableChord) -> str:
    return f"chord {chord.symbol} {chord.start_sec:.2f}-{chord.end_sec:.2f}"