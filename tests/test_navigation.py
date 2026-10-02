from types import SimpleNamespace

from src.decision_engine import DecisionEngine
from src.models import Detection, NavigationState, Proximity
from src.occupancy_analyzer import OccupancyAnalyzer
from src.steering_controller import SteeringController
from src.wheel_controller import WheelController
from src.zone_analyzer import ZoneAnalyzer


def nav_config(zones=5):
    return SimpleNamespace(zones=zones, risk_threshold=42.0, stop_threshold=78.0, emergency_threshold=92.0, collision_corridor_width=0.34, collision_corridor_top=0.52)


def steering_config():
    return SimpleNamespace(max_angle=60.0, smoothing=0.0, min_command_duration_s=0.0)


def detection(label="car", zone=2, risk=80, proximity=Proximity.NEAR):
    item = Detection(label, 0.92, (100, 300, 160, 180), zone=zone, risk_score=risk, proximity=proximity)
    return item


def test_empty_scene_goes_straight():
    assessment = OccupancyAnalyzer(nav_config()).assess([])
    result = DecisionEngine(nav_config()).decide([], assessment)
    assert result.action == "STRAIGHT"
    assert result.state == NavigationState.PATH_CLEAR


def test_center_threat_selects_lower_risk_left_side():
    items = [detection(zone=2, risk=88), detection(zone=3, risk=20), detection(zone=4, risk=10)]
    assessment = OccupancyAnalyzer(nav_config()).assess(items)
    result = DecisionEngine(nav_config()).decide(items, assessment)
    assert assessment.left_risk < assessment.right_risk
    assert result.action == "TURN LEFT"
    assert result.angle_deg < 0


def test_blocked_lateral_corridors_stop():
    items = [detection(zone=0, risk=95, proximity=Proximity.CRITICAL), detection(zone=2, risk=96, proximity=Proximity.CRITICAL), detection(zone=4, risk=95, proximity=Proximity.CRITICAL)]
    assessment = OccupancyAnalyzer(nav_config()).assess(items)
    result = DecisionEngine(nav_config()).decide(items, assessment)
    assert result.action == "EMERGENCY STOP"
    assert result.state == NavigationState.EMERGENCY_STOP


def test_zone_boundaries_are_deterministic():
    analyzer = ZoneAnalyzer(nav_config())
    assert analyzer.zone_for_x(0, 1000) == 0
    assert analyzer.zone_for_x(199, 1000) == 0
    assert analyzer.zone_for_x(200, 1000) == 1
    assert analyzer.zone_for_x(999, 1000) == 4


def test_wheel_differential_drive_sign_convention():
    wheels = WheelController(70.0)
    left = wheels.command(-40, "TURN LEFT")
    right = wheels.command(40, "TURN RIGHT")
    assert left.left < left.right
    assert right.right < right.left
    assert wheels.command(0, "STOP").left == 0


def test_steering_controller_clamps_to_configured_limit():
    controller = SteeringController(steering_config())
    angle, action = controller.update(120, "TURN RIGHT")
    assert angle == 60.0
    assert action == "TURN RIGHT"

