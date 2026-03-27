from __future__ import annotations

from pathlib import Path
import time
import wave

from src.models.entities import TranscriptionRequest
from src.services.audio_ingestion_service import (
    delete_audio_file,
    get_audio_file_info,
    list_audio_files,
    rename_audio_file,
    validate_audio_file,
)
from src.services.transcription_service import transcribe_stub


def test_validate_audio_file_accepts_mp3(tmp_path: Path) -> None:
    audio = tmp_path / "ok.mp3"
    audio.write_bytes(b"x")

    validate_audio_file(audio, (".mp3", ".wav"))


def test_transcribe_stub_returns_notes(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"x")

    request = TranscriptionRequest(source_path=audio, mode="pop", task_id="task_test_001")
    result = transcribe_stub(request)

    assert result.title == "song"
    assert result.task_id == "task_test_001"
    assert len(result.notes) > 0
    assert len(result.segments) > 0


def test_get_audio_file_info_reads_wav_duration(tmp_path: Path) -> None:
    wav_path = tmp_path / "sample.wav"
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b"\x00\x00" * 8000)

    info = get_audio_file_info(wav_path, (".mp3", ".wav"))

    assert info.filename == "sample.wav"
    assert info.extension == ".wav"
    assert info.size_bytes > 0
    assert info.duration_sec is not None
    assert 0.99 <= info.duration_sec <= 1.01


def test_rename_audio_file_preserves_extension_when_missing(tmp_path: Path) -> None:
    audio = tmp_path / "old.mp3"
    audio.write_bytes(b"data")

    renamed = rename_audio_file(audio, "renamed_track", (".mp3", ".wav"))

    assert renamed.name == "renamed_track.mp3"
    assert renamed.exists()
    assert not audio.exists()


def test_delete_audio_file_removes_file(tmp_path: Path) -> None:
    audio = tmp_path / "to_delete.wav"
    audio.write_bytes(b"x")

    delete_audio_file(audio, (".mp3", ".wav"))

    assert not audio.exists()


def test_list_audio_files_returns_recent_first_with_limit(tmp_path: Path) -> None:
    older = tmp_path / "older.mp3"
    newer = tmp_path / "newer.wav"
    oldest = tmp_path / "oldest.mp3"

    oldest.write_bytes(b"a")
    time.sleep(0.01)
    older.write_bytes(b"b")
    time.sleep(0.01)
    newer.write_bytes(b"c")

    files = list_audio_files(tmp_path, (".mp3", ".wav"), max_items=2)

    assert len(files) == 2
    assert files[0].filename == "newer.wav"
    assert files[1].filename == "older.mp3"
