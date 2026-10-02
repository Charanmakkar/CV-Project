"""Scene-level collision risk model."""

from __future__ import annotations

from typing import Any

from .models import Detection, MotionStatus, Proximity


class RiskEngine:
    TYPE_WEIGHT = {"person": 12, "bicycle": 10, "motorcycle": 10, "car": 10, "truck": 12, "bus": 12, "chair": 4}
    PROXIMITY_WEIGHT = {Proximity.SAFE: 8, Proximity.CAUTION: 28, Proximity.NEAR: 62, Proximity.CRITICAL: 90}

    def __init__(self, config: Any) -> None:
        self.config = config

    def score(self, detection: Detection, frame_width: int, frame_height: int) -> float:
        proximity = float(self.PROXIMITY_WEIGHT[detection.proximity])
        _, y, width, height = detection.bbox
        size = min(100.0, ((width * height) / max(frame_width * frame_height, 1)) * 850.0)
        vertical = min(100.0, max(0.0, (y + height) / max(frame_height, 1) * 100.0))
        lane = 26.0 if detection.in_corridor else 7.0
        confidence = detection.confidence * 10.0
        type_weight = self.TYPE_WEIGHT.get(detection.label, 6)
        approach = 14.0 if detection.motion == MotionStatus.APPROACHING else 0.0
        score = 0.46 * proximity + 0.20 * size + 0.12 * vertical + lane + type_weight + confidence + approach
        detection.risk_score = round(min(100.0, score), 1)
        return detection.risk_score

