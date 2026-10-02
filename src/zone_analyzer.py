"""Configurable three/five-zone horizontal and collision-corridor analysis."""

from __future__ import annotations

from typing import Any

from .models import Detection


ZONE_NAMES = {3: ["LEFT", "CENTER", "RIGHT"], 5: ["FAR LEFT", "LEFT", "CENTER", "RIGHT", "FAR RIGHT"]}


class ZoneAnalyzer:
    def __init__(self, config: Any) -> None:
        self.config = config

    @property
    def names(self) -> list[str]:
        return ZONE_NAMES[3 if self.config.zones == 3 else 5]

    def zone_for_x(self, x: float, frame_width: int) -> int:
        return min(len(self.names) - 1, max(0, int((x / max(frame_width, 1)) * len(self.names))))

    def annotate(self, detection: Detection, frame_width: int, frame_height: int) -> Detection:
        cx, cy = detection.center
        detection.zone = self.zone_for_x(cx, frame_width)
        corridor_center = frame_width / 2.0
        corridor_half = frame_width * self.config.collision_corridor_width / 2.0
        corridor_top = frame_height * self.config.collision_corridor_top
        detection.in_corridor = (corridor_center - corridor_half <= cx <= corridor_center + corridor_half and cy >= corridor_top)
        return detection

    def zone_name(self, zone: int) -> str:
        return self.names[min(max(zone, 0), len(self.names) - 1)]

