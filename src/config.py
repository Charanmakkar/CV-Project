"""Configuration dataclasses and YAML loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # Allows headless unit tests to run before dependencies are installed.
    yaml = None


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    source: str = "webcam"
    video_path: str = ""


@dataclass
class DetectionConfig:
    model: str = "yolo11n.pt"
    confidence: float = 0.45
    iou: float = 0.45
    image_size: int = 640
    device: str = "auto"
    enabled: bool = True
    classes: list[str] = field(default_factory=lambda: ["person", "bicycle", "car", "motorcycle", "bus", "truck", "chair"])


@dataclass
class NavigationConfig:
    zones: int = 5
    collision_corridor_width: float = 0.34
    collision_corridor_bottom: float = 0.98
    collision_corridor_top: float = 0.52
    risk_threshold: float = 42.0
    stop_threshold: float = 78.0
    emergency_threshold: float = 92.0


@dataclass
class DistanceConfig:
    critical: float = 2.0
    near: float = 4.0
    caution: float = 6.0
    reference_object_height_m: float = 1.5
    focal_length_px: float = 700.0


@dataclass
class SteeringConfig:
    max_angle: float = 60.0
    sensitivity: float = 1.0
    smoothing: float = 0.72
    min_command_duration_s: float = 0.35
    base_speed: float = 70.0


@dataclass
class TrackingConfig:
    max_missing_frames: int = 12
    match_iou: float = 0.25
    approach_window: int = 8


@dataclass
class LoggingConfig:
    enabled: bool = True
    directory: str = "logs"


@dataclass
class UIConfig:
    update_ms: int = 33
    show_debug: bool = True
    show_trajectory: bool = True
    show_zones: bool = True


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    distance: DistanceConfig = field(default_factory=DistanceConfig)
    steering: SteeringConfig = field(default_factory=SteeringConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)


def _merge_dataclass(instance: Any, values: dict[str, Any]) -> Any:
    for key, value in values.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
    return instance


def load_config(path: Path) -> AppConfig:
    """Load a YAML file, falling back to safe defaults if it is absent."""
    config = AppConfig()
    if not path.exists() or yaml is None:
        return config
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    for name in ("camera", "detection", "navigation", "distance", "steering", "tracking", "logging", "ui"):
        section = getattr(config, name)
        _merge_dataclass(section, raw.get(name, {}))
    config.navigation.zones = 3 if config.navigation.zones == 3 else 5
    return config
