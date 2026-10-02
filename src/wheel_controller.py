"""Differential-drive wheel-speed simulation."""

from __future__ import annotations

from .models import WheelCommand


class WheelController:
    def __init__(self, base_speed: float = 70.0) -> None:
        self.base_speed = base_speed

    def command(self, angle_deg: float, action: str) -> WheelCommand:
        if action in ("STOP", "EMERGENCY STOP"):
            return WheelCommand(0.0, 0.0, action)
        turn = min(1.0, abs(angle_deg) / 60.0)
        inner = max(8.0, self.base_speed * (1.0 - 0.86 * turn))
        outer = min(100.0, self.base_speed * (1.0 + 0.15 * turn))
        if angle_deg < 0:
            return WheelCommand(round(inner, 1), round(outer, 1), action)
        if angle_deg > 0:
            return WheelCommand(round(outer, 1), round(inner, 1), action)
        return WheelCommand(self.base_speed, self.base_speed, "STRAIGHT")

