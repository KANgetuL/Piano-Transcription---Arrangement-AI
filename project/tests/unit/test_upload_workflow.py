from __future__ import annotations

from pathlib import Path
import time

from src.app import upload_workflow


def test_list_recent_uploads_respects_limit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        upload_workflow,
        "get_settings",
        lambda: type("S", (), {"supported_audio_extensions": (".mp3", ".wav")})(),
    )

    (tmp_path / "a.mp3").write_bytes(b"a")
    time.sleep(0.01)
    (tmp_path / "b.wav").write_bytes(b"b")
    time.sleep(0.01)
    (tmp_path / "c.mp3").write_bytes(b"c")

    items = upload_workflow.list_recent_uploads(tmp_path, max_items=2)

    assert len(items) == 2
    assert items[0].filename == "c.mp3"


def test_rename_uploaded_file_with_extension_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        upload_workflow,
        "get_settings",
        lambda: type("S", (), {"supported_audio_extensions": (".mp3", ".wav")})(),
    )
    source = tmp_path / "origin.mp3"
    source.write_bytes(b"x")

    renamed = upload_workflow.rename_uploaded_file(source, "renamed")

    assert renamed.name == "renamed.mp3"
    assert renamed.exists()


def test_delete_uploaded_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        upload_workflow,
        "get_settings",
        lambda: type("S", (), {"supported_audio_extensions": (".mp3", ".wav")})(),
    )
    target = tmp_path / "delete_me.wav"
    target.write_bytes(b"x")

    upload_workflow.delete_uploaded_file(target)

    assert not target.exists()
