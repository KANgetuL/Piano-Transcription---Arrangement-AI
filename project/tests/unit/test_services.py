from __future__ import annotations

from pathlib import Path

from src.models.entities import TranscriptionRequest
from src.services.audio_ingestion_service import validate_audio_file
from src.services.transcription_service import transcribe_stub


def test_validate_audio_file_accepts_mp3(tmp_path: Path) -> None:
    audio = tmp_path / "ok.mp3"
    audio.write_bytes(b"x")

    validate_audio_file(audio, (".mp3", ".wav"))


def test_transcribe_stub_returns_notes(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"x")

    request = TranscriptionRequest(source_path=audio, mode="pop", task_id="task_test_001")
    result = transcribe_stub(request)

    assert result.title == "song"
    assert result.task_id == "task_test_001"
    assert len(result.notes) > 0
    assert len(result.segments) > 0
