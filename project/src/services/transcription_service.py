from __future__ import annotations

import logging

from src.models.entities import (
    TranscriptionRequest,
    TranscriptionResult,
)
from src.config.settings import get_settings
from src.services.model_adapters import HarmonyAdapter, PitchAdapter, SeparationAdapter
from src.services.runtime_probe_service import RuntimeProbeResult, probe_model_runtime

logger = logging.getLogger(__name__)


def transcribe_with_adapters(
    request: TranscriptionRequest,
    separation_adapter: SeparationAdapter | None = None,
    pitch_adapter: PitchAdapter | None = None,
    harmony_adapter: HarmonyAdapter | None = None,
    runtime_probe_result: RuntimeProbeResult | None = None,
) -> TranscriptionResult:
    """Run placeholder adapter pipeline to produce structured transcription output."""

    settings = get_settings().model
    runtime_probe = runtime_probe_result or probe_model_runtime()
    if settings.strict_model_runtime and not runtime_probe.all_available:
        missing = ", ".join(runtime_probe.missing_modules)
        raise RuntimeError(f"[transcription] [runtime_probe] [missing modules in strict mode: {missing}]")

    if not runtime_probe.all_available:
        logger.warning("Runtime probe missing optional model SDKs: %s", runtime_probe.missing_modules)

    separation = separation_adapter or SeparationAdapter.from_settings(settings)
    pitch = pitch_adapter or PitchAdapter.from_settings(settings)
    harmony = harmony_adapter or HarmonyAdapter.from_settings(settings)

    segments = separation.separate(source_path=request.source_path, sample_rate=request.sample_rate)
    notes = pitch.predict_notes(segments=segments, mode=request.mode)
    chords = harmony.estimate_chords(segments=segments)

    return TranscriptionResult(
        task_id=request.task_id,
        title=request.source_path.stem,
        tempo_bpm=120,
        key_signature="C",
        time_signature="4/4",
        bars=1,
        segments=segments,
        notes=notes,
        chords=chords,
    )


def transcribe_stub(request: TranscriptionRequest) -> TranscriptionResult:
    """Compatibility entrypoint currently backed by adapter orchestration."""

    return transcribe_with_adapters(request=request)
