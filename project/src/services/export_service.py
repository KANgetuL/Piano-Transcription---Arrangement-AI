from __future__ import annotations

from pathlib import Path

from src.models.entities import ScoreDocument


def export_to_text(score: ScoreDocument, output_dir: Path) -> Path:
    """Export stub score as plain text for early workflow validation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{score.title}.txt"
    out_path.write_text("\n".join(score.notes), encoding="utf-8")
    return out_path
