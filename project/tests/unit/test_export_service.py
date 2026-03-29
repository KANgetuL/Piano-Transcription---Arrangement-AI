from __future__ import annotations

from pathlib import Path

from src.models.entities import ScoreDocument
from src.services.export_service import export_score, export_to_midi, export_to_musicxml


def test_export_to_midi_creates_mid_file(tmp_path: Path) -> None:
    score = ScoreDocument(title="demo", notes=["60 v90 0.00-0.50 right"], tempo_bpm=120)

    out = export_to_midi(score, tmp_path)

    assert out.suffix == ".mid"
    content = out.read_text(encoding="utf-8")
    assert "MIDI-STUB" in content
    assert "TEMPO:120" in content


def test_export_to_musicxml_creates_musicxml_file(tmp_path: Path) -> None:
    score = ScoreDocument(title="demo", notes=["60 v90 0.00-0.50 right"], tempo_bpm=128)

    out = export_to_musicxml(score, tmp_path)

    assert out.suffix == ".musicxml"
    content = out.read_text(encoding="utf-8")
    assert "<score-partwise" in content
    assert "<work-title>demo</work-title>" in content


def test_export_score_dispatches_by_format(tmp_path: Path) -> None:
    score = ScoreDocument(title="dispatch", notes=["n1"], tempo_bpm=100)

    out_txt = export_score(score, tmp_path, "txt")
    out_mid = export_score(score, tmp_path, "mid")
    out_xml = export_score(score, tmp_path, "musicxml")

    assert out_txt.suffix == ".txt"
    assert out_mid.suffix == ".mid"
    assert out_xml.suffix == ".musicxml"


def test_export_score_accepts_case_and_space_variants(tmp_path: Path) -> None:
    score = ScoreDocument(title="dispatch2", notes=["n1"], tempo_bpm=100)

    out_mid = export_score(score, tmp_path, " MID ")
    out_xml = export_score(score, tmp_path, "MusicXML")

    assert out_mid.suffix == ".mid"
    assert out_xml.suffix == ".musicxml"


def test_export_score_raises_for_unsupported_format(tmp_path: Path) -> None:
    score = ScoreDocument(title="dispatch3", notes=["n1"], tempo_bpm=100)

    try:
        export_score(score, tmp_path, "pdf")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported export format" in str(exc)