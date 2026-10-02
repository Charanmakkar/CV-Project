"""CSV event logger for perception and decision telemetry."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Detection, NavigationDecision, WheelCommand


class DecisionLogger:
    FIELDS = ["timestamp", "object_id", "object_class", "confidence", "bbox", "zone", "distance_m", "risk_score", "navigation_state", "steering_angle", "left_wheel", "right_wheel", "selected_action"]

    def __init__(self, directory: str, enabled: bool = True) -> None:
        self.enabled = enabled
        self.path = Path(directory) / "navigation_events.csv"
        self.handle = None
        self.writer = None
        if enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = self.path.open("a", newline="", encoding="utf-8")
            self.writer = csv.DictWriter(self.handle, fieldnames=self.FIELDS)
            if self.path.stat().st_size == 0:
                self.writer.writeheader()

    def log(self, detections: Iterable[Detection], decision: NavigationDecision, wheels: WheelCommand) -> None:
        if not self.writer:
            return
        timestamp = datetime.now().isoformat(timespec="milliseconds")
        for detection in detections:
            self.writer.writerow({
                "timestamp": timestamp, "object_id": detection.track_id or "", "object_class": detection.label,
                "confidence": f"{detection.confidence:.3f}", "bbox": detection.bbox, "zone": detection.zone,
                "distance_m": detection.distance_m or "", "risk_score": detection.risk_score,
                "navigation_state": decision.state.value, "steering_angle": decision.angle_deg,
                "left_wheel": wheels.left, "right_wheel": wheels.right, "selected_action": decision.action,
            })
        self.handle.flush()

    def close(self) -> None:
        if self.handle:
            self.handle.close()
            self.handle = None

