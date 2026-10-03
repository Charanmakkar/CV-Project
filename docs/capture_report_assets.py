"""Capture reproducible screenshots of the real Qt dashboard for the report.

The outcome scenes inject documented test detections into the normal pipeline;
they demonstrate navigation logic, not YOLO performance on synthetic drawings.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if os.name == "nt" else "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from gui.main_window import MainWindow  # noqa: E402
from src.config import load_config  # noqa: E402
from src.models import Detection  # noqa: E402
from tools.create_sample_video import make_video  # noqa: E402

ASSETS = ROOT / "docs" / "assets"


def capture(window: MainWindow, app: QApplication, name: str) -> None:
    app.processEvents()
    window.repaint()
    app.processEvents()
    if not window.grab().save(str(ASSETS / name)):
        raise RuntimeError(f"Could not save {name}")


def show_scene(window: MainWindow, app: QApplication, video: Path, seconds: int,
               detections: list[Detection], filename: str) -> None:
    window.stop_camera()
    window.pipeline.tracker.tracks.clear()
    window.pipeline.tracker.next_id = 1
    window.pipeline.steering.reset()
    window.pipeline.steering.last_change -= 1
    window.config.detection.enabled = bool(detections)
    window.detect_check.setChecked(bool(detections))
    window.pipeline.detector.status = "INJECTED TEST DETECTIONS" if detections else "DISABLED"
    window.pipeline.detector.detect = lambda frame: (detections, 0.0)
    window.config.camera.source = "video"
    window.config.camera.video_path = str(video)
    assert window.camera.open(), window.camera.last_error
    window.camera.capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    window.process_frame()
    capture(window, app, filename)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    video = make_video()
    app = QApplication.instance() or QApplication([])
    config = load_config(ROOT / "config.yaml")
    config.detection.enabled = False
    config.logging.enabled = False
    config.steering.smoothing = 0.0
    config.steering.min_command_duration_s = 0.0
    window = MainWindow(config)
    window.resize(1600, 1000)
    window.show()
    capture(window, app, "dashboard_idle.png")
    show_scene(window, app, video, 2, [], "dashboard_clear.png")
    show_scene(window, app, video, 6, [
        Detection("car", 0.92, (432, 335, 96, 96)),
        Detection("person", 0.88, (668, 295, 66, 126)),
    ], "dashboard_turn_left.png")
    show_scene(window, app, video, 21, [
        Detection("truck", 0.96, (0, 80, 255, 455)),
        Detection("car", 0.97, (353, 90, 254, 450)),
        Detection("bus", 0.95, (705, 0, 255, 540)),
    ], "dashboard_stop.png")
    window.close()
    print(f"Saved screenshots to {ASSETS}")


if __name__ == "__main__":
    main()
