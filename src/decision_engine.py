"""Deterministic, explainable scene-level navigation decisions."""

from __future__ import annotations

from typing import Any

from .models import Detection, NavigationDecision, NavigationState, Proximity


class DecisionEngine:
    def __init__(self, navigation_config: Any, steering_config: Any | None = None) -> None:
        self.config = navigation_config
        self.steering_config = steering_config

    def decide(self, detections: list[Detection], assessment: Any) -> NavigationDecision:
        threat = max(detections, key=lambda d: d.risk_score, default=None)
        if threat is None or threat.risk_score < self.config.risk_threshold:
            return NavigationDecision(
                action="STRAIGHT", angle_deg=0.0,
                reason="No high-risk object is blocking the projected collision corridor.",
                primary_threat=threat, assessment=assessment, state=NavigationState.PATH_CLEAR,
            )
        if not assessment.safe_route:
            emergency = threat.proximity == Proximity.CRITICAL and threat.risk_score >= self.config.emergency_threshold
            state = NavigationState.EMERGENCY_STOP if emergency else NavigationState.STOPPED
            action = "EMERGENCY STOP" if emergency else "STOP"
            reason = "Both lateral corridors carry high cumulative risk; no safe route is available."
            return NavigationDecision(action, 0.0, reason, threat, assessment, state, 0.98)
        side = assessment.selected_side
        # Left is negative; right is positive. Risk and proximity scale the correction.
        strength = min(1.0, max(0.2, threat.risk_score / 100.0))
        if threat.proximity == Proximity.CRITICAL:
            strength = max(strength, 0.88)
        max_angle = getattr(self.steering_config, "max_angle", 60.0)
        angle = round((1 if side == "RIGHT" else -1) * max_angle * strength, 1)
        action = "TURN RIGHT" if side == "RIGHT" else "TURN LEFT"
        state = NavigationState.TURN_RIGHT if side == "RIGHT" else NavigationState.TURN_LEFT
        reason = (
            f"{threat.label.title()} is {threat.proximity.value.lower()} in the {side.lower()}-blocking scene. "
            f"The {side.lower()} side has the lower cumulative corridor risk "
            f"({assessment.left_risk:.0f}% left vs {assessment.right_risk:.0f}% right)."
        )
        return NavigationDecision(action, angle, reason, threat, assessment, state, min(1.0, threat.confidence))
