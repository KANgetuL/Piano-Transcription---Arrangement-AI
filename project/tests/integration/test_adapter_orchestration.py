from __future__ import annotations

from pathlib import Path

from src.models.entities import TranscriptionRequest
from src.services.transcription_service import transcribe_with_adapters


def test_adapter_orchestration_returns_structured_result(tmp_path: Path) -> None:
    source = tmp_path / "integration.wav"
    source.write_bytes(b"audio")

    request = TranscriptionRequest(source_path=source, mode="classical", task_id="task_it_001")
    result = transcribe_with_adapters(request)

    assert result.task_id == "task_it_001"
    assert result.title == "integration"
    assert result.key_signature == "C"
    assert result.time_signature == "4/4"
    assert len(result.segments) >= 1
    assert len(result.notes) >= 1
    assert len(result.chords) >= 1
