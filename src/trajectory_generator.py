"""Projected curved path for camera-frame visualization."""

from __future__ import annotations

from typing import Any


class TrajectoryGenerator:
    def __init__(self, config: Any) -> None:
        self.config = config

    def points(self, width: int, height: int, angle_deg: float, count: int = 24) -> list[tuple[int, int]]:
        import math
        center_x = width / 2.0
        bottom = height * 0.98
        top = height * 0.54
        curvature = angle_deg / max(self.config.max_angle, 1.0)
        result = []
        for i in range(count):
            t = i / max(count - 1, 1)
            y = bottom - (bottom - top) * t
            x = center_x + curvature * width * 0.40 * (t ** 1.65)
            x += math.sin(t * math.pi) * curvature * width * 0.035
            result.append((int(x), int(y)))
        return result

