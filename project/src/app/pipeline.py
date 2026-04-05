from __future__ import annotations

import logging
from time import perf_counter
import uuid
from pathlib import Path
from typing import Callable

from src.config.settings import get_settings
from src.models.entities import ScoreDocument, TranscriptionMode, TranscriptionRequest, to_score_document
from src.services.audio_ingestion_service import validate_audio_file
from src.services.export_service import export_score
from src.services.transcription_service import transcribe_with_adapters

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str, float | None], None]


def _emit_progress(
    progress_callback: ProgressCallback | None,
    percent: int,
    stage: str,
    started_at: float,
) -> None:
    if progress_callback is None:
        return
    eta_sec: float | None = None
    if 0 < percent < 100:
        elapsed = perf_counter() - started_at
        progress_ratio = percent / 100
        eta_sec = max(0.0, (elapsed / progress_ratio) - elapsed)

    try:
        progress_callback(percent, stage, eta_sec)
    except TypeError:
        # Backward compatibility for old two-argument callbacks.
        progress_callback(percent, stage)  # type: ignore[misc]


def run_transcription_pipeline(
    source_path: Path,
    mode: TranscriptionMode = "normal",
    fmt: str = "txt",
    progress_callback: ProgressCallback | None = None,
) -> tuple[ScoreDocument, Path]:
    """Run minimal end-to-end flow: validate -> transcribe -> export by selected format."""

    settings = get_settings()
    started_at = perf_counter()
    _emit_progress(progress_callback, 5, "progress_validate_audio", started_at)
    validate_audio_file(source_path, settings.supported_audio_extensions)
    _emit_progress(progress_callback, 25, "progress_build_request", started_at)
    request = TranscriptionRequest(
        source_path=source_path,
        mode=mode,
        task_id=f"task_{uuid.uuid4().hex[:8]}",
        sample_rate=settings.model.default_sample_rate,
    )

    def _on_model_debug(message: str) -> None:
        _emit_progress(progress_callback, 58, message, started_at)

    _emit_progress(progress_callback, 55, "progress_run_transcription", started_at)
    result = transcribe_with_adapters(request=request, model_debug_callback=_on_model_debug)
    _emit_progress(progress_callback, 80, "progress_generate_score", started_at)
    score = to_score_document(result)
    _emit_progress(progress_callback, 92, "progress_export_file", started_at)
    output_path = export_score(score=score, output_dir=settings.output_dir, fmt=fmt)
    _emit_progress(progress_callback, 100, "progress_done", started_at)
    logger.info("Pipeline finished. Output: %s", output_path)
    return score, output_path
