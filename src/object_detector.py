"""Ultralytics detector adapter with an explicit no-model fallback."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .models import Detection


class ObjectDetector:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.model: Any = None
        self.status = "DISABLED" if not config.enabled else "NOT LOADED"
        self.last_error = ""
        self._allowed = set(config.classes)

    def load(self) -> bool:
        if not self.config.enabled:
            self.status = "DISABLED"
            return False
        try:
            from ultralytics import YOLO
            import torch
            device = self.config.device
            if device == "auto":
                device = "0" if torch.cuda.is_available() else "cpu"
            self.model = YOLO(self.config.model)
            self.device = device
            self.status = f"READY ({device})"
            return True
        except Exception as exc:  # optional model dependency/download must not crash the GUI
            self.model = None
            self.last_error = str(exc)
            self.status = "UNAVAILABLE - FALLBACK MODE"
            return False

    def detect(self, frame: Any) -> tuple[list[Detection], float]:
        if self.model is None or not self.config.enabled:
            return [], 0.0
        started = time.perf_counter()
        try:
            results = self.model.predict(
                frame,
                conf=self.config.confidence,
                iou=self.config.iou,
                imgsz=self.config.image_size,
                device=self.device,
                verbose=False,
            )
            detections: list[Detection] = []
            names = self.model.names
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = str(names[cls_id])
                    if self._allowed and label not in self._allowed:
                        continue
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    detections.append(Detection(label, float(box.conf[0]), (x1, y1, max(1, x2 - x1), max(1, y2 - y1))))
            return detections, (time.perf_counter() - started) * 1000.0
        except Exception as exc:
            self.last_error = str(exc)
            return [], (time.perf_counter() - started) * 1000.0
