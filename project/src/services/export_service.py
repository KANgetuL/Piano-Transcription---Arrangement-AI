from __future__ import annotations

from pathlib import Path
from typing import Literal

from src.models.entities import ScoreDocument


def export_to_text(score: ScoreDocument, output_dir: Path) -> Path:
    """Export stub score as plain text for early workflow validation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{score.title}.txt"
    out_path.write_text("\n".join(score.notes), encoding="utf-8")
    return out_path


def export_to_midi(score: ScoreDocument, output_dir: Path) -> Path:
    """Export placeholder MIDI content for integration flow validation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{score.title}.mid"
    payload = [
        "MIDI-STUB",
        f"TITLE:{score.title}",
        f"TEMPO:{score.tempo_bpm}",
        *score.notes,
    ]
    out_path.write_text("\n".join(payload), encoding="utf-8")
    return out_path


def export_to_musicxml(score: ScoreDocument, output_dir: Path) -> Path:
    """Export placeholder MusicXML content for integration flow validation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{score.title}.musicxml"
    note_lines = "\n".join(f"    <note>{n}</note>" for n in score.notes)
    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<score-partwise version=\"3.1\">\n"
        f"  <work><work-title>{score.title}</work-title></work>\n"
        f"  <identification><creator type=\"arranger\">PianoTrans AI</creator></identification>\n"
        f"  <defaults><tempo>{score.tempo_bpm}</tempo></defaults>\n"
        "  <part id=\"P1\">\n"
        f"{note_lines}\n"
        "  </part>\n"
        "</score-partwise>\n"
    )
    out_path.write_text(xml, encoding="utf-8")
    return out_path


def export_score(score: ScoreDocument, output_dir: Path, fmt: str) -> Path:
    normalized = fmt.strip().lower()
    if normalized == "txt":
        return export_to_text(score, output_dir)
    if normalized == "mid":
        return export_to_midi(score, output_dir)
    if normalized == "musicxml":
        return export_to_musicxml(score, output_dir)
    raise ValueError(f"Unsupported export format: {fmt}")
