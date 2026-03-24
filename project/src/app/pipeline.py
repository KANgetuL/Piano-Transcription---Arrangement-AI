from __future__ import annotations

import logging
from pathlib import Path

from src.config.settings import get_settings
from src.models.entities import ScoreDocument, TranscriptionMode
from src.services.audio_ingestion_service import validate_audio_file
from src.services.export_service import export_to_text
from src.services.transcription_service import transcribe_stub

logger = logging.getLogger(__name__)


def run_transcription_pipeline(source_path: Path, mode: TranscriptionMode = "normal") -> tuple[ScoreDocument, Path]:
    """Run minimal end-to-end flow: validate -> transcribe stub -> export."""

    settings = get_settings()
    validate_audio_file(source_path, settings.supported_audio_extensions)
    score = transcribe_stub(source_path=source_path, mode=mode)
    output_path = export_to_text(score=score, output_dir=settings.output_dir)
    logger.info("Pipeline finished. Output: %s", output_path)
    return score, output_path
