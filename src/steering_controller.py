"""Temporal steering smoothing and command hysteresis."""

from __future__ import annotations

import time
from typing import Any


class SteeringController:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.angle = 0.0
        self.action = "STRAIGHT"
        self.last_change = time.monotonic()

    def update(self, requested_angle: float, requested_action: str) -> tuple[float, str]:
        alpha = max(0.0, min(1.0, 1.0 - self.config.smoothing))
        now = time.monotonic()
        self.angle = self.angle * (1.0 - alpha) + requested_angle * alpha
        if requested_action != self.action and now - self.last_change >= self.config.min_command_duration_s:
            self.action = requested_action
            self.last_change = now
        if abs(self.angle) < 1.0 and self.action not in ("STOP", "EMERGENCY STOP"):
            self.action = "STRAIGHT"
        return round(max(-self.config.max_angle, min(self.config.max_angle, self.angle)), 1), self.action

    def reset(self) -> None:
        self.angle = 0.0
        self.action = "STRAIGHT"
        self.last_change = time.monotonic()

