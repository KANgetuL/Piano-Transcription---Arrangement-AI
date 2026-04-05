from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.app.pipeline import run_transcription_pipeline
from src.services.runtime_demo_service import run_runtime_demo
from src.utils.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PianoTrans AI minimal runner")
    parser.add_argument("--input", help="Path to audio file (.mp3/.wav)")
    parser.add_argument(
        "--mode",
        default="normal",
        choices=["normal", "pop", "electronic", "classical", "black"],
        help="Transcription mode",
    )
    parser.add_argument(
        "--runtime-demo",
        action="store_true",
        help="Run model runtime callability demo without transcription inference",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="txt",
        choices=["txt", "mid", "musicxml"],
        help="Export format for pipeline output",
    )
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.runtime_demo:
        report = run_runtime_demo()
        print(
            json.dumps(
                {
                    "all_ok": report.all_ok,
                    "python_runtime_ok": report.python_runtime_ok,
                    "python_runtime_missing_modules": list(report.python_runtime_missing_modules),
                    "stage_status": [
                        {"stage": s.stage, "ok": s.ok, "detail": s.detail} for s in report.stage_status
                    ],
                },
                ensure_ascii=False,
            )
        )
        return 0

    if not args.input:
        parser.error("--input is required unless --runtime-demo is used")

    score, output_path = run_transcription_pipeline(source_path=Path(args.input), mode=args.mode, fmt=args.fmt)
    print(
        json.dumps(
            {
                "title": score.title,
                "tempo_bpm": score.tempo_bpm,
                "notes_count": len(score.notes),
                "output": str(output_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
