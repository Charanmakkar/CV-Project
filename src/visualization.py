"""OpenCV overlays for the ADAS-style camera view."""

from __future__ import annotations

from typing import Any

from .models import FrameAnalysis


class FrameVisualizer:
    COLORS = {
        "green": (70, 220, 110), "yellow": (40, 220, 240), "orange": (0, 150, 255),
        "red": (50, 60, 240), "cyan": (220, 220, 30), "white": (240, 240, 240),
        "muted": (110, 130, 145), "blue": (230, 100, 40),
    }

    def render(self, analysis: FrameAnalysis, zone_names: list[str], show_zones: bool = True, show_trajectory: bool = True, debug: bool = True) -> Any:
        import cv2
        frame = analysis.frame.copy()
        height, width = frame.shape[:2]
        overlay = frame.copy()
        if show_zones:
            for index in range(len(zone_names) + 1):
                x = int(width * index / len(zone_names))
                cv2.line(overlay, (x, 0), (x, height), self.COLORS["muted"], 1)
            frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)
            for index, name in enumerate(zone_names):
                x = int(width * (index + 0.5) / len(zone_names))
                self._text(frame, name, (x - 40, 24), self.COLORS["white"], 0.48)
        corridor_half = int(width * 0.17)
        corridor_top = int(height * 0.52)
        pts = [(width // 2 - corridor_half, corridor_top), (width // 2 + corridor_half, corridor_top), (width - 12, height - 12), (12, height - 12)]
        corridor_color = self.COLORS["red"] if analysis.decision.action in ("STOP", "EMERGENCY STOP") else self.COLORS["yellow"]
        cv2.polylines(frame, [self._as_points(pts)], True, corridor_color, 2)
        self._text(frame, "PROJECTED COLLISION CORRIDOR", (width // 2 - 140, corridor_top - 10), corridor_color, 0.45)
        if show_trajectory:
            points = self._trajectory(width, height, analysis.decision.angle_deg, 30)
            path_color = self.COLORS["green"] if analysis.decision.action == "STRAIGHT" else corridor_color
            cv2.polylines(frame, [self._as_points(points)], False, path_color, 4)
            for x_offset in (-26, 26):
                shifted = [(x + x_offset, y) for x, y in points]
                cv2.polylines(frame, [self._as_points(shifted)], False, path_color, 1)
        for detection in analysis.detections:
            x, y, w, h = detection.bbox
            color = self.COLORS["red"] if detection.risk_score >= 70 else self.COLORS["orange"] if detection.risk_score >= 40 else self.COLORS["green"]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cx, cy = detection.center
            cv2.circle(frame, (cx, cy), 4, self.COLORS["white"], -1)
            distance = f"{detection.distance_m:.1f}m est." if detection.distance_m is not None else "n/a"
            ident = f"{detection.label.upper()} #{detection.track_id or '-'}"
            label = f"{ident} {detection.confidence * 100:.0f}% | {detection.proximity.value} | {distance}"
            self._label(frame, label, (x, max(32, y - 8)), color)
        self._hud(frame, analysis, debug)
        return frame

    @staticmethod
    def _as_points(points: list[tuple[int, int]]) -> Any:
        import numpy as np
        return np.array(points, dtype=np.int32).reshape((-1, 1, 2))

    @staticmethod
    def _trajectory(width: int, height: int, angle: float, count: int) -> list[tuple[int, int]]:
        import math
        curve = angle / 60.0
        return [(int(width / 2 + curve * width * 0.40 * (i / (count - 1)) ** 1.7 + math.sin(i / (count - 1) * math.pi) * curve * width * .03), int(height * .98 - height * .44 * i / (count - 1))) for i in range(count)]

    def _hud(self, frame: Any, analysis: FrameAnalysis, debug: bool) -> None:
        import cv2
        height, width = frame.shape[:2]
        cv2.line(frame, (width // 2 - 14, height // 2), (width // 2 + 14, height // 2), self.COLORS["cyan"], 1)
        cv2.line(frame, (width // 2, height // 2 - 14), (width // 2, height // 2 + 14), self.COLORS["cyan"], 1)
        action_color = self.COLORS["red"] if "STOP" in analysis.decision.action else self.COLORS["yellow"] if "TURN" in analysis.decision.action else self.COLORS["green"]
        self._label(frame, f"NAV: {analysis.decision.action} | STEERING {analysis.decision.angle_deg:+.1f}°", (18, 42), action_color, scale=0.68)
        self._text(frame, f"STATE  {analysis.decision.state.value}   OBJECTS {len(analysis.detections)}   FPS {analysis.fps:.1f}", (18, height - 40), self.COLORS["white"], 0.5)
        if debug:
            self._text(frame, f"MODEL {analysis.model_status}   INFERENCE {analysis.inference_ms:.1f} ms   {analysis.timestamp}", (18, height - 18), self.COLORS["muted"], 0.45)

    def _label(self, frame: Any, text: str, origin: tuple[int, int], color: tuple[int, int, int], scale: float = 0.48) -> None:
        import cv2
        x, y = origin
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        cv2.rectangle(frame, (x, y - th - 8), (x + tw + 8, y + 4), (14, 22, 28), -1)
        cv2.putText(frame, text, (x + 4, y - 2), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)

    def _text(self, frame: Any, text: str, origin: tuple[int, int], color: tuple[int, int, int], scale: float) -> None:
        import cv2
        cv2.putText(frame, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)

