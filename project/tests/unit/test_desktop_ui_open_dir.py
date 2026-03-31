from __future__ import annotations

from pathlib import Path

from src.app import desktop_ui


def test_open_directory_in_file_manager_uses_startfile_on_windows(monkeypatch, tmp_path: Path) -> None:
    opened: list[str] = []

    monkeypatch.setattr(desktop_ui.os, "name", "nt", raising=False)
    monkeypatch.setattr(desktop_ui.os, "startfile", lambda path: opened.append(path), raising=False)

    desktop_ui.open_directory_in_file_manager(tmp_path)

    assert opened == [str(tmp_path.resolve())]


def test_open_directory_in_file_manager_uses_xdg_open_on_linux(monkeypatch, tmp_path: Path) -> None:
    command_calls: list[list[str]] = []

    monkeypatch.setattr(desktop_ui.os, "name", "posix", raising=False)
    monkeypatch.setattr(desktop_ui.sys, "platform", "linux", raising=False)
    monkeypatch.setattr(
        desktop_ui.subprocess,
        "run",
        lambda command, check: command_calls.append(command),
    )

    desktop_ui.open_directory_in_file_manager(tmp_path)

    assert command_calls == [["xdg-open", str(tmp_path.resolve())]]
