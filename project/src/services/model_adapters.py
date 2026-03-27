from __future__ import annotations

from dataclasses import dataclass
import importlib
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

    def runtime_check(self) -> tuple[bool, str]:
        """Check Demucs import and expected entrypoint availability."""

        try:
            pretrained = importlib.import_module("demucs.pretrained")
        except Exception as exc:
            return False, f"demucs import failed: {exc}"

        if not hasattr(pretrained, "get_model"):
            return False, "demucs.pretrained.get_model not found"
        return True, "demucs runtime entrypoint available"

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

    def runtime_check(self) -> tuple[bool, str]:
        """Check CREPE and Basic Pitch import/call entrypoints."""

        try:
            crepe = importlib.import_module("crepe")
        except Exception as exc:
            return False, f"crepe import failed: {exc}"

        if not hasattr(crepe, "predict"):
            return False, "crepe.predict not found"

        try:
            inference = importlib.import_module("basic_pitch.inference")
        except Exception as exc:
            return False, f"basic_pitch.inference import failed: {exc}"

        if not hasattr(inference, "predict"):
            return False, "basic_pitch.inference.predict not found"
        return True, "pitch runtime entrypoints available"

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

    def runtime_check(self) -> tuple[bool, str]:
        """Check Basic Pitch note-creation entrypoint for harmony support stage."""

        try:
            note_creation = importlib.import_module("basic_pitch.note_creation")
        except Exception as exc:
            return False, f"basic_pitch.note_creation import failed: {exc}"

        if not hasattr(note_creation, "model_output_to_notes"):
            return False, "basic_pitch.note_creation.model_output_to_notes not found"
        return True, "harmony runtime entrypoint available"

    @classmethod
    def from_settings(cls, settings: ModelAdapterSettings) -> "HarmonyAdapter":
        return cls(
            model_path=settings.basic_pitch_model_path,
            inference_device=settings.inference_device,
        )
