from __future__ import annotations

from pathlib import Path

from src.config.settings import ModelAdapterSettings
from src.models.entities import TranscriptionRequest
from src.services.model_adapters import HarmonyAdapter, PitchAdapter, SeparationAdapter
from src.services.transcription_service import transcribe_with_adapters


def test_adapter_parameterization_controls_output(tmp_path: Path) -> None:
    source = tmp_path / "param.wav"
    source.write_bytes(b"audio")

    custom = ModelAdapterSettings(
        default_sample_rate=32000,
        chunk_duration_sec=2.5,
        pitch_confidence_threshold=0.8,
        inference_device="cpu",
    )

    request = TranscriptionRequest(source_path=source, mode="normal", task_id="task_param_001", sample_rate=32000)
    result = transcribe_with_adapters(
        request,
        separation_adapter=SeparationAdapter.from_settings(custom),
        pitch_adapter=PitchAdapter.from_settings(custom),
        harmony_adapter=HarmonyAdapter.from_settings(custom),
    )

    assert result.segments[0].end_sec == 2.5
    assert result.segments[0].sample_rate == 32000
    assert result.notes[0].velocity == 101
