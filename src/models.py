"""Shared typed data models used throughout the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Proximity(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    NEAR = "NEAR"
    CRITICAL = "CRITICAL"


class MotionStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    STATIONARY = "STATIONARY"
    APPROACHING = "APPROACHING"
    MOVING_AWAY = "MOVING AWAY"


class NavigationState(str, Enum):
    INITIALIZING = "INITIALIZING"
    SEARCHING = "SEARCHING"
    PATH_CLEAR = "PATH_CLEAR"
    FOLLOWING_PATH = "FOLLOWING_PATH"
    OBSTACLE_DETECTED = "OBSTACLE_DETECTED"
    ANALYZING_OBSTACLE = "ANALYZING_OBSTACLE"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    SLOW_DOWN = "SLOW_DOWN"
    STOPPED = "STOPPED"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]
    track_id: int | None = None
    zone: int = 2
    distance_m: float | None = None
    proximity: Proximity = Proximity.SAFE
    risk_score: float = 0.0
    in_corridor: bool = False
    motion: MotionStatus = MotionStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> tuple[int, int]:
        x, y, w, h = self.bbox
        return x + w // 2, y + h // 2

    @property
    def area_ratio(self) -> float:
        _, _, w, h = self.bbox
        return max(0.0, float(w * h))


@dataclass
class CorridorAssessment:
    zone_risks: list[float]
    left_risk: float
    right_risk: float
    selected_side: str
    center_blocked: bool
    safe_route: bool


@dataclass
class NavigationDecision:
    action: str = "STRAIGHT"
    angle_deg: float = 0.0
    reason: str = "No detected obstacle in the projected path."
    primary_threat: Detection | None = None
    assessment: CorridorAssessment = field(default_factory=lambda: CorridorAssessment([0.0] * 5, 0.0, 0.0, "NONE", False, True))
    state: NavigationState = NavigationState.SEARCHING
    confidence: float = 1.0


@dataclass
class WheelCommand:
    left: float = 70.0
    right: float = 70.0
    motion: str = "STRAIGHT"


@dataclass
class FrameAnalysis:
    frame: Any
    detections: list[Detection]
    decision: NavigationDecision
    wheels: WheelCommand
    fps: float = 0.0
    inference_ms: float = 0.0
    camera_ok: bool = True
    model_status: str = "NOT LOADED"
    timestamp: str = ""

