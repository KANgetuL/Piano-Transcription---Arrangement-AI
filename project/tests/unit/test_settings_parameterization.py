from __future__ import annotations

from pathlib import Path

from src.config.settings import get_settings


def test_settings_reads_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("PIANOTRANS_SAMPLE_RATE", "48000")
    monkeypatch.setenv("PIANOTRANS_CHUNK_SEC", "2.25")
    monkeypatch.setenv("PIANOTRANS_PITCH_THRESHOLD", "0.7")
    monkeypatch.setenv("PIANOTRANS_DEVICE", "cuda")
    monkeypatch.setenv("PIANOTRANS_DEMUCS_PATH", "./models/custom_demucs")

    settings = get_settings()

    assert settings.model.default_sample_rate == 48000
    assert settings.model.chunk_duration_sec == 2.25
    assert settings.model.pitch_confidence_threshold == 0.7
    assert settings.model.inference_device == "cuda"
    assert settings.model.demucs_model_path == Path("./models/custom_demucs")
