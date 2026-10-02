"""Monocular relative proximity estimator; values are explicitly estimates."""

from __future__ import annotations

from typing import Any

from .models import Detection, Proximity


class DistanceEstimator:
    # COCO-scale defaults: object height priors are deliberately approximate.
    HEIGHT_PRIORS = {
        "person": 1.70, "bicycle": 1.20, "motorcycle": 1.30, "car": 1.45,
        "truck": 2.50, "bus": 3.00, "chair": 1.00,
    }

    def __init__(self, config: Any) -> None:
        self.config = config

    def estimate(self, detection: Detection, frame_height: int) -> Detection:
        _, _, _, height = detection.bbox
        prior = self.HEIGHT_PRIORS.get(detection.label, self.config.reference_object_height_m)
        if height <= 0:
            detection.distance_m = None
            detection.proximity = Proximity.SAFE
            return detection
        estimate = self.config.focal_length_px * prior / height
        # Avoid a false sense of precision in the UI and downstream model.
        detection.distance_m = round(max(0.2, min(30.0, estimate)), 1)
        if detection.distance_m < self.config.critical:
            detection.proximity = Proximity.CRITICAL
        elif detection.distance_m < self.config.near:
            detection.proximity = Proximity.NEAR
        elif detection.distance_m < self.config.caution:
            detection.proximity = Proximity.CAUTION
        else:
            detection.proximity = Proximity.SAFE
        return detection

