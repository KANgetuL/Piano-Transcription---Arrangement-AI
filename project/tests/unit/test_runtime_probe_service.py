from __future__ import annotations

from src.services import runtime_probe_service


class _SpecPresent:
    pass


def test_probe_model_runtime_all_available(monkeypatch) -> None:
    def _fake_find_spec(_name: str):
        return _SpecPresent()

    monkeypatch.setattr(runtime_probe_service.importlib.util, "find_spec", _fake_find_spec)
    result = runtime_probe_service.probe_model_runtime()

    assert result.all_available is True
    assert result.missing_modules == ()


def test_probe_model_runtime_reports_missing(monkeypatch) -> None:
    def _fake_find_spec(name: str):
        if name == "demucs":
            return None
        return _SpecPresent()

    monkeypatch.setattr(runtime_probe_service.importlib.util, "find_spec", _fake_find_spec)
    result = runtime_probe_service.probe_model_runtime()

    assert result.all_available is False
    assert result.missing_modules == ("demucs",)
