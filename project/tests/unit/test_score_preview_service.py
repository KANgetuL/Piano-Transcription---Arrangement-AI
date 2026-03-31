from __future__ import annotations

from pathlib import Path

from src.services.score_preview_service import load_score_preview


def test_load_score_preview_reads_full_text(tmp_path: Path) -> None:
    output = tmp_path / "demo.txt"
    output.write_text("C4\nE4\nG4", encoding="utf-8")

    preview = load_score_preview(output)

    assert preview == "C4\nE4\nG4"


def test_load_score_preview_truncates_long_content(tmp_path: Path) -> None:
    output = tmp_path / "long.txt"
    output.write_text("A" * 20, encoding="utf-8")

    preview = load_score_preview(output, max_chars=10)

    assert preview.startswith("A" * 10)
    assert "预览已截断" in preview


def test_load_score_preview_uses_custom_truncated_suffix(tmp_path: Path) -> None:
    output = tmp_path / "long_custom.txt"
    output.write_text("B" * 20, encoding="utf-8")

    preview = load_score_preview(output, max_chars=8, truncated_suffix="... (preview truncated)")

    assert preview.startswith("B" * 8)
    assert preview.endswith("... (preview truncated)")