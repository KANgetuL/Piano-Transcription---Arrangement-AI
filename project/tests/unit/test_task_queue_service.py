from __future__ import annotations

from pathlib import Path
import time

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


def test_submit_transcription_forwards_progress_callback(tmp_path: Path) -> None:
    queue = TaskQueueService(worker_count=1)
    input_path = tmp_path / "queue_progress.mp3"
    input_path.write_bytes(b"x")

    updates: list[tuple[int, str, float | None]] = []

    def _fake_runner(source_path: Path, mode: str, progress_callback=None):
        _ = mode
        if progress_callback:
            progress_callback(30, "阶段一", 1.2)
            progress_callback(100, "完成", None)
        return ScoreDocument(title=source_path.stem, notes=["C4"], tempo_bpm=120), tmp_path / "queue_progress.txt"

    future = queue.submit_transcription(
        input_path,
        "normal",
        pipeline_runner=_fake_runner,
        progress_callback=lambda percent, stage, eta: updates.append((percent, stage, eta)),
    )
    result = future.result(timeout=3)
    queue.shutdown()

    assert result.output_path.name == "queue_progress.txt"
    assert updates == [(30, "阶段一", 1.2), (100, "完成", None)]


def test_cancel_transcription_cancels_queued_future(tmp_path: Path) -> None:
    queue = TaskQueueService(worker_count=1)
    first = tmp_path / "first.mp3"
    second = tmp_path / "second.mp3"
    first.write_bytes(b"a")
    second.write_bytes(b"b")

    def _slow_runner(source_path: Path, mode: str):
        _ = source_path
        _ = mode
        time.sleep(0.2)
        return ScoreDocument(title="slow", notes=["C4"], tempo_bpm=120), tmp_path / "slow.txt"

    first_future = queue.submit_transcription(first, "normal", pipeline_runner=_slow_runner)
    second_future = queue.submit_transcription(second, "normal", pipeline_runner=_slow_runner)
    cancelled = queue.cancel_transcription(second_future)

    _ = first_future.result(timeout=3)
    queue.shutdown()

    assert cancelled is True
    assert second_future.cancelled()
