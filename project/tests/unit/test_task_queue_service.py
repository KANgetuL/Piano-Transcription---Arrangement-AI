from __future__ import annotations

from pathlib import Path

from src.models.entities import ScoreDocument
from src.services.task_queue_service import TaskQueueService


def test_submit_transcription_returns_task_result(tmp_path: Path) -> None:
    queue = TaskQueueService(worker_count=1)

    input_path = tmp_path / "queue.mp3"
    input_path.write_bytes(b"x")

    def _fake_runner(source_path: Path, mode: str):
        _ = mode
        return ScoreDocument(title=source_path.stem, notes=["C4"], tempo_bpm=120), tmp_path / "queue.txt"

    future = queue.submit_transcription(input_path, "normal", pipeline_runner=_fake_runner)
    result = future.result(timeout=3)
    queue.shutdown()

    assert result.score.title == "queue"
    assert result.output_path.name == "queue.txt"
