from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModelAdapterSettings:
    """Placeholder configuration for model adapter wiring."""

    default_sample_rate: int = 44100
    chunk_duration_sec: float = 1.5
    pitch_confidence_threshold: float = 0.5
    inference_device: str = "cpu"
    strict_model_runtime: bool = False
    demucs_model_path: Path = Path("./models/demucs")
    crepe_model_path: Path = Path("./models/crepe")
    basic_pitch_model_path: Path = Path("./models/basic_pitch")


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Application-level settings with safe defaults."""

    supported_audio_extensions: tuple[str, ...] = (".mp3", ".wav")
    output_dir: Path = Path("./outputs")
    model: ModelAdapterSettings = ModelAdapterSettings()


def get_settings() -> AppSettings:
    return AppSettings(
        output_dir=Path(os.getenv("PIANOTRANS_OUTPUT_DIR", "./outputs")),
        model=ModelAdapterSettings(
            default_sample_rate=int(os.getenv("PIANOTRANS_SAMPLE_RATE", "44100")),
            chunk_duration_sec=float(os.getenv("PIANOTRANS_CHUNK_SEC", "1.5")),
            pitch_confidence_threshold=float(os.getenv("PIANOTRANS_PITCH_THRESHOLD", "0.5")),
            inference_device=os.getenv("PIANOTRANS_DEVICE", "cpu"),
            strict_model_runtime=os.getenv("PIANOTRANS_STRICT_RUNTIME", "0") == "1",
            demucs_model_path=Path(os.getenv("PIANOTRANS_DEMUCS_PATH", "./models/demucs")),
            crepe_model_path=Path(os.getenv("PIANOTRANS_CREPE_PATH", "./models/crepe")),
            basic_pitch_model_path=Path(os.getenv("PIANOTRANS_BASIC_PITCH_PATH", "./models/basic_pitch")),
        ),
    )
