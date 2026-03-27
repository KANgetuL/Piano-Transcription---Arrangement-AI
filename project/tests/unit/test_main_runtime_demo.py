from __future__ import annotations

from src.app import main as app_main
from src.services.runtime_demo_service import RuntimeDemoReport, StageRuntimeStatus


def test_main_runtime_demo_prints_report(monkeypatch, capsys) -> None:
    report = RuntimeDemoReport(
        python_runtime_ok=True,
        python_runtime_missing_modules=(),
        stage_status=(
            StageRuntimeStatus(stage="separation", ok=True, detail="ok"),
            StageRuntimeStatus(stage="pitch", ok=True, detail="ok"),
            StageRuntimeStatus(stage="harmony", ok=True, detail="ok"),
        ),
    )
    monkeypatch.setattr(app_main, "run_runtime_demo", lambda: report)
    monkeypatch.setattr(app_main, "configure_logging", lambda: None)
    monkeypatch.setattr(app_main.argparse.ArgumentParser, "parse_args", lambda _self: type("A", (), {"runtime_demo": True, "input": None, "mode": "normal"})())

    code = app_main.main()
    output = capsys.readouterr().out

    assert code == 0
    assert '"all_ok": true' in output
    assert '"python_runtime_ok": true' in output


def test_main_requires_input_without_runtime_demo(monkeypatch) -> None:
    monkeypatch.setattr(app_main, "configure_logging", lambda: None)

    def _fake_parse_args(_self):
        return type("A", (), {"runtime_demo": False, "input": None, "mode": "normal"})()

    monkeypatch.setattr(app_main.argparse.ArgumentParser, "parse_args", _fake_parse_args)

    try:
        app_main.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected parser error when input is missing")
