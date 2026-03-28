from __future__ import annotations

from pathlib import Path

from src.services.score_edit_service import (
    add_chord,
    load_editable_score,
    remove_chord,
    save_editable_score,
    scale_rhythm,
    update_chord,
    update_note_duration,
    update_note_pitch,
)


def test_load_and_save_editable_score(tmp_path: Path) -> None:
    file_path = tmp_path / "score.txt"
    file_path.write_text("60 v80 0.00-0.50 right\nchord C:maj 0.00-1.00", encoding="utf-8")

    score = load_editable_score(file_path)
    save_path = tmp_path / "saved.txt"
    save_editable_score(score, save_path)

    saved = save_path.read_text(encoding="utf-8")
    assert "60 v80 0.00-0.50 right" in saved
    assert "chord C:maj 0.00-1.00" in saved


def test_update_note_pitch_and_duration(tmp_path: Path) -> None:
    file_path = tmp_path / "score.txt"
    file_path.write_text("60 v80 0.10-0.60 right", encoding="utf-8")
    score = load_editable_score(file_path)

    update_note_pitch(score, 0, 67)
    update_note_duration(score, 0, 0.75)

    assert score.notes[0].pitch_midi == 67
    assert abs(score.notes[0].end_sec - 0.85) < 1e-8


def test_chord_add_update_remove(tmp_path: Path) -> None:
    file_path = tmp_path / "score.txt"
    file_path.write_text("60 v80 0.00-0.50 right", encoding="utf-8")
    score = load_editable_score(file_path)

    add_chord(score, "Am", 0.0, 1.0)
    update_chord(score, 0, symbol="F:maj", start_sec=0.2, end_sec=1.2)
    assert score.chords[0].symbol == "F:maj"
    assert abs(score.chords[0].start_sec - 0.2) < 1e-8

    remove_chord(score, 0)
    assert len(score.chords) == 0


def test_scale_rhythm_applies_to_notes_and_chords(tmp_path: Path) -> None:
    file_path = tmp_path / "score.txt"
    file_path.write_text("60 v80 0.50-1.00 right\nchord C:maj 1.00-2.00", encoding="utf-8")
    score = load_editable_score(file_path)

    scale_rhythm(score, 2.0)

    assert abs(score.notes[0].start_sec - 1.0) < 1e-8
    assert abs(score.notes[0].end_sec - 2.0) < 1e-8
    assert abs(score.chords[0].start_sec - 2.0) < 1e-8
    assert abs(score.chords[0].end_sec - 4.0) < 1e-8