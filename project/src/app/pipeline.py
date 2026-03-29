from __future__ import annotations

import logging
from time import perf_counter
import uuid
from pathlib import Path
from typing import Callable

from src.config.settings import get_settings
from src.models.entities import ScoreDocument, TranscriptionMode, TranscriptionRequest, to_score_document
from src.services.audio_ingestion_service import validate_audio_file
from src.services.export_service import export_to_text
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
    progress_callback: ProgressCallback | None = None,
) -> tuple[ScoreDocument, Path]:
    """Run minimal end-to-end flow: validate -> transcribe stub -> export."""

    settings = get_settings()
    started_at = perf_counter()
    _emit_progress(progress_callback, 5, "校验音频", started_at)
    validate_audio_file(source_path, settings.supported_audio_extensions)
    _emit_progress(progress_callback, 25, "构建请求", started_at)
    request = TranscriptionRequest(
        source_path=source_path,
        mode=mode,
        task_id=f"task_{uuid.uuid4().hex[:8]}",
        sample_rate=settings.model.default_sample_rate,
    )
    _emit_progress(progress_callback, 55, "执行转写", started_at)
    result = transcribe_with_adapters(request=request)
    _emit_progress(progress_callback, 80, "生成乐谱", started_at)
    score = to_score_document(result)
    _emit_progress(progress_callback, 92, "导出文件", started_at)
    output_path = export_to_text(score=score, output_dir=settings.output_dir)
    _emit_progress(progress_callback, 100, "处理完成", started_at)
    logger.info("Pipeline finished. Output: %s", output_path)
    return score, output_path
