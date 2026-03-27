from __future__ import annotations

from pathlib import Path

from src.models.entities import TranscriptionRequest
from src.services.runtime_probe_service import RuntimeProbeResult
from src.services.transcription_service import transcribe_with_adapters


def test_runtime_soft_fail_continues_when_not_strict(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PIANOTRANS_STRICT_RUNTIME", "0")

    source = tmp_path / "soft_fail.wav"
    source.write_bytes(b"audio")

    request = TranscriptionRequest(source_path=source, mode="normal", task_id="task_soft_001")
    runtime = RuntimeProbeResult(False, True, True)

    result = transcribe_with_adapters(request, runtime_probe_result=runtime)

    assert result.title == "soft_fail"
    assert len(result.notes) >= 1


def test_runtime_strict_mode_raises_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PIANOTRANS_STRICT_RUNTIME", "1")

    source = tmp_path / "strict_fail.wav"
    source.write_bytes(b"audio")

    request = TranscriptionRequest(source_path=source, mode="normal", task_id="task_strict_001")
    runtime = RuntimeProbeResult(False, False, True)

    try:
        transcribe_with_adapters(request, runtime_probe_result=runtime)
        assert False, "Expected strict runtime mode to raise RuntimeError"
    except RuntimeError as exc:
        assert "missing modules in strict mode" in str(exc)
