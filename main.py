"""Entry point for the Computer Vision Autonomous Patrol Simulator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Computer Vision Autonomous Patrol Simulator")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML configuration")
    parser.add_argument("--video", default=None, help="Use a video file instead of the webcam")
    parser.add_argument("--no-model", action="store_true", help="Run perception without loading YOLO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    if args.video:
        config.camera.source = "video"
        config.camera.video_path = args.video
    if args.no_model:
        config.detection.enabled = False

    try:
        from gui.main_window import run_app
    except ImportError as exc:
        print("The GUI dependencies are missing. Install requirements.txt first.")
        print(f"Import detail: {exc}")
        return 2
    return run_app(config)


if __name__ == "__main__":
    sys.exit(main())

