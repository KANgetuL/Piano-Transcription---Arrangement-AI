from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.app.pipeline import run_transcription_pipeline
from src.utils.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PianoTrans AI minimal runner")
    parser.add_argument("--input", required=True, help="Path to audio file (.mp3/.wav)")
    parser.add_argument(
        "--mode",
        default="normal",
        choices=["normal", "pop", "electronic", "classical", "black"],
        help="Transcription mode",
    )
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    score, output_path = run_transcription_pipeline(source_path=Path(args.input), mode=args.mode)
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
