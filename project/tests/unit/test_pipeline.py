from __future__ import annotations

from pathlib import Path

from src.app.pipeline import run_transcription_pipeline


def test_run_pipeline_exports_text_file(tmp_path: Path, monkeypatch) -> None:
    input_file = tmp_path / "demo.mp3"
    input_file.write_bytes(b"fake audio bytes")

    monkeypatch.chdir(tmp_path)

    score, output_path = run_transcription_pipeline(source_path=input_file, mode="normal")

    assert score.title == "demo"
    assert output_path.exists()
    assert output_path.suffix == ".txt"


def test_run_pipeline_rejects_unsupported_file(tmp_path: Path) -> None:
    input_file = tmp_path / "demo.flac"
    input_file.write_bytes(b"fake audio bytes")

    try:
        run_transcription_pipeline(source_path=input_file, mode="normal")
        assert False, "Expected ValueError for unsupported extension"
    except ValueError as exc:
        assert "unsupported extension" in str(exc)
