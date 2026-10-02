"""Headless perception-to-control pipeline used by the GUI and tests."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .decision_engine import DecisionEngine
from .distance_estimator import DistanceEstimator
from .models import FrameAnalysis
from .object_detector import ObjectDetector
from .object_tracker import ObjectTracker
from .occupancy_analyzer import OccupancyAnalyzer
from .risk_engine import RiskEngine
from .state_machine import NavigationStateMachine
from .steering_controller import SteeringController
from .trajectory_generator import TrajectoryGenerator
from .wheel_controller import WheelController
from .zone_analyzer import ZoneAnalyzer


class NavigationPipeline:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.detector = ObjectDetector(config.detection)
        self.tracker = ObjectTracker(config.tracking)
        self.distance = DistanceEstimator(config.distance)
        self.zones = ZoneAnalyzer(config.navigation)
        self.risk = RiskEngine(config.navigation)
        self.occupancy = OccupancyAnalyzer(config.navigation)
        self.decision = DecisionEngine(config.navigation, config.steering)
        self.steering = SteeringController(config.steering)
        self.wheels = WheelController(config.steering.base_speed)
        self.trajectory = TrajectoryGenerator(config.navigation)
        self.state_machine = NavigationStateMachine()

    def initialize(self) -> None:
        self.detector.load()

    def analyze(self, frame: Any, fps: float = 0.0) -> FrameAnalysis:
        height, width = frame.shape[:2]
        detections, inference_ms = self.detector.detect(frame)
        detections = self.tracker.update(detections)
        for detection in detections:
            self.zones.annotate(detection, width, height)
            self.distance.estimate(detection, height)
            self.risk.score(detection, width, height)
        assessment = self.occupancy.assess(detections)
        requested = self.decision.decide(detections, assessment)
        angle, action = self.steering.update(requested.angle_deg, requested.action)
        requested.angle_deg = angle
        requested.action = action
        requested.state = self.state_machine.update(requested.state)
        wheel_command = self.wheels.command(angle, action)
        return FrameAnalysis(
            frame=frame, detections=detections, decision=requested, wheels=wheel_command,
            fps=fps, inference_ms=inference_ms, camera_ok=True, model_status=self.detector.status,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
