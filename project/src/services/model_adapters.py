from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config.settings import ModelAdapterSettings
from src.models.entities import AudioSegment, ChordEvent, NoteEvent


@dataclass(slots=True)
class SeparationAdapter:
    """Placeholder adapter for source separation (Demucs-like stage)."""

    model_path: Path
    inference_device: str
    chunk_duration_sec: float

    def separate(self, source_path: Path, sample_rate: int) -> list[AudioSegment]:
        _ = source_path
        return [
            AudioSegment(
                segment_id="seg_01",
                start_sec=0.0,
                end_sec=self.chunk_duration_sec,
                sample_rate=sample_rate,
            )
        ]

    @classmethod
    def from_settings(cls, settings: ModelAdapterSettings) -> "SeparationAdapter":
        return cls(
            model_path=settings.demucs_model_path,
            inference_device=settings.inference_device,
            chunk_duration_sec=settings.chunk_duration_sec,
        )


@dataclass(slots=True)
class PitchAdapter:
    """Placeholder adapter for pitch extraction (CREPE/Basic Pitch-like stage)."""

    model_path: Path
    inference_device: str
    confidence_threshold: float

    def predict_notes(self, segments: list[AudioSegment], mode: str) -> list[NoteEvent]:
        mode_bias = {
            "normal": 60,
            "pop": 64,
            "electronic": 67,
            "classical": 62,
            "black": 72,
        }
        base_pitch = mode_bias[mode]
        if not segments:
            return []

        end = segments[0].end_sec
        velocity = max(1, min(127, int(127 * self.confidence_threshold)))
        return [
            NoteEvent(pitch_midi=base_pitch, velocity=velocity, start_sec=0.0, end_sec=min(0.5, end), hand="right"),
            NoteEvent(
                pitch_midi=base_pitch + 4,
                velocity=max(1, velocity - 2),
                start_sec=0.5,
                end_sec=min(1.0, end),
                hand="right",
            ),
            NoteEvent(
                pitch_midi=base_pitch - 12,
                velocity=max(1, velocity - 6),
                start_sec=0.0,
                end_sec=min(1.0, end),
                hand="left",
            ),
        ]

    @classmethod
    def from_settings(cls, settings: ModelAdapterSettings) -> "PitchAdapter":
        return cls(
            model_path=settings.crepe_model_path,
            inference_device=settings.inference_device,
            confidence_threshold=settings.pitch_confidence_threshold,
        )


@dataclass(slots=True)
class HarmonyAdapter:
    """Placeholder adapter for chord analysis stage."""

    model_path: Path
    inference_device: str

    def estimate_chords(self, segments: list[AudioSegment]) -> list[ChordEvent]:
        if not segments:
            return []
        return [ChordEvent(symbol="C:maj", start_sec=segments[0].start_sec, end_sec=segments[0].end_sec)]

    @classmethod
    def from_settings(cls, settings: ModelAdapterSettings) -> "HarmonyAdapter":
        return cls(
            model_path=settings.basic_pitch_model_path,
            inference_device=settings.inference_device,
        )
