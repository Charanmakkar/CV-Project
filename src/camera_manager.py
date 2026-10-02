"""Reliable webcam/video-file capture with graceful failure states."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class CameraManager:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.capture: Any = None
        self.last_error = ""
        self.source_name = ""

    def open(self) -> bool:
        try:
            import cv2
        except ImportError:
            self.last_error = "opencv-python is not installed"
            return False
        source: int | str = self.config.index
        if self.config.source == "video":
            source = str(Path(self.config.video_path))
            if not Path(source).exists():
                self.last_error = f"Video file not found: {source}"
                return False
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            self.last_error = f"Unable to open camera/video source: {source}"
            self.capture.release()
            self.capture = None
            return False
        if self.config.source == "webcam":
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)
        self.source_name = str(source)
        self.last_error = ""
        return True

    def read(self) -> tuple[bool, Any, float]:
        if self.capture is None:
            return False, None, 0.0
        started = time.perf_counter()
        ok, frame = self.capture.read()
        elapsed = time.perf_counter() - started
        if not ok:
            self.last_error = "Frame capture failed or stream ended"
        return ok, frame, elapsed * 1000.0

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    @property
    def is_open(self) -> bool:
        return self.capture is not None

