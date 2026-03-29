from __future__ import annotations

from src.models.entities import ChordEvent, NoteEvent
from src.services.arrangement_service import apply_mode_arrangement, mode_tempo


def _sample_notes() -> list[NoteEvent]:
    return [
        NoteEvent(pitch_midi=64, velocity=90, start_sec=0.03, end_sec=0.67, hand="right"),
        NoteEvent(pitch_midi=52, velocity=86, start_sec=0.71, end_sec=1.18, hand="left"),
    ]


def _sample_chords() -> list[ChordEvent]:
    return [ChordEvent(symbol="C:maj", start_sec=0.0, end_sec=1.2)]


def test_mode_tempo_mapping() -> None:
    assert mode_tempo("normal") == 120
    assert mode_tempo("pop") == 124
    assert mode_tempo("electronic") == 128
    assert mode_tempo("classical") == 112
    assert mode_tempo("black") == 140


def test_pop_mode_boosts_right_hand_and_softens_left() -> None:
    notes, _ = apply_mode_arrangement("pop", _sample_notes(), _sample_chords())

    assert notes[0].velocity == 98
    assert notes[1].velocity == 78


def test_electronic_mode_quantizes_timing_and_tags_chord() -> None:
    notes, chords = apply_mode_arrangement("electronic", _sample_notes(), _sample_chords())

    assert notes[0].start_sec == 0.0
    assert notes[0].end_sec == 0.75
    assert notes[0].velocity == 96
    assert chords[0].symbol == "C:maj:loop"


def test_classical_mode_adds_upper_voice() -> None:
    notes, _ = apply_mode_arrangement("classical", _sample_notes(), _sample_chords())

    assert len(notes) == 3
    assert notes[2].pitch_midi == 76


def test_black_mode_increases_note_density() -> None:
    notes, _ = apply_mode_arrangement("black", _sample_notes(), _sample_chords())

    assert len(notes) == 6
    assert max(n.pitch_midi for n in notes) >= 76