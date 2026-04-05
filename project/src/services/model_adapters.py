from __future__ import annotations

from dataclasses import dataclass
import importlib
import logging
import math
from pathlib import Path
from statistics import median
from typing import Callable

from src.config.settings import ModelAdapterSettings
from src.models.entities import AudioSegment, ChordEvent, NoteEvent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SeparationAdapter:
    """Placeholder adapter for source separation (Demucs-like stage)."""

    model_path: Path
    inference_device: str
    chunk_duration_sec: float

    def separate(self, source_path: Path, sample_rate: int) -> list[AudioSegment]:
        duration_sec = self._probe_duration(source_path, sample_rate)
        if duration_sec <= 0:
            duration_sec = self.chunk_duration_sec

        # Best-effort real model loading to validate Demucs availability in runtime path.
        try:
            pretrained = importlib.import_module("demucs.pretrained")
            get_model = getattr(pretrained, "get_model", None)
            if callable(get_model):
                _ = get_model("htdemucs")
        except Exception as exc:
            logger.warning("Demucs runtime warm-up skipped: %s", exc)

        segments: list[AudioSegment] = []
        step = max(0.25, self.chunk_duration_sec)
        cursor = 0.0
        index = 1
        while cursor < duration_sec:
            end_sec = min(duration_sec, cursor + step)
            segments.append(
                AudioSegment(
                    segment_id=f"seg_{index:02d}",
                    start_sec=cursor,
                    end_sec=end_sec,
                    sample_rate=sample_rate,
                )
            )
            cursor = end_sec
            index += 1

        return segments or [
            AudioSegment(
                segment_id="seg_01",
                start_sec=0.0,
                end_sec=self.chunk_duration_sec,
                sample_rate=sample_rate,
            )
        ]

    def _probe_duration(self, source_path: Path, fallback_sample_rate: int) -> float:
        try:
            soundfile = importlib.import_module("soundfile")
            info = soundfile.info(str(source_path))
            if info.samplerate > 0:
                return float(info.frames) / float(info.samplerate)
        except Exception as exc:
            logger.warning("Audio duration probe failed for %s: %s", source_path, exc)

        try:
            import wave

            with wave.open(str(source_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate() or fallback_sample_rate
                return float(frames) / float(sample_rate)
        except Exception:
            pass

        try:
            librosa = importlib.import_module("librosa")
            return float(librosa.get_duration(path=str(source_path)))
        except Exception:
            return self.chunk_duration_sec

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

    def predict_notes(
        self,
        source_path: Path,
        segments: list[AudioSegment],
        mode: str,
        sample_rate: int,
        debug_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[NoteEvent], bool, list[str]]:
        failure_reasons: list[str] = []

        attempt_chain: tuple[tuple[str, Callable[[], tuple[list[NoteEvent], str | None]]], ...] = (
            ("basic_pitch", lambda: self._try_basic_pitch(source_path)),
            ("crepe", lambda: self._try_crepe(source_path, sample_rate)),
            ("torchaudio", lambda: self._try_torchaudio_pitch(source_path, sample_rate)),
        )

        for model_name, runner in attempt_chain:
            if debug_callback:
                debug_callback(f"模型阶段: {model_name} 开始")

            notes, reason = runner()
            if notes:
                if debug_callback:
                    debug_callback(f"模型阶段: {model_name} 成功，音符数 {len(notes)}")
                return notes, False, failure_reasons

            normalized_reason = reason or "未生成有效音符"
            failure_reasons.append(f"{model_name}: {normalized_reason}")
            if debug_callback:
                debug_callback(f"模型阶段: {model_name} 失败，原因: {normalized_reason}")

        logger.warning("Falling back to placeholder pitch notes for %s. Reasons: %s", source_path, " | ".join(failure_reasons))
        if debug_callback:
            debug_callback("模型阶段: fallback 占位音符已启用")
        return self._fallback_notes(segments, mode), True, failure_reasons

    def _fallback_notes(self, segments: list[AudioSegment], mode: str) -> list[NoteEvent]:
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

    def _try_basic_pitch(self, source_path: Path) -> tuple[list[NoteEvent], str | None]:
        try:
            inference = importlib.import_module("basic_pitch.inference")
            predict_fn = getattr(inference, "predict")
            _, _, note_events = predict_fn(str(source_path))
        except Exception as exc:
            logger.info("Basic Pitch inference skipped: %s", exc)
            return [], str(exc)

        parsed: list[NoteEvent] = []
        for item in note_events:
            try:
                if isinstance(item, dict):
                    start_sec = float(item.get("start_time_s", item.get("start", 0.0)))
                    end_sec = float(item.get("end_time_s", item.get("end", start_sec + 0.1)))
                    pitch_midi = int(round(float(item.get("pitch_midi", item.get("pitch", 60)))))
                    confidence = float(item.get("amplitude", item.get("confidence", 0.75)))
                else:
                    seq = list(item)
                    start_sec = float(seq[0])
                    end_sec = float(seq[1])
                    pitch_midi = int(round(float(seq[2])))
                    confidence = float(seq[3]) if len(seq) > 3 else 0.75

                velocity = max(1, min(127, int(127 * max(0.05, min(confidence, 1.0)))))
                hand = "left" if pitch_midi < 60 else "right"
                parsed.append(
                    NoteEvent(
                        pitch_midi=pitch_midi,
                        velocity=velocity,
                        start_sec=max(0.0, start_sec),
                        end_sec=max(start_sec + 0.02, end_sec),
                        hand=hand,
                    )
                )
            except Exception:
                continue

        if not parsed:
            return [], "basic_pitch 输出为空"
        return parsed, None

    def _try_crepe(self, source_path: Path, sample_rate: int) -> tuple[list[NoteEvent], str | None]:
        try:
            crepe = importlib.import_module("crepe")
            audio_np, sr = self._load_audio_mono(source_path, sample_rate)
            times, freqs, confs, _ = crepe.predict(audio_np, sr, viterbi=True, step_size=20)
        except Exception as exc:
            logger.info("CREPE inference skipped: %s", exc)
            return [], str(exc)

        notes: list[NoteEvent] = []
        frame_dur = 0.02
        for idx, (freq_hz, conf) in enumerate(zip(freqs, confs)):
            if conf < self.confidence_threshold or freq_hz <= 0:
                continue
            pitch_midi = int(round(69 + 12 * math.log2(float(freq_hz) / 440.0)))
            if pitch_midi < 21 or pitch_midi > 108:
                continue
            start_sec = float(times[idx])
            end_sec = start_sec + frame_dur
            velocity = max(1, min(127, int(127 * float(conf))))
            hand = "left" if pitch_midi < 60 else "right"
            notes.append(
                NoteEvent(
                    pitch_midi=pitch_midi,
                    velocity=velocity,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    hand=hand,
                )
            )
        merged = self._merge_dense_frames(notes)
        if not merged:
            return [], "crepe 未输出高置信音符"
        return merged, None

    def _try_torchaudio_pitch(self, source_path: Path, sample_rate: int) -> tuple[list[NoteEvent], str | None]:
        try:
            torchaudio = importlib.import_module("torchaudio")
            torch = importlib.import_module("torch")
            audio_np, sr = self._load_audio_mono(source_path, sample_rate)
            mono = torch.from_numpy(audio_np).float().unsqueeze(0)

            frame_time = 0.03
            pitch_track = torchaudio.functional.detect_pitch_frequency(mono, sample_rate=sr, frame_time=frame_time)
            freqs = pitch_track.squeeze(0).detach().cpu().tolist()
        except Exception as exc:
            logger.info("torchaudio pitch extraction skipped: %s", exc)
            return [], str(exc)

        notes: list[NoteEvent] = []
        for idx, freq_hz in enumerate(freqs):
            if not freq_hz or freq_hz <= 0:
                continue
            if freq_hz < 27.5 or freq_hz > 4186.0:
                continue
            pitch_midi = int(round(69 + 12 * math.log2(float(freq_hz) / 440.0)))
            if pitch_midi < 21 or pitch_midi > 108:
                continue
            start_sec = idx * frame_time
            end_sec = start_sec + frame_time
            velocity = max(1, min(127, int(63 + (pitch_midi - 60) * 0.8)))
            hand = "left" if pitch_midi < 60 else "right"
            notes.append(
                NoteEvent(
                    pitch_midi=pitch_midi,
                    velocity=velocity,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    hand=hand,
                )
            )

        merged = self._merge_dense_frames(notes)
        if not merged:
            return [], "torchaudio 未输出可用音符"
        return merged, None

    def _load_audio_mono(self, source_path: Path, sample_rate: int) -> tuple[object, int]:
        load_errors: list[str] = []

        try:
            soundfile = importlib.import_module("soundfile")
            audio, sr = soundfile.read(str(source_path), dtype="float32", always_2d=False)
            if getattr(audio, "ndim", 1) > 1:
                audio = audio.mean(axis=1)

            if sr != sample_rate:
                librosa = importlib.import_module("librosa")
                audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
                sr = sample_rate
            return audio, int(sr)
        except Exception as exc:
            load_errors.append(f"soundfile: {exc}")

        try:
            librosa = importlib.import_module("librosa")
            audio, sr = librosa.load(str(source_path), sr=sample_rate, mono=True)
            return audio, int(sr)
        except Exception as exc:
            load_errors.append(f"librosa: {exc}")

        raise RuntimeError("音频加载失败: " + " | ".join(load_errors))

    def _merge_dense_frames(self, notes: list[NoteEvent]) -> list[NoteEvent]:
        if not notes:
            return []

        merged: list[NoteEvent] = []
        current = notes[0]
        for next_note in notes[1:]:
            if next_note.pitch_midi == current.pitch_midi and next_note.start_sec - current.end_sec <= 0.05:
                current = NoteEvent(
                    pitch_midi=current.pitch_midi,
                    velocity=int(median([current.velocity, next_note.velocity])),
                    start_sec=current.start_sec,
                    end_sec=next_note.end_sec,
                    hand=current.hand,
                )
                continue
            merged.append(current)
            current = next_note
        merged.append(current)
        return merged[:256]

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

    def estimate_chords(self, segments: list[AudioSegment], notes: list[NoteEvent] | None = None) -> list[ChordEvent]:
        if not segments:
            return []

        if not notes:
            return [ChordEvent(symbol="C:maj", start_sec=segments[0].start_sec, end_sec=segments[0].end_sec)]

        root = min(notes, key=lambda n: abs(n.pitch_midi - 60)).pitch_midi % 12
        names = {
            0: "C",
            1: "C#",
            2: "D",
            3: "D#",
            4: "E",
            5: "F",
            6: "F#",
            7: "G",
            8: "G#",
            9: "A",
            10: "A#",
            11: "B",
        }
        symbol = f"{names[root]}:maj"
        return [ChordEvent(symbol=symbol, start_sec=segments[0].start_sec, end_sec=segments[-1].end_sec)]

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
