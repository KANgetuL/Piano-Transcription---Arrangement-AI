from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import inspect
from pathlib import Path
from typing import Callable

from src.app.pipeline import run_transcription_pipeline
from src.models.entities import ScoreDocument, TranscriptionMode


@dataclass(slots=True)
class TaskResult:
    """Result payload returned by queued transcription tasks."""

    score: ScoreDocument
    output_path: Path


class TaskQueueService:
    """Minimal async task queue based on a single-worker thread pool."""

    def __init__(self, worker_count: int = 1) -> None:
        self._executor = ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="transcription")

    def submit_transcription(
        self,
        source_path: Path,
        mode: TranscriptionMode = "normal",
        pipeline_runner: Callable[..., tuple[ScoreDocument, Path]] = run_transcription_pipeline,
        fmt: str = "txt",
        progress_callback: Callable[[int, str, float | None], None] | None = None,
    ) -> Future[TaskResult]:
        def _run() -> TaskResult:
            signature = inspect.signature(pipeline_runner)
            params = signature.parameters

            if "fmt" in params and "progress_callback" in params:
                score, output_path = pipeline_runner(source_path, mode, fmt=fmt, progress_callback=progress_callback)
            elif "fmt" in params:
                score, output_path = pipeline_runner(source_path, mode, fmt=fmt)
            elif "progress_callback" in params:
                score, output_path = pipeline_runner(source_path, mode, progress_callback=progress_callback)
            elif len(params) >= 3:
                score, output_path = pipeline_runner(source_path, mode, progress_callback)
            else:
                score, output_path = pipeline_runner(source_path, mode)
            return TaskResult(score=score, output_path=output_path)

        return self._executor.submit(_run)

    def cancel_transcription(self, future: Future[TaskResult]) -> bool:
        """Try to cancel a queued transcription task before execution starts."""

        return future.cancel()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
