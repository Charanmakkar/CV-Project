"""Aggregates detection risk into zone occupancy and side corridor scores."""

from __future__ import annotations

from typing import Any

from .models import CorridorAssessment, Detection


class OccupancyAnalyzer:
    def __init__(self, config: Any) -> None:
        self.config = config

    def assess(self, detections: list[Detection]) -> CorridorAssessment:
        zone_count = self.config.zones if self.config.zones in (3, 5) else 5
        zone_risks = [0.0] * zone_count
        for detection in detections:
            zone_risks[detection.zone] = max(zone_risks[detection.zone], detection.risk_score)
        if zone_count == 3:
            left_indices, right_indices = [0], [2]
            center_index = 1
        else:
            left_indices, right_indices = [0, 1], [3, 4]
            center_index = 2
        left_risk = self._side_risk(zone_risks, left_indices)
        right_risk = self._side_risk(zone_risks, right_indices)
        center_blocked = zone_risks[center_index] >= self.config.risk_threshold
        safe_route = min(left_risk, right_risk) < self.config.stop_threshold
        if not safe_route:
            selected = "NONE"
        else:
            selected = "LEFT" if left_risk <= right_risk else "RIGHT"
        return CorridorAssessment(zone_risks, left_risk, right_risk, selected, center_blocked, safe_route)

    @staticmethod
    def _side_risk(risks: list[float], indices: list[int]) -> float:
        # Combining risk as a noisy-OR prevents one crowded side from looking safe.
        probability_clear = 1.0
        for index in indices:
            probability_clear *= 1.0 - min(100.0, risks[index]) / 100.0
        return round((1.0 - probability_clear) * 100.0, 1)

